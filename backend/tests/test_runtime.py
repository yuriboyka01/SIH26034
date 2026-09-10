import sys
from app.core.runtime import verify_runtime
import pytest

def test_verify_runtime_passes_on_correct_version(monkeypatch):
    """Test that runtime guard passes on Python 3.11."""
    class MockVersionInfo:
        major = 3
        minor = 11
        micro = 9
        
    monkeypatch.setattr(sys, "version_info", MockVersionInfo())
    
    # Should not raise any exception or exit
    verify_runtime()

def test_verify_runtime_fails_on_incorrect_version(monkeypatch):
    """Test that runtime guard fails on incorrect Python versions."""
    class MockVersionInfo:
        major = 3
        minor = 14
        micro = 7
        
    monkeypatch.setattr(sys, "version_info", MockVersionInfo())
    
    with pytest.raises(SystemExit) as excinfo:
        verify_runtime()
        
    assert excinfo.value.code == 1
