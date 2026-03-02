# -*- coding: utf-8 -*-
# Herman Berghuijs (herman.berghuijs@wur.nl), Allard de Wit (allard.dewit@wur.nl), Tom Schut (tom.schut@wur.nl)
# February 2026

from pcse.traitlets import Float
from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate

class phenology(SimulationObject):
    """
    Class to simulate phenology

    This class simulates the phenology of the crop from its emergence. Phenology is quantified as a temperature sum.
    The crop emerges if 1) the soil moisture content is above the permanent wilting point and 2) the crop is sown and
    fulfilled the thermal requirement to emergence after it has been planted.

    ** Simulation parameters **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Type    Unit
    =================  ==============================================  ======  ===========================
    OPTEMERGTSUM       Temperature sum from sowing to emergence in
                       absence of water stress                         SCr     |C| d
    TBASE              Temperature below which there is no development
                       possible                                        SCr     |C|
    SMW                Soil moisture content at permanent wilting
                       point.                                          SCr     cm3 water cm-3 soil
    =================  ==============================================  ======  ===========================

    ** State variables

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    TSUM               Temperature sum from sowing.                    Y       |C| d
    TSUMCROP           Temperature sum from emergence                  Y       |C| d
    =================  ==============================================  ======  ===========================

    ** Rate variables

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    RTSUM              Rate of increase of temperature sum from
                       sowing.                                         N       |C|
    RTSUMCROP          Rate of increase of temperature sum from
                       emergence                                       N       |C|
    =================  ==============================================  ======  ===========================

    ** Auxillary variables

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    EMERG              Indicates whether (=1) or not (=0) the crop
                       has been emerged.                               Y       -
    DTEFF              Effective temperature for development           Y       |C|
    =================  ==============================================  ======  ===========================

    This class is a Python implementation of the calculations related to the growth of phenology in the R function
    LINTUL2_CASSAVA_NPK in the R version of the model LINTUL Cassava NPK (Adiele et al., 2022; Ezui et al., 2018)

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
