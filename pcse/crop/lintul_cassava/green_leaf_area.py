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
                    k.TRANRF * np.exp(-p.NLAI * (1 - k.NPKI)))  # m2 m-2 d-1

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

# -------------------------------------------------------------------------------------------------#
# FUNCTION gla
#
# Author:       Rob van den Beuken
# Copyright:    Copyright 2019, PPS
# Email:        rob.vandenbeuken@wur.nl
# Date:         29-01-2019
#
# This file contains a component of the LINTUL-CASSAVA_NPK model. The purpose of this function is to
# compute daily increase of the LAI.
#
# --------------------------------------------------------------------------------------------------#
# class green_leaf_area_old():
#
#     def __init__(self, DTEFF, TSUMCROP, LAII, RGRL, SLA, LAI, GLV, TSUMLA_MIN, TRANRF, WC, WCWP, RWCUTTING, FLV,
#                 LAIEXPOEND, DORMANCY, NLAI=1, NPKI=1, delt = 1):
#
#         # Growth during maturation stage
#         GLAI= SLA * GLV * (1 - DORMANCY)  # m2 m-2 d-1
#
#         # Growth during juvenile stage, the growth can be reduced due to nutrient limitation.
#         if (TSUMCROP < TSUMLA_MIN) &  (LAI < LAIEXPOEND):
#             GLAI = (((LAI * (np.exp(RGRL * DTEFF * delt) - 1) / delt) + abs(RWCUTTING) * FLV * SLA) *
#                     TRANRF * np.exp(-NLAI * (1 - NPKI)))  # m2 m-2 d-1
#
#         # Growth at day of seedling emergence
#         if (TSUMCROP > 0) & (LAI == 0) & (WC > WCWP):
#             GLAI = LAII / delt  # m2 m-2 d-1
#
#         # Growth before seedling emergence
#         if (TSUMCROP == 0):
#             GLAI = 0  # m2 m-2 d-1
#         self.GLAI = GLAI

