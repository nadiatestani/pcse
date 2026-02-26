# -*- coding: utf-8 -*-
# Herman Berghuijs (herman.berghuijs@wur.nl), Allard de Wit (allard.dewit@wur.nl), Tom Schut (tom.schut@wur.nl)
# February 2026

from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float

class fibrous_root_growth(SimulationObject):
    """
    Class to simulate the rooting depth.

    The class calculates the increase in rooting depth from emergence until a maximum rooting depth is reached.

    ** Simulation parameters **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Type     Unit
    =================  ==============================================  ======  ===========================
    RDI                Initial rooting depth                           SCr     cm root
    RDMSOL             Maximum rooting depth                           SCr     cm root
    RRDMAX             Maximum growth rate of rooting depth            SCr     cm root
    SMW                Soil moisture content at permanent wilting
                       point                                           SCr     cm root
    =================  ==============================================  ======  ===========================

    ** State variables **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl      Unit
    =================  ==============================================  ======  ===========================
    RD                 Rooting depth                                   Y       cm root
    =================  ==============================================  ======  ===========================

    ** Rate variables **

    =================  ==============================================  ======  ===========================
    Name               Description                                     Pbl      Unit
    =================  ==============================================  ======  ===========================
    RRD                Rate of change of rooting depth                 N        cm root
    =================  ==============================================  ======  ===========================

    This class is a Python implementation of the calculations related to the growth of rooting depth in the
    R function LINTUL2_CASSAVA_NPK in the R version of the model LINTUL Cassava NPK (Adiele et al.,
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
        RDI = Float()
        RDMSOL = Float()
        RRDMAX = Float()
        SMW = Float()

    class RateVariables(RatesTemplate):
        RRD = Float()

    class StateVariables(StatesTemplate):
        RD = Float()

    def initialize(self, day, kiosk, parvalues):
        self.kiosk = kiosk
        self.params = self.Parameters(parvalues)
        k = self.kiosk
        p = self.params
        RD = p.RDI
        self.rates = self.RateVariables(kiosk,
                                        publish = ["RRD"])
        self.states = self.StateVariables(kiosk,
                                          publish = ["RD"],
                                          RD = RD)

    def calc_rates(self,  day, drv, delt=1):
        # If the soil water content drops to, or below, wilting point fibrous root growth stops.
        # Root growth continues till the maximum rooting depth is reached.
        # The rooting depth (cm) is calculated from a maximum rate of change in rooting depth,
        # the emergence of the crop and the constraints mentioned above.

        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        if (s.RD-p.RDMSOL < 0) & (k.SM-p.SMW >= 0):
            RRD = p.RRDMAX * k.EMERG  # cm d-1
        else:
            RRD = 0

        r.RRD = RRD

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.RD += r.RRD * delt
