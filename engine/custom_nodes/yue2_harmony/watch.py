"""Yeufonic: what the engine tells the app about itself.

Carried with the harmony node, so the Docker image and the Windows install both
have it.  Nothing here adds a node.

A job thread that dies on an error ComfyUI did not catch takes the process with it,
and the app never hears why.  Running out of GPU memory does this: ComfyUI catches
the first failure, frees memory to recover, and when freeing runs out too the job
thread dies before it can send its error.  So the error is written, as the thread
dies, to yeufonic/engine-fault.json in the output folder the app shares, and the app
can say what happened to the job it lost.

ComfyUI's "To see the GUI go to" at start-up sends people to the engine's own page.
When YEUFONIC_APP_URL is set, the line gives the app's address instead.
"""
import json
import logging
import os
import threading
import time

FAULT = "engine-fault.json"


def out_of_memory(exc):
    """ComfyUI's own test (comfy.model_management.is_oom), without its side effect of
    clearing CUDA's pending error, along the chain of errors behind this one."""
    try:
        import comfy.model_management as mm
        oom = getattr(mm, "OOM_EXCEPTION", None)
    except Exception:
        oom = None
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if oom is not None and isinstance(exc, oom):
            return True
        if getattr(exc, "error_code", None) == 2 or "out of memory" in str(exc).lower():
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def running_prompt():
    try:
        import server
        return getattr(server.PromptServer.instance, "last_prompt_id", None)
    except Exception:
        return None


def output_folder():
    import folder_paths
    return folder_paths.get_output_directory()


def write_fault(exc):
    """Written whole or not at all: a half-written note is worse than none."""
    try:
        folder = os.path.join(output_folder(), "yeufonic")
        os.makedirs(folder, exist_ok=True)
        record = {"prompt_id": running_prompt(), "at": time.time(), "out_of_memory": out_of_memory(exc),
                  "type": type(exc).__name__, "message": " ".join(str(exc).split())[:300]}
        path = os.path.join(folder, FAULT)
        with open(path + ".tmp", "w", encoding="utf-8") as handle:
            json.dump(record, handle)
            handle.flush()
            os.fsync(handle.fileno())
        # The engine may run as root and the app as its user, who must read it.
        os.chmod(path + ".tmp", 0o644)
        os.replace(path + ".tmp", path)
    except Exception:
        pass


_previous_hook = threading.excepthook


def job_thread_died(args):
    thread = getattr(args, "thread", None)
    if thread is not None and "prompt_worker" in (thread.name or "") and args.exc_value is not None:
        write_fault(args.exc_value)
    _previous_hook(args)


class PointAtYeufonic(logging.Filter):
    def filter(self, record):
        message = record.msg if isinstance(record.msg, str) else ""
        app = os.environ.get("YEUFONIC_APP_URL")
        if app and message.startswith("To see the GUI go to:"):
            record.msg = f"To see the GUI go to: {app}"
            record.args = ()
        return True


def _get_gpu_utilization():
    try:
        import ctypes
        import sys
        lib = ctypes.CDLL("libnvidia-ml.so.1" if sys.platform != "win32" else "nvml.dll")
        if lib.nvmlInit() == 0:
            dev = ctypes.c_void_p()
            if lib.nvmlDeviceGetHandleByIndex(0, ctypes.byref(dev)) == 0:
                class Utilization(ctypes.Structure):
                    _fields_ = [("gpu", ctypes.c_uint), ("memory", ctypes.c_uint)]
                u = Utilization()
                if lib.nvmlDeviceGetUtilizationRates(dev, ctypes.byref(u)) == 0:
                    return int(u.gpu)
    except Exception:
        pass
    try:
        import subprocess
        res = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=1.0, check=False)
        if res.returncode == 0 and res.stdout.strip():
            return int(res.stdout.strip().splitlines()[0].strip())
    except Exception:
        pass
    return None


def install_routes():
    try:
        import server
        from aiohttp import web
        prompt_server = getattr(server.PromptServer, "instance", None)
        if prompt_server and hasattr(prompt_server, "routes"):
            @prompt_server.routes.get("/yeufonic/gpu_stats")
            async def gpu_stats(request):
                return web.json_response({"utilization": _get_gpu_utilization()})
    except Exception:
        pass


def install():
    threading.excepthook = job_thread_died
    logging.getLogger().addFilter(PointAtYeufonic())
    install_routes()

