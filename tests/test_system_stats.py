"""Tests for app/system_stats.py."""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from app import system_stats


def test_cpu_percent_linux():
    stat1 = "cpu  1000 200 300 5000 100 0 50 0 0 0\n"
    stat2 = "cpu  1200 200 350 5100 100 0 50 0 0 0\n"

    m_open = MagicMock(side_effect=[
        MagicMock(__enter__=MagicMock(return_value=MagicMock(readline=MagicMock(return_value=stat1)))),
        MagicMock(__enter__=MagicMock(return_value=MagicMock(readline=MagicMock(return_value=stat2)))),
    ])

    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", m_open):
        system_stats._last_cpu_time = 0.0
        system_stats._last_cpu_pct = None
        # First reading: baseline established
        res1 = system_stats.get_cpu_percent()
        assert res1 is None

        # Second reading after time advance
        with patch("time.time", return_value=system_stats._last_cpu_time + 1.0):
            res2 = system_stats.get_cpu_percent()
            assert res2 is not None
            assert res2 == 71


def test_cpu_percent_windows():
    with patch("os.path.exists", return_value=False), \
         patch("sys.platform", "win32"):
        system_stats._last_cpu_time = 0.0
        system_stats._last_cpu_pct = None
        # Mock ctypes.windll.kernel32.GetSystemTimes
        mock_kernel32 = MagicMock()
        mock_kernel32.GetSystemTimes.return_value = 1
        with patch.object(system_stats.ctypes, "windll", create=True) as mock_windll:
            mock_windll.kernel32 = mock_kernel32
            # Should not raise
            val = system_stats.get_cpu_percent()
            assert val is None or isinstance(val, int)


def test_cpu_percent_graceful_failure():
    with patch("os.path.exists", side_effect=RuntimeError("disk error")), \
         patch("sys.platform", "unknown_os"):
        res = system_stats.get_cpu_percent()
        assert res is None


def test_gpu_percent_nvml():
    mock_lib = MagicMock()
    mock_lib.nvmlInit.return_value = 0
    mock_lib.nvmlDeviceGetHandleByIndex.return_value = 0
    
    def fake_util(dev, util_ref):
        util_ref._obj.gpu = 42
        return 0

    mock_lib.nvmlDeviceGetUtilizationRates.side_effect = fake_util

    with patch.object(system_stats, "_get_nvml", return_value=mock_lib):
        val = system_stats.get_gpu_percent()
        assert val == 42


def test_gpu_percent_nvidia_smi():
    with patch.object(system_stats, "_get_nvml", return_value=None), \
         patch("shutil.which", return_value="/usr/bin/nvidia-smi"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="85\n")
        val = system_stats.get_gpu_percent()
        assert val == 85


def test_gpu_percent_engine_fallback():
    with patch.object(system_stats, "_get_nvml", return_value=None), \
         patch("shutil.which", return_value=None), \
         patch("os.path.exists", return_value=False):
        # Case A: engine reported direct utilization
        val1 = system_stats.get_gpu_percent({"utilization": 55})
        assert val1 == 55

        # Case B: engine reported VRAM
        val2 = system_stats.get_gpu_percent({
            "vram_total": 10000000000,
            "vram_free": 6000000000,
        })
        assert val2 == 40  # (1 - 6/10) * 100 = 40%


def test_gpu_percent_graceful_failure():
    with patch.object(system_stats, "_get_nvml", return_value=None), \
         patch("shutil.which", return_value=None), \
         patch("os.path.exists", return_value=False):
        val = system_stats.get_gpu_percent(None)
        assert val is None
