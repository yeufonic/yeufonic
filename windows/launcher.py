"""Start Yeufonic on Windows: the engine (ComfyUI) and the app together, then the page,
in a window of its own, as soon as the app answers.  The engine takes longer; the page
says it is starting, and anything asked of it meanwhile waits.

Yeufonic.exe runs this with pythonw, so there is no console window.  An icon by the
clock stands for the running app: click it to open the window, right-click it to quit.
Closing the window leaves Yeufonic running there, so a render or a training run is not
stopped by accident.  Problems are shown in a message box.  With --console (the
"with console" shortcut) it also reports to a console window, for diagnosing.

The engine, the app and the window's browser belong to a Windows job that ends when
this process does, however it ends.  Their output goes to logs\\engine.log and
logs\\app.log, and how long each took to start to logs\\launcher.log.

Ports and folders can be changed in settings.ini beside this file.
"""
from __future__ import annotations

import configparser
import ctypes
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.request
import webbrowser
from ctypes import wintypes
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE / "engine"
COMFY = ENGINE / "ComfyUI"
LOGS = HERE / "logs"
STATE = HERE / "state"
ICON = HERE / "yeufonic.ico"
# The window's own browser profiles, one per browser, apart from the user's: they keep
# the window's size and place, and nothing of theirs.
PROFILES = HERE / "browsers"
# Browsers built on Chromium, which can open a page as an app window of its own.
APP_BROWSERS = ("chrome.exe", "msedge.exe", "brave.exe", "vivaldi.exe", "chromium.exe")
APP = "Yeufonic"
CONSOLE = "--console" in sys.argv[1:]


def settings() -> dict:
    """Ports, the folder the library lives in, and how the page opens.  settings.ini
    overrides the defaults.  window = app opens the page in a window of its own (Edge's
    app mode); window = browser opens it in the default browser instead."""
    values = {"app_port": "8090", "engine_port": "8188", "engine_args": "", "data_dir": str(HERE / "data"),
              "import_roots": str(Path.home()), "open_browser": "yes", "window": "app"}
    ini = HERE / "settings.ini"
    if ini.exists():
        parser = configparser.ConfigParser()
        parser.read(ini, encoding="utf-8")
        if parser.has_section("yue2"):
            values.update({k: v for k, v in parser.items("yue2") if v.strip()})
    return values


# ------------------------------------------------------------------ Win32
user32 = ctypes.WinDLL("user32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT), ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128), ("dwState", wintypes.DWORD), ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256), ("uVersion", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64), ("dwInfoFlags", wintypes.DWORD),
                ("guidItem", ctypes.c_byte * 16), ("hBalloonIcon", wintypes.HICON)]


user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND,
                                   wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int,
                              wintypes.UINT]
user32.LoadImageW.restype = wintypes.HANDLE
user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
user32.CreatePopupMenu.restype = wintypes.HMENU
user32.SetMenuDefaultItem.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
user32.TrackPopupMenu.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  wintypes.HWND, wintypes.LPVOID]
user32.DestroyMenu.argtypes = [wintypes.HMENU]
user32.SetTimer.argtypes = [wintypes.HWND, ctypes.c_size_t, wintypes.UINT, wintypes.LPVOID]
user32.KillTimer.argtypes = [wintypes.HWND, ctypes.c_size_t]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

WM_CLOSE, WM_DESTROY, WM_TIMER, WM_NULL = 0x0010, 0x0002, 0x0113, 0x0000
WM_LBUTTONUP, WM_RBUTTONUP, WM_CONTEXTMENU = 0x0202, 0x0205, 0x007B
WM_TRAY = 0x8000 + 1   # WM_APP + 1: the icon's clicks
WM_SHOW = 0x8000 + 2   # WM_APP + 2: a second start asks this one to show the window
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP, NIF_INFO = 0x1, 0x2, 0x4, 0x10
MB_OK, MB_YESNO, MB_ICONERROR, MB_ICONQUESTION, MB_ICONINFO = 0x0, 0x4, 0x10, 0x20, 0x40
MB_DEFBUTTON2, MB_SETFOREGROUND, MB_TOPMOST, IDYES = 0x100, 0x10000, 0x40000, 6
MF_STRING, MF_SEPARATOR = 0x0, 0x800
TPM_RIGHTBUTTON, TPM_NONOTIFY, TPM_RETURNCMD = 0x2, 0x80, 0x100
CMD_OPEN, CMD_LOGS, CMD_QUIT = 1, 2, 3
WINDOW_CLASS = "YeufonicLauncher"


# ------------------------------------------------------------------ the job
# A job with KILL_ON_JOB_CLOSE ends every process in it when its last handle
# closes, which is when this process ends, however it ends.
class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _BasicLimits(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _BasicLimits), ("IoInfo", _IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class _IdList(ctypes.Structure):
    _fields_ = [("assigned", wintypes.DWORD), ("listed", wintypes.DWORD), ("ids", ctypes.c_size_t * 4096)]


kernel32.CreateJobObjectW.restype = wintypes.HANDLE
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
kernel32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                               wintypes.DWORD, ctypes.c_void_p]
kernel32.GetTickCount64.restype = ctypes.c_ulonglong


def join_a_job():
    job = kernel32.CreateJobObjectW(None, None)
    limits = _ExtendedLimits()
    # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE (0x2000) | JOB_OBJECT_LIMIT_BREAKAWAY_OK (0x0800)
    limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x0800
    kernel32.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits))
    if not kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess()):
        say("(could not tie the programs to this launcher; stop them from Task Manager if they linger)")
    return job


def job_processes(job) -> set[int]:
    """The ids of every process in the job: the engine, the app, the window's browser
    and whatever they started."""
    found = _IdList()
    if not kernel32.QueryInformationJobObject(job, 3, ctypes.byref(found), ctypes.sizeof(found), None):
        return set()
    return {found.ids[i] for i in range(found.listed)}


# ---------------------------------------------------------------- helpers
def answering(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1) as reply:
            return reply.status == 200
    except OSError:
        return False


def port_taken(port: int) -> bool:
    import socket
    with socket.socket() as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def tail(path: Path, lines: int = 15) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


def windows_uptime() -> float:
    """Seconds since Windows started: a start soon after a reboot reads everything from
    disk, and is the slow one."""
    return kernel32.GetTickCount64() / 1000


def say(line: str) -> None:
    """To the console, when there is one.  pythonw has none."""
    if CONSOLE and sys.stdout:
        print(line, flush=True)


def record(line: str) -> None:
    """Said, and kept in logs\\launcher.log so start-up times can be compared."""
    say(line)
    try:
        LOGS.mkdir(exist_ok=True)
        with (LOGS / "launcher.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {line}\n")
    except OSError:
        pass


def message(text: str, flags: int = MB_OK | MB_ICONINFO) -> int:
    return user32.MessageBoxW(None, text, APP, flags | MB_SETFOREGROUND | MB_TOPMOST)


def fail(text: str, log: Path | None = None) -> None:
    """Say what went wrong, then stop: leaving ends the job, and the programs in it."""
    record(text)
    if log:
        say(f"The last lines of {log}:\n{tail(log)}")
        if message(f"{text}\n\nThe details are in {log}. Open the logs folder?", MB_YESNO | MB_ICONERROR) == IDYES:
            os.startfile(LOGS)
    else:
        message(text, MB_OK | MB_ICONERROR)
    sys.exit(1)


def default_browser() -> str | None:
    """The program Windows opens web links with, from the user's choice for https and
    that choice's open command."""
    try:
        import shlex
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations"
                            r"\UrlAssociations\https\UserChoice") as key:
            prog_id = winreg.QueryValueEx(key, "ProgId")[0]
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{prog_id}\shell\open\command") as key:
            command = winreg.QueryValue(key, None)
        return shlex.split(command, posix=False)[0].strip('"')
    except (OSError, IndexError, ValueError):
        return None


def app_browser() -> str | None:
    """The browser for the page's window: the default one when it can open an app
    window (Chrome, Edge, Brave, Vivaldi), else Edge, which comes with Windows 10 and
    11.  Firefox cannot, so its users get Edge's window, which is only its engine: none
    of their browsing comes into it.  None means a tab in the default browser."""
    chosen = default_browser()
    if chosen and Path(chosen).name.lower() in APP_BROWSERS and Path(chosen).exists():
        return chosen
    return find_edge()


def find_edge() -> str | None:
    """Edge comes with Windows 10 and 11, whatever browser is the default, though in
    some countries it can be removed."""
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
        if base:
            path = Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
            if path.exists():
                return str(path)
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe") as key:
            return winreg.QueryValue(key, None) or None
    except OSError:
        return None


# ------------------------------------------------------- the window's identity
# The taskbar knows a window by its app ID, and pinning one records its relaunch
# command.  An Edge app window says Edge for both, so a pin had Edge's icon and started
# Edge.  These properties, set on the window, make it Yeufonic's: its own taskbar group,
# and a pin that starts Yeufonic.exe with our icon.
class _GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8)]


class _PROPERTYKEY(ctypes.Structure):
    _fields_ = [("fmtid", _GUID), ("pid", wintypes.DWORD)]


class _PROPVARIANT(ctypes.Structure):
    _fields_ = [("vt", ctypes.c_ushort), ("r1", ctypes.c_ushort), ("r2", ctypes.c_ushort),
                ("r3", ctypes.c_ushort), ("value", ctypes.c_void_p), ("pad", ctypes.c_void_p)]


def _guid(text: str) -> _GUID:
    import uuid
    raw = uuid.UUID(text).bytes_le
    return _GUID.from_buffer_copy(raw)


_APP_USER_MODEL = "{9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3}"
# PKEY_AppUserModel_RelaunchCommand, _RelaunchIconResource, _RelaunchDisplayNameResource, _ID
_RELAUNCH_COMMAND, _RELAUNCH_ICON, _RELAUNCH_NAME, _APP_ID = 2, 3, 4, 5
APP_ID = "Yeufonic.App"


def claim_window(hwnd: int) -> bool:
    """Make a window of Edge's Yeufonic's on the taskbar.  The relaunch properties go
    first: Windows reads them when the app ID arrives."""
    shell32.SHGetPropertyStoreForWindow.argtypes = [wintypes.HWND, ctypes.POINTER(_GUID), ctypes.POINTER(ctypes.c_void_p)]
    store = ctypes.c_void_p()
    iid = _guid("{886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99}")   # IID_IPropertyStore
    if shell32.SHGetPropertyStoreForWindow(hwnd, ctypes.byref(iid), ctypes.byref(store)) != 0 or not store:
        return False
    vtable = ctypes.cast(ctypes.cast(store, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
    set_value = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(_PROPERTYKEY),
                                   ctypes.POINTER(_PROPVARIANT))(vtable[6])
    commit = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(vtable[7])
    release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
    exe = HERE / "Yeufonic.exe"
    values = [(_RELAUNCH_COMMAND, f'"{exe}"'), (_RELAUNCH_NAME, APP),
              (_RELAUNCH_ICON, f"{exe},0"), (_APP_ID, APP_ID)]
    ok = True
    for pid, text in values:
        key = _PROPERTYKEY(_guid(_APP_USER_MODEL), pid)
        buffer = ctypes.create_unicode_buffer(text)   # SetValue copies it
        variant = _PROPVARIANT(vt=31, value=ctypes.cast(buffer, ctypes.c_void_p))   # VT_LPWSTR
        ok = set_value(store, ctypes.byref(key), ctypes.byref(variant)) == 0 and ok
    commit(store)
    release(store)
    return ok


def seed_browser_profile(profile: Path) -> None:
    """Preferences for the window's profile: no signing in, and prompt where to save downloads."""
    prefs_file = profile / "Default" / "Preferences"
    prefs = {}
    if prefs_file.exists():
        try:
            prefs = json.loads(prefs_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            prefs = {}
    prefs.setdefault("signin", {})["allowed"] = False
    prefs.setdefault("signin", {})["allowed_on_next_startup"] = False
    prefs.setdefault("sync", {})["requested"] = False
    prefs.setdefault("browser", {})["has_seen_welcome_page"] = True
    if "download" not in prefs or not isinstance(prefs["download"], dict):
        prefs["download"] = {}
    prefs["download"]["prompt_for_download"] = True
    try:
        (profile / "Default").mkdir(parents=True, exist_ok=True)
        prefs_file.write_text(json.dumps(prefs), encoding="utf-8")
    except OSError:
        pass


# ------------------------------------------------------------ the launcher
class Launcher:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.app_port, self.engine_port = int(cfg["app_port"]), int(cfg["engine_port"])
        self.url = f"http://localhost:{self.app_port}"
        self.app_url = f"http://127.0.0.1:{self.app_port}/api/health"
        self.engine_url = f"http://127.0.0.1:{self.engine_port}/system_stats"
        self.job = None
        self.programs: tuple = ()
        self.started = 0.0
        self.app_ready = self.engine_ready = False
        self.had_window = False
        self.claimed: set[int] = set()
        self.quitting = False
        self.hwnd = None
        self._wndproc = WNDPROC(self.wndproc)   # kept, so it is not collected
        self.taskbar_created = user32.RegisterWindowMessageW("TaskbarCreated")
        # IMAGE_ICON, from the file, at the size the notification area wants.
        self.icon = user32.LoadImageW(None, str(ICON), 1, user32.GetSystemMetrics(49),
                                      user32.GetSystemMetrics(50), 0x10)

    # ---------- the icon by the clock
    def notify(self, action: int, balloon: tuple[str, str] | None = None) -> None:
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        data.hWnd, data.uID = self.hwnd, 1
        data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        data.uCallbackMessage, data.hIcon = WM_TRAY, self.icon
        data.szTip = self.tip()[:127]
        if balloon:
            data.uFlags |= NIF_INFO
            data.szInfoTitle, data.szInfo = balloon[0][:63], balloon[1][:255]
            data.dwInfoFlags = 0x1   # NIIF_INFO
        shell32.Shell_NotifyIconW(action, ctypes.byref(data))

    def tip(self) -> str:
        if not self.app_ready:
            return f"{APP}: starting"
        return APP if self.engine_ready else f"{APP}: the engine is starting"

    def menu(self) -> None:
        menu = user32.CreatePopupMenu()
        user32.AppendMenuW(menu, MF_STRING, CMD_OPEN, f"Open {APP}")
        user32.AppendMenuW(menu, MF_STRING, CMD_LOGS, "Open the logs folder")
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, CMD_QUIT, f"Quit {APP}")
        user32.SetMenuDefaultItem(menu, CMD_OPEN, False)
        point = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point))
        user32.SetForegroundWindow(self.hwnd)   # else the menu stays open when clicked away from
        chosen = user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_NONOTIFY | TPM_RETURNCMD,
                                       point.x, point.y, 0, self.hwnd, None)
        user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        user32.DestroyMenu(menu)
        if chosen == CMD_OPEN:
            self.show()
        elif chosen == CMD_LOGS:
            os.startfile(LOGS)
        elif chosen == CMD_QUIT:
            self.ask_to_quit()

    # ---------- the page's window
    def windows(self) -> list[int]:
        """The page's own windows: visible browser windows of processes in our job."""
        ids = job_processes(self.job) if self.job else set()
        found: list[int] = []

        def each(hwnd, _):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in ids and user32.IsWindowVisible(hwnd):
                name = ctypes.create_unicode_buffer(64)
                user32.GetClassNameW(hwnd, name, 64)
                if name.value.startswith("Chrome_WidgetWin"):
                    found.append(hwnd)
            return True

        user32.EnumWindows(WNDENUMPROC(each), 0)
        return found

    def show(self) -> None:
        """Bring the page's window forward, or open one."""
        if not self.app_ready:
            return
        open_windows = self.windows()
        if open_windows:
            hwnd = open_windows[0]
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)   # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            return
        browser = app_browser() if self.cfg["window"].lower() != "browser" else None
        if not browser:
            webbrowser.open(self.url)
            return
        # A profile of its own, which the browser would otherwise sign in to the user's
        # account: Edge synced their extensions and opened an Extensions tab beside it.
        profile = PROFILES / Path(browser).stem.lower()
        args = [browser, f"--app={self.url}", f"--user-data-dir={profile}", "--no-first-run",
                "--no-default-browser-check", "--disable-sync", "--disable-extensions"]
        if not profile.exists():
            args.append("--window-size=1500,950")   # the first time; after that, where it was left
        seed_browser_profile(profile)
        record(f"Opening the window in {Path(browser).stem}.")
        subprocess.Popen(args)   # in our job, so it goes when Yeufonic does

    # ---------- quitting
    def busy(self) -> str:
        """What quitting would stop, in a few words, or nothing."""
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.app_port}/api/state", timeout=2) as reply:
                state = json.load(reply)
        except (OSError, ValueError):
            return ""
        if state.get("training"):
            return "A LoRA is training. Quitting stops it."
        if state.get("current") or state.get("queue"):
            return "A job is running. Quitting stops it."
        return ""

    def ask_to_quit(self) -> None:
        if self.quitting:
            return
        warning = self.busy()
        text = f"Quit {APP}?" + (f"\n\n{warning}" if warning else "")
        if message(text, MB_YESNO | MB_ICONQUESTION | (MB_DEFBUTTON2 if warning else 0)) != IDYES:
            return
        self.quitting = True
        record("Quit.")
        # The window closes as a window should, rather than being cut off with the rest.
        for hwnd in self.windows():
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        deadline = time.time() + 3
        while self.windows() and time.time() < deadline:
            time.sleep(0.2)
        self.notify(NIM_DELETE)
        user32.DestroyWindow(self.hwnd)

    def stop_with(self, text: str, log: Path | None = None) -> None:
        # fail() shows a message box, and a message box runs a message loop of its own, so this half-second timer
        # would fire again underneath it, find the engine still dead, and stack another box: 126 of them in one
        # failure. Stop the timer and refuse further ticks before the first box goes up.
        self.quitting = True
        user32.KillTimer(self.hwnd, 1)
        self.notify(NIM_DELETE)
        fail(text, log)

    # ---------- the loop
    def tick(self) -> None:
        if self.quitting:
            return
        for name, process, log in self.programs:
            if process.poll() is not None:
                self.stop_with(f"The {name} stopped unexpectedly.", log)
        now = time.time()
        if not self.app_ready:
            if answering(self.app_url):
                self.app_ready = True
                record(f"App ready in {now - self.started:.1f} s.")
                self.notify(NIM_MODIFY)
                if self.cfg["open_browser"].lower() not in ("no", "false", "0"):
                    self.show()
            elif now - self.started > 180:
                self.stop_with("The app did not start within 3 minutes.", LOGS / "app.log")
        if not self.engine_ready:
            if answering(self.engine_url):
                self.engine_ready = True
                record(f"Engine ready in {now - self.started:.1f} s.")
                self.notify(NIM_MODIFY)
            elif now - self.started > 600:
                self.stop_with("The engine did not start within 10 minutes.", LOGS / "engine.log")
        if self.app_ready:
            open_windows = self.windows()
            for hwnd in open_windows:
                if hwnd not in self.claimed and claim_window(hwnd):
                    self.claimed.add(hwnd)
            # The first time the window is closed, say where Yeufonic went.
            open_now = bool(open_windows)
            if self.had_window and not open_now:
                hint = STATE / "closed-to-tray"
                if not hint.exists():
                    self.notify(NIM_MODIFY, balloon=(f"{APP} is still running",
                                                     "It's by the clock. Click it to open, or right-click it to quit."))
                    try:
                        STATE.mkdir(exist_ok=True)
                        hint.write_text("shown", encoding="utf-8")
                    except OSError:
                        pass
            self.had_window = open_now

    def wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_TRAY:
                if lparam == WM_LBUTTONUP:
                    self.show()
                elif lparam in (WM_RBUTTONUP, WM_CONTEXTMENU):
                    self.menu()
                return 0
            if msg == WM_SHOW:
                self.show()
                return 0
            if msg == WM_TIMER:
                self.tick()
                return 0
            if msg == self.taskbar_created:   # Explorer restarted: the icon has to be added again
                self.notify(NIM_ADD)
                return 0
            if msg == WM_CLOSE:
                self.ask_to_quit()
                return 0
            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
        except SystemExit:
            # fail() inside a window callback: end the loop, and the process with it.
            user32.PostQuitMessage(1)
            self.exit_code = 1
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def run(self, data: Path) -> int:
        self.exit_code = 0
        ctypes.WinDLL("ole32").CoInitialize(None)   # for the window's property store
        cls = WNDCLASSW()
        cls.lpfnWndProc = self._wndproc
        cls.hInstance = kernel32.GetModuleHandleW(None)
        cls.lpszClassName = WINDOW_CLASS
        user32.RegisterClassW(ctypes.byref(cls))
        # Never shown: it carries the icon's messages and the timer.
        self.hwnd = user32.CreateWindowExW(0, WINDOW_CLASS, APP, 0, 0, 0, 0, 0, None, None, cls.hInstance, None)
        self.notify(NIM_ADD)
        self.job = join_a_job()
        self.start(data)
        user32.SetTimer(self.hwnd, 1, 500, None)
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        return self.exit_code

    def start(self, data: Path) -> None:
        """The engine and the app at once: the app is up in seconds and copes with an
        engine still starting, so the page need not wait for ComfyUI."""
        engine_python = ENGINE / "python_embeded" / "python.exe"
        self.started = time.time()
        record(f"Starting the engine and the app (Windows up {windows_uptime() / 60:.0f} min)...")
        engine_log = LOGS / "engine.log"
        engine = subprocess.Popen(
            [str(engine_python), "-s", str(COMFY / "main.py"), "--windows-standalone-build",
             "--disable-auto-launch", "--listen", "127.0.0.1", "--port", str(self.engine_port),
             *shlex.split(self.cfg.get("engine_args", ""))],
            cwd=str(COMFY), stdout=engine_log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
            # Its start-up message then sends people to the app, not the engine.
            env=dict(os.environ, YEUFONIC_APP_URL=f"http://127.0.0.1:{self.app_port}"))

        env = dict(os.environ)
        tools = HERE / "tools"
        env.update({
            "PATH": os.pathsep.join([str(HERE / "venv" / "Scripts"), str(tools / "ffmpeg" / "bin"), str(tools / "fluidsynth" / "bin"), env.get("PATH", "")]),
            "DATA_DIR": str(data),
            "MODELS_DIR": str(COMFY / "models"),
            "VERSION_FILE": str(HERE / "studio" / "VERSION"),
            "BUILD_FILE": str(HERE / "studio" / "BUILD"),
            "ENGINE_URL": f"http://127.0.0.1:{self.engine_port}",
            "ENGINE_INPUT_DIR": str(COMFY / "input"),
            "ENGINE_OUTPUT_DIR": str(COMFY / "output"),
            "IMPORT_ROOTS": self.cfg["import_roots"],
            "TORCH_HOME": str(data / "models" / "torch"),
            "HF_HOME": str(data / "models" / "whisper"),
            "TRAINING_ENABLED": "1",
            "PYTHONUTF8": "1",
            # Set only by a test build of the installer: where to look for an update to try.
            "YEUFONIC_UPDATE_MANIFEST": self.cfg.get("update_manifest", ""),
            # Windows without Developer Mode cannot make symlinks; the library copies instead
            # and says so every time.
            "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
        })
        app_log = LOGS / "app.log"
        app = subprocess.Popen(
            [str(HERE / "venv" / "Scripts" / "python.exe"), "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", str(self.app_port), "--no-access-log"],
            cwd=str(HERE / "studio"), env=env, stdout=app_log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        self.programs = (("engine", engine, engine_log), ("app", app, app_log))
        say(f"{APP} opens at {self.url} once the app answers. Quit it from the icon by the clock.")


def main() -> int:
    if CONSOLE:
        os.system(f"title {APP}")
        say(APP)
    cfg = settings()
    app_port, engine_port = int(cfg["app_port"]), int(cfg["engine_port"])

    # Already running (a second click on the shortcut): that copy shows its window.
    running = user32.FindWindowW(WINDOW_CLASS, None)
    if running:
        user32.PostMessageW(running, WM_SHOW, 0, 0)
        return 0
    if answering(f"http://127.0.0.1:{app_port}/api/health"):
        # Started some other way, such as by an older launcher: just open the page.
        webbrowser.open(f"http://localhost:{app_port}")
        return 0
    for port, what in ((app_port, "the app"), (engine_port, "the engine")):
        if port_taken(port):
            fail(f"Port {port}, which {what} uses, is taken by another program. If Docker Desktop is "
                 f"running Yeufonic or ComfyUI, stop it first. The ports can be changed in "
                 f"{HERE / 'settings.ini'}.")
    if not (ENGINE / "python_embeded" / "python.exe").exists() or not (COMFY / "main.py").exists():
        fail("The engine is not installed. Run the installer again.")

    LOGS.mkdir(exist_ok=True)
    # The first version kept a single Edge profile here; each browser has its own now.
    if (HERE / "browser").is_dir():
        import shutil
        shutil.rmtree(HERE / "browser", ignore_errors=True)
    data = Path(cfg["data_dir"])
    data.mkdir(parents=True, exist_ok=True)
    return Launcher(cfg).run(data)


if __name__ == "__main__":
    sys.exit(main())
