from blehrm.interface import SensorReaderInterface
from blehrm.registry import blehrmRegistry
import asyncio
import random
import time
import numpy as np
import math

@blehrmRegistry.register("MockSensor")
class MockSensorReader(SensorReaderInterface):
    '''
    Mock sensor that simulates rr-interval
    '''
    def __init__(self, mock_id: str = "MOCK001"):
        super().__init__(mock_id)
        self.is_connected = False
        self.stream_ibi = False
        self.stream_acc = False

    @staticmethod
    def is_supported(device_name: str) -> bool:
        return device_name is not None and "Mock" in device_name

    async def connect(self) -> None:
        self.is_connected = True
    
    async def disconnect(self) -> None:
        self.is_connected = False

    async def get_device_info(self) -> None:
        self.model_number = "Mock"
        self.manufacturer_name = "Mock sensor ltd"
        self.battery_level = "99"

    async def start_ibi_stream(self, callback) -> None: 
        self.stream_ibi = True
        asyncio.create_task(self._ibi_stream(callback))

    async def _ibi_stream(self, callback) -> None:
        ''' Random ibi data at random intervals
        '''
        while self.stream_ibi:
            await asyncio.sleep(random.uniform(0.8, 1.3))
            callback(np.array([time.time_ns()/1.0e9, random.randint(55, 80)]))
    
    def _ibi_data_handler(self, sender, data) -> None:
        ''' Required by the ABC'''
        pass

    async def stop_ibi_stream(self) -> None:
        self.stream_ibi = False

    async def start_acc_stream(self, callback) -> None: 
        self.stream_acc = True
        asyncio.create_task(self._acc_stream(callback))

    async def _acc_stream(self, callback) -> None:
        ''' Sine acc data at constant interval
        '''
        while self.stream_acc:
            await asyncio.sleep(0.01)
            t = time.time_ns()/1.0e9
            x = math.sin(2 * math.pi * 2 * time.time())
            y = math.cos(2 * math.pi * 2 * time.time())
            z = random.uniform(-0.1, 0.1)

            callback(np.array([t, x, y, z]))
           
    async def stop_acc_stream(self) -> None:
        self.stream_acc = False