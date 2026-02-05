from pcse.base import SimulationObject, ParamTemplate, StatesTemplate, RatesTemplate
from pcse.crop.lintul_cassava.phenology import phenology
from pcse.crop.lintul_cassava.canopy_rain_interception import canopy_rain_interception
from pcse.crop.lintul_cassava.biomass_partitioning import biomass_partitioning
from pcse.crop.lintul_cassava.dormancy import dormancy
from pcse.crop.lintul_cassava.lintul_cassava_meteo import penman
from pcse.crop.lintul_cassava.evapotranspiration import evapotranspiration
from pcse.crop.lintul_cassava.fibrous_root_growth import fibrous_root_growth
from pcse.crop.lintul_cassava.green_leaf_area import green_leaf_area
from pcse.crop.lintul_cassava.leaf_senescence import leaf_senescence
from pcse.crop.lintul_cassava.light_interception_and_growth import light_interception_and_growth
from pcse.crop.lintul_cassava.nutrient_dynamics import crop_nutrient_dynamics
from pcse.crop.lintul_cassava.nutrient_stress import npk_stress
from pcse.traitlets import Instance

class LINTUL_CASSAVA(SimulationObject):
    phenology = Instance(SimulationObject)
    fibrous_root_growth = Instance(SimulationObject)
    penman = Instance(SimulationObject)
    canopy_rain_interception = Instance(SimulationObject)
    evapotranspiration = Instance(SimulationObject)
    npk_stress = Instance(SimulationObject)
    dormancy = Instance(SimulationObject)
    leaf_senescence = Instance(SimulationObject)
    light_interception_and_growth = Instance(SimulationObject)
    biomass_partitioning = Instance(SimulationObject)
    crop_nutrient_dynamics = Instance(SimulationObject)
    green_leaf_area = Instance(SimulationObject)

    class Parameters(ParamTemplate):
        pass

    class StateVariables(StatesTemplate):
        pass

    class RateVariables(RatesTemplate):
        pass

    def initialize(self, day, kiosk, parvalues):
        self.kiosk = kiosk
        self.params = self.Parameters(parvalues)
        self.states = self.StateVariables(kiosk, publish = [])
        self.rates = self.RateVariables(kiosk, publish = [])

        self.phenology = phenology(day, kiosk, parvalues)
        self.fibrous_root_growth = fibrous_root_growth(day, kiosk, parvalues)
        self.canopy_rain_interception = canopy_rain_interception(day, kiosk, parvalues)
        self.penman = penman(day, kiosk, parvalues)
        self.evapotranspiration = evapotranspiration(day, kiosk, parvalues)
        self.npk_stress = npk_stress(day, kiosk, parvalues)
        self.dormancy = dormancy(day, kiosk, parvalues)
        self.leaf_senescence = leaf_senescence(day, kiosk, parvalues)
        self.light_interception_and_growth = light_interception_and_growth(day, kiosk, parvalues)
        self.biomass_partitioning = biomass_partitioning(day, kiosk, parvalues)
        self.crop_nutrient_dynamics = crop_nutrient_dynamics (day, kiosk, parvalues)
        self.green_leaf_area = green_leaf_area(day, kiosk, parvalues)

    def calc_rates(self, day, drv, delt = 1):
        self.phenology.calc_rates(day, drv, delt)
        self.fibrous_root_growth.calc_rates(day, drv, delt)
        self.canopy_rain_interception.calc_rates(day, drv, delt)
        self.penman(day, drv)
        self.evapotranspiration(day, drv)
        self.npk_stress(day, drv)
        self.dormancy.calc_rates(day, drv, delt)
        self.light_interception_and_growth.calc_rates(day, drv, delt)
        self.leaf_senescence.calc_rates(day, drv)
        self.biomass_partitioning.calc_rates(day, drv)
        self.crop_nutrient_dynamics.calc_rates(day, drv)
        self.green_leaf_area.calc_rates(day, drv)

    def integrate(self, day, drv, delt = 1):
        self.phenology.integrate(day, delt)
        self.fibrous_root_growth.integrate(day, delt)
        self.canopy_rain_interception.integrate(day, delt)
        self.dormancy.integrate(day, delt)
        self.leaf_senescence.integrate(day, drv)
        self.light_interception_and_growth.integrate(day, drv, delt)
        self.biomass_partitioning.integrate(day, drv, delt)
        self.crop_nutrient_dynamics.integrate(day, drv, delt)
        self.green_leaf_area.integrate(day, drv)

class LINTUL_CASSAVA_NO_NUTRIENT_STRESS(LINTUL_CASSAVA):
    def initialize(self, day, kiosk, parvalues):
        super().initialize(day, kiosk, parvalues)
        self.npk_stress.NUTRIENT_LIMITED = False