import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)

import app
import unittest
from httpretty import HTTPretty


class MockConsulKV:
    """
    context manager that mocks a consul KV response
    """

    def __enter__(self):
        """
        Defines the behaviour for __enter__
        """

        HTTPretty.enable()
        host = os.environ.get('CONSUL_HOST', 'localhost')
        service_name = os.environ.get('SERVICE', 'generic_service')
        environ_name = os.environ.get('ENVIRONMENT', 'generic_environment')

        HTTPretty.register_uri(
            HTTPretty.GET,
            "http://{host}:8500/v1/kv/config/{service}/{environment}/".format(
                host=host,
                service=service_name,
                environment=environ_name,
            ),
            body='''[
    {{
        "CreateIndex": 5729,
        "Flags": 0,
        "Key": "config/{service}/{environment}/cfg_1",
        "LockIndex": 0,
        "ModifyIndex": 5729,
        "Value": "Y29uc3VsXzE="
    }},
    {{
        "CreateIndex": 5730,
        "Flags": 0,
        "Key": "config/{service}/{environment}/cfg_3",
        "LockIndex": 0,
        "ModifyIndex": 5730,
        "Value": "Y29uc3VsXzM="
    }}
]'''.format(service=service_name, environment=environ_name),
        )

    def __exit__(self, etype, value, traceback):
        """
        Defines the behaviour for __exit__

        :param etype: exit type
        :param value: exit value
        :param traceback: the traceback for the exit
        """

        HTTPretty.reset()
        HTTPretty.disable()


class TestConfig(unittest.TestCase):
    """
    Test that the config is properly read by the application
    """

    def test_config_without_consul(self):
        """
        Ensures that the application loads configuration even if consul
        is not reachable.
        """
        a = app.create_app()

        self.assertIsNotNone(a.config)
        self.assertNotIn('cfg_1', a.config)
        self.assertNotIn('cfg_3', a.config)

    def test_config_with_consul_defaults(self):
        """
        Ensures that application config is loaded by consul using the default
        namespace and host
        """

        with MockConsulKV():
            a = app.create_app()

        self.assertEqual(a.config['cfg_1'], 'consul_1')
        self.assertEqual(a.config['cfg_3'], 'consul_3')

    def test_config_with_consul_environ(self):
        """
        Ensures that application config is loaded by consul using host and
        namespace defined by environmental variables
        """

        os.environ['CONSUL_HOST'] = "consul.adsabs"
        os.environ['SERVICE'] = "sample_application"
        os.environ['ENVIRONMENT'] = "testing"

        with MockConsulKV():
            a = app.create_app()

        del os.environ['CONSUL_HOST']
        del os.environ['SERVICE']
        del os.environ['ENVIRONMENT']

        self.assertEqual(a.config['cfg_1'], 'consul_1')
        self.assertEqual(a.config['cfg_3'], 'consul_3')


if __name__ == '__main__':
    unittest.main(verbosity=2)
