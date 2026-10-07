"""Files the engine writes on the host.

The engine runs as root, and its models folder is the user's own, mounted in.  A folder the engine makes there belongs
to root: whoever runs the app or the setup script as themselves can neither write in it nor tidy it, and may have no
root to change that.  So what the engine writes for itself (a model it fetches) is opened up to everyone, and anyone can
delete or replace it.
"""
from __future__ import annotations

import os


def open_up(path: str) -> None:
    """Every folder under `path` (and it) readable, writable and enterable by all, and every file readable and writable
    by all.  Best effort: a mode that cannot be set is left, and a link is left alone."""
    if os.name != "posix" or not os.path.isdir(path):
        return
    for here, dirs, files in os.walk(path):
        for name in [here] + [os.path.join(here, d) for d in dirs] + [os.path.join(here, f) for f in files]:
            if os.path.islink(name):
                continue
            try:
                os.chmod(name, 0o777 if os.path.isdir(name) else (os.stat(name).st_mode & 0o777) | 0o666)
            except OSError:
                pass
