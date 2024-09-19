from blehrm.registry import BlehrmRegistry 
from blehrm import clients
from bleak import BleakScanner
import asyncio
import tqdm
import matplotlib.pyplot as plt
import numpy as np
import logging

logger = logging.getLogger(__name__)

async def main(record_len):
    ''' Stream interbeat-interval from all available HR monitors
    Records for record_len then plots a comparison of HR across time
    '''
    print(f'Registered sensors:{BlehrmRegistry.get_registered_sensors()}')

    logger.info('Scanning for devices...')
    ble_devices = await BleakScanner.discover()
    supported_sensors = BlehrmRegistry.get_supported_devices(ble_devices)
    BlehrmRegistry.print_supported_devices(supported_sensors)

    sensor_clients = [BlehrmRegistry.create_client(device) for device, _ in supported_sensors]
    
    logged_data = [[] for _ in sensor_clients]
    for i, client in enumerate(sensor_clients):
        await client.connect()
        await client.start_ibi_stream(logged_data[i].append)

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
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    record_len = 60
    asyncio.run(main(record_len))