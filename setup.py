from setuptools import setup, find_packages

__author__ = "Luis Santos"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Luis Santos, Jimeno Fonseca, Daren Thomas"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

setup(name='calibration_plugin',
      version=__version__,
      description="A plugin for the City Energy Analyst, used to calibrate building inputs and validate output metrics",
      license='MIT',
      author='Architecture and Building Systems',
      author_email='cea@arch.ethz.ch',
      url='https://github.com/architecture-building-systems/cea-plugin-template',
      long_description="This CEA plugin is used to validate and calibrate building energy, while comparing with measurements reported for each individual building.",
      py_modules=[''],
      packages=find_packages(),
      package_data={},
      install_requires=['glob2', 'hyperopt'],
      include_package_data=True)
