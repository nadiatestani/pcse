# -*- coding: utf-8 -*-
# Herman Berghuijs (herman.berghuijs@wur.nl), Allard de Wit (allard.dewit@wur.nl), Tom Schut (tom.schut@wur.nl)
# February 2026

import numpy as np
from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

class green_leaf_area(SimulationObject):
    """
    Class to simulate the growth of green leaf area index.

    The class calculates the growth of the leaf area index from crop emergence. Its growth can be reduced
    by both water stress and nutrient stress.

    ** Simulation parameters **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Type     Unit
    =================  ==============================================  ======  ===========================
    NLAI               Coefficient for the reduction of leaf area
                       growth due to nutrient stress                   SCr     -
    LAIEXPOEND         Leaf area index below which the exponential
                       growth stage ends                               SCr     m2 leaf m-2 ground
    LAII               Leaf area index at emergence                    SCr     m2 leaf m-2 ground
    RGRL               Temperature dependent relative growth rate
                       leaf area index during juvenile stage           SCr     m2 leaf m-2 ground |C|-1
    SMW                Soil moisture content at permanent wilting
                       point                                           SCr     cm3 water cm-3 ground
    TSUMLA_MIN         Temperature sum above which the exponential
                       growth stage ends                               SCr     |C| d
    =================  ==============================================  ======  ===========================

    ** Rate parameters **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    RLAI               Growth rate of leaf area index                  N       m2 leaf m-2 ground d-1
    =================  ==============================================  ======  ===========================

    ** State variables **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    LAI                Leaf area index                                 Y       m2 leaf m-2 ground
    =================  ==============================================  ======  ===========================

    This class is a Python implementation of the calculations related to the dynamics of the green leaf
    area in the R function LINTUL2_CASSAVA_NPK in the R version of the model LINTUL Cassava NPK (Adiele et al.,
    2022; Ezui et al., 2018)

    Authors LINTUL2_CASSAVA_NPK:     Rob van den Beuken, Joy Adiele, Tom Schut
    Authors Python implementation:   Herman Berghuijs, Allard de Wit, Tom Schut

    References:
    Adiele J.G., Schut A.G.T., Ezui K.S., Giller K.E. (2022) LINTUL-Cassava-NPK: A simulation
    model for nutrient-limited cassava growth. Field Crops Research 281: ARTN 108488

    Ezui K.S., Leffelaar P.A., Franke A.C., Mando A., Giller K.E. (2018) Simulating drought impact
    and mitigation in cassava using the LINTUL model. Field Crops Research 219: 256-272.
    https://doi.org/10.1016/j.fcr.2018.01.033

    """

    class Parameters(ParamTemplate):
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
        LAII = 0.
        self.states = self.StateVariables(kiosk,
                                          publish = ["LAI"],
                                          LAI = LAII)
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

