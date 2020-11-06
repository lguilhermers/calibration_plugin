"""
This tool calibrates a set of inputs from CEA to minimize the error between model outputs (predicted) and measured data (observed)
"""
from __future__ import division
from __future__ import print_function
from hyperopt.pyll import scope
import cea.config
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf
from cea.datamanagement import archetypes_mapper
from cea.demand import demand_main, schedule_maker
from cea.demand.schedule_maker import schedule_maker
from cea_calibration.validation import *
from cea_calibration.global_variables import *
from cea.utilities.schedule_reader import read_cea_schedule, save_cea_schedule
from collections import OrderedDict
from hyperopt import fmin, tpe, hp, Trials
import pandas as pd
import numpy as np
import glob2
import os

# def outputdatafolder(self):
#     return self._ensure_folder(self.scenario, 'outputs', 'data')
#
#
# def get_calibrationresults(self):
#     """scenario/outputs/data/calibration_results/calibrationresults.csv"""
#     return os.path.join(self.scenario, 'outputs', 'data', 'calibration_results', 'calibrationresults.csv')
#
#
# def get_project_calibrationresults(self):
#     """project/outputs/calibration_results/calibrationresults.csv"""
#     return os.path.join(self.project, 'outputs', 'calibration_results', 'calibrationresults.csv')
#
#
# def get_totaloccupancy(self):
#     """scenario/outputs/data/totaloccupancy.csv"""
#     return os.path.join(self.scenario, "outputs", "data", "totaloccupancy.csv")
#
#
# def get_measurements_folder(self):
#     return self._ensure_folder(self.scenario, 'inputs', 'measurements')
#
#
# def get_annual_measurements(self):
#     return os.path.join(self.get_measurements_folder(), 'annual_measurements.csv')
#
#
# def get_monthly_measurements(self):
#     return os.path.join(self.get_measurements_folder(), 'monthly_measurements.csv')
#
#
# def get_global_monthly_measurements(self):
#     return os.path.join(self.get_measurements_folder(), 'monthly_measurements.csv')

MONTHS_IN_YEAR_NAMES = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL',
                        'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER',
                        'OCTOBER', 'NOVEMBER', 'DECEMBER']

__author__ = "Luis Santos"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Luis Santos, Jimeno Fonseca, Daren Thomas"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def modify_monthly_multiplier(locator, config, measured_building_names):
    ##create building input schedules to set monthly multiplier
    archetypes_mapper.archetypes_mapper(locator,
                      update_architecture_dbf=False,
                      update_air_conditioning_systems_dbf=False,
                      update_indoor_comfort_dbf=False,
                      update_internal_loads_dbf=False,
                      update_supply_systems_dbf=False,
                      update_schedule_operation_cea=True,
                      buildings=[])

    ##calculate monthly multiplier based on buildings real consumption (adjusts monthly measured loads in CEA for each building accordingly to what is observed in real life)
    for building_name in measured_building_names:
        # monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())
        monthly_measured_data = locator.get_monthly_measurements.read()
        fields_to_extract = ['Name'] + MONTHS_IN_YEAR_NAMES
        monthly_measured_demand = monthly_measured_data[fields_to_extract].set_index('Name')
        monthly_measured_demand = monthly_measured_demand.loc[building_name]
        monthly_measured_demand = pd.DataFrame({'Month': monthly_measured_demand.index.values,
                                                'measurements': monthly_measured_demand.values})
        monthly_measured_load = monthly_measured_demand.measurements / max(monthly_measured_demand.measurements)

        path_to_schedule = locator.get_building_weekly_schedules(building_name)
        data_schedule, data_metadata = read_cea_schedule(path_to_schedule)
        data_metadata["MONTHLY_MULTIPLIER"] = list(monthly_measured_load.round(2))

        # save cea schedule format
        save_cea_schedule(data_schedule, data_metadata, path_to_schedule)


def calc_score(static_params, dynamic_params):
    """
    This tool reduces the error between observed (real life measured data) and predicted (output of the model data) values by changing some of CEA inputs.
    Monthly data is compared in terms of NMBE and CvRMSE (follwing ASHRAE Guideline 14-2014).
    A new input folder with measurements has to be created, with a csv each for monthly data provided as input for this tool.
    The input file contains: Name (CEA ID)| ZipCode (optional) | Monthly Data (JAN - DEC) | Type of equivalent variable in CEA (GRID_kWh is the default for total electricity consumption)
    The script prints the NBME and CvRMSE for each building in each iteration. It also outputs the number of calibrated buildings and a score metric (calibrated buildings weighted by their energy consumption).
    A new output csv is generated providing the calibration results (iteration number, parameters tested and results(score metric))
    """

    ## define set of CEA inputs to be calibrated and initial guess values
    SEED = dynamic_params['SEED']
    np.random.seed (SEED)                   #initalize seed numpy randomly npy.random.seed (once call the function) - inside put the seed
     #import random (initialize) npy.random.randint(low=1, high=100, size= number of buildings)/1000 - for every parameter.
    Hs_ag = dynamic_params['Hs_ag']
    Tcs_set_C = dynamic_params['Tcs_set_C']
    Es = dynamic_params['Es']
    Ns = dynamic_params['Ns']
    Occ_m2pax = dynamic_params['Occ_m2pax']
    Vww_lpdpax = dynamic_params['Vww_lpdpax']
    Ea_Wm2 = dynamic_params['Ea_Wm2']
    El_Wm2 = dynamic_params['El_Wm2']

    ##define fixed constant parameters (to be redefined by CEA config file)
    #Hs_ag = 0.15
    #Tcs_set_C = 28
    Tcs_setb_C = 40
    void_deck = 1
    height_bg = 0
    floors_bg = 0

    scenario_list = static_params['scenario_list']
    config = static_params['config']

    locators_of_scenarios = []
    measured_building_names_of_scenarios = []
    for scenario in scenario_list:
        config.scenario = scenario
        locator = cea.inputlocator.InputLocator(config.scenario, config.plugins)
        measured_building_names = get_measured_building_names(locator)
        modify_monthly_multiplier(locator, config, measured_building_names)

        # store for later use
        locators_of_scenarios.append(locator)
        measured_building_names_of_scenarios.append(measured_building_names)

        ## overwrite inputs with corresponding initial values

        # Changes and saves variables related to the architecture
        df_arch = dbf_to_dataframe(locator.get_building_architecture())
        number_of_buildings = df_arch.shape[0]
        Rand_it = np.random.randint(low=-30, high=30, size=number_of_buildings) / 100
        df_arch.Es = Es*(1+Rand_it)
        df_arch.Ns = Ns*(1+Rand_it)
        df_arch.Hs_ag = Hs_ag*(1+Rand_it)
        df_arch.void_deck = void_deck
        dataframe_to_dbf(df_arch, locator.get_building_architecture())

        # Changes and saves variables related to intetnal loads
        df_intload = dbf_to_dataframe(locator.get_building_internal())
        df_intload.Occ_m2pax = Occ_m2pax*(1+Rand_it)
        df_intload.Vww_lpdpax = Vww_lpdpax*(1+Rand_it)
        df_intload.Ea_Wm2 = Ea_Wm2*(1+Rand_it)
        df_intload.El_Wm2 = El_Wm2*(1+Rand_it)
        dataframe_to_dbf(df_intload, locator.get_building_internal())

        #Changes and saves variables related to comfort
        df_comfort = dbf_to_dataframe(locator.get_building_comfort())
        df_comfort.Tcs_set_C = Tcs_set_C*(1+Rand_it)
        df_comfort.Tcs_setb_C = Tcs_setb_C
        dataframe_to_dbf(df_comfort, locator.get_building_comfort())


        # Changes and saves variables related to zone
        df_zone = dbf_to_dataframe(locator.get_zone_geometry().split('.')[0]+'.dbf')
        df_zone.height_bg = height_bg
        df_zone.floors_bg = floors_bg
        dataframe_to_dbf(df_zone, locator.get_zone_geometry().split('.')[0]+'.dbf')

        ## run building schedules and energy demand
        config.schedule_maker.buildings = measured_building_names
        schedule_maker.schedule_maker_main(locator, config)
        config.demand.buildings = measured_building_names
        demand_main.demand_calculation(locator, config)


    # calculate the score
    score = validation(scenario_list=scenario_list, locators_of_scenarios=locators_of_scenarios,
                       measured_building_names_of_scenarios=measured_building_names_of_scenarios)

    return score

    ## save the iteration number, the value of each parameter tested and the score obtained


def calibration(config, list_scenarios):
    max_evals = 2 #maximum number of iterations allowed by the algorithm to run

    #  define a search space
    DYNAMIC_PARAMETERS = OrderedDict([('SEED', scope.int(hp.uniform('SEED', 0.0, 100.0))),
                                      ('Hs_ag', hp.uniform('Hs_ag', 0.1, 0.25)),
                                      ('Tcs_set_C', hp.uniform('Tcs_set_C', 24, 26)),
                                      ('Es', hp.uniform('Es', 0.4, 0.6)),
                                      ('Ns', hp.uniform('Ns', 0.4, 0.6)),
                                      ('Occ_m2pax', hp.uniform('Occ_m2pax', 35.0, 45.0)),
                                      ('Vww_lpdpax', hp.uniform('Vww_lpdpax', 25.0, 30.0)),
                                      ('Ea_Wm2', hp.uniform('Ea_Wm2', 1, 2.5)),
                                      ('El_Wm2', hp.uniform('El_Wm2', 1, 2.5))
                                      ])
    STATIC_PARAMS = {'scenario_list': list_scenarios, 'config': config}

    # define the objective
    def objective(dynamic_params):
        return -1.0 * calc_score(STATIC_PARAMS, dynamic_params) #score is set to negative as optimization looks for minimum

    # run the algorithm
    trials = Trials()
    best = fmin(objective,
                space=DYNAMIC_PARAMETERS,
                algo=tpe.suggest,
                max_evals=max_evals,
                trials=trials)
    print(best)
    print('Best Params: {}'.format(best))
    print(trials.losses())

    validation_n_calib = pd.DataFrame(global_validation_n_calibrated)
    validation_percentage = pd.DataFrame(global_validation_percentage)

    results = pd.DataFrame()
    for counter in range(0, max_evals):
        results_it = [counter,
                      trials.trials[counter]['misc']['vals']['SEED'][0],
                      trials.trials[counter]['misc']['vals']['Hs_ag'][0],
                      trials.trials[counter]['misc']['vals']['Tcs_set_C'][0],
                      trials.trials[counter]['misc']['vals']['Ea_Wm2'][0],
                      trials.trials[counter]['misc']['vals']['El_Wm2'][0],
                      trials.trials[counter]['misc']['vals']['Es'][0],
                      trials.trials[counter]['misc']['vals']['Ns'][0],
                      trials.trials[counter]['misc']['vals']['Occ_m2pax'][0],
                      trials.trials[counter]['misc']['vals']['Vww_lpdpax'][0],
                      trials.losses()[counter]
                      ]
        results_it = pd.DataFrame([results_it])
        results = results.append(results_it)
    results.reset_index(drop=True, inplace=True)
    results = pd.concat([results, validation_n_calib, validation_percentage],  axis=1, sort=False).sort_index()

    results.columns = ['eval', 'SEED','Hs_ag','Tcs_set_C', 'Ea_Wm2', 'El_Wm2', 'Es',
                       'Ns', 'Occ_m2pax', 'Vww_lpdpax', 'score_weighted_demand', 'buildings_calibrated', 'percentage_buildings_calibrated_%']
    project_path = config.project
    output_path = (project_path + r'/output/calibration/')

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    file_name = output_path+'calibration_results.csv'
    results.to_csv(file_name, index=False)

def main(config):
    """
    The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    project_path = config.project
    measurement_files = sorted(glob2.glob(project_path + '/**/monthly_measurements.csv'))

    list_scenarios = []
    for f in measurement_files:
        list_scenarios.append(os.path.dirname(os.path.dirname(os.path.dirname(f))))
    print(list_scenarios[:])

    calibration(config, list_scenarios[:])

if __name__ == '__main__':
    main(cea.config.Configuration())
