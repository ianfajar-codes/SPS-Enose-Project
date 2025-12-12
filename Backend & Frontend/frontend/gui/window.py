"""
Main Window - Backend TCP Mode
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QComboBox,
                               QTextEdit, QGroupBox, QFileDialog,
                               QMessageBox)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
from datetime import datetime
import os

from .tcp import TcpClient
from .data_manager import DataManager

# Edge Impulse Integration (Optional)
try:
    import tensorflow as tf
    import numpy as np
    EI_AVAILABLE = True
except ImportError:
    EI_AVAILABLE = False
    print("⚠  TensorFlow not available.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Electronic Nose - Backend Mode")
        self.setGeometry(50, 50, 1400, 900)

        self.tcp_client = TcpClient()
        self.data_manager = DataManager()
        self.is_sampling = False
        self.log_text = None

        if EI_AVAILABLE:
            self.tflite_model = None
            self.model_loaded = False
            self.class_labels = ["Jeruk", "Kari", "Kemangi", "Pandan"]
        
        self.init_ui()
        self.setup_connections()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        self.update_timer.start(100)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        title_label = QLabel("🌿 Electronic Nose Project SPS")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        control_group = self.create_control_panel()
        main_layout.addWidget(control_group)
        
        # SYSTEM STATUS BOX DIHAPUS DI SINI
        
        if EI_AVAILABLE:
            ei_group = self.create_edge_impulse_panel()
            main_layout.addWidget(ei_group)
        
        plot_group = self.create_plot_area()
        main_layout.addWidget(plot_group)
        
        log_group = self.create_log_area()
        main_layout.addWidget(log_group)

    def create_control_panel(self):
        group = QGroupBox("Control Panel")
        layout = QVBoxLayout()
        
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("Backend Server:"))
        self.server_input = QLineEdit("127.0.0.1:8080")
        self.server_input.setMaximumWidth(150)
        conn_layout.addWidget(self.server_input)
        
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        conn_layout.addWidget(self.connect_btn)
        
        self.status_indicator = QLabel("⚫ Disconnected")
        self.status_indicator.setStyleSheet("color: gray; font-weight: bold;")
        conn_layout.addWidget(self.status_indicator)
        conn_layout.addStretch()
        layout.addLayout(conn_layout)
        
        info_layout = QHBoxLayout()
        info_label = QLabel("🔗 Connect ke backend Rust (pastikan cargo run aktif!)")
        info_label.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        info_layout.addWidget(info_label)
        layout.addLayout(info_layout)
        
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Save CSV")
        self.save_btn.clicked.connect(self.save_data_csv)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("padding: 8px;")
        btn_layout.addWidget(self.save_btn)
        
        self.save_json_btn = QPushButton("📄 Save JSON (Edge Impulse)")
        self.save_json_btn.clicked.connect(self.save_data_json)
        self.save_json_btn.setEnabled(False)
        self.save_json_btn.setStyleSheet("padding: 8px; background-color: #FF9800; color: white; font-weight: bold;")
        btn_layout.addWidget(self.save_json_btn)
        
        self.clear_btn = QPushButton("🗑 Clear Data")
        self.clear_btn.clicked.connect(self.clear_data)
        self.clear_btn.setStyleSheet("padding: 8px;")
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        group.setLayout(layout)
        return group

    def create_edge_impulse_panel(self):
        group = QGroupBox("🤖 Edge Impulse - Model Inference")
        layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        
        self.ei_load_model_btn = QPushButton("📥 Load Model (.tflite)")
        self.ei_load_model_btn.clicked.connect(self.load_tflite_model)
        self.ei_load_model_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        btn_layout.addWidget(self.ei_load_model_btn)
        
        self.ei_predict_btn = QPushButton("🔮 Predict Current Data")
        self.ei_predict_btn.clicked.connect(self.predict_current_data)
        self.ei_predict_btn.setEnabled(False)
        self.ei_predict_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        btn_layout.addWidget(self.ei_predict_btn)
        
        layout.addLayout(btn_layout)
        
        self.prediction_label = QLabel("Prediction: -")
        self.prediction_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.prediction_label.setStyleSheet("color: green; padding: 15px; background: #f0f0f0; border-radius: 5px; border: 2px solid #4CAF50;")
        self.prediction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.prediction_label)
        
        group.setLayout(layout)
        return group

    def create_plot_area(self):
        group = QGroupBox("📊 Real-Time Sensor Data (7 Channels)")
        layout = QVBoxLayout()
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Sensor Reading', units='ppm')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        
        colors = ['r', 'g', 'b', 'm', 'c', 'y', 'k']
        sensors = ['CO (MICS)', 'Ethanol (MICS)', 'VOC (MICS)', 'NO2',
                   'Ethanol (Grove)', 'VOC (Grove)', 'CO (Grove)']
        
        self.plot_lines = {}
        for i, (sensor, color) in enumerate(zip(sensors, colors)):
            key = ['co_m', 'eth_m', 'voc_m', 'no2', 'eth_gm', 'voc_gm', 'co_gm'][i]
            self.plot_lines[key] = self.plot_widget.plot(
                pen=pg.mkPen(color, width=2),
                name=sensor
            )
        
        layout.addWidget(self.plot_widget)
        group.setLayout(layout)
        return group

    def create_log_area(self):
        group = QGroupBox("📝 System Log")
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 9pt;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_text)
        
        group.setLayout(layout)
        return group

    def setup_connections(self):
        self.tcp_client.data_received.connect(self.on_data_received)
        self.tcp_client.status_received.connect(self.on_status_received)
        self.tcp_client.connection_status.connect(self.on_connection_status)

    def toggle_connection(self):
        if self.tcp_client.is_connected:
            self.tcp_client.disconnect()
        else:
            try:
                host, port = self.server_input.text().split(':')
                self.tcp_client.connect(host, int(port))
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid server format. Use: IP:PORT")

    def on_connection_status(self, connected):
        if connected:
            self.status_indicator.setText("🟢 Connected")
            self.status_indicator.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setText("🔌 Disconnect")
            self.log_message("✓ Connected to backend server")
        else:
            self.status_indicator.setText("⚫ Disconnected")
            self.status_indicator.setStyleSheet("color: gray; font-weight: bold;")
            self.connect_btn.setText("🔌 Connect")
            self.log_message("✗ Disconnected from server")

    def on_data_received(self, data):
        self.data_manager.add_data(data)
        
        if not self.is_sampling:
            self.is_sampling = True
            self.save_btn.setEnabled(True)
            self.save_json_btn.setEnabled(True)

    def on_status_received(self, status):
        msg_type = status.get('msg_type', '')
        if msg_type == 'status':
            msg = status.get('msg', '') or status.get('message', '')
            arduino_status = status.get('status', '')
            if msg:
                self.log_message(f"📡 {msg}")
            if arduino_status:
                self.log_message(f"Status: {arduino_status}")
        elif msg_type == 'motor':
            motor = status.get('motor', '')
            speed = status.get('speed', 0)
            self.log_message(f"Motor {motor}: {speed}%")
        elif msg_type == 'calib_progress':
            progress = status.get('progress', 0)
            self.log_message(f"Calibration: {progress}/10")

    # ========================================================================
    # DATA MANAGEMENT
    # ========================================================================

    def update_plot(self):
        """Update real-time plot"""
        data = self.data_manager.get_plot_data()
        if data:
            times = data['times']
            for sensor_key in ['co_m', 'eth_m', 'voc_m', 'no2', 'eth_gm', 'voc_gm', 'co_gm']:
                if sensor_key in self.plot_lines:
                    self.plot_lines[sensor_key].setData(times, data[sensor_key])

    def save_data_csv(self):
        """Save data ke CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Data as CSV", "", "CSV Files (*.csv)"
        )
        if filename:
            success = self.data_manager.save_to_file(filename)
            if success:
                self.log_message(f"💾 CSV saved: {filename}")
                QMessageBox.information(self, "Success", "Data saved successfully!")
            else:
                self.log_message("✗ Failed to save CSV")
                QMessageBox.warning(self, "Error", "Failed to save data")

    def save_data_json(self):
        """Save data ke JSON (Edge Impulse format)"""
        if not self.data_manager.current_session:
            QMessageBox.warning(self, "Error", "No data to save")
            return
        
        sample_type = self.data_manager.current_session[0].get('sample', 'Unknown')
        default_name = f"EI_{sample_type.replace(' ', '')}{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save as JSON (Edge Impulse)", default_name, "JSON Files (*.json)"
        )
        if filename:
            success = self.data_manager.export_edge_impulse_format(filename, sample_type)
            if success:
                self.log_message(f"📄 JSON saved: {filename}")
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Data exported to Edge Impulse format!\n\n"
                    f"File: {os.path.basename(filename)}\n"
                    f"Label: {sample_type}\n\n"
                    f"Upload ke studio.edgeimpulse.com"
                )
            else:
                self.log_message("✗ Failed to save JSON")
                QMessageBox.warning(self, "Error", "Failed to export data")

    def clear_data(self):
        """Clear all data"""
        reply = QMessageBox.question(
            self, "Confirm Clear", 
            "Clear all recorded data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.clear_all()
            self.is_sampling = False
            self.save_btn.setEnabled(False)
            self.save_json_btn.setEnabled(False)
            self.log_message("🗑 Data cleared")

    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        if hasattr(self, 'log_text') and self.log_text is not None:
            self.log_text.append(log_line)

    # ========================================================================
    # EDGE IMPULSE METHODS
    # ========================================================================

    def load_tflite_model(self):
        """Load TFLite model"""
        if not EI_AVAILABLE:
            QMessageBox.warning(self, "Error", "TensorFlow not available.\nInstall: pip install tensorflow")
            return
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select TFLite Model", "", "TFLite Files (*.tflite)"
        )
        
        if filename:
            try:
                self.tflite_model = tf.lite.Interpreter(model_path=filename)
                self.tflite_model.allocate_tensors()
                self.model_loaded = True
                self.ei_predict_btn.setEnabled(True)
                self.log_message(f"✓ Model loaded: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success", "Model loaded successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load model:\n{e}")
                self.log_message(f"✗ Model load failed: {e}")

    def predict_current_data(self):
        """Predict dengan model TFLite"""
        if not EI_AVAILABLE or not self.model_loaded:
            QMessageBox.warning(self, "Error", "Please load model first")
            return
        
        if not self.data_manager.current_session:
            QMessageBox.warning(self, "Error", "No data available.")
            return
        
        try:
            features = self.data_manager.get_feature_array()
            if features is None:
                QMessageBox.warning(self, "Error", "Cannot extract features")
                return
            
            input_details = self.tflite_model.get_input_details()
            output_details = self.tflite_model.get_output_details()
            
            self.tflite_model.set_tensor(input_details[0]['index'], features)
            self.tflite_model.invoke()
            output_data = self.tflite_model.get_tensor(output_details[0]['index'])
            
            predicted_class = np.argmax(output_data[0])
            confidence = output_data[0][predicted_class]
            predicted_label = self.class_labels[predicted_class] if predicted_class < len(self.class_labels) else f"Class {predicted_class}"
            
            self.prediction_label.setText(f"🎯 {predicted_label} ({confidence*100:.1f}%)")
            self.log_message(f"🔮 Prediction: {predicted_label} ({confidence*100:.1f}%)")
            
            prob_text = "\n".join([f"{self.class_labels[i]}: {output_data[0][i]*100:.1f}%" 
                                   for i in range(len(self.class_labels))])
            QMessageBox.information(
                self, 
                "Prediction Result",
                f"Predicted: {predicted_label}\n"
                f"Confidence: {confidence*100:.1f}%\n\n"
                f"All Probabilities:\n{prob_text}"
            )
            
        except Exception as e:
            QMessageBox.warning(self, "Prediction Error", f"Error:\n{e}")
            self.log_message(f"✗ Prediction error: {e}")

    def closeEvent(self, event):
        """Clean up saat window ditutup"""
        self.tcp_client.disconnect()
        event.accept()