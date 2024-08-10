import napari
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QComboBox, QDialog, 
                            QLabel, QLineEdit, QFormLayout, QDialogButtonBox)
from qtpy.QtCore import Qt
import requests
import json

class AlbumWidget(QWidget):
    def __init__(self, hostname="localhost", port=8080, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Album Server Widget")
        self.hostname = hostname
        self.port = port
        self.layout = QVBoxLayout(self)
        
        # Dropdown to fetch solutions from the album server
        self.dropdown = QComboBox(self)
        self.layout.addWidget(self.dropdown)

        # Button to fetch the solution info
        self.info_button = QPushButton("Info", self)
        self.info_button.clicked.connect(self.show_info)
        self.layout.addWidget(self.info_button)

        # Button to run the solution
        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.run_solution)
        self.layout.addWidget(self.run_button)
        
        self.setLayout(self.layout)
        self.populate_dropdown()

    def populate_dropdown(self):
        try:
            response = requests.get(f"http://{self.hostname}:{self.port}/index")
            if response.status_code == 200:
                index_response = response.json()

                # Debugging: Print the received index to the console in a more compact form
                print("Received index from server:")
                # print(json.dumps(index_response, indent=2)[:1000], "...")  # Only print the first 1000 characters

                # Navigate into the 'index' key
                if isinstance(index_response, dict) and 'index' in index_response:
                    index = index_response['index']
                    if isinstance(index, dict) and 'catalogs' in index:
                        for catalog in index['catalogs']:
                            catalog_name = catalog.get('name', 'unknown_catalog')
                            solutions = catalog.get('solutions', [])
                            if isinstance(solutions, list):
                                for solution_info in solutions:
                                    if isinstance(solution_info, dict) and "setup" in solution_info:
                                        setup_info = solution_info["setup"]
                                        if isinstance(setup_info, dict):
                                            entry = f"{catalog_name}:{setup_info['group']}:{setup_info['name']}:{setup_info['version']}"
                                            self.dropdown.addItem(entry)
                                        else:
                                            print("Unexpected setup_info format.")
                                    else:
                                        print(f"Unexpected solution_info format in catalog '{catalog_name}' or 'setup' key missing.")
                            else:
                                print(f"Unexpected solutions format in catalog '{catalog_name}': {type(solutions).__name__}")
                    else:
                        print("Unexpected data format in 'index'.")
                else:
                    print("Unexpected data format in index_response.")
            else:
                print("Failed to fetch index from the server. Status code:", response.status_code)
        except Exception as e:
            print(f"Error occurred: {e}")

    def show_info(self):
        selected_solution = self.dropdown.currentText()
        if not selected_solution:
            return
        
        catalog, group, name, version = selected_solution.split(":")
        try:
            response = requests.get(f"http://{self.hostname}:{self.port}/info/{catalog}/{group}/{name}/{version}")
            if response.status_code == 200:
                info = response.json().get('info', {})

                if isinstance(info, dict):
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Solution Info")
                    dialog_layout = QVBoxLayout(dialog)
                    
                    info_label = QLabel(json.dumps(info, indent=4))
                    info_label.setWordWrap(True)
                    
                    dialog_layout.addWidget(info_label)
                    dialog.setLayout(dialog_layout)
                    dialog.exec_()
                else:
                    print("Invalid response format received.")
            else:
                print("Failed to fetch solution info.")
        except Exception as e:
            print(f"Error occurred: {e}")

    def run_solution(self):
        selected_solution = self.dropdown.currentText()
        if not selected_solution:
            return

        catalog, group, name, version = selected_solution.split(":")
        try:
            response = requests.get(f"http://{self.hostname}:{self.port}/info/{catalog}/{group}/{name}/{version}")
            if response.status_code == 200:
                info = response.json().get('info', {})

                if isinstance(info, dict):
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Run Solution")
                    dialog_layout = QVBoxLayout(dialog)
                    
                    form_layout = QFormLayout()
                    dialog_fields = {}

                    # Handle 'args' as a list
                    args = info.get("args", [])
                    if isinstance(args, list):
                        for arg in args:
                            if isinstance(arg, dict):
                                arg_name = arg.get("name", "unknown_arg")
                                field = QLineEdit()
                                form_layout.addRow(arg_name, field)
                                dialog_fields[arg_name] = field

                    dialog_layout.addLayout(form_layout)
                    
                    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                    buttons.accepted.connect(lambda: self.execute_solution(catalog, group, name, version, dialog_fields))
                    buttons.rejected.connect(dialog.reject)
                    dialog_layout.addWidget(buttons)
                    
                    dialog.setLayout(dialog_layout)
                    dialog.exec_()
                else:
                    print("Invalid response format received.")
            else:
                print("Failed to fetch solution info.")
        except Exception as e:
            print(f"Error occurred: {e}")

    def execute_solution(self, catalog, group, name, version, dialog_fields):
        solution_args = {}
        for key, field in dialog_fields.items():
            solution_args[key] = field.text()

        try:
            response = requests.post(f"http://{self.hostname}:{self.port}/run/{catalog}/{group}/{name}/{version}", json={"args": solution_args})
            if response.status_code == 200:
                result = response.json()
                print(f"Execution result: {result}")
            else:
                print("Failed to execute solution.")
        except Exception as e:
            print(f"Error occurred: {e}")

def main():
    viewer = napari.Viewer()
    widget = AlbumWidget()
    viewer.window.add_dock_widget(widget, area='right')
    napari.run()

if __name__ == "__main__":
    main()
