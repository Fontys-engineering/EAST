import time
import matplotlib.pyplot as plt
import sys
import argparse
from datetime import datetime
from gdx import gdx

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="godirect.backend_bleak")

class SensorCollector:
    def __init__(self, time_between_readings=2, num_readings=100, precision=2):
        self.time_between_readings = time_between_readings
        self.num_readings = num_readings
        self.precision = precision
        self.gdx = gdx.gdx()
        self.device_ids = "proximity_pairing" #"GDX-HD 154005F6, GDX-HD 154005L1"
        self.max_attempts = 5  # Maximum number of connection attempts
        self.found_devices = []
        self.device_count = 0
        self.setup_sensors()

    def connect_to_sensors(self):
        self.gdx.open(connection="ble", device_to_open=self.device_ids)
        print("Bluetooth connection opened.")
        try:
            self.gdx.select_sensors([[1], [1]])
            print("Selecting sensors")
            self.found_devices = self.gdx.godirect.list_devices()
            print(self.found_devices)
            if len(self.found_devices) == 2:
                print("Found 2 sensors.")
                self.device_count = 2
                return 0
            else:
                self.found_devices = []
                print("Trying again...")
                self.gdx.close()
                return 1
        except Exception as e:
            print(f"Failed to find both sensors: {e}")
            self.found_devices = []
            self.gdx.close()


    def setup_sensors(self):
        attempt = 1
        while attempt <= self.max_attempts:
            try:
                result = self.connect_to_sensors()
                if result == 0:
                    attempt = 7
            except Exception as e:
                print(f"Failed to open Bluetooth connection or select sensors: {e}")
                if attempt < self.max_attempts:
                    print(f"Retrying connection attempt {attempt + 1}/{self.max_attempts}...")
                else:
                    print("Max connection attempts reached. Exiting setup.")
                    return  # Stop the function after max attempts
            attempt += 1

        # Initialize column headers
        print(self.gdx.sensor_info())
        self.column_headers = self.gdx.enabled_sensor_info()
        print(self.column_headers)

        try:
            if self.device_count == 0:
                print("List empty.")
                raise ValueError("Device list is empty.")
            else:
                print("List found.", self.found_devices)
                if self.device_count == 2:
                    self.unit_list = [str(header[header.find('('):header.find(')') + 1]) for header in self.column_headers]
                    self.column_headers_string = ', '.join([header.split('(')[0].strip() for header in self.column_headers])
                    print(f"Found devices: {self.found_devices}")
                    return  # Exit the function if connection is successful
                else:
                    print("Not all devices in list.")
                    raise ValueError("Not all devices are found.")
        except Exception as e:
            print(f"Failed to open Bluetooth connection or select sensors: {e}")





    def collect_data(self):
        if self.device_count == 2:
            return self.start_collection()
        else:
            self.gdx.stop()
            self.gdx.close()
            return "BothF" if len(self.found_devices) == 0 else "OneF"

    def start_collection(self):
        sensor_times = []
        sensor_readings0 = []
        sensor_readings1 = []
        sensor_readings2 = []
        print_table_string = []

        fig, ax = plt.subplots()
        plt.pause(1)
        period_in_ms = self.time_between_readings * 1000
        self.gdx.start(period_in_ms)
        collection_complete = False

        while not collection_complete:
            try:
                time_elapsed = 0
                for i in range(self.num_readings):
                    sensor_times.append(time_elapsed)
                    try:
                        print("Taking measurement")
                        measurements = self.gdx.read()
                        print(measurements)
                    except Exception as e:
                        print("Measurement Failed", e)
                    if measurements is None:
                        break

                    self.store_measurements(measurements, sensor_readings0, sensor_readings1, sensor_readings2)
                    #data_string, title_string = self.build_strings(measurements)

                    if self.time_between_readings > 0.4:
                        print(measurements)
                        if i >= self.num_readings - 1:
                            plt.title(f"{self.column_headers_string} vs Time (s)")
                        #else:
                            #plt.title(title_string)
                        self.plot_graph(ax, sensor_times, sensor_readings0, sensor_readings1)
                    
                    time_elapsed += self.time_between_readings

                if time_elapsed >= 45:
                    collection_complete = True
                    self.gdx.stop()

                if self.time_between_readings <= 0.4:
                    self.print_table(print_table_string)
                    plt.title(f"{self.column_headers[0]} vs Time (s)")
                    self.plot_graph(ax, sensor_times, sensor_readings0, sensor_readings1)

            except KeyboardInterrupt:
                collection_complete = True
                self.gdx.stop()

    def store_measurements(self, measurements, sensor_readings0, sensor_readings1, sensor_readings2):
        for d, data in enumerate(measurements):
            if d == 0:
                sensor_readings0.append(data)
            elif d == 1:
                sensor_readings1.append(data)
            elif d == 2:
                sensor_readings2.append(data)

    def build_strings(self, measurements):
        data_string = ''
        title_string = ''
        for d, data in enumerate(measurements):
            round_data = str(round(data, self.precision))
            data_string += f"{round_data}   "
            title_string += f"{round_data}{self.unit_list[d]}   "
        return data_string, title_string

    def plot_graph(self, ax, sensor_times, sensor_readings0, sensor_readings1):
        ax.plot(sensor_times, sensor_readings0, color='r', label=self.column_headers[0])
        if len(sensor_readings1) > 0:
            ax.plot(sensor_times, sensor_readings1, color='b', label=self.column_headers[1])
        plt.ylabel(self.column_headers_string)
        plt.xlabel('Time(s)')
        plt.grid(True)
        plt.pause(0.05)

    def print_table(self, print_table_string):
        for string in print_table_string:
            print(string)

    def save_data(self, path_save):
        plt.savefig(path_save)
        plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", help="Data passed from the original script")
    args = parser.parse_args()


class SingleSensorTest:
    def __init__(self):
        self.gdx1 = gdx.gdx()
        self.device_ids1 = "GDX-HD 154005F6"
        self.connect_to_sensors1()

    def connect_to_sensors1(self):
        print("Opening bluetooth connection")
        self.gdx1.open(connection="ble", device_to_open=self.device_ids1)
        print("Bluetooth connection opened. Selecting Sensor")
        self.gdx1.select_sensors([1])
        print("Sensor selected.")
