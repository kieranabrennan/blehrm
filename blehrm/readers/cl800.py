from blehrm.interface import SensorReaderInterface
from blehrm.registry import blehrmRegistry
import time
import numpy as np

@blehrmRegistry.register("CL800")
class CL800Reader(SensorReaderInterface):
    
    ## ACCELEROMETER SERVCIE
    ACC_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
    # Characteristics
    ACC_CHAR1_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0" # write-without-response, write
    ACC_CHAR2_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0" # notify
    # ACC Notify Requests
    ACC_WRITE = bytearray([0x0C])
    ACC_SAMPLING_FREQ = 26

    def __init__(self, ble_device):
        super().__init__(ble_device)

    @staticmethod
    def is_supported(device_name: str) -> bool:
        return device_name is not None and "CL800" in device_name
    
    def _ibi_data_processor(self, data: bytearray) -> np.ndarray:
        if len(data) < 2:
            print(f"Warning: Received data is too short: {data}")
            return np.array([])

        byte0 = data[0]  # heart rate format
        uint8_format = (byte0 & 1) == 0
        energy_expenditure = ((byte0 >> 3) & 1) == 1
        rr_interval = ((byte0 >> 4) & 1) == 1

        if not rr_interval:
            print("Warning: No RR interval data present")
            return np.array([])

        first_rr_byte = 2
        try:
            if uint8_format:
                hr = data[1]
            else:
                hr = (data[2] << 8) | data[1]  # uint16
                first_rr_byte += 1
            
            if energy_expenditure:
                first_rr_byte += 2

            if first_rr_byte >= len(data):
                print(f"Warning: No IBI data present after HR and flags: {data}")
                return np.array([])

            sample_data = []
            for i in range(first_rr_byte, len(data) - 1, 2):
                try:
                    ibi = (data[i + 1] << 8) | data[i]
                    ibi_ms = np.ceil(ibi / 1024 * 1000)
                    timestamp = time.time_ns() / 1.0e9
                    sample_data.append([timestamp, ibi_ms])
                except IndexError:
                    print(f"Warning: Incomplete IBI data at index {i}")
                    break

            if not sample_data:
                print("Warning: No valid IBI data processed")
                return np.array([])

            return np.array(sample_data)

        except Exception as e:
            print(f"Error processing IBI data: {e}")
            return np.array([])

    async def start_acc_stream(self, callback):
        self.set_acc_callback(callback)
        await self.bleak_client.write_gatt_char(CL800Reader.ACC_CHAR1_UUID, CL800Reader.ACC_WRITE, response=True)
        await self.bleak_client.start_notify(CL800Reader.ACC_CHAR2_UUID, self._acc_data_handler)
        
    async def stop_acc_stream(self):
        await self.bleak_client.stop_notify(CL800Reader.ACC_CHAR2_UUID)

    def _acc_data_processor(self, data: bytearray) -> np.ndarray: 
        '''
        Handles accelerometer data
        First three bytes will be \xff \x2d \x0c if ACC data follows
        Ignore when first 3 bytes are \xff \x0d \x15 
        Byte 1-2: 0x-- X-axis data, little endian
        Byte 3-4: 0x-- Y-axis ''
        Byte 5-6: 0x-- Z-axis 
        Byte 7-8: 0x-- X-axis 
        Accelerometer values are 16 bit 
        ''' 
        if len(data) < 3:
            print(f"Warning: Received data is too short: {data}")
            return np.array([])

        prefix = data[0:3]
        acc_bytes = data[3:]

        if prefix[2] != 0x0c:
            # print(f"Warning: Unexpected prefix: {prefix}")
            return np.array([])

        # if len(acc_bytes) % 6 != 0:
        #     print(f"Warning: Incomplete accelerometer data: {len(acc_bytes)} bytes")
        #     return np.array([])

        message_timestamp = time.time_ns()/1.0e9
        n_samples = len(acc_bytes) // 6  # x,y,z 16 bit each axis    
        sample_data = []

        for sample_id in range(n_samples):    
            sample_timestamp = message_timestamp + sample_id * (1.0 / self.ACC_SAMPLING_FREQ)
            start_id = sample_id * 6  # index of the first x byte
            
            try:
                x = int.from_bytes(acc_bytes[start_id:start_id+2], byteorder='little', signed=True) * 9.81 / 4096.0
                y = int.from_bytes(acc_bytes[start_id+2:start_id+4], byteorder='little', signed=True) * 9.81 / 4096.0
                z = int.from_bytes(acc_bytes[start_id+4:start_id+6], byteorder='little', signed=True) * 9.81 / 4096.0
                sample_data.append([sample_timestamp, x, y, z])
            except Exception as e:
                print(f"Error processing sample {sample_id}: {e}")
                continue

        return np.array(sample_data)