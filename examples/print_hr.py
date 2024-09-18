from blehrm import readers
from blehrm import registry
from bleak import BleakScanner
import asyncio
import sys
from datetime import datetime

ADDRESS = "CF7582F0-5AA4-7279-63A3-5850A4B6F780" # CL800
# ADDRESS = "5BE8C8E0-8FA7-CEE7-4662-D49695040AF7" # Polar H10
# ADDRESS = "34987821-60E5-03FB-70CC-BF552DC66039" # Garmin HRM Pro

def print_callback(data):
    if data.size > 0:
        t, ibi = data
        t_str = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S.%f")
        hr = round(60000/ibi, 1)
        sys.stdout.write(f"\r{t_str}: {hr} bpm")
        sys.stdout.flush()
    
async def main():
    ble_device = await BleakScanner.find_device_by_address(ADDRESS, timeout=20.0)
    if ble_device is None:
        print(f"Device with address {ADDRESS} not found")
        return

    blehrm_reader = registry.blehrmRegistry.create_reader(ble_device)    
    await blehrm_reader.connect()
    await blehrm_reader.start_ibi_stream(print_callback)

    print("Streaming interbeat-interval data. Press Ctrl+C to stop.")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStream stopped by user.")