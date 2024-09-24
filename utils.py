from bleak import BleakScanner, BleakClient
from tabulate import tabulate
import asyncio

async def ble_scanner_tabulate():
    ''' Scan for all BLE devices and print out the details using tabulate
    '''
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    
    # Prepare data for tabulate
    table_data = []
    for device in devices:
        table_data.append([
            device.name if device.name else "Unknown",
            device.address,
            device.rssi
        ])
    
    # Sort devices by RSSI (strongest signal first)
    table_data.sort(key=lambda x: x[2] if x[2] is not None else -100, reverse=True)
    
    headers = ["Name", "Address", "RSSI (dBm)"]
    print(tabulate(table_data, headers=headers, tablefmt="simple"))

    print(f"\nTotal devices found: {len(devices)}")

async def print_device_info(address):
    """
    Print all available services and characteristics for a given BLE device address.
    
    Args:
    address (str): The MAC address of the BLE device.
    """
    device = await BleakScanner.find_device_by_address(address)
    if not device:
        print(f"Device with address {address} not found.")
        return

    try:
        async with BleakClient(device) as client:
            print(f"Connected to device: {device.name or 'Unknown'} ({device.address})")
            
            services = client.services
            service_table = []
            characteristic_table = []

            for service in services:
                service_table.append([
                    service.uuid,
                    service.description or "No description"
                ])

                for char in service.characteristics:
                    props = ", ".join(char.properties)
                    characteristic_table.append([
                        service.uuid,
                        char.uuid,
                        char.description or "No description",
                        props
                    ])

            print("\nServices:")
            print(tabulate(service_table, headers=["UUID", "Description"], tablefmt="simple"))

            print("\nCharacteristics:")
            print(tabulate(characteristic_table, 
                           headers=["Service UUID", "Char UUID", "Description", "Properties"], 
                           tablefmt="simple"))

    except Exception as e:
        print(f"Error connecting to device: {e}")

if __name__ == "__main__":

    asyncio.run(ble_scanner_tabulate())
    
    device_address = "371221C5-1A6F-185C-0265-1F2829C71932"
    
    asyncio.run(print_device_info(device_address))