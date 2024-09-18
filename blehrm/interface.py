from abc import ABC, abstractmethod
from bleak import BLEDevice, BleakClient
from blehrm.UUIDS import (HEART_RATE_MEASUREMENT_UUID, MANUFACTURER_NAME_UUID, 
                   MODEL_NBR_UUID, BATTERY_LEVEL_UUID)
from typing import Callable, Union, Any, Optional
import numpy as np
import logging

DataCallback = Callable[[np.ndarray], None]

class SensorReaderInterface(ABC):
    """Abstract base class for sensor reader.

    This class defines the interface for interacting with various ECG chest strap sensors.
    Two methods required at minimum:
        is_supported
        _ibi_data_processor

    To support acc (or ecg) streaming, implement:
        start_acc_stream (or start_ecg_stream)
        stop_acc_stream (or stop_ecg_stream)
        _acc_data_processor (or _ecg_data_processor)
    """
    def __init__(self, ble_device: Union[BLEDevice, str]):
        """Initialize the sensor reader.

        Args:
            ble_device: The BLEDevice (bleak)
        """
        self.ble_device = ble_device
        self._ibi_callback: Optional[DataCallback] = None
        self._acc_callback: Optional[DataCallback] = None
        self._ecg_callback: Optional[DataCallback] = None
        self.logger = logging.getLogger(__name__)

    @staticmethod
    @abstractmethod
    def is_supported(device_name: str) -> bool:
        """Check if the device is supported by this sensor reader.

        Args:
            device_name: The name of the device to check.

        Returns:
            True if the device is supported, False otherwise.
        """
        pass

    async def connect(self) -> None:
        """Connect to the bleak BLE device.

        Raises:
            Exception: If connection fails.
        """
        try:
            self.bleak_client = BleakClient(self.ble_device)
            await self.bleak_client.connect()
            self.logger.info("Connected to device successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the BLE device.

        Raises:
            Exception: If disconnection fails.
        """
        try:
            await self.bleak_client.disconnect()
            self.logger.info("Disconnected from device successfully")
        except Exception as e:
            self.logger.error(f"Failed to disconnect: {e}")

    async def get_device_info(self) -> None:
        """Retrieve device information.

        This method reads the model number, manufacturer name, and battery level
        from the device.
        """
        self.model_number = await self.bleak_client.read_gatt_char(MODEL_NBR_UUID)
        self.manufacturer_name = await self.bleak_client.read_gatt_char(MANUFACTURER_NAME_UUID)
        self.battery_level = await self.bleak_client.read_gatt_char(BATTERY_LEVEL_UUID)

    async def print_device_info(self) -> None:
        """Print device information to console.

        Displays the model number, manufacturer name, and battery level.
        """   
        BLUE = "\033[94m"
        RESET = "\033[0m"
        print(f"Model No.: {BLUE}{''.join(map(chr, self.model_number))}{RESET}\n"
            f"Manufacturer: {BLUE}{''.join(map(chr, self.manufacturer_name))}{RESET}\n"
            f"Battery: {BLUE}{int(self.battery_level[0])}%{RESET}")

    @property
    def ibi_callback(self) -> DataCallback:
        if not self._ibi_callback:
            raise ValueError('Set the ibi_callback first with set_ibi_callback')
        else:
            return self._ibi_callback

    def set_ibi_callback(self, callback: DataCallback) -> None:
        self._ibi_callback = callback
        
    async def start_ibi_stream(self, callback: Callable[[np.ndarray], None]) -> None:
        """Start streaming interbeat interval data.

        Args:
            callback: Function to call with IBI data. Expects an ndarray from _ibi_data_handler.
            Function to call with IBI data. Expects a 2-element NumPy array of floats.
        """
        self.set_ibi_callback(callback)
        await self.bleak_client.start_notify(HEART_RATE_MEASUREMENT_UUID, self._ibi_data_handler)

    async def stop_ibi_stream(self) -> None:
        """Stop streaming interbeat interval data."""
        await self.bleak_client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
        
    def _ibi_data_handler(self, sender: Any, data: bytearray) -> None:
        """Handle heart rate data.

        Args:
            sender: The sender of the data.
            data: The raw heart rate data.
        """
        result = self._ibi_data_processor(data)
        for row in result:
            if row.ndim > 1:
                self.logger.warning("More than one IBI data row")
            self.ibi_callback(row)

    @abstractmethod
    def _ibi_data_processor(self, data:bytearray) -> np.ndarray:
        """ Process sensor byte data, returning 1D numpy array of the result
        """
        pass

    @property
    def acc_callback(self) -> DataCallback:
        if not self._acc_callback:
            raise ValueError('Set the acc callback first with set_acc_callback')
        else:
            return self._acc_callback

    def set_acc_callback(self, callback: DataCallback) -> None:
        self._acc_callback = callback

    async def start_acc_stream(self, callback: Callable[[np.ndarray], None]) -> None:
        """Start streaming accelerometer data.

        Args:
            callback: Function to call with accelerometer data.

        Raises:
            NotImplementedError: If ACC streaming is not supported.
        """
        raise NotImplementedError("ACC streaming is not supported for this sensor")

    async def stop_acc_stream(self) -> None:
        """Stop streaming accelerometer data.

        Raises:
            NotImplementedError: If ACC streaming is not supported.
        """
        raise NotImplementedError("ACC streaming is not supported for this sensor")

    def _acc_data_handler(self, sender: Any, data: bytearray) -> None:
        """Handle acc data.

        Args:
            sender: The sender of the data.
            data: The raw bytes data from accelerometer.
        """
        result = self._acc_data_processor(data)
        for row in result:
            if row.ndim > 1:
                self.logger.warning("More than one ACC data row")
            self.acc_callback(row)
        pass

    def _acc_data_processor(self, data:bytearray) -> np.ndarray:
        """ Process sensor byte data, returning numpy array of the result, where each row is a data point
        """
        raise NotImplementedError("ACC streaming is not supported for this sensor")

    @property
    def ecg_callback(self) -> DataCallback:
        if not self._ecg_callback:
            raise ValueError('Set the ecg callback first with set_ecg_callback')
        else:
            return self._ecg_callback
    
    def set_ecg_callback(self, callback: DataCallback) -> None:
        self._ecg_callback = callback

    async def start_ecg_stream(self) -> None:
        """Start streaming ECG data.

        Raises:
            NotImplementedError: If ECG streaming is not supported.
        """
        raise NotImplementedError("ECG streaming is not supported for this sensor")
    
    async def stop_ecg_stream(self) -> None:
        """Stop streaming ECG data.

        Raises:
            NotImplementedError: If ECG streaming is not supported.
        """
        raise NotImplementedError("ECG streaming is not supported for this sensor")
    
    def _ecg_data_handler(self, sender: Any, data: bytearray) -> None:
        """Handle ecg data.

        Args:
            sender: The sender of the data.
            data: The raw bytes ecg data.
        """
        result = self._ecg_data_processor(data)
        for row in result:
            if row.ndim > 1:
                self.logger.warning("More than one ECG data row")
            self.ecg_callback(row)
        pass

    def _ecg_data_processor(self, data:bytearray) -> np.ndarray:
        """ Process sensor byte data, returning numpy array of the result, where each row is a data point
        """
        raise NotImplementedError("ECG streaming is not supported for this sensor")
