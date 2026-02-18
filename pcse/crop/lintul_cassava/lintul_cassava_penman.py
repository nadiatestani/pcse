from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float
import numpy as np
import datetime as dt

hPa_to_kPa = 1e-1
J_to_MJ = 1e-6
mm_to_cm = 1e-1
cm_to_mm = 1e1

class penman(SimulationObject):
    class Parameters(ParamTemplate):
        pass

    class StateVariables(StatesTemplate):
        pass

    class RateVariables(RatesTemplate):
        ES0 = Float()
        ET0 = Float()

    def initialize(self, day, kiosk, parameters):
        self.kiosk = kiosk
        self.params = self.Parameters(parameters)
        self.rates = self.RateVariables(kiosk,
                                        publish = ["ES0", "ET0"])
        self.states = self.StateVariables(
            kiosk,
            publish=[],
        )

    def __call__(self, day, drv, delt = 1):
        # Potential evaporation and transpiration are calculated using the Penman equation.
        k = self.kiosk
        p = self.params
        r = self.rates

        # Determine weather conditions
        DAVTMP = drv.TEMP
        DTR = drv.IRRAD * J_to_MJ
        VP = drv.VAP * hPa_to_kPa
        WN = drv.WIND

        DTRJM2 = DTR * 1E6  # J m-2 d-1     :    Daily radiation in Joules
        BOLTZM = 5.668E-8  # J m-1 s-1 K-4 :    Stefan-Boltzmann constant
        LHVAP = 2.4E6  # J kg-1        :    Latent heat of vaporization
        PSYCH = 0.067  # kPa deg. C-1  :    Psychrometric constant

        BBRAD = BOLTZM * (DAVTMP + 273) ** 4 * 86400  # J m-2 d-1   :     Black body radiation
        SVP = 0.611 * np.exp(17.4 * DAVTMP / (DAVTMP + 239))  # kPa         :     Saturation vapour pressure
        SLOPE = 4158.6 * SVP / (DAVTMP + 239) ** 2  # kPa dec. C-1:     Change of SVP per degree C
        RLWN = BBRAD * max(0, 0.55 * (1 - VP / SVP))  # J m-2 d-1   :     Net outgoing long-wave radiation
        WDF = 2.63 * (1.0 + 0.54 * WN)  # kg m-2 d-1  :     Wind function in the Penman equation

        # Net radiation (J m-2 d-1) for soil (1) and crop (2)
        NRADS = DTRJM2 * (1 - 0.15) - RLWN  # (1)
        NRADC = DTRJM2 * (1 - 0.25) - RLWN  # (2)

        # Radiation terms (J m-2 d-1) of the Penman equation for soil (1) and crop (2)
        PENMRS = NRADS * SLOPE / (SLOPE + PSYCH)  # (1)
        PENMRC = NRADC * SLOPE / (SLOPE + PSYCH)  # (2)

        # Drying power term (J m-2 d-1) of the Penman equation
        PENMD = LHVAP * WDF * (SVP - VP) * PSYCH / (SLOPE + PSYCH)

        # Reference evapotranspiration for bare soil (ES0) and crop (ET0)
        ES0 = (PENMRS + PENMD) / LHVAP * mm_to_cm  # cm d-1
        ET0 = (PENMRC + PENMD) / LHVAP * mm_to_cm  # cm d-1

        r.ES0 = ES0
        r.ET0 = ET0