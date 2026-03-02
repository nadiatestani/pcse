# -*- coding: utf-8 -*-
# Herman Berghuijs (herman.berghuijs@wur.nl), Allard de Wit (allard.dewit@wur.nl), Tom Schut (tom.schut@wur.nl)
# February 2026

from pcse.base import SimulationObject, ParamTemplate, RatesTemplate, StatesTemplate, ParameterProvider
from traitlets_pcse import Float

class canopy_rain_interception(SimulationObject):
    """Class to simulate  rain interception by the canopy in the LINTUL Cassava model

    Simulates the daily amount of rain water that is intercepted by the canopy. Depending on the precipitation rate,
    the canopy either intercepts all rain water or it participates a maximum amount per unit of leaf area index.

    ** Simulation parameters **
    ==============  ==============================================  ======  ===============================
     Name           Description                                     Type     Unit
    ==============  ==============================================  ======  ===============================
    FRACRNINTC      Maximum daily amount of water that can be
                    intercepted by the canopy per unit of leaf
                    area index                                      SCr     cm water m2 ground m-2 leaf d-1
    ==============  ==============================================  ======  ===============================

    ** Rate variables **

    ==============  ==============================================  ======  ===============================
     Name           Description                                     Pbl     Unit
    ==============  ==============================================  ======  ===============================
    RNINTC          Rate of rain interception by the canopy         Y        cm water d-1
    ==============  ==============================================  ======  ===============================

    ** Auxillary variables **

    None

    ** State variables **

    None

    This class is a Python implementation of the calculations related to rain interception by the canopy in the
    R function LINTUL2_CASSAVA_NPK in the R version of the model LINTUL Cassava NPK (Adiele et al.,
    2022; Ezui et al., 2018)

    Authors LINTUL2_CASSAVA_NPK:     Rob van den Beuken, Joy Adiele, Tom Schut
    Authors Python implementation:   Herman Berghuijs, Allard de Wit, Tom Schut

    References:
    Adiele J.G., Schut A.G.T., Ezui K.S., Giller K.E. (2022) LINTUL-Cassava-NPK: A simulation
    model for nutrient-limited cassava growth. Field Crops Research 281: ARTN 108488.
    https://doi.org/10.1007/s13593-020-00649-w

    Ezui K.S., Leffelaar P.A., Franke A.C., Mando A., Giller K.E. (2018) Simulating drought impact
    and mitigation in cassava using the LINTUL model. Field Crops Research 219: 256-272.
    https://doi.org/10.1016/j.fcr.2018.01.033
    """

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

        # Interception of the canopy, depends on the amount of rainfall and the LAI.
        RTRAIN = drv.RAIN / delt  # cm d-1           : rain rate
        RNINTC = min(RTRAIN, (p.FRACRNINTC * k.LAI))  # cm d-1
        r.RNINTC = RNINTC

    def integrate(self, day, drv, delt = 1):
        pass


