# cea-calibration

This CEA plugin is used to validate and calibrate building energy, while comparing with measurements reported for each individual building.

As preparation, the user needs to include in each scenario a new file that contains the energy measurements. The file must be stored in project/scenario/inputs/measurements/monthly_measurements.csv.
The file must contain the building name from CEA associated to this building, the ZIP code (optional, serving as the ID of the building outside CEA), monthly readings from JAN - DEC, and variable
    (in general GRID_kWh is used, as it indicates the total energy consumption from the building).

The validation script compares results from CEA with measurements obtained from the building. Following the ASHRAE Guideline 14-2014, we evaluate the differences in terms of Normalized Mean Bias Error (NMBE) and
    Coefficient of Variation of the Root Mean Square Error (CvRMSE). For monthly data, it establishes a model is considered calibrated/ validated if its NMBE is within -5% to 5% and its CV(RMSE) is lower or equal to 15%.

The calibration script defines variables and ranges to be changed, with the objective to maximize the total energy consumption that is considered calibrated, according to ASHRAE standards.
    As a remark, the ASHRAE standard is focused on individual building calibration, while this script offers the possibility of calibrating for multiple buildings simultaneously.

