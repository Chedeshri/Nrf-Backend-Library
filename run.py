import sys
import os
import runpy
import configparser

config = configparser.ConfigParser(allow_no_value=True)

def read_config():
    if os.path.isfile("config.ini"):
        config.read("config.ini")
        return True
    elif os.path.isfile("config_default.ini"):
        config.read("config_default.ini")
        print("Falling back to default configuration file.")
        return True
    else:
        print("Could not find config.ini!")

    return False


def setup_arguments_for_robot_framework():
    arguments = []

    # Return returncode 0 when tests are failing
    # If return code >= 250 then some thing else is wrong.
    # This is needed for jenkins:
    # http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#return-codes
    arguments.append("--nostatusrc")

    # Add the variable to use
    if 'VARIABLES' in config.sections():
        for variable in config['VARIABLES']:
            arguments.append("--variable")
            arguments.append(variable + ":" + config['VARIABLES'][variable])

    if 'LIBS_TO_USE' in config.sections():
        for path in config['LIBS_TO_USE']:
            arguments.append("--pythonpath")
            arguments.append(path)

    arguments.append("--pythonpath")
    arguments.append(os.getcwd())

    # Run all tests with tags that match "INCLUDE_TAGS"
    if config.get('TAGS', 'INCLUDE_TAGS'):
        arguments.append("--include")
        arguments.append(config['TAGS']['INCLUDE_TAGS'])

    # Run all tests, but exclude tags that match "EXCLUDE_TAGS"
    if config.get('TAGS', 'EXCLUDE_TAGS'):
        arguments.append("--exclude")
        arguments.append(config['TAGS']['EXCLUDE_TAGS'])

    # Add log level
    if config.get('SETTINGS', 'LOGLEVEL'):
        arguments.append("--loglevel")
        arguments.append(config['SETTINGS']['LOGLEVEL'])

    # Add the variable file to use
    if config.get('PATHS', 'VARIABLE_FILE'):
        arguments.append("--variablefile")
        arguments.append(config['PATHS']['VARIABLE_FILE'])

    # Set the output directory for the test results
    if config.get('PATHS', 'TEST_RESULT_DIRECTORY'):
        arguments.append("--outputdir")
        arguments.append(config['PATHS']['TEST_RESULT_DIRECTORY'])

    # Set the test root directory
    if config.get('PATHS', 'TEST_ROOT_DIRECTORY', fallback='tests'):
        arguments.append(config['PATHS']['TEST_ROOT_DIRECTORY'])

    print("Appended command line arguments: ")
    sys.argv = [os.path.basename(__file__)] + arguments
    #for argument in arguments:
    #    sys.argv.append(argument)
    print(' '.join(sys.argv))


if __name__ == '__main__':
    if read_config():
        setup_arguments_for_robot_framework()

        print("Starting python module called \"robot\"")
        runpy.run_module("robot", alter_sys=True)
    else:
        raise IOError("No valid configuration found!")
