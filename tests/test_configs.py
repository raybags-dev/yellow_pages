import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from ochestrator.ochestrator import load_configs


# Test when the configuration file does not exist
def test_load_configs_file_not_exist():
    with patch('ochestrator.ochestrator.Path.exists', return_value=False):
        with patch('ochestrator.ochestrator.custom_logger') as mock_logger:
            result = load_configs()
            expected_path = Path(__file__).parent.parent / 'configurations' / 'configs.json'
            mock_logger.assert_called_once_with(
                f"> Error: true\n> Source: The configuration file '{expected_path}'\n> Message: File does not exist Or is empty",
                'warn'
            )
            assert result is None


# Test when the configuration file is empty
def test_load_configs_file_empty():
    with patch('ochestrator.ochestrator.Path.exists', return_value=True):
        with patch('ochestrator.ochestrator.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 0
            with patch('ochestrator.ochestrator.custom_logger') as mock_logger:
                result = load_configs()
                expected_path = Path(__file__).parent.parent / 'configurations' / 'configs.json'
                mock_logger.assert_called_once_with(
                    f"> Error: true\n> Source: The configuration file '{expected_path}'\n> Message: File does not exist Or is empty",
                    'warn'
                )
                assert result is None


# Test when key_word_default is missing in the configuration file
def test_load_configs_missing_key_word_default():
    with patch('ochestrator.ochestrator.Path.exists', return_value=True):
        with patch('ochestrator.ochestrator.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 100
            mock_json_content = '{"country": "nl", "default_region": "some_region"}'
            with patch('builtins.open', mock_open(read_data=mock_json_content)):
                with patch('ochestrator.ochestrator.custom_logger') as mock_logger:
                    result = load_configs()
                    mock_logger.assert_called_once_with(
                        "> Error: true\n> Source: Configuration\n> Message: 'key_word_default' is missing or empty",
                        'warn')
                    assert result is None


# Test when country is missing in the configuration file
def test_load_configs_missing_country():
    with patch('ochestrator.ochestrator.Path.exists', return_value=True):
        with patch('ochestrator.ochestrator.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 100
            mock_json_content = '{"key_word_default": "some_keyword", "default_region": "some_region"}'
            with patch('builtins.open', mock_open(read_data=mock_json_content)):
                with patch('ochestrator.ochestrator.custom_logger') as mock_logger:
                    result = load_configs()
                    mock_logger.assert_called_once_with(
                        "> Error: true\n> Source: Configuration\n> Message: 'country' is missing or empty (options: nl|es)",
                        'warn')
                    assert result is None


# Test with a valid configuration file
def test_load_configs_valid_file():
    with patch('ochestrator.ochestrator.Path.exists', return_value=True):
        with patch('ochestrator.ochestrator.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 100
            mock_json_content = '{"key_word_default": "some_keyword", "country": "nl", "default_region": "some_region", "run_pipeline": true}'
            with patch('builtins.open', mock_open(read_data=mock_json_content)):
                result = load_configs()
                expected_result = {
                    'default_region': 'some_region',
                    'key_word_default': 'some_keyword',
                    'run_pipeline': True,
                    'country': 'nl'
                }
                assert result == expected_result
