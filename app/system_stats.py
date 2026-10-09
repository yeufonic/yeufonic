"""Yeufonic: lightweight CPU and GPU utilization stats.

Works on both Linux and Windows platforms, supporting both native and Docker installs.
Assumes nothing about the target platform; uses standard OS facilities and APIs without
requiring external tools or packages. Fails gracefully with a debug log entry if stats
are unavailable.
"""
from __future__ import annotations

import ctypes
import logging
import os
import shutil
import subprocess
import sys
import time
from typing import Any

log = logging.getLogger(__name__)

# State for CPU delta calculation
_last_cpu_time: float = 0.0
_last_cpu_total: float = 0.0
_last_cpu_idle: float = 0.0
_last_cpu_pct: int | None = None

# NVML cache state
_nvml_initialized: bool = False
_nvml_lib: Any = None
_nvml_failed: bool = False


def _read_cpu_raw() -> tuple[float, float] | None:
    """Read raw (total_ticks, idle_ticks) across Linux and Windows without external dependencies."""
    # 1. Linux /proc/stat (native Linux, WSL, Docker containers)
    try:
        if os.path.exists("/proc/stat"):
            with open("/proc/stat", "r", encoding="ascii") as f:
                line = f.readline()
            parts = line.split()
            if len(parts) >= 5 and parts[0] == "cpu":
                fields = [float(x) for x in parts[1:]]
                idle = fields[3] + (fields[4] if len(fields) > 4 else 0.0)
                total = sum(fields)
                return total, idle
    except Exception as exc:
        log.debug("failed to read /proc/stat: %s", exc)

    # 2. Windows GetSystemTimes (native Windows installer)
    if sys.platform == "win32":
        try:
            class FILETIME(ctypes.Structure):
                _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]

            def _to_int(ft: FILETIME) -> int:
                return (ft.dwHighDateTime << 32) | ft.dwLowDateTime

            idle_ft, kernel_ft, user_ft = FILETIME(), FILETIME(), FILETIME()
            if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle_ft), ctypes.byref(kernel_ft), ctypes.byref(user_ft)):
                idle = float(_to_int(idle_ft))
                # On Windows, kernel_time already includes idle_time
                total = float(_to_int(kernel_ft) + _to_int(user_ft))
                return total, idle
        except Exception as exc:
            log.debug("GetSystemTimes call failed: %s", exc)

    return None


def get_cpu_percent() -> int | None:
    """Return CPU utilization percentage (0-100) or None if unavailable."""
    global _last_cpu_time, _last_cpu_total, _last_cpu_idle, _last_cpu_pct

    raw = _read_cpu_raw()
    now = time.time()

    if raw is not None:
        total, idle = raw
        if _last_cpu_time > 0.0:
            dt = total - _last_cpu_total
            di = idle - _last_cpu_idle
            elapsed = now - _last_cpu_time
            if dt > 0.0 and elapsed >= 0.2:
                _last_cpu_pct = max(0, min(100, round(100.0 * (1.0 - di / dt))))
                _last_cpu_time = now
                _last_cpu_total = total
                _last_cpu_idle = idle
        else:
            _last_cpu_time = now
            _last_cpu_total = total
            _last_cpu_idle = idle
            _last_cpu_pct = None
        return _last_cpu_pct

    # Fallback if psutil is available
    try:
        import psutil  # type: ignore
        _last_cpu_pct = int(round(psutil.cpu_percent(interval=None)))
        return _last_cpu_pct
    except Exception as exc:
        log.debug("psutil cpu read failed: %s", exc)

    return None


def _get_nvml() -> Any:
    """Load NVML via ctypes without external packages."""
    global _nvml_initialized, _nvml_lib, _nvml_failed
    if _nvml_initialized:
        return _nvml_lib
    if _nvml_failed:
        return None

    candidates: list[str] = []
    if sys.platform == "win32":
        candidates = [
            "nvml.dll",
            os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "nvml.dll"),
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvml.dll",
        ]
    else:
        candidates = [
            "libnvidia-ml.so.1",
            "libnvidia-ml.so",
            "/usr/lib/wsl/lib/libnvidia-ml.so.1",
        ]

    for c in candidates:
        try:
            lib = ctypes.CDLL(c)
            if lib.nvmlInit() == 0:
                _nvml_lib = lib
                _nvml_initialized = True
                return _nvml_lib
        except Exception:
            continue

    _nvml_failed = True
    return None


def get_gpu_percent(engine_gpu: dict[str, Any] | None = None) -> int | None:
    """Return GPU utilization percentage (0-100) or None if unavailable.

    Works across native installations (via NVML or nvidia-smi) and Docker
    (via engine_gpu reported by the engine container).
    """
    # 1. Try NVML via ctypes (fastest, in-memory, 0 external tools)
    lib = _get_nvml()
    if lib:
        try:
            device = ctypes.c_void_p()
            if lib.nvmlDeviceGetHandleByIndex(0, ctypes.byref(device)) == 0:
                class Utilization(ctypes.Structure):
                    _fields_ = [("gpu", ctypes.c_uint), ("memory", ctypes.c_uint)]

                util = Utilization()
                if lib.nvmlDeviceGetUtilizationRates(device, ctypes.byref(util)) == 0:
                    return int(util.gpu)
        except Exception as exc:
            log.debug("nvml read failed: %s", exc)

    # 2. Try nvidia-smi if available on host/system
    smi = shutil.which("nvidia-smi")
    if not smi:
        known_smi = [
            r"C:\Windows\System32\nvidia-smi.exe",
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
            "/usr/lib/wsl/lib/nvidia-smi",
            "/usr/bin/nvidia-smi",
        ]
        for p in known_smi:
            if os.path.exists(p):
                smi = p
                break
    if smi:
        try:
            res = subprocess.run(
                [smi, "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                first_line = res.stdout.strip().splitlines()[0].strip()
                return max(0, min(100, int(first_line)))
        except Exception as exc:
            log.debug("nvidia-smi read failed: %s", exc)

    # 3. Docker setup fallback: use engine_gpu provided by engine
    if engine_gpu:
        if engine_gpu.get("utilization") is not None:
            return max(0, min(100, int(engine_gpu["utilization"])))
        vram_total = engine_gpu.get("vram_total")
        vram_free = engine_gpu.get("vram_free")
        if vram_total and vram_free is not None and vram_total > 0:
            return max(0, min(100, round(100.0 * (1.0 - float(vram_free) / float(vram_total)))))

    return None
