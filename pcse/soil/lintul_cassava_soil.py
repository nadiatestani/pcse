# -*- coding: utf-8 -*-
# Herman Berghuijs (herman.berghuijs@wur.nl), Allard de Wit (allard.dewit@wur.nl), Tom Schut (tom.schut@wur.nl)
# March 2026

from pcse.soil.lintul_cassava_drunir import drunir
from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

J_to_MJ = 1e-6
m2_to_ha = 1e-4
hPa_to_kPa = 1e-1
kg_to_g = 1000
ha_to_m2 = 10000

class soil_water_dynamics_PP(SimulationObject):
    """
    Class to simulate soil water dynamics under potential growth condition

    This class simulates a fake water balance in which the soil moisture content is always at field capacity. It is
    used to run LINTUL Cassava under not-water limiting conditions.

    ** Simulation parameters **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Type    Unit
    =================  ==============================================  ======  ===========================
    RDI                Initial rooting depth                           SCr     cm3 water cm-2 ground d-1
    RDMSOL             Maximum rooting depth                           SCr     cm soil
    SMFCF              Soil moisture content at field capacity         SCr     m3 water m-3 soil
    =================  ==============================================  ======  ===========================

    ** State variables **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    SM                 Soil moisture content in rooted soil            Y       cm3 water cm-3 ground
    W                  Amount of water in rooted soil                  Y       cm3 water cm-2 ground
    =================  ==============================================  ======  ===========================

    The original R version of LINTUL Cassava did not have an independent soil water module for non-water-limited
    growth conditions (Ezui et al., 2018; Adiele et al., 2022). Instead, it assumed that irrigation was applied to
    bring the soil moisture content back to field capacity at any day that the soil moisture content would otherwise
    drop below field capacity. The disadvantage of this approach is that it makes oxygen stress more likely,
    especially when the difference between the soil moisture content at field capacity and the soil moisture content
    above which oxygen stress occurs is small. Indeed, the simulations for potential growth with the original R version
    showed that oxygen stress did occur at various days at some locations. Since we think that the terms "potential
    growth" and "non-water limited growth" do not only apply that there is no drought stress but also no oxygen stress
    due to excess water, we decided not to follow the methodology of the R version of simulating non-water limited
    growth.

    References:
    Adiele J.G., Schut A.G.T., Ezui K.S., Giller K.E. (2022) LINTUL-Cassava-NPK: A simulation
    model for nutrient-limited cassava growth. Field Crops Research 281: ARTN 108488.
    https://doi.org/10.1007/s13593-020-00649-w

    Ezui K.S., Leffelaar P.A., Franke A.C., Mando A., Giller K.E. (2018) Simulating drought impact
    and mitigation in cassava using the LINTUL model. Field Crops Research 219: 256-272.
    https://doi.org/10.1016/j.fcr.2018.01.033
    """

    class Parameters(ParamTemplate):
        SMFCF = Float()
        RDMSOL = Float()
        RDI = Float()

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
        W = p.RDMSOL * p.SMFCF
        SM = W / p.RDMSOL
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
        W = k.RD * p.SMFCF
        SM = W / k.RD
        s.W = W
        s.SM = SM

class soil_water_dynamics(SimulationObject):
    """
    Class to simulate soil water dynamics

    This class simulate the amount of water and the soil moisture content and the rooted soil. Sources for water are
    1) effective precipitation, 2) exploration, and 3) irrigation. Sinks for water are 1) root water uptake, 2) soil
    evaporation 3) drainage, and 4) surface-runoff. The depth of the rooted soil can increase due to root growth.

    ** Simulation parameters **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Type    Unit
    =================  ==============================================  ======  ===========================
    DRATE              Maximum drainage rate                           SCr     cm d-1
    IRRIGF             Faction of amount of water that is applied by
                       irrigation and the amount of water that is
                       necessary to bring the soil moisture content
                       to its value at field capacity.                 SCr     -
    RDI                Initial rooted soil depth                       SCr     cm soil
    RRDMAX             Maximum depth of rooted soil                    SCr     cm soil
    SM0                Soil moisture content at saturation             SCr     cm3 water cm-3 soil
    SMFCF              Soil moisture content at field capacity         SCr     cm3 water cm-3 soil
    SMW                Soil moisture content at wilting point          SCr     cm3 water cm-3 soil
    WCWET              Soil moisture content above which oxygen stress
                       can occur.                                      SCr     cm3 water cm-3 soil
    =================  ==============================================  ======  ===========================

    ** State variables **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    DRAIN              Total amount of water lost by drainage          N       cm3 water cm-2 ground
    RUNOFF             Total amount of water lost by surface-runoff    N       cm3 water cm-2 ground
    SM                 Soil moisture content                           Y       cm3 water cm-3 soil
    W                  Amount of water in rooted soil                  Y       cm3 water cm-2 ground
    =================  ==============================================  ======  ===========================

    ** Rate variables **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl     Unit
    =================  ==============================================  ======  ===========================
    EVS                Rate of change of water in rooted soil due to
                       transpiration and soil evaporation              N       cm3 water cm-2 ground d-1
    EXPLOR             Rate of change of water in rooted soil due to
                       exploration by roots                            N       cm3 water cm-2 ground d-1
    RDRAIN             Drainage rate                                   N       cm3 water cm-2 ground d-1
    RIRRIG             Irrigation rate                                 N       cm3 water cm-2 ground d-1
    RRUNOFF            Surface-runoff rate                             N       cm3 water cm-2 ground d-1
    RWA                Rate of change of water in rooted soil          N       cm3 water cm-2 ground d-1
    RTRAIN             Precipitation rate                              N       cm3 water cm-2 ground d-1
    =================  ==============================================  ======  ===========================

    This class is a Python implementation of the calculations related to soil water dynamics in the R function
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
        DRATE = Float()
        IRRIGF = Float()
        RRDMAX = Float()
        RDI = Float()
        WCAD = Float()
        SMFCF = Float()
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
        EVS = Float()
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
        W = p.RDI * p.SMFCF
        SM = W / p.RDI
        WCCR = p.SMW
        self.states = self.StateVariables(kiosk,
                                          publish = ["W", "SM"],
                                          W = W,
                                          SM = SM,
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
        RTRAIN = drv.RAIN / delt             # cm d-1           : rain rate

        # ----------------------------------------WATER BALANCE---------------------------------------------#
        # Explored water of new soil water layers by the roots, explored soil is assumed to have a FC soil moisture
        # content).
        EXPLOR = RROOTD * p.SMFCF  # cm d-1

        # Drainage and Runoff is calculated using the drunir function.
        dr = drunir(RTRAIN, k.RNINTC, k.EVSMX, k.TRA, p.IRRIGF, p.DRATE, delt, s.W, ROOTD, p.SMFCF, p.SM0)
        RDRAIN = dr.DRAIN
        RRUNOFF = dr.RUNOFF
        RIRRIG = dr.IRRIG

        # Rate of change of soil water amount
        RWA = (RTRAIN + EXPLOR + RIRRIG) - (k.RNINTC + RRUNOFF + k.TRA + k.EVSMX + RDRAIN)  # cm d-1

        r.RWA = RWA
        r.EXPLOR = EXPLOR

        # In the native water balance of PCSE, there is no difference between EVSMX and EVS, because the soil
        # evaporation rate is not affected by the number of days with a dry soil before the current day. EVS and
        # EVSMX nevertheless stored separately for for consistency with other soil water modules in PCSE.
        r.EVS = k.EVSMX
        r.RIRRIG = RIRRIG
        r.RUNOFF = RRUNOFF
        r.RDRAIN = RDRAIN

    def integrate(self, day, drv, delt = 1):
        k = self.kiosk
        r = self.rates
        s = self.states

        s.W += r.RWA
        s.SM = s.W / k.RD
        s.RUNOFF += delt * r.RRUNOFF
        s.DRAIN += delt * r.RDRAIN