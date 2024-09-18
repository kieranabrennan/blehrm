from blehrm.registry import blehrmRegistry 
from blehrm import readers
from bleak import BleakScanner
import asyncio

async def main():
    print(f'Registered sensors:{blehrmRegistry.get_registered_sensors()}')

    print('Scanning for devices...')
    ble_devices = await BleakScanner.discover()
    supported_sensors = blehrmRegistry.get_supported_devices(ble_devices)
    blehrmRegistry.print_supported_devices(supported_sensors)

if __name__ == "__main__":
    asyncio.run(main())