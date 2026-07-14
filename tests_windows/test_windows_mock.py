import pytest
import os
from unittest.mock import patch, MagicMock

# We must mock winreg and other Windows specifics before importing GhostPurge
import sys
mock_winreg = MagicMock()
mock_wmi = MagicMock()
mock_win32serviceutil = MagicMock()

sys.modules['winreg'] = mock_winreg
sys.modules['wmi'] = mock_wmi
sys.modules['win32serviceutil'] = mock_win32serviceutil

# Now we can safely import the cleaner
from ghostpurge.windows.cleaner_windows import WindowsCleaner

class DummyConfig:
    pass

@pytest.fixture
def windows_cleaner():
    # Force os.name to 'nt' for the cleaner logic
    with patch('os.name', 'nt'):
        cleaner = WindowsCleaner(DummyConfig())
        yield cleaner

def test_mock_registry_cleanup(windows_cleaner):
    """Test that the cleaner correctly targets Windows registry keys."""
    # Run the clean method
    windows_cleaner._clean_registry("TestApp")
    
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

def test_mock_folder_cleanup(windows_cleaner):
    """Test that the cleaner targets correct Windows AppData paths."""
    with patch('os.environ.get') as mock_env, \
         patch('os.path.exists', return_value=True), \
         patch('shutil.rmtree') as mock_rmtree:
        
        # Mock environment variables
        def env_side_effect(key, default=''):
            if key == 'APPDATA': return 'C:\\Users\\Mock\\AppData\\Roaming'
            if key == 'LOCALAPPDATA': return 'C:\\Users\\Mock\\AppData\\Local'
            if key == 'ProgramData': return 'C:\\ProgramData'
            return default
        mock_env.side_effect = env_side_effect
        
        windows_cleaner._clean_folders("TestApp")
        
        # Verify rmtree was called on the correct concatenated paths
        assert mock_rmtree.call_count == 3
        mock_rmtree.assert_any_call(os.path.join('C:\\Users\\Mock\\AppData\\Roaming', 'TestApp'))
        mock_rmtree.assert_any_call(os.path.join('C:\\Users\\Mock\\AppData\\Local', 'TestApp'))
        mock_rmtree.assert_any_call(os.path.join('C:\\ProgramData', 'TestApp'))
