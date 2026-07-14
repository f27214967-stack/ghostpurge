import pytest
import os
import typing
from unittest.mock import patch

from ghostpurge.cleaners.clean_win_registry import CleanWinRegistry # noqa: E402
from ghostpurge.cleaners.clean_win_folders import CleanWinFolders # noqa: E402

from ghostpurge.config import Config

@pytest.fixture
def win_registry_cleaner() -> typing.Generator[CleanWinRegistry, None, None]:
    with patch('os.name', 'nt'):
        cleaner = CleanWinRegistry(Config())
        yield cleaner

@pytest.fixture
def win_folders_cleaner() -> typing.Generator[CleanWinFolders, None, None]:
    with patch('os.name', 'nt'):
        cleaner = CleanWinFolders(Config())
        yield cleaner

@patch('ghostpurge.cleaners.clean_win_registry.winreg')
def test_mock_registry_cleanup(mock_winreg: typing.Any, win_registry_cleaner: CleanWinRegistry) -> None:
    """Test that the cleaner correctly targets Windows registry keys."""
    # Run the clean method
    win_registry_cleaner.clean("TestApp", "mock_source")
    
    # Assert that winreg.DeleteKey was called for the expected paths
    expected_calls = [
        (mock_winreg.HKEY_CURRENT_USER, r"Software\TestApp"),
        (mock_winreg.HKEY_LOCAL_MACHINE, r"Software\TestApp"),
        (mock_winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\TestApp")
    ]
    
    # Verify the calls were made
    assert mock_winreg.DeleteKey.call_count == 3
    for hkey, subkey in expected_calls:
        mock_winreg.DeleteKey.assert_any_call(hkey, subkey)

def test_mock_folder_cleanup(win_folders_cleaner: CleanWinFolders) -> None:
    """Test that the cleaner targets correct Windows AppData paths."""
    with patch('os.environ.get') as mock_env, \
         patch('os.path.exists', return_value=True), \
         patch('shutil.rmtree') as mock_rmtree:
        
        # Mock environment variables
        def env_side_effect(key: str, default: str = '') -> str:
            if key == 'APPDATA':
                return 'C:\\Users\\Mock\\AppData\\Roaming'
            if key == 'LOCALAPPDATA':
                return 'C:\\Users\\Mock\\AppData\\Local'
            if key == 'ProgramData':
                return 'C:\\ProgramData'
            return default
        mock_env.side_effect = env_side_effect
        
        win_folders_cleaner.clean("TestApp", "mock_source")
        
        # Verify rmtree was called on the correct concatenated paths
        assert mock_rmtree.call_count == 3
        mock_rmtree.assert_any_call(os.path.join('C:\\Users\\Mock\\AppData\\Roaming', 'TestApp'))
        mock_rmtree.assert_any_call(os.path.join('C:\\Users\\Mock\\AppData\\Local', 'TestApp'))
        mock_rmtree.assert_any_call(os.path.join('C:\\ProgramData', 'TestApp'))
