from pcse.soil.lintul_cassava_drunir import drunir
from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

cm_to_mm = 1e1
J_to_MJ = 1e-6
m2_to_ha = 1e-4
hPa_to_kPa = 1e-1
kg_to_g = 1000
ha_to_m2 = 10000

class soil_water_dynamics_PP(SimulationObject):

    class Parameters(ParamTemplate):
        SMFCF = Float()
        ROOTDM = Float()
        ROOTDI = Float()

    class StateVariables(StatesTemplate):
        W = Float()
        SM = Float()

    class RateVariables(RatesTemplate):
        pass

    def initialize(self, day, kiosk, parameters):
        self.kiosk = kiosk
        self.rates = self.RateVariables(kiosk, publish = [])
        self.params = self.Parameters(parameters)
        p = self.params
        W = 1000. * p.ROOTDI * p.SMFCF
        SM = 0.001 * W / p.ROOTDI
        self.states = self.StateVariables(kiosk,
                                          publish = ["SM", "W"],
                                          W = W,
                                          SM = SM
                                          )
    def calc_rates(self, day, drv):
        pass

    def integrate(self, day, drv):
        k = self.kiosk
        p = self.params
        s = self.states
        W = 1000. * k.RD * p.SMFCF
        SM = 0.001 * W / k.RD
        s.W = W
        s.SM = SM

class soil_water_dynamics(SimulationObject):

    class Parameters(ParamTemplate):
        DRATE = Float()
        FRACRNINTC = Float()
        IRRIGF = Float()
        RRDMAX = Float()
        ROOTDI = Float()
        TRANCO = Float()
        WCAD = Float()
        SMFCF = Float()
        WCI = Float()
        SM0 = Float()
        SMW = Float()
        WCWET = Float()

    class StateVariables(StatesTemplate):
        W = Float()
        SM = Float()
        DRAIN = Float()
        RUNOFF = Float()

    class RateVariables(RatesTemplate):
        RWA = Float()
        RTRAIN = Float()
        EXPLOR = Float()
        RIRRIG = Float()
        RDRAIN = Float()
        RRUNOFF = Float()

    def initialize(self, day, kiosk, parameters):
        self.kiosk = kiosk
        self.rates = self.RateVariables(kiosk, publish = [])
        self.params = self.Parameters(parameters)
        p = self.params
        W = 1000. * p.ROOTDI * p.SMFCF
        SM = 0.001 * W / p.ROOTDI
        WCCR = p.SMW
        self.states = self.StateVariables(kiosk,
                                          publish = ["W", "SM"],
                                          W = W,
                                          SM = SM,
                                          TRAN = 0.,
                                          EVAP = 0.,
                                          PTRAN = 0.,
                                          PEVAP = 0.,
                                          RUNOFF = 0.,
                                          DRAIN = 0.,
                                          WCCR=WCCR
        )
    def calc_rates(self, day, drv, delt = 1):
        p = self.params
        r = self.rates
        s = self.states
        k = self.kiosk
        if "EMERG" in k.keys():
            ROOTD = k.RD
            RROOTD = k.RRD
        else:
            ROOTD = p.ROOTDI
            RROOTD = 0.

        p = self.params
        s = self.states
        r = self.rates

        # Determine weather conditions
        RTRAIN = drv.RAIN * cm_to_mm / delt             # mm d-1           : rain rate

        # ----------------------------------------WATER BALANCE---------------------------------------------#
        # Explored water of new soil water layers by the roots, explored soil is assumed to have a FC soil moisture
        # content).
        EXPLOR = 1000 * RROOTD * p.SMFCF  # mm d-1

        # Drainage and Runoff is calculated using the drunir function.
        dr = drunir(RTRAIN, k.RNINTC, k.REVAP, k.RTRAN, p.IRRIGF, p.DRATE, delt, s.W, ROOTD, p.SMFCF, p.SM0)
        RDRAIN = dr.DRAIN
        RRUNOFF = dr.RUNOFF
        RIRRIG = dr.IRRIG

        # Rate of change of soil water amount
        RWA = (RTRAIN + EXPLOR + RIRRIG) - (k.RNINTC + RRUNOFF + k.RTRAN + k.REVAP + RDRAIN)  # mm d-1

        r.RWA = RWA
        r.EXPLOR = EXPLOR

    def integrate(self, day, drv, delt = 1):
        k = self.kiosk
        r = self.rates
        s = self.states

        s.W += r.RWA
        s.SM = 0.001 * s.W / k.RD
        s.RUNOFF += delt * r.RRUNOFF
        s.DRAIN += delt * r.RDRAIN