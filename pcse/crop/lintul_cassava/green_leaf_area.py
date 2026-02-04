import numpy as np
from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

class green_leaf_area(SimulationObject):

    class Parameters(ParamTemplate):
        FR_MAX = Float()
        LAII = Float()
        NLAI = Float()
        RGRL = Float()
        LAIEXPOEND = Float()
        TSUMLA_MIN = Float()
        SMW = Float()

    class RateVariables(RatesTemplate):
        RLAI = Float()

    class StateVariables(StatesTemplate):
        LAI = Float()

    def initialize(self, day, kiosk, parvalues):
        self.kiosk = kiosk
        self.params = self.Parameters(parvalues)
        LAI = 0.

        self.states = self.StateVariables(kiosk,
                                          publish = ["LAI"],
                                          LAI = 0.)
        self.rates = self.RateVariables(kiosk, publish = [])

    def calc_rates(self,  day, drv, delt=1):
        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        # Green leaf weight
        GLV = k.FLV * (k.GTOTAL + abs(k.RWCUTTING)) + k.RREDISTLVG * k.PUSHREDIST  # g green leaves DM m-2 d-1

        # Growth during maturation stage
        GLAI= k.SLA * GLV * (1 - k.DORMANCY)  # m2 m-2 d-1

        # Growth during juvenile stage, the growth can be reduced due to nutrient limitation.
        if (k.TSUMCROP < p.TSUMLA_MIN) &  (s.LAI < p.LAIEXPOEND):
            GLAI = (((s.LAI * (np.exp(p.RGRL * k.DTEFF * delt) - 1) / delt) + abs(k.RWCUTTING) * k.FLV * k.SLA) *
                    k.RFTRA * np.exp(-p.NLAI * (1 - k.NPKI)))  # m2 m-2 d-1

        # Growth at day of seedling emergence
        if (k.TSUMCROP > 0) & (k.LAI == 0) & (k.SM > p.SMW):
            GLAI = p.LAII / delt  # m2 m-2 d-1

        # Growth before seedling emergence
        if (k.TSUMCROP == 0):
            GLAI = 0  # m2 m-2 d-1

        # Change in LAI due to new growth of leaves
        RLAI = GLAI - k.DLAI  # m2 m-2 d-1

        # ---------------------------------------------SET RATES----------------------------------------------------#
        r.RLAI = RLAI

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.LAI += r.RLAI

