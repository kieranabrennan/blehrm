# 🎴 blehrm

Bluetooth Low Energy Heart Rate Monitoring

Blehrm is a platform for streaming data from bluetooth low energy (BLE) heart rate monitors. Built on [Bleak](https://github.com/hbldh/bleak)

Blehrm provides a simple asynchronous platform to connect with commonly available heart rate monitors including the Polar H10.

- Free software: MIT License

## Supported Devices:
- Polar H10
- Garmin HRM Pro
- CL800

## Installation

```
pip install blehrm
```

## Features

- Stream interbeat interval (time between heart beats), and raw ECG and accelerometer for supported devices
- A simple interface to easily extend to other BLE HR monitors
- Discover supported BLE HR monitors nearby

## Usage

To discover (supported) HR monitors:

```python

    import blehrm
    from bleak import BleakScanner
    import asyncio

    async def main():
        print('Scanning for devices...')
        ble_devices = await BleakScanner.discover()
        blehrm.print_supported_devices(ble_devices)

    if __name__ == "__main__":
        asyncio.run(main())
```

```
╒════════════════════╤══════════════════════════════════════╤══════════════╤═══════════════╕
│ Name               │ Address                              │ Type         │ Services      │
╞════════════════════╪══════════════════════════════════════╪══════════════╪═══════════════╡
│ CL800-0643016      │ CF7582F0-5AA4-7279-63A3-5850A4B6F780 │ CL800        │ ibi, acc      │
├────────────────────┼──────────────────────────────────────┼──────────────┼───────────────┤
│ HRM-Pro:982040     │ 34987821-60E5-03FB-70CC-BF552DC66039 │ GarminHRMPro │ ibi           │
├────────────────────┼──────────────────────────────────────┼──────────────┼───────────────┤
│ Polar H10 79324520 │ 5BE8C8E0-8FA7-CEE7-4662-D49695040AF7 │ PolarH10     │ ibi, acc, ecg │
╘════════════════════╧══════════════════════════════════════╧══════════════╧═══════════════╛
```

Connect and stream interbeat interval 

Consume data stream with a callback

```python

    # examples/print_hr.py 

    import asyncio
    from bleak import BleakScanner
    import blehrm
    import sys
    from datetime import datetime

    ADDRESS = "CF7582F0-5AA4-7279-63A3-5850A4B6F780" 
        
    async def main():
        ble_device = await BleakScanner.find_device_by_address(ADDRESS, timeout=20.0)
        if ble_device is None:
            print(f"Device with address {ADDRESS} not found")
            return

        blehrm_client = blehrm.create_client(ble_device) 
        await blehrm_client.connect()
        await blehrm_client.start_ibi_stream(print_callback)

        print("Streaming interbeat-interval data. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)

    def print_callback(data):
        if data.size > 0:
            t, ibi = data
            t_str = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S.%f")
            hr = round(60000/ibi, 1)
            sys.stdout.write(f"\r{t_str}: {hr} bpm")
            sys.stdout.flush()

    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nStream stopped by user.")
```

```
python3 examples/print_hr.py 
Streaming interbeat-interval data. Press Ctrl+C to stop.
2024-09-19 15:15:35.011178: 77.2 bpm
```

## Application Examples

### Live ECG
examples/live_ecg.py

![Live ECG Example](images/live_ecg.gif "Live ECG Example")


### Accelerometer visualisation

examples/live_acc.py

![Live ACC Example](images/live_acc.gif "Live ACC Example")

### Compare HR accuracy between sensors

examples/hr_comparison.py

![HR Comparison](images/hr_comparison.png "HR Comparison")


## Development

Extend support for a custom HR monitor by subclassing the interface base class, and implementing two methods:

```python

    # blehrm/clients/custom_hrm.py

    from blehrm.interface import BlehrmClientInterface
    from blehrm.registry import BlehrmRegistry
    import time
    import numpy as np

    @BlehrmRegistry.register("CustomHRMReader")
    class CustomHRMReader(BlehrmClientInterface):
        
        def __init__(self, ble_device):
            super().__init__(ble_device)
        
        @staticmethod
        def is_supported(device_name):
            return device_name is not None and "Device_name" in device_name
        
        def _ibi_data_processor(self, bytes_data):
            ibi = bytes_data_to_ibi(bytes_data) # Code to process bytes message to ibi

            return np.array([time.time_ns/1.0e9, ibi])

```
