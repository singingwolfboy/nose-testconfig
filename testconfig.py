from nose.plugins.base import Plugin
from nose.util import tolist

import os
import ConfigParser
import logging

log = logging.getLogger(__name__)

warning = "Cannot access the test config because the plugin has not \
been activated.  Did you specify --tc or any other command line option?"

class _uninitialized_config(object):
    """a dummy config until the plugin creates a real one"""
    def _warn(self):
        import warnings
        warnings.warn(warning, RuntimeWarning)

    def __getitem__(self, item):
        self._warn()
        return None

    def get(self, item, default=None):
        self._warn()
        return None


config = _uninitialized_config()


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


class TestConfig(Plugin):

    enabled = False
    name = "test_config"
    score = 1

    env_opt = "NOSE_TEST_CONFIG_FILE"
    format = "ini"
    valid_loaders = { 'yaml' : load_yaml, 'ini' : load_ini,
                      'python' : load_python }

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
        if not options.testconfig:
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
        self.valid_loaders[self.format](options.testconfig)

        if options.overrides:
            self.overrides = []
            overrides = tolist(options.overrides)
            for override in overrides:
                keys, val = override.split(":")
                if options.exact:
                    config[keys] = val
                else:                    
                    ns = ''.join(['["%s"]' % i for i in keys.split(".") ])
                    # BUG: Breaks if the config value you're overriding is not
                    # defined in the configuration file already. TBD
                    exec('config%s = "%s"' % (ns, val))
