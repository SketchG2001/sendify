import traceback

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox,
    QFormLayout, QGroupBox, QAbstractItemView
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from api_client import ApiClient

class EmailConfigWidget(QWidget):
    config_updated = pyqtSignal()
    
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.api_client = ApiClient()
        self.current_config_id = None
        self.current_worker = None
        self.active_workers = []  # Track all active workers to prevent memory leaks
        self.init_ui()

    def create_safe_worker(self, api_method, *args, **kwargs):
        """Create and manage a worker safely to prevent crashes"""
        try:
            # Clean up any finished workers first
            self.cleanup_finished_workers()
            
            # Create the worker
            worker = api_method(*args, **kwargs)
            if worker:
                # Add to active workers list
                self.active_workers.append(worker)
                
                # Connect signals with proper error handling
                worker.success.connect(lambda data, w=worker: self.on_worker_success(data, w))
                worker.error.connect(lambda error, w=worker: self.on_worker_error(error, w))
                worker.finished.connect(lambda w=worker: self.on_worker_finished(w))
                
                return worker
            else:
                print("DEBUG: No worker created - likely token issue")
                return None
        except Exception as e:
            print(f"DEBUG: Error creating worker: {e}")
            return None

    def cleanup_finished_workers(self):
        """Remove finished workers from the active list"""
        try:
            # Remove finished workers
            self.active_workers = [w for w in self.active_workers if w.isRunning()]
        except Exception as e:
            print(f"DEBUG: Error cleaning up workers: {e}")

    def on_worker_success(self, data, worker):
        """Handle worker success - route to appropriate handler based on worker type"""
        try:
            # Determine which type of operation this worker was for
            if hasattr(worker, 'operation_type'):
                if worker.operation_type == 'load_configs':
                    self.on_configs_loaded(data)
                elif worker.operation_type == 'create_config':
                    self.on_config_created(data)
                elif worker.operation_type == 'update_config':
                    self.on_config_updated(data)
                elif worker.operation_type == 'delete_config':
                    self.on_config_deleted(data)
                elif worker.operation_type == 'use_config':
                    self.on_config_used(data)
                elif worker.operation_type == 'get_config':
                    self.populate_form_for_edit(data)
                else:
                    print(f"DEBUG: Unknown worker operation type: {worker.operation_type}")
            else:
                print("DEBUG: Worker has no operation type, using default handler")
                # Default to configs loaded if no type specified
                self.on_configs_loaded(data)
        except Exception as e:
            print(f"DEBUG: Error in worker success handler: {e}")

    def on_worker_error(self, error, worker):
        """Handle worker errors - route to appropriate error handler"""
        try:
            if hasattr(worker, 'operation_type'):
                if worker.operation_type == 'load_configs':
                    self.on_configs_error(error)
                elif worker.operation_type == 'create_config':
                    self.on_config_error(error)
                elif worker.operation_type == 'update_config':
                    self.on_config_error(error)
                elif worker.operation_type == 'delete_config':
                    self.on_config_error(error)
                elif worker.operation_type == 'use_config':
                    self.on_config_error(error)
                elif worker.operation_type == 'get_config':
                    self.on_edit_config_error(error, getattr(worker, 'config_id', 'unknown'))
                else:
                    print(f"DEBUG: Unknown worker operation type for error: {worker.operation_type}")
                    self.on_config_error(error)
            else:
                print("DEBUG: Worker has no operation type, using default error handler")
                self.on_config_error(error)
        except Exception as e:
            print(f"DEBUG: Error in worker error handler: {e}")

    def on_worker_finished(self, worker):
        """Handle worker finished - cleanup and route to appropriate handler"""
        try:
            if hasattr(worker, 'operation_type'):
                if worker.operation_type == 'load_configs':
                    self.on_configs_finished()
                elif worker.operation_type == 'get_config':
                    self.on_edit_config_finished()
                # Other operations don't have specific finished handlers
            else:
                print("DEBUG: Worker finished with no operation type")
        except Exception as e:
            print(f"DEBUG: Error in worker finished handler: {e}")
        finally:
            # Always cleanup the worker
            try:
                if worker in self.active_workers:
                    self.active_workers.remove(worker)
                worker.deleteLater()
            except Exception as e:
                print(f"DEBUG: Error cleaning up worker: {e}")
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Email Configuration Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.create_config_form(layout)

        self.create_form_buttons(layout)

        separator = QLabel("=" * 50)
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)
        

        self.create_config_table(layout)
        

        self.create_table_buttons(layout)
        
        # Add a load configurations button for manual loading
        self.create_load_button(layout)
        
        self.setLayout(layout)
    
    def create_load_button(self, parent_layout):
        """Create a button to manually load configurations"""
        load_layout = QHBoxLayout()
        
        self.load_configs_button = QPushButton("Load Email Configurations")
        self.load_configs_button.clicked.connect(self.load_configurations)
        self.load_configs_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        load_layout.addWidget(self.load_configs_button)
        load_layout.addStretch()
        
        parent_layout.addLayout(load_layout)
    
    def create_config_form(self, parent_layout):
        """Create the configuration input form"""
        form_group = QGroupBox("Email Configuration Form")
        form_layout = QFormLayout()
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        form_layout.addRow("Email:", self.email_input)
        
        # App Password field
        self.app_password_input = QLineEdit()
        self.app_password_input.setPlaceholderText("Enter your app password")
        self.app_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("App Password:", self.app_password_input)
        
        # Is Active checkbox
        self.is_active_checkbox = QCheckBox("Active")
        self.is_active_checkbox.setChecked(True)
        form_layout.addRow("Status:", self.is_active_checkbox)
        
        form_group.setLayout(form_layout)
        parent_layout.addWidget(form_group)
    
    def create_form_buttons(self, parent_layout):
        """Create buttons for form actions"""
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Configuration")
        self.add_button.clicked.connect(self.add_configuration)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.update_button = QPushButton("Update Configuration")
        self.update_button.clicked.connect(self.update_configuration)
        self.update_button.setEnabled(False)
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clear_form)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        parent_layout.addLayout(button_layout)
    
    def create_config_table(self, parent_layout):
        """Create the configurations table"""
        table_group = QGroupBox("Email Configurations")
        table_layout = QVBoxLayout()
        
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(5)
        self.config_table.setHorizontalHeaderLabels([
            "ID", "Email", "App Password", "Status", "Actions"
        ])

        self.config_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.config_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.config_table.setAlternatingRowColors(True)

        header = self.config_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.config_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        
        table_layout.addWidget(self.config_table)
        table_group.setLayout(table_layout)
        parent_layout.addWidget(table_group)
    
    def create_table_buttons(self, parent_layout):
        """Create buttons for table actions"""
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_configurations)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        self.use_config_button = QPushButton("Use Selected Configuration")
        self.use_config_button.clicked.connect(self.use_selected_config)
        self.use_config_button.setEnabled(False)
        self.use_config_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.use_config_button)
        button_layout.addStretch()
        
        parent_layout.addLayout(button_layout)
    
    def load_configurations(self):
        """Load email configurations from API"""
        try:
            # Disable the load button and show loading state
            self.load_configs_button.setEnabled(False)
            self.load_configs_button.setText("Loading...")
            
            # Show loading message in table
            self.show_loading_state()
            
            # Use safe worker creation
            worker = self.create_safe_worker(self.api_client.get_email_configurations)
            if worker:
                # Mark the worker type for proper routing
                worker.operation_type = 'load_configs'
                worker.start()
            else:
                self.show_error_state("No valid token available")
                self.reset_load_button()
        except Exception as e:
            print(f"Error in load_configurations: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_state(f"Failed to load configurations: {str(e)}")
            self.reset_load_button()
    
    def show_loading_state(self):
        """Show loading state in the table"""
        try:
            self.config_table.setRowCount(1)
            loading_item = QTableWidgetItem("Loading configurations...")
            # QTableWidgetItem doesn't have setAlignment - use text alignment instead
            loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.config_table.setItem(0, 0, loading_item)
            
            # Clear other columns
            for col in range(1, self.config_table.columnCount()):
                self.config_table.setItem(0, col, QTableWidgetItem(""))
        except Exception as e:
            print(f"Error showing loading state: {e}")
    
    def show_error_state(self, error_message):
        """Show error state in the table"""
        try:
            self.config_table.setRowCount(1)
            error_item = QTableWidgetItem(f"Error: {error_message}")
            # QTableWidgetItem doesn't have setAlignment - use text alignment instead
            error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # QTableWidgetItem doesn't have setForeground - use setBackground instead for visual indication
            error_item.setBackground(Qt.GlobalColor.red)
            error_item.setForeground(Qt.GlobalColor.white)  # White text on red background
            self.config_table.setItem(0, 0, error_item)
            
            # Clear other columns
            for col in range(1, self.config_table.columnCount()):
                self.config_table.setItem(0, col, QTableWidgetItem(""))
        except Exception as e:
            print(f"Error showing error state: {e}")
    
    def reset_load_button(self):
        """Reset the load button to its normal state"""
        try:
            self.load_configs_button.setEnabled(True)
            self.load_configs_button.setText("Load Email Configurations")
        except Exception as e:
            print(f"Error resetting load button: {e}")
    
    def on_configs_finished(self):
        """Called when the API worker finishes (success or error)"""
        try:
            self.reset_load_button()
            # Clean up the worker to prevent memory leaks
            if self.current_worker:
                self.current_worker.deleteLater()
                self.current_worker = None
        except Exception as e:
            print(f"Error in on_configs_finished: {e}")

    def on_configs_loaded(self, data):
        """Handle successful configuration loading"""
        try:
            if not data:
                print("No data received from API")
                self.show_error_state("No configurations found")
                return

            configs = data
            if configs is None:
                print("API response missing 'configurations' key")
                self.show_error_state("Invalid response from server")
                return

            if not isinstance(configs, list):
                print("Configurations data is not a list")
                self.show_error_state("Invalid data format")
                return

            self.populate_table(configs)
            print("Configurations loaded successfully")

        except Exception as e:
            print(f"Error in on_configs_loaded: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_state("Error processing loaded configurations")

    def on_configs_error(self, error):
        """Handle configuration loading error"""
        try:
            print(f"Configuration loading error: {error}")
            self.show_error_state(f"Failed to load configurations: {error}")
        except Exception as e:
            print(f"Error in on_configs_error: {e}")
            import traceback
            traceback.print_exc()

    def populate_table(self, configs):
        """Populate the table with configurations"""
        try:
            # Handle no configs
            if not configs:
                self.config_table.setRowCount(1)
                no_data_item = QTableWidgetItem("No configurations found")
                no_data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_item.setFlags(no_data_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.config_table.setItem(0, 0, no_data_item)

                # Clear remaining columns
                for col in range(1, self.config_table.columnCount()):
                    empty_item = QTableWidgetItem("")
                    empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.config_table.setItem(0, col, empty_item)
                return

            # Clear existing table first to prevent memory issues
            self.config_table.clearContents()
            self.config_table.setRowCount(len(configs))

            for row, config in enumerate(configs):
                try:
                    # Ensure config is a dict
                    if not isinstance(config, dict):
                        raise ValueError(f"Config at row {row} is not a dict")

                    # ID
                    id_item = QTableWidgetItem(str(config.get("id", "")))
                    id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.config_table.setItem(row, 0, id_item)

                    # Email
                    email_item = QTableWidgetItem(config.get("email", ""))
                    email_item.setFlags(email_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.config_table.setItem(row, 1, email_item)

                    # App Password (masked)
                    password_item = QTableWidgetItem("*" * 8 if config.get("_app_password") else "")
                    password_item.setFlags(password_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.config_table.setItem(row, 2, password_item)

                    # Status
                    status_text = "Active" if config.get("is_active") else "Inactive"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.config_table.setItem(row, 3, status_item)

                    # Actions - Create actions widget with proper memory management
                    try:
                        actions_widget = QWidget()
                        actions_layout = QHBoxLayout(actions_widget)
                        actions_layout.setContentsMargins(2, 2, 2, 2)

                        edit_btn = QPushButton("Edit")
                        edit_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #007bff;
                                color: white;
                                border: none;
                                padding: 4px 8px;
                                border-radius: 3px;
                                font-size: 10px;
                            }
                            QPushButton:hover {
                                background-color: #0056b3;
                            }
                        """)
                        # Use a safer lambda approach to prevent memory issues
                        edit_btn.clicked.connect(lambda checked, row_num=row: self.edit_configuration(row_num))

                        delete_btn = QPushButton("Delete")
                        delete_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #dc3545;
                                color: white;
                                border: none;
                                padding: 4px 8px;
                                border-radius: 3px;
                                font-size: 10px;
                            }
                            QPushButton:hover {
                                background-color: #c82333;
                            }
                        """)
                        delete_btn.clicked.connect(lambda checked, row_num=row: self.delete_configuration(row_num))

                        actions_layout.addWidget(edit_btn)
                        actions_layout.addWidget(delete_btn)
                        actions_layout.addStretch()

                        self.config_table.setCellWidget(row, 4, actions_widget)
                    except Exception as action_error:
                        print(f"Error creating actions for row {row}: {action_error}")
                        # Fallback to simple text
                        action_item = QTableWidgetItem("Actions")
                        action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        self.config_table.setItem(row, 4, action_item)

                except Exception as row_error:
                    print(f"Error populating row {row}: {row_error}")
                    traceback.print_exc()
                    error_item = QTableWidgetItem(f"Error loading row {row}")
                    error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.config_table.setItem(row, 0, error_item)

        except Exception as e:
            print(f"Error in populate_table: {e}")
            traceback.print_exc()
            self.show_error_state("Error populating table")

    def on_table_selection_changed(self):
        """Handle table selection change"""
        selected_rows = self.config_table.selectionModel().selectedRows()
        self.use_config_button.setEnabled(len(selected_rows) > 0)
    
    def add_configuration(self):
        """Add new email configuration"""
        email = self.email_input.text().strip()
        app_password = self.app_password_input.text().strip()
        is_active = self.is_active_checkbox.isChecked()
        
        if not email or not app_password:
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return
        
        try:
            worker = self.create_safe_worker(self.api_client.create_email_configuration, email, app_password, is_active)
            if worker:
                worker.operation_type = 'create_config'
                worker.start()
            else:
                QMessageBox.warning(self, "Error", "No valid token available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create configuration: {str(e)}")
    
    def on_config_created(self, data):
        """Handle successful configuration creation"""
        QMessageBox.information(self, "Success", "Email configuration created successfully!")
        self.clear_form()
        self.load_configurations()
        self.config_updated.emit()
    
    def edit_configuration(self, row):
        """Edit configuration from table row"""
        config_id = int(self.config_table.item(row, 0).text())
        email = self.config_table.item(row, 1).text()
        
        
        print(f"DEBUG: edit_configuration called for row {row}, config_id: {config_id}, email: {email}")
        
        # Get the actual configuration data
        try:
            worker = self.create_safe_worker(self.api_client.get_email_configuration, config_id)
            if worker:
                worker.operation_type = 'get_config'
                worker.config_id = config_id  # Store config_id for error handling
                worker.start()
                print(f"DEBUG: Worker started for config_id: {config_id}")
            else:
                QMessageBox.warning(self, "Error", "No valid token available")
        except Exception as e:
            print(f"DEBUG: Exception in edit_configuration: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load configuration: {str(e)}")

    def on_edit_config_error(self, error, config_id):
        """Handle errors when loading configuration for editing"""
        print(f"DEBUG: Error loading config {config_id} for editing: {error}")
        QMessageBox.critical(self, "Error", f"Failed to load configuration for editing: {error}")

    def on_edit_config_finished(self):
        """Called when the edit configuration worker finishes"""
        print("DEBUG: Edit configuration worker finished")
    
    def populate_form_for_edit(self, data):
        """Populate form with configuration data for editing"""
        
        # Debug: Print the actual data structure received
        print(f"DEBUG: populate_form_for_edit received data: {data}")
        print(f"DEBUG: Data type: {type(data)}")
        if isinstance(data, dict):
            print(f"DEBUG: Data keys: {list(data.keys())}")
        
        # The API returns the configuration object directly, not nested under 'configuration'
        config = data if isinstance(data, dict) else {}
        self.current_config_id = config.get('id')
        self.email_input.setText(config.get('email', ''))
        self.app_password_input.setText(config.get('app_password', ''))
        self.is_active_checkbox.setChecked(config.get('is_active', False))
        
        # Switch to update mode
        self.add_button.setEnabled(False)
        self.update_button.setEnabled(True)
    
    def update_configuration(self):
        """Update existing configuration"""
        if not self.current_config_id:
            return
        
        email = self.email_input.text().strip()
        app_password = self.app_password_input.text().strip()
        is_active = self.is_active_checkbox.isChecked()
        
        if not email or not app_password:
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return
        
        try:
            worker = self.create_safe_worker(
                self.api_client.update_email_configuration,
                self.current_config_id, email, app_password, is_active
            )
            if worker:
                worker.operation_type = 'update_config'
                worker.start()
            else:
                QMessageBox.warning(self, "Error", "No valid token available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update configuration: {str(e)}")
    
    def on_config_updated(self, data):
        """Handle successful configuration update"""
        QMessageBox.information(self, "Success", "Email configuration updated successfully!")
        self.clear_form()
        self.load_configurations()
        self.config_updated.emit()
    
    def delete_configuration(self, row):
        """Delete configuration from table row"""
        config_id = int(self.config_table.item(row, 0).text())
        email = self.config_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete the configuration for {email}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                worker = self.create_safe_worker(self.api_client.delete_email_configuration, config_id)
                if worker:
                    worker.operation_type = 'delete_config'
                    worker.start()
                else:
                    QMessageBox.warning(self, "Error", "No valid token available")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete configuration: {str(e)}")
    
    def on_config_deleted(self, data):
        """Handle successful configuration deletion"""
        QMessageBox.information(self, "Success", "Email configuration deleted successfully!")
        self.load_configurations()
        self.config_updated.emit()
    
    def on_config_error(self, error):
        """Handle configuration operation errors"""
        QMessageBox.critical(self, "Error", f"Operation failed: {error}")
    
    def use_selected_config(self):
        """Use the selected configuration"""
        selected_rows = self.config_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        config_id = int(self.config_table.item(row, 0).text())
        email = self.config_table.item(row, 1).text()
        
        try:
            
            worker = self.create_safe_worker(self.api_client.use_email_configuration, config_id)
            if worker:
                worker.operation_type = 'use_config'
                worker.start()
            else:
                QMessageBox.warning(self, "Error", "No valid token available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to use configuration: {str(e)}")
    
    def on_config_used(self, data):
        """Handle successful configuration usage"""
        QMessageBox.information(self, "Success", "Email configuration activated successfully!")
        self.load_configurations()
        self.config_updated.emit()
    
    def clear_form(self):
        """Clear the configuration form"""
        self.email_input.clear()
        self.app_password_input.clear()
        self.is_active_checkbox.setChecked(True)
        self.current_config_id = None
        
        # Switch back to add mode
        self.add_button.setEnabled(True)
        self.update_button.setEnabled(False)

    def closeEvent(self, event):
        """Clean up resources when widget is closed to prevent memory leaks"""
        try:
            # Clean up all active workers
            for worker in self.active_workers[:]:  # Copy list to avoid modification during iteration
                try:
                    if worker.isRunning():
                        worker.quit()
                        worker.wait(1000)  # Wait up to 1 second
                    worker.deleteLater()
                except Exception as e:
                    print(f"DEBUG: Error cleaning up worker: {e}")
            
            # Clear the list
            self.active_workers.clear()
            
            # Also clean up the current worker if it exists
            if self.current_worker and self.current_worker.isRunning():
                self.current_worker.quit()
                self.current_worker.wait(1000)
                self.current_worker.deleteLater()
                self.current_worker = None
        except Exception as e:
            print(f"Error during cleanup: {e}")
        super().closeEvent(event)

    def __del__(self):
        """Destructor to ensure cleanup when widget is garbage collected"""
        try:
            # Clean up all active workers
            for worker in getattr(self, 'active_workers', [])[:]:
                try:
                    if worker.isRunning():
                        worker.quit()
                        worker.wait(1000)
                    worker.deleteLater()
                except Exception as e:
                    print(f"DEBUG: Error in destructor cleanup: {e}")
            
            # Clean up current worker if it exists
            if hasattr(self, 'current_worker') and self.current_worker:
                if self.current_worker.isRunning():
                    self.current_worker.quit()
                    self.current_worker.wait(1000)
                self.current_worker.deleteLater()
        except Exception as e:
            print(f"Error in destructor: {e}")
