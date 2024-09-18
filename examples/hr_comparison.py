from blehrm.registry import blehrmRegistry 
from blehrm import readers
from bleak import BleakScanner
import asyncio
import tqdm
import matplotlib.pyplot as plt
import numpy as np

async def main(record_len):
    ''' Stream interbeat-interval from all available HR monitors
    Records for record_len then plots a comparison of HR across time
    '''

    print(f'Registered sensors:{blehrmRegistry.get_registered_sensors()}')

    print('Scanning for devices...')
    ble_devices = await BleakScanner.discover()
    supported_sensors = blehrmRegistry.get_supported_devices(ble_devices)
    blehrmRegistry.print_supported_devices(supported_sensors)

    sensor_readers = [blehrmRegistry.create_reader(device) for device, _ in supported_sensors]
    
    logged_data = [[] for _ in sensor_readers]
    for i, reader in enumerate(sensor_readers):
        await reader.connect()
        await reader.start_ibi_stream(logged_data[i].append)

    for t in tqdm.tqdm(range(record_len)):
        await asyncio.sleep(1)

    plt.figure(figsize=(12,6))
    for i, d in enumerate(logged_data):
        arr = np.array(d)
        plt.plot(arr[:,0], np.round(60000/arr[:,1]), label=supported_sensors[i][0].name)

    plt.legend()    
    plt.ylabel('Heart rate (bpm)')
    plt.show()

if __name__ == "__main__":
    record_len = 60
    asyncio.run(main(record_len))