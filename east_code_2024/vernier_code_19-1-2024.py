import logging
import tkinter as tk
from tkinter import ttk, Toplevel
from datetime import datetime, timedelta
import os
import subprocess
from PythonCode import SensorCollector

logging.basicConfig()

class SensorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sensor GUI")
        self.loading_popup = None
        
        print("Initializing sensors.")
        self.collector = SensorCollector()
        print("Sensors ready.")

#        self.check_and_prompt_old_files()

        self.setup_ui()
        self.setup_styles()


    def setup_ui(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width_factor = screen_width / 1280
        height_factor = screen_height / 800
        window_width = int(1280 * min(width_factor, height_factor))
        window_height = int(800 * min(width_factor, height_factor))
        self.root.geometry(f"{window_width}x{window_height}+0+0")

        self.preload_images()
        self.setup_buttons()
        self.setup_entries()
        self.setup_timer()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("ImageButton.TButton", borderwidth=0, highlightthickness=0)
    
    def preload_images(self):
        # Preload images once and store them in instance variables
        self.start_img = tk.PhotoImage(file="start.png")
        self.save_img = tk.PhotoImage(file="save.png")
        self.result_img = tk.PhotoImage(file="reslult.png")
        self.reset_img = tk.PhotoImage(file="reset.png")

    def setup_buttons(self):
        self.start_button = self.create_image_button(self.start_img, self.check_if_patient, 0, 6)
        self.save_button = self.create_image_button(self.save_img, None, 9, 12)
        self.result_button = self.create_image_button(self.result_img, None, 7, 12)
        self.reset_button = self.create_image_button(self.reset_img, None, 6, 12)

    def create_image_button(self, img_path, command, row, column):
        img = tk.PhotoImage(file=img_path)
        button = ttk.Button(self.root, image=img, style="ImageButton.TButton", command=command)
        button.image = img
        button.grid(row=row, column=column, padx=10, pady=5, sticky="w")
        return button

    def setup_entries(self):
        self.entry_widgets = {}
        
        self.create_label_entry("Patient Name:", 1, 1, 1, 2)
        self.create_label_entry("Comments:", 2, 1, 2, 2)

    def create_label_entry(self, label_text, row, label_column, entry_row, entry_column):
        label = ttk.Label(self.root, text=label_text)
        label.grid(row=row, column=label_column, padx=10, pady=5, sticky="w")
        entry = ttk.Entry(self.root)
        entry.grid(row=entry_row, column=entry_column, padx=10, pady=5, sticky="w")
        self.entry_widgets[label_text] = entry

    def setup_timer(self):
        timer_frame = ttk.Label(self.root, background="#d8b3e9")
        timer_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nwe")

        self.timer_var = tk.StringVar()
        self.timer_var.set("Time: 00:00")
        self.timer_label = ttk.Label(timer_frame, textvariable=self.timer_var, font=("Arial", 20), foreground="black", background="#d8b3e9")
        self.timer_label.grid(row=0, column=0, padx=10, pady=5, sticky="nw")



    def show_loading_popup(self):
        if self.loading_popup is not None:
            return
        self.loading_popup = Toplevel(self.root)
        self.loading_popup.title("Loading")

        width, height = 400, 100
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.loading_popup.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        label = tk.Label(self.loading_popup, text="Please wait while the system connects to the sensors")
        label.pack(expand=True)

    def close_loading_popup(self):
        if self.loading_popup is not None:
            self.loading_popup.destroy()
            self.loading_popup = None



    def check_if_patient(self):
        pat_name_entry = self.entry_widgets.get("Patient Name:")
        pat_name = pat_name_entry.get()
        if not pat_name:
            self.show_popup("No patient specified", "No patient defined, there needs to be at least a patient name\nClick on new to set new patient and start graphing")
        else:
            #self.show_loading_popup()
            self.run_custom_script(pat_name)

    def show_popup(self, title, message):
        popup_window = Toplevel(self.root)
        popup_window.title(title)
        popup_label = ttk.Label(popup_window, text=message, font=("Arial", 18))
        popup_label.pack(padx=20, pady=10)
        close_button = ttk.Button(popup_window, text="Close", command=popup_window.destroy)
        close_button.pack(pady=10)

    def run_custom_script(self, pat_name):
        try:
            #self.close_loading_popup()

            result = self.collector.collect_data()

            if result is None:
                current_datetime = datetime.now()
                formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H:%M:%S")
                path_save = f"/home/east/Desktop/PatientDataFolder/{pat_name}/{formatted_datetime}.png"
                self.collector.save_data(path_save)
                self.process_script_output(formatted_datetime, pat_name)
            else:
                self.process_script_output(result, pat_name)
        except Exception as e:
            logging.error(f"Error running the script: {e}")
            self.close_loading_popup()
            self.show_popup("Script Error", f"Error running the script: {e}")


    def process_script_output(self, output_str, pat_name):
        if output_str == "BothF":
            self.show_popup("Failed connection", "Both sensors failed to connect\nCheck if they are on\nIf the button is pressed and no light blinks charge the device")
        elif output_str == "OneF":
            self.show_popup("Failed connection", "One of the sensors failed\nCheck if both are on\nIf the button is pressed and no light blinks charge the device")
        elif output_str == "ConnectionTimeout":
            self.show_popup("Connection Timeout", "Failed to connect to sensors within the timeout period.")
        elif output_str == "Error":
            self.show_popup("Error", "An error occurred during sensor setup or data collection.")
        else:
            image_filename = f"/home/east/Desktop/PatientDataFolder/{pat_name}/{output_str}.png"
            self.embed_graph(image_filename)

    def embed_graph(self, image_filename):
        image_label = ttk.Label(self.root)
        image_label.grid(row=4, column=0, columnspan=4, rowspan=7, padx=10, pady=5, sticky="nwse")
        img = tk.PhotoImage(file=image_filename)
        image_label.img = img
        image_label.config(image=img)


"""
    def check_and_prompt_old_files(self):
        directory = "/home/east/Desktop/PatientDataFolder/"
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)

        old_files = [
            (os.path.join(directory, filename), filename)
            for filename in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, filename)) and datetime.fromtimestamp(os.path.getmtime(os.path.join(directory, filename))) <= one_day_ago
        ]

        if old_files:
            self.prompt_delete_old_files(old_files)

    def prompt_delete_old_files(self, old_files):
        popup = Toplevel(self.root)
        popup.title("Delete old files")

        label = ttk.Label(popup, text="Do you want to delete the following files?", font=("Arial", 12))
        label.pack(padx=20, pady=10)

        for file_path, filename in old_files:
            file_label = ttk.Label(popup, text=filename, font=("Arial", 10))
            file_label.pack(padx=20, pady=5)

        button_frame = ttk.Frame(popup)
        button_frame.pack(pady=10)

        yes_button = ttk.Button(button_frame, text="Yes", command=lambda: self.delete_old_files(old_files, popup))
        yes_button.pack(side=tk.LEFT, padx=5)

        no_button = ttk.Button(button_frame, text="No", command=popup.destroy)
        no_button.pack(side=tk.RIGHT, padx=5)

    def delete_old_files(self, old_files, popup):
        for file_path, _ in old_files:
            try:
                os.remove(file_path)
                logging.info(f"Deleted old file: {file_path}")
            except OSError as e:
                logging.error(f"Error deleting file {file_path}: {e}")
        popup.destroy()
"""

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorGUI(root)
    root.mainloop()