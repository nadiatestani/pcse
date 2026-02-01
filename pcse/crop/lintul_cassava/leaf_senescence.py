from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float
from pcse.util import AfgenTrait

class leaf_senescence(SimulationObject):

    class Parameters(ParamTemplate):
        FRACTLLFENHSH = Float()
        FRACSLATB = AfgenTrait()
        FASTRANSLSO = Float()
        LAICR = Float()
        RDRB = Float()
        RDRNS = Float()
        RDRT = AfgenTrait()
        RDRSHM = Float()
        SLA_MAX = Float()
        TSUMLLIFE = Float()
        WCWET = Float()

    class RateVariables(RatesTemplate):
        DLAI = Float()
        DLV = Float()
        RTSUMCROPLEAFAGE = Float()
        RWLVD = Float()
        RWSOFASTRANSLSO = Float()
        SLA = Float()

    class StateVariables(StatesTemplate):
        TSUMCROPLEAFAGE = Float()
        WLVD = Float()
        WSOFASTRANSLSO = Float()

    def initialize(self, day, kiosk, parameters):
        TSUMCROPLEAFAGE = 0.
        WLVD = 0.
        WSOFASTRANSLSO = 0.
        self.kiosk = kiosk
        self.params = self.Parameters(parameters)
        self.rates = self.RateVariables(kiosk,
                                        publish = [
                                            "DLAI",
                                            "DLV",
                                            "RTSUMCROPLEAFAGE",
                                            "RWLVD",
                                            "RWSOFASTRANSLSO",
                                            "SLA"])
        self.states = self.StateVariables(
            kiosk,
            publish=["WLVD"],
            TSUMCROPLEAFAGE = TSUMCROPLEAFAGE,
            WLVD = WLVD,
            WSOFASTRANSLSO = WSOFASTRANSLSO
        )

    def calc_rates(self,  day, drv, delt=1):
        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        # -------- AGE
        # The calculation of the physiological leaf age.
        RTSUMCROPLEAFAGE = k.DTEFF * k.EMERG - (s.TSUMCROPLEAFAGE / delt) * k.PUSHREDIST  # Deg. C

        # Relative death rate due to aging depending on leaf age and the daily average temperature.
        if s.TSUMCROPLEAFAGE - p.TSUMLLIFE >= 0:
            RDRDV = p.RDRT(drv.TEMP)
        else:
            RDRDV = 0

        # -------- SHEDDING
        # Relative death rate due to self shading, depending on a critical leaf area index at which leaf shedding is
        # induced. Leaf shedding is limited to a maximum leaf shedding per day.
        RDRSH1 = p.RDRSHM * (k.LAI-p.LAICR) / p.LAICR  # d-1

        if (RDRSH1 < 0):
            RDRSH = 0  # d-1
        elif RDRSH1 >= p.RDRSHM:
            RDRSH = p.RDRSHM  # d-1
        else:
            RDRSH = RDRSH1

        # -------- DROUGHT
        # ENSHED triggers enhanced leaf senescence due to severe drought or excessive soil water. It assumes that drought or
        # excessive water does not affect young leaves. It only affects leaves that have a reached a given fraction of the leaf
        # age.
        if k.SM - k.WCSD >= 0:
            ENHSHED1 = 0
        else:
            ENHSHED1 = 1

        if k.SM - p.WCWET >= 0:
            ENHSHED2 = 1
        else:
            ENHSHED2 = 0

        if (s.TSUMCROPLEAFAGE - p.FRACTLLFENHSH * p.TSUMLLIFE) >= 0:
            ENHSHED3 = 1
        else:
            ENHSHED3 = 0

        ENHSHED = max(ENHSHED1, ENHSHED2) * ENHSHED3

        # Relative death rate due to severe drought
        RDRSD = p.RDRB * ENHSHED  # d-1
        # --------

        # -------- NUTRIENT LIMITATION
        # Leaf death due to nutrient limitation is added on top op the relative death rate due to age, shade
        # and drought.
        RDRNS = p.RDRNS * (1-k.NPKI)  # d-1
        # --------

        # Effective relative death rate and the resulting decrease in LAI. Leaf death can only occur, when
        # the leaves are old enough.
        if s.TSUMCROPLEAFAGE - p.TSUMLLIFE >= 0:
            RDR = (max(RDRDV, RDRSH, RDRSD) + RDRNS)
        else:
            RDR = 0.

        DLAI = k.LAI * RDR * (1 - k.DORMANCY)  # m2 m-2 d-1

        # Fraction of the maximum specific leaf area index depending on the temperature sum of the crop. And its specific leaf
        # area index.
        FRACSLACROPAGE = p.FRACSLATB(k.TSUMCROP)
        SLA = p.SLA_MAX * FRACSLACROPAGE  # m2 g-1 DM

        # The rate of storage root DM production with DM supplied by the leaves before abscission.
        RWSOFASTRANSLSO = k.WLVG * RDR * p.FASTRANSLSO * (1 - k.DORMANCY)  # g storage root DM m-2 d-1

        # Decrease in leaf weight due to leaf senesence.
        DLV = k.WLVG * RDR * (1 - k.DORMANCY)  # g leaves DM m-2 d-1
        RWLVD = (DLV - RWSOFASTRANSLSO)  # g leaves DM m-2 d-1

        r.DLAI = DLAI
        r.DLV = DLV
        r.RTSUMCROPLEAFAGE = RTSUMCROPLEAFAGE
        r.RWLVD = RWLVD
        r.RWSOFASTRANSLSO = RWSOFASTRANSLSO
        r.SLA = SLA

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.WLVD += r.RWLVD
        s.WSOFASTRANSLSO += r.RWSOFASTRANSLSO
        s.TSUMCROPLEAFAGE += r.RTSUMCROPLEAFAGE