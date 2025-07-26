from ..interface import BlehrmClientInterface
from ..registry import BlehrmRegistry
from .polar_h10 import PolarH10Client

@BlehrmRegistry.register("Coospo H6M")
class CoospoH6mClient(BlehrmClientInterface):
    def __init__(self, ble_device):
        super().__init__(ble_device)

    @staticmethod
    def is_supported(device_name: str) -> bool:
        return device_name is not None and "H6M" in device_name

    def _ibi_data_processor(self, data):
        # Use the implementation of the Polar H10
        return PolarH10Client._ibi_data_processor(self, data)
