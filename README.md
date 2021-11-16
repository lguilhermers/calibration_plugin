# cea-calibration

This CEA plugin is used to validate and calibrate building electricity demand, while comparing with measurements reported for each individual building.

As preparation, the user needs to include in each scenario a new file that contains the electricity demand measurements. The file must be stored in `project/scenario/inputs/measurements/monthly_measurements.csv`. The file must contain the building name from CEA associated to this building, the ZIP code (optional, serving as the ID of the building outside CEA), monthly readings from JAN - DEC, and variable (in general GRID_kWh is used, as it indicates the total energy consumption from the building). A sample input file is included.

The validation script compares results from CEA with measurements obtained from the building. Following the ASHRAE Guideline 14-2014, we evaluate the differences in terms of Normalized Mean Bias Error (NMBE) and Coefficient of Variation of the Root Mean Square Error (CVRMSE). For monthly data, it establishes a model is considered calibrated/ validated if its NMBE is within -5% to 5% and its CV(RMSE) is lower or equal to 15%.

The calibration script defines variables and ranges to be changed, with the objective to maximize the total energy consumption that is considered calibrated, according to ASHRAE standards. As a remark, the ASHRAE standard is focused on individual building calibration, while this script offers the possibility of calibrating for multiple buildings simultaneously.

## Installation
To install, clone this repo to a desired path (you would need to have `git` installed to run this command. Alternatively you can also run this command in the CEA console, which comes with `git` pre-installed):

```git clone https://github.com/lguilhermers/calibration_plugin.git DESIRED_PATH```

Open CEA console and enter the following command to install the plugin to CEA:

```pip install -e PATH_OF_PLUGIN_FOLDER```

(NOTE: PATH_OF_PLUGIN_FOLDER would be the DESIRED_PATH + 'calibration_plugin')


In the CEA console, enter the following command to enable the plugin in CEA:

```cea-config write --general:plugins cea_calibration.CalibrationPlugin```

NOTE: If you are installing multiple plugins, add them as a comma separated list in the `cea-config write --general:plugins ...` command.
