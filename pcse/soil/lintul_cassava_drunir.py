# -*- coding: utf-8 -*-
# Herman Berghuijs (herman.berghuijs@wur.nl), Allard de Wit (allard.dewit@wur.nl), Tom Schut (tom.schut@wur.nl)
# February 2026

# -------------------------------------------------------------------------------------------------#
# FUNCTION drunir
#
# Author:       Rob van den Beuken
# Copyright:    Copyright 2019, PPS
# Email:        rob.vandenbeuken@wur.nl
# Date:         29-01-2019
#
# This file contains a component of the LINTUL-CASSAVA_NPK model. The purpose of this function is to
# compute rates of drainage, runoff and irrigation.
#
# --------------------------------------------------------------------------------------------------#

class drunir():
    """
    Class to simulate the rates of drainage, surface-runoff, and irrigation

    The rate of irrigation is a fraction of the amount of water that needs to be applied to bring the soil moisture c
    content back to field capacity. Excess water (i.e. difference between amount of water in soil and amount of water
    at field capacity) is removed by drainage with a maximum daily rate DRATE (cm d-1). If drainage alone cannot bring
    the soil moisture content back to field capacity, the remaining excess water is removed by surface runoff with a
    daily rate RUNOFF.

    This class is a Python implementation of the calculations related to drainage, surface-runoff, and irrigation in
    the R function drunir in the R version of the model LINTUL Cassava NPK (Adiele et al., 2022; Ezui et al., 2018).

    Authors drunir:                  Rob van den Beuken
    Authors Python implementation:   Herman Berghuijs, Allard de Wit, Tom Schut

    References:
    Adiele J.G., Schut A.G.T., Ezui K.S., Giller K.E. (2022) LINTUL-Cassava-NPK: A simulation
    model for nutrient-limited cassava growth. Field Crops Research 281: ARTN 108488

    Ezui K.S., Leffelaar P.A., Franke A.C., Mando A., Giller K.E. (2018) Simulating drought impact
    and mitigation in cassava using the LINTUL model. Field Crops Research 219: 256-272.
    https://doi.org/10.1016/j.fcr.2018.01.033
    """

    def __init__(self, RAIN, RNINTC, EVAP, TRAN, IRRIGF, DRATE, DELT, WA, ROOTD, WCFC, WCST):
        # Soil water content
        WC = WA / ROOTD # cm3 cm-3
        # The amount of soil water at air dryness (AD) and field capacity (FC).
        WAFC = WCFC * ROOTD  # cm
        WAST = WCST * ROOTD  # cm

        # Drainage below the root zone occurs when the amount of water in the soil exceeds field capacity
        # or when the amount of rainfall in excess of interception and evapotranspiration fills up soil
        # water above field capacity.
        DRAIN = min(DRATE,
                    max((WA - WAFC) / DELT + (RAIN - (RNINTC + EVAP + TRAN)), 0)
                    )

        # Surface runoff occurs when the amount of soil water exceeds total saturation or when the amount
        # of rainfall in excess of interception, evapotranspiration and drainage fills up soil water
        # above total saturation.
        RUNOFF = max(0, (WA - WAST) / DELT + (RAIN - (RNINTC + EVAP + TRAN + DRAIN)))  # cm d-1

        # The irrigation rate is the extra amount of water that is needed to keep soil water at a fraction
        # of field capacity that is defined by setting the parameter IRRIGF. If IRRIGF is set to 1, the
        # soil will be irrigated every timestep to keep the amount of water in the soil at field capacity.
        # IRRIGF = 0 implies rainfed conditions.
        IRRIG = IRRIGF * max(0, (WAFC - WA) / DELT - (RAIN - (RNINTC + EVAP + TRAN + DRAIN + RUNOFF)))  # cm d-1

        self.DRAIN = DRAIN
        self.RUNOFF = RUNOFF
        self.IRRIG = IRRIG