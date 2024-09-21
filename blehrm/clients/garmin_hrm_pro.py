from ..interface import BlehrmClientInterface
from ..registry import BlehrmRegistry
import time
import numpy as np

@BlehrmRegistry.register("GarminHRMPro")
class GarminHRMProClient(BlehrmClientInterface):
    
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

        if len(data) < 2:
            return np.array([])

        flags = data[0]
        hr_format = flags & 0x01
        has_ibi = (flags >> 4) & 0x01

        if not has_ibi:
            # print(f"No IBI data present. Flags: {flags:08b}")
            return np.array([])

        ibi_start = 2 if hr_format == 0 else 3
        ibis = []
        sample_time = time.time()

        for i in range(ibi_start, len(data), 2):
            if i + 1 < len(data):
                ibi = (data[i + 1] << 8) | data[i]
                ibis.append(ibi)

        if not ibis:
            print(f"No IBI values extracted. Data length: {len(data)}, IBI start: {ibi_start}")
            return np.array([])

        # Convert IBI values from 1/1024 seconds to milliseconds
        ibis_ms = [ibi * 1000 / 1024 for ibi in ibis]

        return np.array([[sample_time, ibi_ms] for ibi_ms in ibis_ms])