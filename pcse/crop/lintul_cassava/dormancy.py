from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

class dormancy(SimulationObject):

    class Parameters(ParamTemplate):
        DELREDIST = Float()
        LAI_MIN = Float()
        RECOV = Float()
        RRREDISTSO = Float()
        SO2LV = Float()
        TSUMSBR = Float()
        TSUMREDISTMAX = Float()
        WSOREDISTFRACMAX = Float()
        WLVGNEWN = Float()
        SMW = Float()

    class RateVariables(RatesTemplate):
        RDORMTSUM = Float()
        RPUSHDORMRECTSUM = Float()
        RPUSHREDISTENDTSUM = Float()
        RDORMTIME = Float()
        RREDISTLVG = Float()
        RREDISTSO = Float()
        RPUSHREDISTSUM = Float()
        DORMANCY = Float()
        PUSHREDIST = Float()

    class StateVariables(StatesTemplate):
        DORMTSUM = Float()
        PUSHDORMRECTSUM = Float()
        PUSHREDISTENDTSUM = Float()
        DORMTIME = Float()
        REDISTLVG = Float()
        REDISTSO = Float()
        PUSHREDISTSUM = Float()

    def initialize(self, day, kiosk, parvalues):
        self.kiosk = kiosk
        self.params = self.Parameters(parvalues)
        self.rates = self.RateVariables(kiosk,
                                        publish = ["DORMANCY",
                                                   "PUSHREDIST",
                                                   "RREDISTLVG",
                                                   "RREDISTSO"])

        DORMTSUM = 0.
        PUSHDORMRECTSUM = 0.
        PUSHREDISTENDTSUM = 0.
        DORMTIME = 0.
        REDISTLVG = 0.
        REDISTSO = 0.
        PUSHREDISTSUM = 0.
        self.states = self.StateVariables(kiosk,
                                          publish = [],
                                          DORMTSUM=DORMTSUM,
                                          PUSHDORMRECTSUM=PUSHDORMRECTSUM,
                                          PUSHREDISTENDTSUM=PUSHREDISTENDTSUM,
                                          DORMTIME=DORMTIME,
                                          REDISTLVG=REDISTLVG,
                                          REDISTSO=REDISTSO,
                                          PUSHREDISTSUM=PUSHREDISTSUM
                                          )

    def calc_rates(self, day, drv, delt=1):
        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        # The crop enters the dormancy phase as the soil water content is lower than the soil water content at
        # severe drought and as the LAI is lower than the minimal LAI.
        if (k.SM-k.WCSD <= 0)  & (k.LAI - p.LAI_MIN <= 0):
            dormancy = 1
        else:
            dormancy = 0

        # # The crop goes out of dormancy if the water content is higher than a certain recovery water content and as the
        # # water content is larger than the wilting point soil moisture content.
        if (k.SM - p.RECOV * k.WCCR >= 0) & (k.SM - p.SMW >= 0):
            pushdor = 1
        else:
            pushdor = 0

        # # The redistributed fraction of storage root DM to the leaves.
        if k.WSO == 0:
            WSOREDISTFRAC = 1
        else:
            WSOREDISTFRAC = s.REDISTSO / k.WSO

        # Three push functions are used to determine the redistribution and recovery from dormancy, a final function DORMANCY
        # is used to indicate if the crop is still in dormancy:
        # (1) PUSHREDISTEND: The activation of the PUSHREDISTEND function ends the redistribution phase. Redistribution stops
        # when the redistributed fraction reached the maximum redistributed fraction or when the minimum amount of new leaves
        # is produced after dormancy or when the Tsum during the recovery exceeds the maximum redistribution temperature sum.
        # (2) PUSHREDIST: The activation of the PUSHREDIST function ends the dormancy phase including the delay temperature
        # sum needed for the redistribution of DM.
        # (3) PUSHDORMREC: Indicates if the the crop is still in dormancy. Dormancy can only when the temperature sum of the
        # crop exceeds the temperature sum of the branching.
        if WSOREDISTFRAC - p.WSOREDISTFRACMAX >= 0:
            PUSHREDISTEND1 = 1
        else:
            PUSHREDISTEND1 = 0

        if s.REDISTLVG - p.WLVGNEWN  >= 0:
            PUSHREDISTEND2 = 1
        else:
            PUSHREDISTEND2 = 0

        if s.PUSHREDISTSUM - p.TSUMREDISTMAX >= 0:
            PUSHREDISTEND3 = 1
        else:
            PUSHREDISTEND3 = 0

        if -s.PUSHREDISTSUM >= 0:
            PUSHREDISTEND4 = 0
        else:
            PUSHREDISTEND4 = 1

        PUSHREDISTEND = max(max([PUSHREDISTEND1, PUSHREDISTEND2]), PUSHREDISTEND3 * PUSHREDISTEND4)

        if s.PUSHDORMRECTSUM - p.DELREDIST >= 0:
            PUSHREDIST1 = 1
        else:
            PUSHREDIST1 = 0

        PUSHREDIST2 = (1- PUSHREDISTEND)
        PUSHREDIST = PUSHREDIST1 * PUSHREDIST2

        if -s.DORMTSUM >= 0:
            PUSHDORMREC1 = 0
        else:
            PUSHDORMREC1 = 1

        if k.TSUMCROP - p.TSUMSBR >= 0:
            PUSHDORMREC2 = 1
        else:
            PUSHDORMREC2 = 0

        PUSHDORMREC = pushdor * PUSHDORMREC1 * (1 - PUSHREDIST) * PUSHDORMREC2

        if k.TSUMCROP - p.TSUMSBR >= 0:
            DORMANCY1 = 1
        else:
            DORMANCY1 = 0

        DORMANCY = max(dormancy, PUSHDORMREC) * (1 - PUSHREDIST) * DORMANCY1 # (-)

        # The temperature sums related to the dormancy and recovery periods.
        RDORMTSUM = k.DTEFF * DORMANCY - (s.DORMTSUM / delt) * PUSHREDIST  # Deg. C
        RPUSHDORMRECTSUM = k.DTEFF * PUSHDORMREC - (s.PUSHDORMRECTSUM / delt) * (1 - PUSHDORMREC) * (1 - PUSHREDIST)  # Deg. C
        RPUSHREDISTSUM = k.DTEFF * PUSHREDIST - (s.PUSHREDISTSUM / delt) * PUSHREDISTEND  # Deg. C
        RPUSHREDISTENDTSUM = k.DTEFF * PUSHREDIST - (s.PUSHREDISTENDTSUM / delt) * (1 - PUSHREDISTEND)  # Deg. C

        # No. of days in dormancy
        RDORMTIME = DORMANCY  # d

        if -s.DORMTSUM >= 0:
            RREDISTSO1 = 0
        else:
            RREDISTSO1 = 1

        # Dry matter redistribution after dormancy. The rate of redistribution of the storage roots dry matter to
        # leaf dry matter. A certain fraction is lost for the conversion of storage organs dry matter to leaf dry
        # matter.
        RREDISTSO = p.RRREDISTSO * k.WSO * PUSHREDIST - (s.REDISTSO / delt) * RREDISTSO1  # g DM m-2 d-1
        RREDISTLVG = p.SO2LV * RREDISTSO * (1- DORMANCY)  # g DM m-2 d-1
        RREDISTMAINTLOSS = (1 - p.SO2LV) * RREDISTSO  # g DM m-2 d-1

        r.RDORMTSUM = RDORMTSUM
        r.RPUSHDORMRECTSUM = RPUSHDORMRECTSUM
        r.RPUSHREDISTENDTSUM = RPUSHREDISTENDTSUM
        r.RDORMTIME = RDORMTIME
        r.RREDISTLVG = RREDISTLVG
        r.RREDISTSO = RREDISTSO
        r.RPUSHREDISTSUM = RPUSHREDISTSUM

        r.DORMANCY = DORMANCY
        r.PUSHREDIST = PUSHREDIST

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.DORMTSUM += delt * r.RDORMTSUM
        s.PUSHDORMRECTSUM += delt * r.RPUSHDORMRECTSUM
        s.PUSHREDISTENDTSUM += delt * r.RPUSHREDISTENDTSUM
        s.DORMTIME += delt * r.RDORMTIME
        s.REDISTLVG += delt * r.RREDISTLVG
        s.REDISTSO += delt * r.RREDISTSO
        s.PUSHREDISTSUM += delt * r.RPUSHREDISTSUM
        pass

class dormancy_old():
    def __init__(self, k, p, s):

        # The crop enters the dormancy phase as the soil water content is lower than the soil water content at
        # severe drought and as the LAI is lower than the minimal LAI.
        if (k.WC-k.WCSD <= 0)  & (s.LAI - p.LAI_MIN <= 0):
            dormancy = 1
        else:
            dormancy = 0

        # # The crop goes out of dormancy if the water content is higher than a certain recovery water content and as the
        # # water content is larger than the wilting point soil moisture content.
        if (k.WC - p.RECOV * k.WCCR >= 0) & (k.WC - p.WCWP >= 0):
            pushdor = 1
        else:
            pushdor = 0

        # # The redistributed fraction of storage root DM to the leaves.
        if s.WSO == 0:
            WSOREDISTFRAC = 1
        else:
            WSOREDISTFRAC = s.REDISTSO / s.WSO

        # Three push functions are used to determine the redistribution and recovery from dormancy, a final function DORMANCY
        # is used to indicate if the crop is still in dormancy:
        # (1) PUSHREDISTEND: The activation of the PUSHREDISTEND function ends the redistribution phase. Redistribution stops
        # when the redistributed fraction reached the maximum redistributed fraction or when the minimum amount of new leaves
        # is produced after dormancy or when the Tsum during the recovery exceeds the maximum redistribution temperature sum.
        # (2) PUSHREDIST: The activation of the PUSHREDIST function ends the dormancy phase including the delay temperature
        # sum needed for the redistribution of DM.
        # (3) PUSHDORMREC: Indicates if the the crop is still in dormancy. Dormancy can only when the temperature sum of the
        # crop exceeds the temperature sum of the branching.
        if WSOREDISTFRAC - p.WSOREDISTFRACMAX >= 0:
            PUSHREDISTEND1 = 1
        else:
            PUSHREDISTEND1 = 0

        if s.REDISTLVG - p.WLVGNEWN  >= 0:
            PUSHREDISTEND2 = 1
        else:
            PUSHREDISTEND2 = 0

        if s.PUSHREDISTSUM - p.TSUMREDISTMAX >= 0:
            PUSHREDISTEND3 = 1
        else:
            PUSHREDISTEND3 = 0

        if -s.PUSHREDISTSUM >= 0:
            PUSHREDISTEND4 = 0
        else:
            PUSHREDISTEND4 = 1

        PUSHREDISTEND = max(max([PUSHREDISTEND1, PUSHREDISTEND2]), PUSHREDISTEND3 * PUSHREDISTEND4)

        if s.PUSHDORMRECTSUM - p.DELREDIST >= 0:
            PUSHREDIST1 = 1
        else:
            PUSHREDIST1 = 0

        PUSHREDIST2 = (1- PUSHREDISTEND)
        PUSHREDIST = PUSHREDIST1 * PUSHREDIST2

        if -s.DORMTSUM >= 0:
            PUSHDORMREC1 = 0
        else:
            PUSHDORMREC1 = 1

        if k.TSUMCROP - p.TSUMSBR >= 0:
            PUSHDORMREC2 = 1
        else:
            PUSHDORMREC2 = 0

        PUSHDORMREC = pushdor * PUSHDORMREC1 * (1 - PUSHREDIST) * PUSHDORMREC2

        if k.TSUMCROP - p.TSUMSBR >= 0:
            DORMANCY1 = 1
        else:
            DORMANCY1 = 0

        DORMANCY = max(dormancy, PUSHDORMREC) * (1 - PUSHREDIST) * DORMANCY1 # (-)

        # The temperature sums related to the dormancy and recovery periods.
        RDORMTSUM = k.DTEFF * DORMANCY - (s.DORMTSUM / p.DELT) * PUSHREDIST  # Deg. C
        RPUSHDORMRECTSUM = k.DTEFF * PUSHDORMREC - (s.PUSHDORMRECTSUM / p.DELT) * (1 - PUSHDORMREC) * (1 - PUSHREDIST)  # Deg. C
        RPUSHREDISTSUM = k.DTEFF * PUSHREDIST - (s.PUSHREDISTSUM / p.DELT) * PUSHREDISTEND  # Deg. C
        RPUSHREDISTENDTSUM = k.DTEFF * PUSHREDIST - (s.PUSHREDISTENDTSUM / p.DELT) * (1 - PUSHREDISTEND)  # Deg. C

        # No. of days in dormancy
        RDORMTIME = DORMANCY  # d

        if -s.DORMTSUM >= 0:
            RREDISTSO1 = 0
        else:
            RREDISTSO1 = 1

        # Dry matter redistribution after dormancy. The rate of redistribution of the storage roots dry matter to
        # leaf dry matter. A certain fraction is lost for the conversion of storage organs dry matter to leaf dry
        # matter.
        RREDISTSO = p.RRREDISTSO * s.WSO * PUSHREDIST - (s.REDISTSO / p.DELT) * RREDISTSO1  # g DM m-2 d-1
        RREDISTLVG = p.SO2LV * RREDISTSO * (1- DORMANCY)  # g DM m-2 d-1
        RREDISTMAINTLOSS = (1 - p.SO2LV) * RREDISTSO  # g DM m-2 d-1

        self.DORMANCY = DORMANCY
        self.PUSHREDIST = PUSHREDIST
        self.RDORMTSUM = RDORMTSUM
        self.RPUSHDORMRECTSUM = RPUSHDORMRECTSUM
        self.RPUSHREDISTSUM = RPUSHREDISTSUM
        self.RPUSHREDISTENDTSUM = RPUSHREDISTENDTSUM
        self.RDORMTIME = RDORMTIME
        self.RREDISTSO = RREDISTSO
        self.RREDISTLVG = RREDISTLVG
