import asyncio
from ble import ble_scan_devices, connect_and_fetch_data

async def scan_devices_async(callback):
    await ble_scan_devices(callback)

def handle_device_found(device_name, device_address, device_list, create_device_button, remove_device_button, is_active=False):
    if is_active == False:
        # Device is inactive, remove it from the list and destroy the button
        if (device_name, device_address) in device_list:
            device_list.remove((device_name, device_address))
            remove_device_button(device_name, device_address)
    else:
        # New device found, add it to the list and create a button
        if (device_name, device_address) not in device_list:
            device_list.append((device_name, device_address))
            create_device_button(device_name, device_address)

def fetch_device_details(device_name, device_address, update_device_details_gui, show_error_message):
    try:
        # Run the coroutine in the thread's event loop
        device_details = asyncio.run(connect_and_fetch_data(device_address))
        update_device_details_gui(device_details, device_name)
    except Exception as e:
        error_message = f"Error occurred while fetching device details: {str(e)}"
        show_error_message(error_message)