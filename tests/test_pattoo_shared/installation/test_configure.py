#!/usr/bin/env/python3
"""Test pattoo configuration script."""

from unittest.mock import patch
import os
import getpass
import grp
import unittest
import sys
import tempfile
import yaml

# Try to create a working PYTHONPATH
EXEC_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(os.path.abspath(os.path.join(
    os.path.abspath(os.path.join(EXEC_DIR, os.pardir)), os.pardir)), os.pardir))
_EXPECTED = '''\
{0}pattoo-shared{0}tests{0}test_pattoo_shared{0}installation'''.format(os.sep)
if EXEC_DIR.endswith(_EXPECTED) is True:
    # We need to prepend the path in case PattooShared has been installed
    # elsewhere on the system using PIP. This could corrupt expected results
    sys.path.insert(0, ROOT_DIR)
else:
    print('''This script is not installed in the "{0}" directory. Please fix.\
'''.format(_EXPECTED))
    sys.exit(2)

# Pattoo imports
from tests.libraries.configuration import UnittestConfig
from pattoo_shared.installation import configure


class TestConfigure(unittest.TestCase):
    """Checks all functions for the Pattoo config script."""

    @classmethod
    def setUpClass(cls):
        """Declare class attributes for Unittesting."""
        # Initialize key variables
        cls.config_obj = configure.Configure()
        cls._log_directory = tempfile.mkdtemp()
        cls._cache_directory = tempfile.mkdtemp()
        cls._daemon_directory = tempfile.mkdtemp()
        cls._system_daemon_directory = tempfile.mkdtemp()

    def test__init__(self):
        """Unittest to test the __init__ function."""
        # Initialize key variables
        expected = {
            'pattoo': {
                    'language': 'en',
                    'log_directory': (
                        '/var/log/pattoo'),
                    'log_level': 'debug',
                    'cache_directory': (
                        '/opt/pattoo-cache'),
                    'daemon_directory': (
                        '/opt/pattoo-daemon'),
                    'system_daemon_directory': '/var/run/pattoo'
                },
            'pattoo_agent_api': {
                'ip_address': '127.0.0.1',
                'ip_bind_port': 20201
            },
            'pattoo_web_api': {
                'ip_address': '127.0.0.1',
                'ip_bind_port': 20202,
            }
        }

        result = self.config_obj.default_config

        # Ensure class attributes exist
        self.assertEqual(result, expected)

    def test_group_exists(self):
        """Unittest to test the group exists function."""
        # Test case for when the group does not exist
        with self.subTest():
            expected = False

            # Generating random string
            result = self.config_obj.group_exists(str(os.urandom(5)))
            self.assertEqual(result, expected)

        # Test case for when the group exists
        with self.subTest():
            expected = True

            # Creating grp.struct object
            grp_struct = grp.getgrgid(os.getgid())
            result = self.config_obj.group_exists(grp_struct.gr_name)
            self.assertEqual(result, expected)

    def test_user_exists(self):
        """Unittest to test the user_exists function."""
        # Test case for when the user does not exist
        with self.subTest():
            expected = False

            # Generating random string
            result = self.config_obj.user_exists(str(os.urandom(5)))
            self.assertEqual(result, expected)

        # Test case for when the user does exist
        with self.subTest():
            expected = True
            result = self.config_obj.user_exists(getpass.getuser())
            self.assertEqual(result, expected)

    def test_read_config(self):
        """Unittest to test the read_server_config function."""
        # Initialize key variables
        expected = self.config_obj.default_config

        # Create temporary directory using the temp file package
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "pattoo_temp_config.yaml")

            # Dumps default configuration to file in temp directory
            with open(file_path, 'w+') as temp_config:
                yaml.dump(expected, temp_config, default_flow_style=False)
            config = self.config_obj.read_config(file_path, expected)
            result = config == expected
            self.assertEqual(result, True)

    def test_pattoo_config_server(self):
        """Unittest to test the pattoo_config function for the pattoo server."""
        # Initialize key variables
        expected = '''\
pattoo_api_agentd:
ip_bind_port: 20201
ip_listen_address: 0.0.0.0
pattoo_apid:
  ip_bind_port: 20202
ip_listen_address: 0.0.0.0
pattoo_db:
db_hostname: localhost
  db_max_overflow: 20
db_name: pattoo
  db_password: password
db_pool_size: 10
  db_username: pattoo
pattoo_ingesterd:
batch_size: 500
  graceful_timeout: 10
ingester_interval: 3600
'''.strip().replace(' ', '')

        # Initialize temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "pattoo_server.yaml")

            # Create config file
            self.config_obj.pattoo_config(temp_dir, server=True)

            with open(file_path, 'r') as temp_config:

                # Remove all whitespace
                result = temp_config.read().strip().replace(' ', '')
            self.assertEqual(result, expected)

    def test_pattoo_config_default(self):
        """Unittest to test the pattoo_config function with default values."""
        # Initialize key variables
        expected = '''\
pattoo:
  cache_directory: /opt/pattoo-cache
  daemon_directory: /opt/pattoo-daemon
  language: en
  log_directory: /var/log/pattoo
  log_level: debug
  system_daemon_directory: /var/run/pattoo
pattoo_agent_api:
  ip_address: 127.0.0.1
  ip_bind_port: 20201
pattoo_web_api:
  ip_address: 127.0.0.1
  ip_bind_port: 20202'''.strip().replace(' ', '')

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "pattoo.yaml")

            # Create config file
            self.config_obj.pattoo_config(temp_dir)

            # Open config file for reading
            with open(file_path, 'r') as temp_config:

                # Remove all whitespace
                result = temp_config.read().strip().replace(' ', '')
            self.assertEqual(result, expected)

    def test_pattoo_config_custom_dict(self):
        """Unittest to test the pattoo_config function with custom dictionary."""
        # Initialize key variables
        expected = {
            'pattoo': {
                'log_directory': self._log_directory,
                'log_level': 'debug',
                'language': 'xyz',
                'cache_directory': self._cache_directory,
                'daemon_directory': self._daemon_directory,
                'system_daemon_directory': self._system_daemon_directory,
            },
            'pattoo_agent_api': {
                'ip_address': '127.0.0.6',
                'ip_bind_port': 50505,
            },
            'pattoo_web_api': {
                'ip_address': '127.0.0.3',
                'ip_bind_port': 30303,
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "pattoo.yaml")

            # Create config file
            self.config_obj.pattoo_config(temp_dir, expected)

            # Retrieve config dict from yaml file
            result = self.config_obj.read_config(file_path, expected)
            self.assertEqual(result, expected)


if __name__ == '__main__':
    # Make sure the environment is OK to run unittests
    UnittestConfig().create()

    # Do the unit test
    unittest.main()