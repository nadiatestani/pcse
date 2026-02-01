from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

class fibrous_root_growth(SimulationObject):

    class Parameters(ParamTemplate):
        ROOTDI = Float()
        ROOTDM = Float()
        RRDMAX = Float()
        SMW = Float()

    class RateVariables(RatesTemplate):
        RROOTD = Float()

    class StateVariables(StatesTemplate):
        ROOTD = Float()

    def initialize(self, day, kiosk, parvalues):
        self.kiosk = kiosk
        self.params = self.Parameters(parvalues)
        k = self.kiosk
        p = self.params
        ROOTD = p.ROOTDI
        self.rates = self.RateVariables(kiosk,
                                        publish = ["RROOTD"])
        self.states = self.StateVariables(kiosk,
                                          publish = ["ROOTD"],
                                          ROOTD = ROOTD)

    def calc_rates(self,  day, drv, delt=1):
        # If the soil water content drops to, or below, wilting point fibrous root growth stops.
        # Root growth continues till the maximum rooting depth is reached.
        # The rooting depth (m) is calculated from a maximum rate of change in rooting depth,
        # the emergence of the crop and the constraints mentioned above.

        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        if (s.ROOTD-p.ROOTDM < 0) & (k.SM-p.SMW >= 0):
            RROOTD = p.RRDMAX * k.EMERG  # mm d-1
        else:
            RROOTD = 0

        r.RROOTD = RROOTD

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.ROOTD += r.RROOTD * delt
