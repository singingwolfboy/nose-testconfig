from nose.plugins.base import Plugin
from nose.util import tolist

import os
import ConfigParser
import logging

log = logging.getLogger(__name__)

warning = "Cannot access the test config because the plugin has not \
been activated.  Did you specify --tc or any other command line option?"

config = {}


def load_yaml(yaml_file):
    """ Load the passed in yaml configuration file """
    try:
        import yaml
    except (ImportError):
        raise Exception('unable to import YAML package. Can not continue.')
    global config
    config = yaml.load(open(yaml_file).read())


def load_ini(ini_file):
    """ Parse and collapse a ConfigParser-Style ini file into a nested,
    eval'ing the individual values, as they are assumed to be valid
    python statement formatted """

    import ConfigParser
    global config
    tmpconfig = ConfigParser.ConfigParser()
    tmpconfig.read(ini_file)
    config = {}
    for section in tmpconfig.sections():
        config[section] = {}
        for option in tmpconfig.options(section):
            config[section][option] = tmpconfig.get(section, option)


def load_python(py_file):
    """ This will exec the defined python file into the config variable - 
    the implicit assumption is that the python is safe, well formed and will
    not do anything bad. This is also dangerous. """
    exec(open(py_file, 'r'))


def load_json(json_file):
    """ This will use the json module to to read in the config json file.
    """
    import json
    global config
    with open(json_file, 'r') as handle:
        config = json.load(handle)


class TestConfig(Plugin):

    enabled = False
    name = "test_config"
    score = 1

    env_opt = "NOSE_TEST_CONFIG_FILE"
    format = "ini"
    valid_loaders = { 'yaml' : load_yaml, 'ini' : load_ini,
                      'python' : load_python, 'json': load_json }

    def options(self, parser, env=os.environ):
        """ Define the command line options for the plugin. """
        parser.add_option(
            "--tc-file", action="store",
            default=env.get(self.env_opt),
            dest="testconfig",
            help="Configuration file to parse and pass to tests"
                 " [NOSE_TEST_CONFIG_FILE]")
        parser.add_option(
            "--tc-format", action="store",
            default=env.get('NOSE_TEST_CONFIG_FILE_FORMAT') or self.format, 
            dest="testconfigformat",
            help="Test config file format, default is configparser ini format"
                 " [NOSE_TEST_CONFIG_FILE_FORMAT]")
        parser.add_option(
            "--tc", action="append",
            dest="overrides",
            default = [],
            help="Option:Value specific overrides.")
        parser.add_option(
            "--tc-exact", action="store_true",
            dest="exact",
            default = False,
            help="Optional: Do not explode periods in override keys to "
                 "individual keys within the config dict, instead treat them"
                 " as config[my.toplevel.key] ala sqlalchemy.url in pylons")

    def configure(self, options, noseconfig):
        """ Call the super and then validate and call the relevant parser for
        the configuration file passed in """
        if not options.testconfig and not options.overrides:
            return
        Plugin.configure(self, options, noseconfig)

        self.config = noseconfig
        if not options.capture:
            self.enabled = False
        if options.testconfigformat:
            self.format = options.testconfigformat
            if self.format not in self.valid_loaders.keys():
                raise Exception('%s is not a valid configuration file format' \
                                                                % self.format)

        # Load the configuration file:
        if options.testconfig:
            self.valid_loaders[self.format](options.testconfig)

        overrides = tolist(options.overrides) or []
        for override in overrides:
            keys, val = override.split(":", 1)
            if options.exact:
                config[keys] = val
            else:
                # Create all *parent* keys that may not exist in the config
                section = config
                keys = keys.split('.')
                for key in keys[:-1]:
                    if key not in section:
                        section[key] = {}
                    section = section[key]

                # Finally assign the value to the last key
                key = keys[-1]
                section[key] = val


# Use an environment hack to allow people to set a config file to auto-load
# in case they want to put tests they write through pychecker or any other
# syntax thing which does an execute on the file.
if 'NOSE_TESTCONFIG_AUTOLOAD_YAML' in os.environ:
    load_yaml(os.environ['NOSE_TESTCONFIG_AUTOLOAD_YAML'])

if 'NOSE_TESTCONFIG_AUTOLOAD_INI' in os.environ:
    load_ini(os.environ['NOSE_TESTCONFIG_AUTOLOAD_INI'])

if 'NOSE_TESTCONFIG_AUTOLOAD_PYTHON' in os.environ:
    load_python(os.environ['NOSE_TESTCONFIG_AUTOLOAD_PYTHON'])

if 'NOSE_TESTCONFIG_AUTOLOAD_JSON' in os.environ:
    load_json(os.environ['NOSE_TESTCONFIG_AUTOLOAD_JSON'])
