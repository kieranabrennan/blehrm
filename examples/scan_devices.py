import blehrm
from bleak import BleakScanner
import asyncio

async def main():
    blehrm.print_registered_devices()

    print('Scanning for devices...')
    ble_devices = await BleakScanner.discover()
    blehrm.print_supported_devices(ble_devices)

if __name__ == "__main__":
    asyncio.run(main())