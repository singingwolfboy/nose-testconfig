import unittest

from nose.plugins import Plugin, PluginTester
from nose.plugins.capture import Capture

from testconfig import TestConfig

# Base class for tests of the TestConfig nose plugin
# See https://nose.readthedocs.org/en/latest/plugins/testing.html
class _TestPluginTestConfig(PluginTester):
    plugins = [TestConfig(), Capture()]

    def test_suite_passed(self):
        for line in self.output:
            line = line.rstrip()
            print('line: %s' % line)

        self.assertTrue('Ran 1 test' in self.output)
        self.assertTrue('OK' in self.output)

    def makeSuite(outer_self):
        class TC(unittest.TestCase):
            def runTest(self):
                outer_self.test_assertions()

        return unittest.TestSuite([TC()])

class TestPluginTestConfigCommandLine(_TestPluginTestConfig, unittest.TestCase):
    activate = '--tc=myapp_servers.main_server:10.1.1.1'

    def test_assertions(self):
        from testconfig import config
        self.assertEqual(config['myapp_servers']['main_server'], '10.1.1.1')

class TestPluginTestConfigIniFile(_TestPluginTestConfig, unittest.TestCase):
    activate = '--tc-file=examples/example_cfg.ini'

    def test_assertions(self):
        from testconfig import config
        self.assertEqual(config['myapp_servers']['main_server'], "'10.1.1.1'")

class TestPluginTestConfigJsonFile(_TestPluginTestConfig, unittest.TestCase):
    activate = '--tc-file=examples/example_cfg.json'
    args = ['--tc-format=json']

    def test_assertions(self):
        from testconfig import config
        self.assertEqual(config['myapp']['servers']['main_server'], '10.1.1.1')

class TestPluginTestConfigYamlFile(_TestPluginTestConfig, unittest.TestCase):
    activate = '--tc-file=examples/example_cfg.yaml'
    args = ['--tc-format=yaml']

    def test_assertions(self):
        from testconfig import config
        self.assertEqual(config['myapp']['servers']['main_server'], '10.1.1.1')

class TestPluginTestConfigPyFile(_TestPluginTestConfig, unittest.TestCase):
    activate = '--tc-file=examples/example_cfg2.py'
    args = ['--tc-format=python']

    def test_assertions(self):
        from testconfig import config
        self.assertEqual(config['myapp']['servers']['main_server'], '10.1.1.1')

