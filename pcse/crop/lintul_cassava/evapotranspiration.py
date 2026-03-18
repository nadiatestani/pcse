# -*- coding: utf-8 -*-
# Herman Berghuijs (herman.berghuijs@wur.nl), Allard de Wit (allard.dewit@wur.nl), Tom Schut (tom.schut@wur.nl)
# February 2026

from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float
import numpy as np

class evapotranspiration(SimulationObject):
    """
    Class to simulate potential and actual transpiration and soil evaporation in LINTUL Cassava.
    
    The class first calculates the rates op potential transpiration and soil evaporation from the reference
    evapotranspiration, the rain interception and the soil moisture content. Next it calculates the
    critical soil moisture contents above which drought stress occurs or above which oxygen stress
    occurs. This is used to calculate both the actual transpiration and actual soil evaporation
    rates. Finally, a transpiration reduction factor is calculated.     
    
   **Simulation parameters**

    =================  ==============================================  ======  ===========================
    Name               Description                                     Type     Unit
    =================  ==============================================  ======  ===========================    
    SMFCF              Soil moisture content at field capacity         SCr      cm3 water cm-2 ground
    SM0                Soil moisture content at saturation             SCr      cm3 water cm-2 ground
    SMW                Soil moisture content at wilting point          SCr      cm3 water cm-2 ground
    TRANCO             Transpiration constant that indicates the 
                       level of drought tolerance                      SCr      cm3 water cm-2 ground d-1
    TWCSD              Ratio of soil moisture content at extreme
                       drought and the soil moisture content at 
                       wilting point.                                  SCr      cm3 water cm3 water
    WCAD               Soil moisture content at air dry                SCr      cm3 water cm-3 ground
    WCWET              Soil moisture content above which oxygen stress
                       occurs                                          SCr      cm3 water cm-3 ground
    =================  ==============================================  ======  ===========================    
    
   **State variables**

    None

   **Rate variables**

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    EVWMX              Maximum evaporation rate of an open water
                       surface                                         Y       cm3 water cm-2 ground d-1
    EVSMX              Maximum soil evaporation rate                   N       cm3 water cm-2 ground d-1
    RPEVAP             Potential soil evaporation rate                 N       cm3 water cm-2 ground d-1
    RPTRAN             Potential transpiration rate                    N       cm3 water cm-2 ground d-1
    TRA                Actual transpiration rate                       Y       cm3 water cm-2 ground d-1

   **Auxillary variables**

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    RFTRA              Transpiration reduction factor                  Y       cm3 water cm-3 water
    WCCR               Critical soil moisture content below which
                       drought stress can occur                        Y       cm3 water cm-3 ground
    WCSD               Soil moisture content at severe drought         Y       cm3 water cm-3 ground
    =================  ==============================================  ======  ===========================


    """
    
    class Parameters(ParamTemplate):
        TRANCO = Float()
        TWCSD = Float()
        WCAD = Float()
        SMFCF = Float()
        SM0 = Float()
        WCWET = Float()
        SMW = Float()

    class RateVariables(RatesTemplate):
        RPEVAP = Float()
        RPTRAN = Float()
        EVSMX = Float()
        EVWMX = Float()
        TRA = Float()
        RFTRA = Float()
        WCCR = Float()
        WCSD = Float()

    class StateVariables(StatesTemplate):
        pass

    def initialize(self, day, kiosk, parameters):
        self.kiosk = kiosk
        self.params = self.Parameters(parameters)
        self.rates = self.RateVariables(kiosk,
                                        publish = ["EVSMX", "TRA", "RFTRA", "WCCR", "WCSD", "EVWMX"])
        self.states = self.StateVariables(
            kiosk,
            publish=[]
        )

    def __call__(self, day, drv, delt = 1):
        # The actual evaporation and transpiration is based on the soil moisture contents and the potential evaporation
        # and transpiration rates.
        k = self.kiosk
        p = self.params
        r = self.rates

        # The amount of soil water at air dryness (AD) and field capacity (FC).
        WAAD = p.WCAD * k.RD  # mm
        WAFC = p.SMFCF * k.RD  # mm

        # Evaporation is decreased when water content is below field capacity,
        # but continues until WC = WCAD. It is ensured to stay within 0-1 range
        limit_evap = (k.SM - p.WCAD) / (p.SMFCF - p.WCAD)  # (-)
        limit_evap = min(1, max(0, limit_evap))  # (-)

        # Potential evaporation and transpiration are weighed by a factor representing the plant canopy (exp(-0.5 * LAI)).
        RPEVAP = np.exp(-0.5 * k.LAI) * drv.ES0 # cm d-1
        RPTRAN = (1 - np.exp(-0.5 * k.LAI)) * drv.ET0 # cm d-1
        RPTRAN = max(0, RPTRAN - 0.5 * k.RNINTC)  # cm d-1

        # Maximum evaporation from an open water surface (cm). It is not used by the native soil water balance of LINTUL
        # Cassava, but other soil water balances in PCSE require this as input from evapotranspiration modules.
        REVAPW = drv.E0

        EVAP = RPEVAP * limit_evap  # mm d-1

        # Water content at severe drought
        WCSD = p.SMW * p.TWCSD
        # Critical water content
        WCCR = p.SMW + max(WCSD - p.SMW, RPTRAN / (RPTRAN + p.TRANCO) * (p.SMFCF - p.SMW))

        # If water content is below the critical soil water content a correction factor is calculated
        # that reduces the transpiration until it stops at WC = WCWP.
        FR = (k.SM - p.SMW) / (WCCR - p.SMW)  # (-)

        # If water content is above the critical soil water content a correction factor is calculated
        # that reduces the transpiration when the crop is hampered by waterlogging (WC > WCWET).
        FRW = (p.SM0 - k.SM) / (p.SM0 - p.WCWET)  # (-)

        # Replace values for wet days with a higher water content than the critical water content.
        if k.SM > WCCR:
            # Original R code: FR[WC > WCCR] = FRW[WC > WCCR]  # (-)
            FR = FRW

        # Ensure to stay within the 0-1 range
        FR = min(1, max(0, FR))  # (-)

        # Actual transpiration
        TRAN = RPTRAN * FR  # mm d-1

        # A final correction term is calculated to reduce evaporation and transpiration when evapotranspiration exceeds
        # the amount of water in soil present in excess of air dryness.
        aux = EVAP + TRAN  # mm d-1
        if aux <= 0:
            # Original R code: aux[aux <= 0] = 1  # mm d-1
            aux = 1

        W = k.SM * k.RD
        AVAILF = min(1, (W - WAAD) / (delt * aux))  # mm
        TRAN = TRAN * AVAILF
        EVAP = EVAP * AVAILF

        # The transpiration reduction factor is defined as the ratio between actual and potential transpiration
        if RPTRAN <= 0:
            RFTRA = 1
        else:
            RFTRA = TRAN / RPTRAN

        # Soil moisture content at severe drought and the critical soil moisture content are calculated to see if
        # drought stress occurs in the crop. The critical soil moisture content depends on the transpiration coefficient
        # which is a measure of how drought resistant the crop is.
        WCSD = p.SMW * p.TWCSD
        WCCR = p.SMW + max(WCSD-p.SMW, (RPTRAN / (RPTRAN + p.TRANCO) * (p.SMFCF-p.SMW)))

        r.RPEVAP = RPEVAP
        r.RPTRAN = RPTRAN

        r.EVWMX = REVAPW
        r.EVSMX = EVAP
        r.TRA = TRAN
        r.RFTRA = RFTRA
        r.WCCR = WCCR
        r.WCSD = WCSD