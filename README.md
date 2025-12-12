# 🌿 Electronic Nose (E-Nose) System
**Real-time Aroma Classification using Multi-Channel Gas Sensors, Rust Backend, and Python GUI**

---

## 📋 Project Description

This project implements a complete **Electronic Nose (E-Nose) system** for real-time aroma classification of aromatic leaves (e.g., curry leaves, basil, lemongrass, pandan). The system integrates:

- **Hardware**: Arduino-based gas sensor array (MICS + Grove multichannel sensors)
- **Backend**: Asynchronous Rust server for data processing and communication
- **Frontend**: Python/Qt GUI for real-time visualization and control
- **Machine Learning**: Edge Impulse integration for on-device aroma classification

## 🏗️ System Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ACQUISITION LAYER                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Sample      │───▶│  Gas Sensor  │───▶│  Arduino     │ │
│  │  Chamber     │    │  Array (7ch) │    │  WiFi Module │ │
│  └──────────────┘    └──────────────┘    └──────┬───────┘ │
└──────────────────────────────────────────────────┼─────────┘
                                                   │ WiFi
                                                   ▼
┌─────────────────────────────────────────────────────────────┐
│              PROCESSING & COMMUNICATION LAYER               │
│                   (Rust Backend - Tokio)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Arduino     │  │  Data        │  │  TCP Server  │     │
│  │  Receiver    │─▶│  Processor   │─▶│  (Broadcast) │     │
│  │  (Port 8081) │  │  (Smoothing) │  │  (Port 8080) │     │
│  └──────────────┘  └──────────────┘  └──────┬───────┘     │
└──────────────────────────────────────────────┼─────────────┘
                                               │ TCP JSON
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                        │
│              (Python GUI - PySide6/PyQt)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  TCP Client  │─▶│  Data        │─▶│  Real-time   │     │
│  │  (Receiver)  │  │  Manager     │  │  Plot (7ch)  │     │
│  └──────────────┘  └──────┬───────┘  └──────────────┘     │
│                           │                                 │
│                           ▼                                 │
│                  ┌──────────────┐                           │
│                  │  TFLite      │                           │
│                  │  Inference   │                           │
│                  └──────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Acquisition**: Arduino reads 7-channel sensor array (CO, Ethanol, VOC, NO2 from MICS + Grove sensors)
2. **Transmission**: Data sent via WiFi (TCP) as JSON packets to Rust backend
3. **Processing**: Backend applies moving average smoothing, normalizes sample names, broadcasts to GUI clients
4. **Visualization**: Python GUI displays real-time plots with pyqtgraph
5. **Classification**: TFLite model predicts aroma class from sensor patterns

---

## 🚀 Features

### Backend (Rust)
- ✅ **Dual Mode Operation**:
  - **Normal Mode**: Receives real sensor data from Arduino WiFi
  - **Dummy Mode**: Generates structured test data for GUI development
- ✅ **Async TCP Server** (Tokio): Supports multiple GUI clients simultaneously
- ✅ **Data Processing**: Moving average filter, sample name normalization
- ✅ **Message Types**: `SensorData`, `StatusMessage`, `Command`
- ✅ **CSV Logging**: Automatic sensor data logging to `sensor_data.csv`

### Frontend (Python/Qt)
- ✅ **Real-time Visualization**: 7-channel sensor plot with pyqtgraph
- ✅ **Connection Management**: Connect/disconnect to backend server
- ✅ **Data Export**:
  - CSV format (for analysis/gnuplot)
  - JSON format (Edge Impulse compatible)
- ✅ **Edge Impulse Integration**:
  - Load `.tflite` model
  - Real-time inference on sensor data
  - Display predicted class + confidence
- ✅ **System Log**: Real-time status messages and motor control feedback

---

## 📦 Installation

### Prerequisites

**Hardware**:
- Arduino Uno R4 Wifi
- Step Down DC
- Grove Base Shield + Motor Shield
- Mean Well LRS 50-24 (PSU)
- Gas sensor array: Grove Multichannel Gas Sensor v2 + MiCS-5524
- Acrylic chamber with controlled airflow

**Software**:
- **Rust** (1.70+): [Install Rust](https://rustup.rs/)
- **Python** (3.9+): [Download Python](https://www.python.org/downloads/)
- **Arduino IDE** (for uploading sensor firmware)

---

### Backend Setup (Rust)

1. **Clone repository**:
   ```
   git clone https://github.com/your-username/enose-project.git
   cd enose-project/backend
   ```

2. **Install dependencies** (automatic via Cargo):
   ```
   cargo build --release
   ```

3. **Run in dummy mode** (for testing without hardware):
   ```
   cargo run dummy
   ```

4. **Run in normal mode** (with Arduino WiFi):
   ```
   cargo run
   ```

**Backend listens on**:
- GUI clients: `0.0.0.0:8080`
- Arduino WiFi: `0.0.0.0:8081`

---

### Frontend Setup (Python)

1. **Navigate to frontend**:
   ```
   cd ../frontend
   ```

2. **Create virtual environment** (recommended):
   ```
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

   **requirements.txt**:
   ```
   PySide6>=6.5.0
   pyqtgraph>=0.13.0
   numpy>=1.24.0
   tensorflow>=2.13.0  # for Edge Impulse inference
   ```

4. **Run GUI**:
   ```
   python main.py
   ```

---

### Arduino Setup

1. **Upload WiFi sensor code**:
   - Open `arduino/enose_wifi/enose_wifi.ino` in Arduino IDE
   - Configure WiFi credentials:
     ```
     const char* ssid = "YOUR_WIFI_SSID";
     const char* password = "YOUR_WIFI_PASSWORD";
     const char* serverIP = "192.168.1.100";  // Backend IP
     ```
   - Upload to Arduino Uno R4 WiFi

## 📖 Usage Guide

### Quick Start

1. **Start backend** (in one terminal):
   ```
   cd backend
   cargo run dummy  # or just `cargo run` for real Arduino
   ```

2. **Start GUI** (in another terminal):
   ```
   cd frontend
   python main.py
   ```

3. **Connect GUI to backend**:
   - Click **🔌 Connect** button
   - Default server: `127.0.0.1:8080`

4. **View real-time data**:
   - Sensor plots update automatically (100ms interval)
   - System log shows connection status and messages

---

### Data Export

#### Save as CSV
1. Click **💾 Save CSV** button
2. Choose save location
3. File format:
   ```
   time,co_m,eth_m,voc_m,no2,eth_gm,voc_gm,co_gm
   0.00,45.2,25.3,60.1,5.2,33.8,55.2,50.4
   0.10,45.5,25.6,60.3,5.3,34.0,55.5,50.6
   ...
   ```

#### Save as JSON
1. Click **📄 Save JSON** button
2. File structure:
   ```
   {
     "protected": {"ver": "v1", "alg": "none"},
     "signature": "",
     "payload": {
       "device_name": "E-Nose-Arduino",
       "device_type": "ARDUINO_UNO_R4_WIFI",
       "interval_ms": 100,
       "sensors": [
         {"name": "co_m", "units": "ppm"},
         ...
       ],
       "values": [[45.2, 25.3, 60.1, ...], ...]
     }
   }
   ```

---

## 🤖 Edge Impulse Integration

### Training Workflow

1. **Collect training data**:
   - Run GUI with different leaf samples
   - Save each sample session as JSON
   - Recommended: 3-5 sessions per class, 50-100 samples each

2. **Upload to Edge Impulse**:
   - Create project at [edgeimpulse.com](https://www.edgeimpulse.com)
   - Go to **Data Acquisition** → **Upload data**
   - Upload JSON files, label each class (e.g., "Jeruk", "Kari", "Kemangi", "Pandan")

3. **Create Impulse**:
   - **Input block**: Raw data (7 features: `co_m`, `eth_m`, `voc_m`, `no2`, `eth_gm`, `voc_gm`, `co_gm`)
   - **Processing block**: Raw Data (or Spectral Analysis if using time-series features)
   - **Learning block**: Classification (Keras) - Suggested architecture:
     ```
     Dense(20, activation='relu')
     Dropout(0.25)
     Dense(10, activation='relu')
     Dense(4, activation='softmax')  # 4 classes
     ```

4. **Train model**:
   - Set training cycles: 100 epochs
   - Validation split: 20%
   - Target accuracy: >90%

5. **Deploy model**:
   - Go to **Deployment**
   - Select **TensorFlow Lite (int8 quantized)**
   - Download `.zip` file
   - Extract `model.tflite`

---

### Inference in GUI

1. **Load model**:
   - Click **📥 Load Model (.tflite)**
   - Select downloaded `model.tflite`
   - Status: "Model loaded successfully"

2. **Run prediction**:
   - Ensure data is streaming from backend
   - Click **🔮 Predict Current Data**
   - Result displays predicted class + confidence:
     ```
     Prediction: Daun Kemangi (92.4%)
     ```

3. **Model performance**:
   - Inference time: ~10-50ms (CPU)
   - Input: 7-element float array (averaged sensor values)
   - Output: 4-element probability distribution

---

## 📂 Project Structure

```
enose-project/
├── backend/                  # Rust backend
│   ├── src/
│   │   ├── main.rs           # Entry point, mode selection
│   │   ├── server.rs         # TCP server (async broadcast)
│   │   ├── arduino.rs        # Arduino WiFi receiver
│   │   └── data_process.rs   # Data structures + smoothing
│   ├── Cargo.toml
│
├── frontend/                 # Python GUI
│   ├── gui/
│   │   ├── __init__.py       # Package init
│   │   ├── window.py         # MainWindow (GUI layout)
│   │   ├── tcp.py            # TcpClient (network)
│   │   └── data_manager.py   # Data storage + export
│   ├── main.py               # Entry point
│   └── requirements.txt
│
├── arduino/
│   └── enose_project.ino    # Arduino sensor code
│
├── models/                   # Edge Impulse models
│   └── model.tflite
│
│
└── README.md
```

---

## 🛠️ Module Overview

### Backend Modules (Rust)

| Module | Function |
|--------|----------|
| `main.rs` | Orchestrates dummy/normal mode, initializes server and Arduino receiver |
| `server.rs` | Async TCP server using Tokio, broadcasts `Message` enum to all connected clients |
| `arduino.rs` | Receives JSON packets from Arduino WiFi, forwards to data processor |
| `data_process.rs` | Defines `SensorData` and `StatusMessage` structs, applies moving average smoothing, normalizes sample names |

### Frontend Modules (Python)

| Module | Function |
|--------|----------|
| `main.py` | Entry point, initializes `QApplication` and `MainWindow` |
| `window.py` | Main GUI window, handles layout, controls, plots, and Edge Impulse panel |
| `tcp.py` | `TcpClient` class (QThread), manages TCP connection, parses `DATA:` and `STATUS:` packets |
| `data_manager.py` | `DataManager` class, stores session data, exports CSV/JSON, calculates statistics |

---


## 📊 Data Visualization with Gnuplot

After exporting CSV, visualize with gnuplot:

1. **Install gnuplot**: [gnuplot.info](http://www.gnuplot.info/download.html)

2. **Create plot script** (`plot_jeruk.gnu, plot_kemangi.gnu, plot_pandan.gnu, plot_kari.gnu`):
   ```
   # ============================================
    # GNUPLOT SCRIPT
    # ============================================
    # Kolom data:
    # 1=timestamp, 2=relative_time, 3=sample, 
    # 4=co_m, 5=eth_m, 6=voc_m, 7=no2, 
    # 8=eth_gm, 9=voc_gm, 10=co_gm
    # ============================================
    
    reset
    
    # ============================================
    # KONFIGURASI DASAR
    # ============================================
    
    set datafile separator ","
    set terminal pngcairo size 1600,1000 enhanced font 'Arial,12'
    set output 'plot_nama_sampel.png'
    
    # ============================================
    # STYLE
    # ============================================
    
    set title "Respons Sensor eNose Terhadap Sampel Kari (Level 1 IDLE)" font 'Arial,18' enhanced
    
    set xlabel "Relative Time (detik)" font 'Arial,14'
    set ylabel "Nilai Sensor" font 'Arial,14'
    
    set grid xtics ytics mxtics mytics
    set grid linetype 1 linecolor rgb '#d0d0d0' linewidth 0.5
    
    set key outside right top vertical
    set key box linestyle 1 linecolor rgb '#808080'
    set key spacing 1.3
    set key font 'Arial,11'
    
    set format y "%.2f"
    set format x "%.1f"
    
    set border linewidth 1.5
    set rmargin 35
    
    # Auto range
    set autoscale
    
    # ============================================
    # PLOT DATA (ALL SENSOR)
    # ============================================
    
    plot 'nama_data.csv' every ::1 using 2:4 with linespoints \
         linewidth 2.5 pointtype 7 pointsize 0.6 linecolor rgb "#e74c3c" \
         title 'CO (Metal Oxide)', \
         \
         'nama_data.csv' every ::1 using 2:5 with linespoints \
         linewidth 2.5 pointtype 5 pointsize 0.6 linecolor rgb "#3498db" \
         title 'Ethanol (Metal Oxide)', \
         \
         'nama_data.csv' every ::1 using 2:6 with linespoints \
         linewidth 2.5 pointtype 9 pointsize 0.6 linecolor rgb "#2ecc71" \
         title 'VOC (Metal Oxide)', \
         \
         'nama_data.csv' every ::1 using 2:7 with linespoints \
         linewidth 2.5 pointtype 11 pointsize 0.6 linecolor rgb "#f39c12" \
         title 'NO2', \
         \
         'nama_data.csv' every ::1 using 2:8 with linespoints \
         linewidth 2.5 pointtype 13 pointsize 0.6 linecolor rgb "#9b59b6" \
         title 'Ethanol (Gas Meter)', \
         \
         'nama_data.csv' every ::1 using 2:9 with linespoints \
         linewidth 2.5 pointtype 4 pointsize 0.6 linecolor rgb "#e67e22" \
         title 'VOC (Gas Meter)', \
         \
         'nama_data.csv' every ::1 using 2:10 with linespoints \
         linewidth 2.5 pointtype 6 pointsize 0.6 linecolor rgb "#16a085" \
         title 'CO (Gas Meter)'
   ```

3. **Run**:
   ```
   gnuplot plot_script_name.gnu
   ```
