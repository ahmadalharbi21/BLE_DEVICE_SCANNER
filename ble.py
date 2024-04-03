import asyncio
import time
from bleak import BleakScanner, BleakClient

# Flag to control scanning
keep_scanning = True
discovered_devices = []

async def ble_scan_devices(callback):
    global discovered_devices
    scanner = BleakScanner()

    def handle_device_found(device, advertisement_data):
        current_time = time.time()
        if device.address not in [d[1] for d in discovered_devices]:
            discovered_devices.append((device.name, device.address, current_time))
            callback(device.name, device.address, True)
        else:
            for i, (name, address, timestamp) in enumerate(discovered_devices):
                if address == device.address:
                    discovered_devices[i] = (name, address, current_time)
                    break

    scanner.register_detection_callback(handle_device_found)

    while True:
        await scanner.start()
        await asyncio.sleep(5.0)
        await scanner.stop()

        # Keep track of active and inactive devices
        current_time = time.time()
        inactive_devices = [(name, address) for name, address, timestamp in discovered_devices if current_time - timestamp > 10.0]
        discovered_devices = [(name, address, timestamp) for name, address, timestamp in discovered_devices if current_time - timestamp <= 10.0]

        # Notify the callback about inactive devices
        for name, address in inactive_devices:
            callback(name, address, False)

        await asyncio.sleep(1)

async def connect_and_fetch_data(device_address):
    result = "# Device Details\n\n"
    async with BleakClient(device_address) as client:
        services = await client.get_services()
        for service in services:
            result += f"## Service: {service.uuid}\n"
            result += f"- Description: {service.description}\n"
            characteristics = service.characteristics
            result += "\n### Characteristics\n"
            for char in characteristics:
                result += f"- Characteristic: {char.uuid}\n"
                result += f" - Properties: {', '.join(char.properties)}\n"
                if "read" in char.properties:
                    try:
                        value = bytes(await client.read_gatt_char(char.uuid))
                        result += f" - Value: {value.hex()}\n"
                    except Exception as e:
                        result += f" - Value: Error reading characteristic: {str(e)}\n"
                else:
                    result += " - Value: (Not readable)\n"
                descriptors = char.descriptors
                if descriptors:
                    result += "\n #### Descriptors\n"
                    for descriptor in descriptors:
                        result += f" - Descriptor: {descriptor.uuid}\n"
                        try:
                            desc_value = bytes(await client.read_gatt_descriptor(descriptor.handle))
                            result += f" - Value: {desc_value.hex()}\n"
                        except Exception as e:
                            result += f" - Value: Error reading descriptor: {str(e)}\n"
                result += "\n"
            result += "\n"
        await client.disconnect()
        result += "\n---\n"
        result += "Disconnected from the device"
    return result