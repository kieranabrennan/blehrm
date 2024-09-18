from blehrm.interface import SensorReaderInterface
from blehrm.registry import blehrmRegistry
import time
import numpy as np

@blehrmRegistry.register("GarminHRMPro")
class GarminHRMProReader(SensorReaderInterface):
    
    def __init__(self, ble_device):
        super().__init__(ble_device)
    
    @staticmethod
    def is_supported(device_name):
        return device_name is not None and "HRM-Pro" in device_name
    
    def _ibi_data_processor(self, data):
        """
        Process IBI data from Garmin HRM-Pro.
        Args:
            data: bytearray of the ibi to be processed
        Returns:
            ndarray of where each row is a datapoint [epoch time in s, interbeat interval in milliseconds]
            Returns an empty array if no IBI data is present
        """
        flags = data[0]
        hr_format = flags & 0x01
        has_ibi = (flags >> 4) & 0x01
        
        if not has_ibi:
            self.logger.warning("No IBI data present. Flags: {flags:08b}")
            return np.array([])
        
        ibi_start = 2 if hr_format == 0 else 3
        ibis = []
        sample_time = time.time_ns() / 1.0e9
        
        for i in range(ibi_start, len(data), 2):
            ibi = (data[i + 1] << 8) | data[i]
            ibis.append(ibi)
        
        if not ibis:
            self.logger.warning(f"No IBI values extracted. Data length: {len(data)}, IBI start: {ibi_start}")
            return np.array([]) 
        
        return np.array([[sample_time, ibi] for ibi in ibis])