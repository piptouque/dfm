"""Config and state management tools."""
import sys
import os
from pathlib import Path

def home_dir():
    """Return the home user directory"""
    return Path.home()

def xdg_dir():
    """Return the XDG_CONFIG_HOME or default."""
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config is not None:
        return xdg_config
    return home_dir().joinpath(".config")

def system_dir():
    """Return the system-wide config directory"""
    platform = os.platform
    if platform.startswith('linux') or platform.startswith('darwin'):
        return Path('/etc')
    elif platform.startswith('win32') or platform.startswith('cygwin'):
        # see: https://learn.microsoft.com/en-us/windows/deployment/usmt/usmt-recognized-environment-variables
        # and:https://stackoverflow.com/a/2363730
        return Path(os.getenv("ALLUSERSAPPDATA"))
    else:
        raise NotImplemented


def dfm_dir(is_system):
    """Return the dfm configuration / state directory."""
    if os.getenv("DFM_CONFIG_DIR"):
        return os.getenv("DFM_CONFIG_DIR")
    config_dir = system_dir() if is_system else xdg_dir()
    return config_dir.joinpath("dfm")
