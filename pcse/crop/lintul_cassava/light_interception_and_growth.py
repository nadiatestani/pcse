import numpy as np
from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float
from pcse.util import AfgenTrait

J_to_MJ = 1e-6

class light_interception_and_growth(SimulationObject):

    class Parameters(ParamTemplate):
        FPAR = Float()
        K_EXT = Float()
        LUE_OPT = Float()
        TTB = AfgenTrait()

    class RateVariables(RatesTemplate):
        GTOTAL = Float()
        RPAR = Float()

    class StateVariables(StatesTemplate):
        PAR = Float()

    def initialize(self, day, kiosk, parvalues, delt = 1.):
        PAR = 0.
        self.params = self.Parameters(parvalues)
        self.rates = self.RateVariables(kiosk,
                                        publish = ["GTOTAL"])
        self.states = self.StateVariables(kiosk,
                                          publish = ["PAR"],
                                          PAR = PAR)

    def calc_rates(self,  day, drv, delt = 1.):
        p = self.params
        r = self.rates
        k = self.kiosk

        DTR = drv.IRRAD * J_to_MJ
        RPAR = p.FPAR * DTR

        # Light interception and total crop growth rate.
        PARINT = RPAR * (1 - np.exp(-p.K_EXT * k.LAI))  # MJ m-2 d-1

        TEMPRF = p.TTB(drv.TEMP)
        LUE = p.LUE_OPT * TEMPRF # g DM m-2 d-1

        # When water stress is more severe or nutrient is stress is more severe
        if k.TRANRF <= k.NPKI:
            GTOTAL = LUE * PARINT * k.TRANRF * (1 - k.DORMANCY)  # g DM m-2 d-1
        else:
            GTOTAL = LUE * PARINT * k.NPKI * (1 - k.DORMANCY)  # g DM m-2 d-1

        r.RPAR = RPAR
        r.GTOTAL = GTOTAL

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.PAR += r.RPAR