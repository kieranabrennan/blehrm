"""
blehrm - A package for interfacing with Bluetooth Low Energy Heart Rate Monitors.

This package provides a unified interface for various BLE ECG sensors,
allowing easy connection, data streaming, and device management.
"""

__version__ = "0.1.0"

from .registry import BlehrmRegistry
from .interface import BlehrmClientInterface
from . import UUIDS
from . import clients

from .registry import DeviceNotSupportedError

from typing import List, Tuple
from bleak import BLEDevice
from tabulate import tabulate

class Blehrm:

    @staticmethod
    def create_client(ble_device: BLEDevice) -> BlehrmClientInterface:
        return BlehrmRegistry.create_client(ble_device)

    @staticmethod
    def print_registered_devices() -> None:
        '''
        Print the details of the registered devices in a formatted table
        '''
        sensor_names = BlehrmRegistry.get_registered_sensors()
        if not sensor_names:
            print("No registered sensors.")
            return
        
        headers = ["Name", "Services"]
        table_data = []
        for name in sensor_names:
            services = BlehrmRegistry.get_device_services(name)
            services_str = ", ".join([s for s, available in services.items() if available])

            table_data.append([name, services_str])

        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    
    @staticmethod
    def get_supported_devices(ble_devices: List[BLEDevice]) -> List[Tuple[BLEDevice, str]]:
        return BlehrmRegistry.get_supported_devices(ble_devices)

    @staticmethod
    def print_supported_devices(ble_devices: List[BLEDevice]) -> None:
        """
        Print details of BLEDevice objects in a formatted table.

        Args:
        supported_devices (List[Tuple[BLEDevice, BlehrmClientInterface]]): A list of BLEDevice objects 
        to print and their corresponding class, and available services
        """
        supported_devices = BlehrmRegistry.get_supported_devices(ble_devices)
        
        if not supported_devices:
            print("No supported devices found.")
            return

        headers = ["Name", "Address", "Type", "Services"]
        table_data = []

        for device, device_type in supported_devices:
            name = device.name if device.name else "N/A"
            address = device.address
            services = BlehrmRegistry.get_device_services(device_type)
            services_str = ", ".join([s for s, available in services.items() if available])

            table_data.append([name, address, device_type, services_str])

        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

blehrm = Blehrm()