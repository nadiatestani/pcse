from pcse.base import SimulationObject, ParamTemplate, RatesTemplate, StatesTemplate, ParameterProvider
from traitlets_pcse import Float

class canopy_rain_interception(SimulationObject):
    class Parameters(ParamTemplate):
        FRACRNINTC = Float()

    class RateVariables(RatesTemplate):
        RNINTC = Float()

    class StateVariables(StatesTemplate):
        pass

    def initialize(self, day, kiosk, parvalues):
        self.kiosk = kiosk
        self.params = self.Parameters(parvalues)
        self.rates = self.RateVariables(kiosk,
                                        publish = ["RNINTC"])
        self.states = self.StateVariables(kiosk,
                                          publish = [])

    def calc_rates(self,  day, drv, delt=1):
        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        # Interception of the canopy, depends on the amount of rainfall and the LAI.
        RTRAIN = drv.RAIN / delt  # cm d-1           : rain rate
        RNINTC = min(RTRAIN, (p.FRACRNINTC * k.LAI))  # cm d-1
        r.RNINTC = RNINTC

    def integrate(self, day, drv, delt = 1):
        pass


