from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

class fibrous_root_growth(SimulationObject):

    class Parameters(ParamTemplate):
        ROOTDI = Float()
        ROOTDM = Float()
        RRDMAX = Float()
        SMW = Float()

    class RateVariables(RatesTemplate):
        RRD = Float()

    class StateVariables(StatesTemplate):
        RD = Float()

    def initialize(self, day, kiosk, parvalues):
        self.kiosk = kiosk
        self.params = self.Parameters(parvalues)
        k = self.kiosk
        p = self.params
        RD = p.ROOTDI
        self.rates = self.RateVariables(kiosk,
                                        publish = ["RRD"])
        self.states = self.StateVariables(kiosk,
                                          publish = ["RD"],
                                          RD = RD)

    def calc_rates(self,  day, drv, delt=1):
        # If the soil water content drops to, or below, wilting point fibrous root growth stops.
        # Root growth continues till the maximum rooting depth is reached.
        # The rooting depth (m) is calculated from a maximum rate of change in rooting depth,
        # the emergence of the crop and the constraints mentioned above.

        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        if (s.RD-p.ROOTDM < 0) & (k.SM-p.SMW >= 0):
            RRD = p.RRDMAX * k.EMERG  # mm d-1
        else:
            RRD = 0

        r.RRD = RRD

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.RD += r.RRD * delt
