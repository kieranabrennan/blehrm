from blehrm.interface import SensorReaderInterface
from typing import Dict, Type, List, Tuple, Any, Optional
from bleak import BLEDevice
from tabulate import tabulate

class blehrmRegistry:
    """Registry for available sensors.
    Register a sensor class with the decorator:
        
        @blehrmRegistry.register("SensorName")

    Methods:
        register
        _is_method_overwritten
        get_registered_sensors
        device_support
        get_supported_devices
        get_device_class
        get_device_services
        create_reader
        print_supported_devices
    """

    _sensors: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, sensor_name: str):
        """Register sensors using a decorator.

        This method is used as a decorator to register sensor classes in the _sensors dict.
        Note: Decorators are run at import time.

        Args:
            sensor_name: The name of the sensor to register.

        Returns:
            A decorator function that registers the sensor class.
        """
        def decorator(sensor_class: Type[SensorReaderInterface]):
            services = {
                'ibi': hasattr(sensor_class, 'start_ibi_stream'),
                'acc': cls._is_method_overridden(sensor_class, '_acc_data_processor'),
                'ecg': cls._is_method_overridden(sensor_class, '_ecg_data_processor')
            }
            cls._sensors[sensor_name] = {
                'class' : sensor_class,
                'services' : services
            }
            return sensor_class
        return decorator
    
    @staticmethod
    def _is_method_overridden(sensor_class: Type[SensorReaderInterface], method_name: str) -> bool:
        """Check if a method is overridden in the concrete subclass."""
        if not hasattr(sensor_class, method_name):
            return False
        concrete_method = getattr(sensor_class, method_name)
        base_method = getattr(SensorReaderInterface, method_name)
        return concrete_method is not base_method

    @classmethod
    def get_registered_sensors(cls) -> List[str]:
        """Get a list of registered sensors.

        Returns:
            A list of names (str) of registered sensors.
        """
        return [s for s in cls._sensors.keys()]
    
    @classmethod
    def device_support(cls, device: BLEDevice) -> Optional[str]:
        ''' Returns the class name of a BLEDevice if it is supported, otherwise returns None
        '''
        for sensor_class_name, sensor_info in cls._sensors.items():
            if sensor_info['class'].is_supported(device.name):
                return sensor_class_name
        return None

    @classmethod
    def get_supported_devices(cls, devices: List[BLEDevice]) -> List[Tuple[BLEDevice, str]]:
        """Get supported sensors for given BLEDevices. Support is checked based on device.name

        Args:
            device_names: A list of devices to check for support.

        Returns:
            A list of tuples containing the device (BLEDevice) and device type for supported devices.
        """
        supported = []
        for device in devices:
            support = cls.device_support(device)
            if support:
                supported.append((device, support))
        return supported
    
    @classmethod
    def get_device_class(cls, device_type: str) -> SensorReaderInterface:
        ''' Returns the class of the device with device_type
        '''
        return cls._sensors[device_type]['class']
    
    @classmethod
    def get_device_services(cls, device_type: str) -> Dict[str, bool]:
        ''' Returns the services for the device with device_type
        '''
        return cls._sensors[device_type]['services']

    @classmethod
    def create_reader(cls, device: BLEDevice) -> SensorReaderInterface:
        ''' Returns a concrete subclass of SensorReaderInterface for the BLEDevice
        '''
        support = cls.device_support(device)
        if not support:
            raise DeviceNotSupportedError(f"Device {device.name} is not supported")
        device_class = cls.get_device_class(support)
        return device_class(device)

    @staticmethod
    def print_supported_devices(supported_devices: List[Tuple[BLEDevice, SensorReaderInterface]]) -> None:
        """
        Print details of BLEDevice objects in a formatted table.

        Args:
        supported_devices (List[Tuple[BLEDevice, SensorReaderInterface]]): A list of BLEDevice objects 
        to print and their corresponding class, and available services

        Returns:
        None: This function prints to stdout and doesn't return anything.
        """
        if not supported_devices:
            print("No supported devices found.")
            return

        headers = ["Name", "Address", "Type", "Services"]
        table_data = []

        for device, device_type in supported_devices:
            name = device.name if device.name else "N/A"
            address = device.address
            services = blehrmRegistry.get_device_services(device_type)
            services_str = ", ".join([s for s, available in services.items() if available])

            table_data.append([name, address, device_type, services_str])

        print(tabulate(table_data, headers=headers, tablefmt="simple"))

class DeviceNotSupportedError(Exception):
    pass