import threading
import customtkinter
from ble_utils import scan_devices_async, handle_device_found, fetch_device_details
import asyncio
from PIL import Image

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.scanning_thread = None
        self.scanning_paused = False

        self.title("BLE Device Scanner")
        self.geometry("800x600")
        # Main Screen
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True)

        self.logo_label = customtkinter.CTkLabel(self.main_frame, text="BLE Device Scanner", font=("Arial", 24))
        self.logo_label.pack(pady=55)

        self.scan_button = customtkinter.CTkButton(self.main_frame, text="Scan Devices", command=self.start_scan,width=150,height=50)
        self.scan_button.pack(pady=55,)

        self.navigation_frame = customtkinter.CTkFrame(self.main_frame)
        self.navigation_frame.pack(side="bottom", fill="x")
        self.footer_label = customtkinter.CTkLabel(self.main_frame, text="BLE Device Scanner v1.0 © 2023",
                                                   font=("Arial", 14))
        self.footer_label.pack(side="bottom", pady=10)

        self.navigation_frame.grid_columnconfigure(0, weight=1)
        self.navigation_frame.grid_columnconfigure(1, weight=1)
        self.navigation_frame.grid_columnconfigure(2, weight=1)


        self.history_button = customtkinter.CTkLabel(self.navigation_frame, text="", width=100)
        self.history_button.grid(row=0, column=2, padx=10, pady=10)

        # Scanning Screen
        self.scanning_frame = customtkinter.CTkFrame(self, width=400)
        self.scanning_frame.pack(side="left", fill="both", expand=True,)
        self.scanning_frame.pack_forget()

        self.scanning_label = customtkinter.CTkLabel(self.scanning_frame, text="Scanning...", font=("Arial", 20))
        self.scanning_label.pack(pady=20)

        try:
            self.radar_image = customtkinter.CTkImage(Image.open(r"C:\Users\ahmad\Downloads\Bluetooth_FM_Color.png"), size=(200, 200))
            self.radar_label = customtkinter.CTkLabel(self.scanning_frame, image=self.radar_image, text='')
            self.radar_label.pack(pady=10)
        except FileNotFoundError:
            print("Radar image not found. Skipping radar label.")

        self.devices_frame = customtkinter.CTkScrollableFrame(self.scanning_frame)
        self.devices_frame.pack(fill="both", expand=True)

        self.scan_control_button = customtkinter.CTkLabel(self.scanning_frame, text="", width=100)
        self.scan_control_button.pack(side="bottom", pady=20)

        # Device Details Screen
        self.device_details_frame = customtkinter.CTkFrame(self, width=400)
        self.device_details_frame.pack(side="right", fill="both", expand=True)
        self.device_details_frame.pack_forget()

        self.details_label = customtkinter.CTkLabel(self.device_details_frame, text="")
        self.details_label.pack(padx=20, pady=20)
        self.details_label.configure(bg_color="red")

        self.device_list = []
        self.device_buttons = {}

    def start_scan(self):
        self.main_frame.pack_forget()
        self.scanning_frame.pack(side="left", fill="both", expand=True)
        self.device_details_frame.pack_forget()

        # Clear existing devices
        for widget in self.devices_frame.winfo_children():
            widget.destroy()
        self.device_buttons = {}

        self.scanning_thread = threading.Thread(target=self.scan_devices)
        self.scanning_thread.start()

    def scan_devices(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(scan_devices_async(self.handle_device_found))

    def handle_device_found(self, device_name, device_address, is_active=False):
        handle_device_found(device_name, device_address, self.device_list, self.create_device_button, self.remove_device_button, is_active)

    def create_device_button(self, device_name, device_address):
        if (device_name, device_address) not in self.device_buttons:
            device_button = customtkinter.CTkButton(
                self.devices_frame,
                text=f"{device_name} ({device_address})",
                command=lambda: self.show_device_details(device_name, device_address)
            )
            device_button.pack(pady=10, padx=20, fill="x")
            self.device_buttons[(device_name, device_address)] = device_button

    def remove_device_button(self, device_name, device_address):
        if (device_name, device_address) in self.device_buttons:
            device_button = self.device_buttons.pop((device_name, device_address))
            device_button.destroy()

    def show_device_details(self, device_name, device_address):
        self.scanning_frame.pack(side="left", fill="both", expand=False)
        self.scanning_frame.configure(width=400)
        self.device_details_frame.pack(side="right", fill="both", expand=True)

        # Create a separate thread to fetch device details
        threading.Thread(target=fetch_device_details, args=(
        device_name, device_address, self.update_device_details_gui, self.show_error_message)).start()

    def show_error_message(self, error_message):
        customtkinter.CTkLabel(self.device_details_frame, text=error_message, text_color="red").pack(padx=20, pady=20)

    def update_device_details_gui(self, device_details, device_name):
        # Clear existing details
        for widget in self.device_details_frame.winfo_children():
            widget.destroy()

        if device_details == "Error occurred":
            self.show_error_message("Error occurred while fetching device details.")
        else:
            # Create a scrollable frame for the device details
            details_scrollable_frame = customtkinter.CTkScrollableFrame(self.device_details_frame)
            details_scrollable_frame.pack(fill="both", expand=True)

        # Create a header label for the device name
        device_name_label = customtkinter.CTkLabel(details_scrollable_frame, text="Device Details", font=("Arial", 18))
        device_name_label.pack(pady=10)
        device_name_label = customtkinter.CTkLabel(details_scrollable_frame, text=device_name, font=("Arial", 18))
        device_name_label.pack(pady=10)

        # Create a frame for each service
        services = device_details.split("## Service:")[1:]
        for service in services:
            service_frame = customtkinter.CTkFrame(details_scrollable_frame)
            service_frame.pack(pady=10, padx=20, fill="x")

            # Extract service UUID and characteristics
            service_uuid = service.split("\n", 1)[0].strip()
            characteristics = service.split("- Characteristic:")[1:]

            # Create a label for the service UUID
            service_label = customtkinter.CTkLabel(service_frame, text=f"Service: {service_uuid}")
            service_label.pack(pady=5, anchor="w")

            # Create a frame for each characteristic
            for characteristic in characteristics:
                char_frame = customtkinter.CTkFrame(service_frame)
                char_frame.pack(pady=5, padx=20, fill="x")

                # Extract characteristic details
                char_lines = characteristic.strip().split("\n")
                char_uuid = char_lines[0].strip()

                # Create a label for the characteristic UUID
                char_uuid_label = customtkinter.CTkLabel(char_frame, text=f"Characteristic: {char_uuid}")
                char_uuid_label.pack(pady=2, anchor="w")

                # Create a frame for characteristic properties and value
                char_details_frame = customtkinter.CTkFrame(char_frame)
                char_details_frame.pack(pady=2, padx=20, fill="x")

                # Extract and display characteristic properties and value
                for line in char_lines[1:]:
                    if line.strip().startswith("- Properties:"):
                        char_properties = line.split(": ")[1]
                        char_properties_label = customtkinter.CTkLabel(char_details_frame,
                                                                       text=f"Properties: {char_properties}")
                        char_properties_label.pack(pady=2, anchor="w")
                    elif line.strip().startswith("- Value:"):
                        char_value = line.split(": ")[1]
                        char_value_label = customtkinter.CTkLabel(char_details_frame, text=f"Value: {char_value}")
                        char_value_label.pack(pady=2, anchor="w")

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print(f"An error occurred: {str(e)}")