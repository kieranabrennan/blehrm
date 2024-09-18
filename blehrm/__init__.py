"""
blehrm - A package for interfacing with Bluetooth Low Energy Heart Rate Monitors.

This package provides a unified interface for various BLE ECG sensors,
allowing easy connection, data streaming, and device management.
"""

__version__ = "0.1.0"

from . import registry
from . import interface
from . import UUIDS

from .registry import DeviceNotSupportedError
