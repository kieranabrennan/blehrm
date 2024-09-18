from blehrm.interface import SensorReaderInterface
from blehrm.registry import blehrmRegistry
import time
import numpy as np
import math

@blehrmRegistry.register("PolarH10")
class PolarH10Reader(SensorReaderInterface):
    
    ## UNKNOWN 1 SERVICE
    U1_SERVICE_UUID = "6217ff4b-fb31-1140-ad5a-a45545d7ecf3"
    U1_CHAR1_UUID = "6217ff4c-c8ec-b1fb-1380-3ad986708e2d"      # read
    U1_CHAR2_UUID = "6217ff4d-91bb-91d0-7e2a-7cd3bda8a1f3"      # write-without-response, indicate

    ## Polar Measurement Data (PMD) Service
    PMD_SERVICE_UUID = "fb005c80-02e7-f387-1cad-8acd2d8df0c8"
    PMD_CHAR1_UUID = "fb005c81-02e7-f387-1cad-8acd2d8df0c8" #read, write, indicate – Request stream settings?
    PMD_CHAR2_UUID = "fb005c82-02e7-f387-1cad-8acd2d8df0c8" #notify – Start the notify stream?

    # POLAR ELECTRO Oy SERIVCE
    ELECTRO_SERVICE_UUID = "0000feee-0000-1000-8000-00805f9b34fb"
    ELECTRO_CHAR1_UUID = "fb005c51-02e7-f387-1cad-8acd2d8df0c8" #write-without-response, write, notify
    ELECTRO_CHAR2_UUID = "fb005c52-02e7-f387-1cad-8acd2d8df0c8" #notify
    ELECTRO_CHAR3_UUID = "fb005c53-02e7-f387-1cad-8acd2d8df0c8" #write-without-response, write

    # START PMD STREAM REQUEST
    HR_ENABLE = bytearray([0x01, 0x00])
    HR_DISABLE = bytearray([0x00, 0x00])

    # ECG and ACC Notify Requests
    ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])
    ACC_WRITE = bytearray([0x02, 0x02, 0x00, 0x01, 0xC8, 0x00, 0x01, 0x01, 0x10, 0x00, 0x02, 0x01, 0x08, 0x00])

    ACC_SAMPLING_FREQ = 200
    ECG_SAMPLING_FREQ = 130

    def __init__(self, ble_device):
        super().__init__(ble_device)
        self.acc_stream_start_time = None
        self.polar_to_epoch_s = 0
        self.first_acc_record = True
        self.first_ecg_record = True
    
    @staticmethod
    def is_supported(device_name):
        return device_name is not None and "Polar H10" in device_name
    
    def _ibi_data_processor(self, data):
        """
        Args:
            data: bytearray of the ibi to be processed
        Returns:
            ndarray of where each row is a datapoint [epoch time in s, interbeat interval in milliseconds]

        Notes:
        `data` is formatted according to the GATT Characteristic and Object Type 0x2A37 Heart Rate Measurement which is one of the three characteristics included in the "GATT Service 0x180D Heart Rate".
        `data` can include the following bytes:
        - flags
            Always present.
            - bit 0: HR format (uint8 vs. uint16)
            - bit 1, 2: sensor contact status
            - bit 3: energy expenditure status
            - bit 4: RR interval status
        - HR
            Encoded by one or two bytes depending on flags/bit0. One byte is always present (uint8). Two bytes (uint16) are necessary to represent HR > 255.
        - energy expenditure
            Encoded by 2 bytes. Only present if flags/bit3.
        - inter-beat-intervals (IBIs)
            One IBI is encoded by 2 consecutive bytes. Up to 18 bytes depending on presence of uint16 HR format and energy expenditure.
        """
        byte0 = data[0] # heart rate format
        uint8_format = (byte0 & 1) == 0
        energy_expenditure = ((byte0 >> 3) & 1) == 1
        rr_interval = ((byte0 >> 4) & 1) == 1

        if not rr_interval:
            return

        first_rr_byte = 2
        if uint8_format:
            hr = data[1]
            pass
        else:
            hr = (data[2] << 8) | data[1] # uint16
            first_rr_byte += 1
        
        if energy_expenditure:
            # ee = (data[first_rr_byte + 1] << 8) | data[first_rr_byte]
            first_rr_byte += 2
        ibis = []
        for i in range(first_rr_byte, len(data), 2):
            ibi = (data[i + 1] << 8) | data[i]
            # Polar H7, H9, and H10 record IBIs in 1/1024 seconds format.
            # Convert 1/1024 sec format to milliseconds.
            ibi = np.ceil(ibi / 1024 * 1000)
            ibis.append(ibi)
        # mean_ibi = np.mean(ibis)
        sample_time = time.time_ns()/1.0e9

        return np.array([[sample_time, ibi] for ibi in ibis])

    async def start_acc_stream(self, callback):
        self.set_acc_callback(callback)
        await self.bleak_client.write_gatt_char(PolarH10Reader.PMD_CHAR1_UUID, PolarH10Reader.ACC_WRITE, response=True)
        await self.bleak_client.start_notify(PolarH10Reader.PMD_CHAR2_UUID, self._acc_data_handler)

    async def stop_acc_stream(self):
        await self.bleak_client.stop_notify(PolarH10Reader.PMD_CHAR2_UUID)

    def _acc_data_processor(self, data): 
    # [02 EA 54 A2 42 8B 45 52 08 01 45 FF E4 FF B5 03 45 FF E4 FF B8 03 ...]
    # 02=ACC, 
    # EA 54 A2 42 8B 45 52 08 = last sample timestamp in nanoseconds, 
    # 01 = ACC frameType, 
    # sample0 = [45 FF E4 FF B5 03] x-axis(45 FF=-184 millig) y-axis(E4 FF=-28 millig) z-axis(B5 03=949 millig) , 
    # sample1, sample2,

        if data[0] == 0x02:
            time_step = 0.005 # 200 Hz sample rate
            timestamp = PolarH10Reader.convert_to_unsigned_long(data, 1, 8)/1.0e9 # timestamp of the last sample in the record
            
            frame_type = data[9]
            resolution = (frame_type + 1) * 8 # 16 bit
            step = math.ceil(resolution / 8.0)
            samples = data[10:] 
            n_samples = math.floor(len(samples)/(step*3))
            record_duration = (n_samples-1)*time_step # duration of the current record received in seconds

            if self.first_acc_record: # First record at the start of the stream
                stream_start_t_epoch_s = time.time_ns()/1.0e9 - record_duration
                stream_start_t_polar_s = timestamp - record_duration
                self.polar_to_epoch_s = stream_start_t_epoch_s - stream_start_t_polar_s
                self.first_acc_record = False

            sample_timestamp = timestamp - record_duration + self.polar_to_epoch_s # timestamp of the first sample in the record in epoch seconds
            offset = 0
            sample_data = []
            while offset < len(samples):
                x = PolarH10Reader.convert_array_to_signed_int(samples, offset, step)/100.0
                offset += step
                y = PolarH10Reader.convert_array_to_signed_int(samples, offset, step)/100.0
                offset += step
                z = PolarH10Reader.convert_array_to_signed_int(samples, offset, step)/100.0
                offset += step

                sample_data.append([sample_timestamp, x, y, z])
                sample_timestamp += time_step

            return np.array(sample_data)

    async def start_ecg_stream(self, callback):
        self.set_ecg_callback(callback)
        await self.bleak_client.write_gatt_char(PolarH10Reader.PMD_CHAR1_UUID, PolarH10Reader.ECG_WRITE, response=True)
        await self.bleak_client.start_notify(PolarH10Reader.PMD_CHAR2_UUID, self._ecg_data_handler)

    async def stop_ecg_stream(self):
        await self.bleak_client.stop_notify(PolarH10Reader.PMD_CHAR2_UUID)
        
    def _ecg_data_processor(self, data):
    # [00 EA 1C AC CC 99 43 52 08 00 68 00 00 58 00 00 46 00 00 3D 00 00 32 00 00 26 00 00 16 00 00 04 00 00 ...]
    # 00 = ECG; EA 1C AC CC 99 43 52 08 = last sample timestamp in nanoseconds; 00 = ECG frameType, sample0 = [68 00 00] microVolts(104), sample1, sample2, ....
        if data[0] == 0x00:
            timestamp = PolarH10Reader.convert_to_unsigned_long(data, 1, 8)/1.0e9
            step = 3
            time_step = 1.0/ self.ECG_SAMPLING_FREQ
            samples = data[10:]
            n_samples = math.floor(len(samples)/step)
            offset = 0
            recordDuration = (n_samples-1)*time_step

            if self.first_ecg_record:
                stream_start_t_epoch_s = time.time_ns()/1.0e9 - recordDuration
                stream_start_t_polar_s = timestamp - recordDuration
                self.polar_to_epoch_s = stream_start_t_epoch_s - stream_start_t_polar_s
                self.first_ecg_record = False

            sample_timestamp = timestamp - recordDuration + self.polar_to_epoch_s # timestamp of the first sample in the record in epoch seconds
            sample_data = []
            while offset < len(samples):
                ecg = PolarH10Reader.convert_array_to_signed_int(samples, offset, step)       
                offset += step

                sample_data.append([sample_timestamp, ecg])
                sample_timestamp += time_step
            
            return np.array(sample_data)


    @staticmethod
    def convert_array_to_signed_int(data, offset, length):
        return int.from_bytes(
            bytearray(data[offset : offset + length]), byteorder="little", signed=True,
        )
    @staticmethod
    def convert_to_unsigned_long(data, offset, length):
        return int.from_bytes(
            bytearray(data[offset : offset + length]), byteorder="little", signed=False,
        )
    

    