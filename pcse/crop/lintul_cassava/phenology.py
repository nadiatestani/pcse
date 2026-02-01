from pcse.traitlets import Float
from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate

class phenology(SimulationObject):
    class Parameters(ParamTemplate):
        OPTEMERGTSUM = Float()
        TBASE = Float()
        SMW = Float()

    class RateVariables(RatesTemplate):
        RTSUM = Float()
        RTSUMCROP = Float()
        DTEFF = Float()

    class StateVariables(StatesTemplate):
        EMERG = Float()
        TSUM = Float()
        TSUMCROP = Float()

    def initialize(self, day, kiosk, parameters):
        EMERG = 0.
        TSUM = 0.
        TSUMCROP = 0.

        self.kiosk = kiosk
        self.params = self.Parameters(parameters)
        self.rates = self.RateVariables(kiosk,
                                        publish = ["DTEFF"])
        self.states = self.StateVariables(
            kiosk,
            publish=["EMERG", "TSUM", "TSUMCROP"],
            EMERG = EMERG,
            TSUM = TSUM,
            TSUMCROP = TSUMCROP
        )

    def calc_rates(self, day, drv, delt=1):
        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        DTEFF = max(0, drv.TEMP - p.TBASE)      # Deg. C           : effective daily temperature

        # -----------------------------------------EMERGENCE-----------------------------------------------#
        # emergence occurs (1) when the temperature sum exceeds the temperature sum needed for emergence. And (2)
        # when enough water is available in the soil.
        if (k.SM-p.SMW >= 0) & (k.TSUM-p.OPTEMERGTSUM >= 0):
            emerg1 = 1
        else:
            emerg1 = 0

        # once the crop is established is does not disappear again
        if s.TSUMCROP > 0:
            emerg2 = 1
        else:
            emerg2 = 0

        EMERG = max(emerg1, emerg2)  # (-)
        RTSUM = DTEFF / delt

        # Emergence of the crop is used to calculate the temperature sum of the crop.
        RTSUMCROP = DTEFF * EMERG  # Deg. C

        r.DTEFF = DTEFF
        r.RTSUM = RTSUM
        r.RTSUMCROP = RTSUMCROP

        s.EMERG = EMERG

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.TSUM += r.RTSUM
        s.TSUMCROP += r.RTSUMCROP
