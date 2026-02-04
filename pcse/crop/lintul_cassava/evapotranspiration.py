from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

m_to_mm = 1e3

class evapotranspiration(SimulationObject):
    class Parameters(ParamTemplate):
        TRANCO = Float()
        TWCSD = Float()
        WCAD = Float()
        SMFCF = Float()
        SM0 = Float()
        WCWET = Float()
        SMW = Float()

    class RateVariables(RatesTemplate):
        REVAP = Float()
        RTRAN = Float()
        TRANRF = Float()
        WCCR = Float()
        WCSD = Float()

    class StateVariables(StatesTemplate):
        pass

    def initialize(self, day, kiosk, parameters):
        self.kiosk = kiosk
        self.params = self.Parameters(parameters)
        self.rates = self.RateVariables(kiosk,
                                        publish = ["REVAP", "RTRAN", "TRANRF", "WCCR", "WCSD"])
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
        WAAD = m_to_mm * p.WCAD * k.RD  # mm
        WAFC = m_to_mm * p.SMFCF * k.RD  # mm

        # Evaporation is decreased when water content is below field capacity,
        # but continues until WC = WCAD. It is ensured to stay within 0-1 range
        limit_evap = (k.SM - p.WCAD) / (p.SMFCF - p.WCAD)  # (-)
        limit_evap = min(1, max(0, limit_evap))  # (-)
        EVAP = k.RPEVAP * limit_evap  # mm d-1

        # Water content at severe drought
        WCSD = p.SMW * p.TWCSD
        # Critical water content
        WCCR = p.SMW + max(WCSD - p.SMW, k.RPTRAN / (k.RPTRAN + p.TRANCO) * (p.SMFCF - p.SMW))

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

        # Actual transpration
        TRAN = k.RPTRAN * FR  # mm d-1

        # A final correction term is calculated to reduce evaporation and transpiration when evapotranspiration exceeds
        # the amount of water in soil present in excess of air dryness.
        aux = EVAP + TRAN  # mm d-1
        if aux <= 0:
            # Original R code: aux[aux <= 0] = 1  # mm d-1
            aux = 1

        AVAILF = min(1, (k.W - WAAD) / (delt * aux))  # mm
        TRAN = TRAN * AVAILF
        EVAP = EVAP * AVAILF

        # The transpiration reduction factor is defined as the ratio between actual and potential transpiration
        if k.RPTRAN <= 0:
            TRANRF = 1
        else:
            TRANRF = TRAN / k.RPTRAN

        # Soil moisture content at severe drought and the critical soil moisture content are calculated to see if
        # drought stress occurs in the crop. The critical soil moisture content depends on the transpiration coefficient
        # which is a measure of how drought resistant the crop is.
        WCSD = p.SMW * p.TWCSD
        WCCR = p.SMW + max(WCSD-p.SMW, (k.RPTRAN / (k.RPTRAN + p.TRANCO) * (p.SMFCF-p.SMW)))

        r.REVAP = EVAP
        r.RTRAN = TRAN
        r.TRANRF = TRANRF
        r.WCCR = WCCR
        r.WCSD = WCSD