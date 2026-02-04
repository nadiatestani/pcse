from pcse.base import ParamTemplate, RatesTemplate, SimulationObject, StatesTemplate
from pcse.traitlets import Float
from pcse.util import AfgenTrait

class biomass_partitioning(SimulationObject):

    class Parameters(ParamTemplate):
        LAICR = Float()
        FLV_CUTT = Float()
        FLVTB = AfgenTrait()
        FRT_CUTT = Float()
        FRTTB = AfgenTrait()
        FST_CUTT = Float()
        FSTTB = AfgenTrait()
        FSO_CUTT = Float()
        FSOTB = AfgenTrait()
        NCUTTINGS = Float()
        OPTEMERGTSUM = Float()
        RDRWCUTTING = Float()
        WCUTTINGMINPRO = Float()
        WCUTTINGIP = Float()
        WCUTTINGUNIT = Float()

    class RateVariables(RatesTemplate):
        FLV = Float()
        FRT = Float()
        FST = Float()
        FSO = Float()
        RWRT = Float()
        RWST = Float()
        RWLV = Float()
        RWLVG = Float()
        RWSO = Float()
        RWCUTTING= Float()
        RNCUTTING= Float()
        RPCUTTING= Float()
        RKCUTTING= Float()

    class StateVariables(StatesTemplate):
        NCUTTING = Float()
        PCUTTING = Float()
        KCUTTING = Float()
        WCUTTING = Float()
        WLV = Float()
        WLVG = Float()
        WST = Float()
        WSO = Float()
        WRT = Float()

    def initialize(self, day, kiosk, parvalues):
        self.kiosk = kiosk
        self.params = self.Parameters(parvalues)
        p = self.params

        WLV = 0.
        WST = 0.
        WSO = 0.
        WRT = 0.
        WLVG = 0.
        NCUTTING = 0.015 * p.WCUTTINGUNIT * p.NCUTTINGS  # g N m-2
        PCUTTING = 0.0015 * p.WCUTTINGUNIT * p.NCUTTINGS  # g P m-2
        KCUTTING = 0.010 * p.WCUTTINGUNIT * p.NCUTTINGS  # g K m-2
        WCUTTING = p.WCUTTINGUNIT * p.NCUTTINGS

        self.rates = self.RateVariables(kiosk,
                                        publish = [
                                            "FLV",
                                            "FRT",
                                            "FSO",
                                            "FST",
                                            "RWLV",
                                            "RWRT",
                                            "RNCUTTING",
                                            "RPCUTTING",
                                            "RKCUTTING",
                                            "RWCUTTING"
                                        ])
        self.states = self.StateVariables(kiosk,
                                          publish = ["WSO", "WLVG", "WRT", "WST", "WSO"],
                                          NCUTTING = NCUTTING,
                                          PCUTTING = PCUTTING,
                                          KCUTTING = KCUTTING,
                                          WCUTTING = WCUTTING,
                                          WLV = WLV,
                                          WLVG = WLVG,
                                          WRT = WRT,
                                          WSO = WSO,
                                          WST = WST
                                          )

    def calc_rates(self,  day, drv, delt=1):
        k = self.kiosk
        p = self.params
        r = self.rates
        s = self.states

        # Allocation of assimilates to the different organs. The fractions are modified for water availability.
        # Nutrient limitation is also assumed to affect partitioning to the roots.
        FRTMOD = max(1, 1 / (k.RFTRA * k.NPKI + 0.5))  # (-)
        # Fibrous roots
        FRT1 = p.FRTTB(k.TSUMCROP)
        FRT = FRT1 * FRTMOD  # (-)

        FSHMOD = (1 - FRT) / (1 - FRT / FRTMOD)  # (-)

        # Leaves
        FLV1 = p.FLVTB(k.TSUMCROP)
        FLV = FLV1 * FSHMOD

        # Stems
        FST1 = p.FSTTB(k.TSUMCROP)
        FST = FST1 * FSHMOD

        # Storage roots
        FSO1 = p.FSOTB(k.TSUMCROP)
        FSO = FSO1 * FSHMOD

        # When plants emerge from dormancy, leaf growth may go far too quickly.
        # Adjust partitioning if LAI too large
        FLV_ADJ = FLV * max(0, min(1, (k.LAI - p.LAICR) / p.LAICR))
        FLV = FLV - FLV_ADJ
        FSO = FSO + 0.66 * FLV_ADJ  # Not used assimilated go for 2/3 to storage roots
        FST = FST + 0.34 * FLV_ADJ  # Not used assimilated go for 1/3 to stem

        # Minimal stem cutting weight.
        WCUTTINGMIN = p.WCUTTINGMINPRO * p.WCUTTINGIP

        # Default rates for weight, N,P,K amount changes in plant organs and the stem cutting
        RWRT = 0  # g fibrous root DM m-2 d-1
        RWST = 0  # g stem DM m-2 d-1
        RWLVG = 0  # g leaves DM m-2 d-1
        RWSO = 0  # g storage root DM m-2 d-1
        RWCUTTING=0  # g cutting DM m-2 d-1
        RNCUTTING=0  # g cutting N m-2 d-1
        RPCUTTING=0  # g cutting P m-2 d-1
        RKCUTTING=0  # g cutting K m-2 d-1

        # Stem cutting partioning at emergence.
        if (k.EMERG  == 1) & (s.WST == 0):
            RWCUTTING = s.WCUTTING * (-p.FST_CUTT - p.FRT_CUTT - p.FLV_CUTT - p.FSO_CUTT)
            RWRT = p.WCUTTINGIP * p.FRT_CUTT  # g fibrous root DM m-2 d-1
            RWST = p.WCUTTINGIP * p.FST_CUTT  # g stem DM m-2 d-1
            RWLVG = p.WCUTTINGIP * p.FLV_CUTT  # g leaves DM m-2 d-1
            RWSO = p.WCUTTINGIP * p.FSO_CUTT  # g storage root DM m-2 d-1

            # The amount of N, P, K transfered depends on max. concentrations in LV, ST, RT and SO
            RNCUTTING = -(RWLVG * k.NMAXLV + RWST * k.NMAXST + RWSO * k.NMAXSO + RWRT * k.NMAXRT)
            RPCUTTING = -(RWLVG * k.PMAXLV + RWST * k.PMAXST + RWSO * k.PMAXSO + RWRT * k.PMAXRT)
            RKCUTTING = -(RWLVG * k.KMAXLV + RWST * k.KMAXST + RWSO * k.KMAXSO + RWRT * k.KMAXRT)

        elif k.TSUM > p.OPTEMERGTSUM:
            # Movement of DM and NPK to other plant parts, depending on partitioning
            if s.WCUTTING-WCUTTINGMIN >= 0:
                RWCUTTING = -p.RDRWCUTTING * s.WCUTTING * k.RFTRA * k.EMERG * (1 - k.DORMANCY)
            else:
                RWCUTTING = 0

            RWRT = (abs(k.GTOTAL)+abs(RWCUTTING)) * FRT  # g fibrous root DM m-2 d-1
            RWST = (abs(k.GTOTAL)+abs(RWCUTTING)) * FST  # g stem DM m-2 d-1
            RWLVG = (abs(k.GTOTAL)+abs(RWCUTTING)) * FLV - k.DLV + k.RREDISTLVG * k.PUSHREDIST  # g leaves DM m-2 d-1
            RWSO = (abs(k.GTOTAL)+abs(RWCUTTING)) * FSO + k.RWSOFASTRANSLSO - k.RREDISTSO  # g storage root DM m-2 d-1

            # The amount of N, P, K transfered depends on max. concentrations in LV, ST, RT and SO
            RNCUTTING = (RWCUTTING / s.WCUTTING) * s.NCUTTING  # g N m-2 d-1, proportional to DM
            RPCUTTING = (RWCUTTING / s.WCUTTING) * s.PCUTTING  # g P m-2 d-1, proportional to DM
            RKCUTTING = (RWCUTTING / s.WCUTTING) * s.KCUTTING  # g K m-2 d-1, proportional to DM

        # Growth of the leaf weight
        RWLV = RWLVG+k.RWLVD  # g leaves DM m-2 d-1

        r.FLV = FLV
        r.FRT = FRT
        r.FSO = FSO
        r.FST = FST
        r.RWLV = RWLV
        r.RWLVG = RWLVG
        r.RWST = RWST
        r.RWSO = RWSO
        r.RWRT = RWRT
        r.RWLVG = RWLVG
        r.RNCUTTING = RNCUTTING
        r.RPCUTTING = RPCUTTING
        r.RKCUTTING = RKCUTTING
        r.RWCUTTING = RWCUTTING

    def integrate(self, day, drv, delt = 1):
        r = self.rates
        s = self.states
        s.NCUTTING += delt * r.RNCUTTING
        s.PCUTTING += delt * r.RPCUTTING
        s.KCUTTING += delt * r.RKCUTTING
        s.WCUTTING += delt * r.RWCUTTING
        s.WLV += delt * r.RWLV
        s.WLVG += delt * r.RWLVG
        s.WST += delt * r.RWST
        s.WSO += delt * r.RWSO
        s.WRT += delt * r.RWRT