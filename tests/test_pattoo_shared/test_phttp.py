#!/usr/bin/env python3
"""Test the phttp module."""

# Standard imports
import unittest
import requests
import requests_mock
from unittest.mock import patch
import os
import sys
from time import time

# Try to create a working PYTHONPATH
EXEC_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(
    os.path.abspath(os.path.join(EXEC_DIR, os.pardir)), os.pardir))
_EXPECTED = '{0}pattoo-shared{0}tests{0}test_pattoo_shared'.format(os.sep)
if EXEC_DIR.endswith(_EXPECTED) is True:
    # We need to prepend the path in case PattooShared has been installed
    # elsewhere on the system using PIP. This could corrupt expected results
    sys.path.insert(0, ROOT_DIR)
else:
    print('''This script is not installed in the "{0}" directory. Please fix.\
'''.format(_EXPECTED))
    sys.exit(2)

# Pattoo imports
from pattoo_shared import phttp
from pattoo_shared import data
from pattoo_shared import converter
from pattoo_shared.files import set_gnupg, get_gnupg
from pattoo_shared.configuration import Config
from tests.libraries.configuration import UnittestConfig
from tests.resources import test_agent as ta


class Test_Post(unittest.TestCase):
    """Test _Post."""

    # Create agent data
    agentdata = ta.test_agent()

    # Get agent variables
    identifier = agentdata.agent_id
    _data = converter.agentdata_to_post(agentdata)
    data = converter.posting_data_points(_data)

    def test___init__(self):
        """Testing method or function named __init__."""

        # Test
        _post = phttp._Post(self.identifier, self.data)

        self.assertEqual(_post._identifier, self.identifier)
        self.assertEqual(_post._data, self.data)


class TestPost(unittest.TestCase):
    """Checks all functions and methods."""

    #########################################################################
    # General object setup
    #########################################################################

    # Create agent data
    agentdata = ta.test_agent()

    # Get agent variables
    identifier = agentdata.agent_id
    _data = converter.agentdata_to_post(agentdata)
    data = converter.posting_data_points(_data)

    def test___init__(self):
        """Testing method or function named __init__."""

        # Initialize
        post = phttp.Post(self.identifier, self.data)

        # Test
        expected_server_url = \
            '''http://127.0.0.6:50505/pattoo/api/v1/agent/receive/{}'''\
            .format(self.identifier)
        result_server_url = post._url

        self.assertEqual(result_server_url, expected_server_url)

    def test_post(self):
        """Testing method or function named post."""
        # Initialize
        post_test = phttp.Post(self.identifier, self.data)

        # Magically simulate post request
        with patch('pattoo_shared.phttp.requests.post') as mock_post:

            # Magically assign post response values
            mock_post.return_value.ok = True
            mock_post.return_value.text = 'OK'
            mock_post.return_value.status_code = 200

            # Run post
            success = post_test.post()

            # Check that the post request was to the right URL
            # and that it contained the right data
            mock_post.assert_called_with(
                '''http://127.0.0.6:50505/pattoo/api/v1/agent/receive/{}'''
                .format(self.identifier), json=self.data
                )

            # Assert that the success is True
            self.assertTrue(success)

    def test_purge(self):
        """Testing method or function named purge."""
        # Initialize
        purge_test = phttp.Post(self.identifier, self.data)

        # Magically simulate post request
        with patch('pattoo_shared.phttp.requests.post') as mock_post:

            # Magically assign post response values
            mock_post.return_value.ok = True
            mock_post.return_value.text = 'OK'
            mock_post.return_value.status_code = 200

            # Run post
            success = purge_test.post()

            # Check that the post request was to the right URL
            # and that it contained the right data
            mock_post.assert_called_with(
                '''http://127.0.0.6:50505/pattoo/api/v1/agent/receive/{}'''
                .format(self.identifier), json=self.data
                )

            # Assert that the success is True
            self.assertTrue(success)


class TestEncryptedPost(unittest.TestCase):
    """Checks all functions and methods."""

    #########################################################################
    # General object setup
    #########################################################################

    # Create agent data
    agentdata = ta.test_agent()

    # Get agent variables
    identifier = agentdata.agent_id
    _data = converter.agentdata_to_post(agentdata)
    data = converter.posting_data_points(_data)

    # Initialize
    # Create Pgpier object
    gpg = set_gnupg(
        'test_agent0', Config(), 'test_agent0@example.org'
            )
    # Create EncryptedPost object
    encrypted_post = phttp.EncryptedPost(identifier, data, gpg)

    def test___init__(self):
        """Testing method or function named __init__."""

        # Test variables
        expected_exchange_key = \
            '''http://127.0.0.6:50505/pattoo/api/v1/agent/key'''
        result_exchange_key = self.encrypted_post._exchange_key

        expected_validate_key = \
            '''http://127.0.0.6:50505/pattoo/api/v1/agent/validation'''
        result_validate_key = self.encrypted_post._validate_key

        expected_encryption = \
            '''http://127.0.0.6:50505/pattoo/api/v1/agent/encrypted'''
        result_encryption = self.encrypted_post._encryption

        # Test URL's
        self.assertEqual(result_exchange_key, expected_exchange_key)
        self.assertEqual(result_validate_key, expected_validate_key)
        self.assertEqual(result_encryption, expected_encryption)
        # Test that Pgpier object is valid
        self.assertIsInstance(self.encrypted_post._gpg.keyid, str)


class TestKeyExchangeSuite(unittest.TestCase):
    """Checks basic functions of the key exchange process."""

    # Initialize
    # Create Pgpier object for test API
    api_gpg = set_gnupg(
        'api_server', Config(), 'api_server@example.org'
            )
    # Create Pgpier object for test agent
    agent_gpg = set_gnupg(
        'encrypted_agent', Config(), 'encrypted_agent@example.org'
            )
    # Create test request session
    req_session = requests.Session()
    # Exchange URL
    exchange_url = \
        '''http://127.0.0.6:50505/pattoo/api/v1/agent/key'''
    # Validation URL
    validation_url = \
        '''http://127.0.0.6:50505/pattoo/api/v1/agent/validation'''
    # Short symmetric key
    symmetric_key = '''315602dcecc28d8bbb6af7c5'''

    def test_basic_functions(self):
        """Test functions in order"""




class TestPassiveAgent(unittest.TestCase):
    """Checks all functions and methods."""

    #########################################################################
    # General object setup
    #########################################################################

    def test___init__(self):
        """Testing method or function named __init__."""
        pass

    def test_relay(self):
        """Testing method or function named relay."""
        pass

    def test_get(self):
        """Testing method or function named get."""
        pass


class TestBasicFunctions(unittest.TestCase):
    """Checks all functions and methods."""

    #########################################################################
    # General object setup
    #########################################################################

    def test_post(self):
        """Testing method or function named post."""
        pass

    def test_purge(self):
        """Testing method or function named purge."""
        pass

    def test__save_data(self):
        """Testing method or function named _save_data."""
        # Initialize key variables
        identifier = data.hashstring(str(time()))

        # Test valid
        _data = {'Test': 'data'}
        success = phttp._save_data(_data, identifier)
        self.assertTrue(success)

        # Test invalid
        _data = ''
        success = phttp._save_data(_data, identifier)
        self.assertTrue(success)

    def test__log(self):
        """Testing method or function named _log."""
        pass


if __name__ == '__main__':
    # Make sure the environment is OK to run unittests
    UnittestConfig().create()

    # Do the unit test
    unittest.main()
