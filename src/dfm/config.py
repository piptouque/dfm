"""Config and state management tools."""

import os
from pathlib import Path

def home_dir():
    """Return the home user directory"""
    dir = Path.home()
    return dir


def xdg_dir():
    """Return the XDG_CONFIG_HOME or default."""
    if os.getenv("XDG_CONFIG_HOME"):
        return os.getenv("XDG_CONFIG_HOME")
    return os.path.join(home_dir(), ".config")


def dfm_dir():
    """Return the dfm configuration / state directory."""
    if os.getenv("DFM_CONFIG_DIR"):
        return os.getenv("DFM_CONFIG_DIR")
    return os.path.join(xdg_dir(), "dfm")
