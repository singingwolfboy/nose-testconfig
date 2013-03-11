import os
import sys
import unittest

class TestAutoloads(unittest.TestCase):
    def setUp(self):
        # Force reload of testconfig module to prevent side-effects from
        # previous tests
        try:
            del sys.modules['testconfig']
        except KeyError:
            pass

    def tearDown(self):
        # Remove any environment variables that we set
        keys_to_delete = [key for key in os.environ if key.startswith('NOSE_TESTCONFIG')]

        for key in keys_to_delete:
            print('*** Deleting key: %s' % key)
            del os.environ[key]

    def test_ini_file(self):
        os.environ['NOSE_TESTCONFIG_AUTOLOAD_INI'] = 'examples/example_cfg.ini'
        from testconfig import config

        self.assertEqual(config['myapp_servers']['main_server'], "'10.1.1.1'")

    def test_json_file(self):
        os.environ['NOSE_TESTCONFIG_AUTOLOAD_JSON'] = 'examples/example_cfg.json'
        from testconfig import config

        self.assertEqual(config['myapp']['servers']['main_server'], '10.1.1.1')

