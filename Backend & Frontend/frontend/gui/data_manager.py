import json
import csv
import numpy as np
from datetime import datetime


class DataManager:
    """
    Class untuk manage data sensor dari E-Nose
    - Menyimpan data real-time
    - Export ke CSV, JSON, Edge Impulse format
    - Provide data untuk plotting
    """
    
    def __init__(self):
        """Initialize data manager"""
        self.current_session = []
        self.session_name = ""
        self.start_time = None
        print("✓ DataManager initialized")

    def start_session(self, name):
        """
        Mulai session baru untuk recording
        
        Args:
            name (str): Nama session/sample (misal: "Daun Kari")
        """
        self.session_name = name
        self.start_time = None
        print(f"✓ Session started: {name}")

    def add_data(self, data):
        """
        Tambahkan data sensor ke session saat ini
        
        Args:
            data (dict): Dictionary dengan keys:
                - timestamp (int/float): Unix timestamp in ms
                - sample (str): Sample name
                - co_m, eth_m, voc_m, no2, eth_gm, voc_gm, co_gm (float): Sensor values
        """
        # Set start time untuk relative time
        if self.start_time is None:
            self.start_time = data.get('timestamp', 0)
        
        # Calculate relative time (in seconds)
        timestamp = data.get('timestamp', 0)
        relative_time = (timestamp - self.start_time) / 1000.0  # Convert ms to seconds
        
        # Add relative time to data
        data_with_time = data.copy()
        data_with_time['relative_time'] = relative_time
        
        # Append to session
        self.current_session.append(data_with_time)

    def get_plot_data(self, max_points=1000):
        """
        Ambil data untuk plotting (dengan downsampling jika perlu)
        
        Args:
            max_points (int): Maximum data points untuk plot (untuk performance)
        
        Returns:
            dict: Dictionary dengan keys untuk setiap sensor dan time array
                  None jika tidak ada data
        """
        if not self.current_session:
            return None
        
        data = self.current_session
        
        # Downsample jika data terlalu banyak
        if len(data) > max_points:
            step = len(data) // max_points
            data = data[::step]
        
        # Extract data untuk plotting
        plot_data = {
            'times': [d.get('relative_time', 0) for d in data],
            'co_m': [d.get('co_m', 0) for d in data],
            'eth_m': [d.get('eth_m', 0) for d in data],
            'voc_m': [d.get('voc_m', 0) for d in data],
            'no2': [d.get('no2', 0) for d in data],
            'eth_gm': [d.get('eth_gm', 0) for d in data],
            'voc_gm': [d.get('voc_gm', 0) for d in data],
            'co_gm': [d.get('co_gm', 0) for d in data],
        }
        
        return plot_data

    def save_to_file(self, filename):
        """
        Save data ke file (CSV atau JSON)
        
        Args:
            filename (str): Path file output
        
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        if not self.current_session:
            print("✗ No data to save")
            return False
        
        try:
            if filename.endswith('.csv'):
                return self._save_csv(filename)
            else:
                return self._save_json(filename)
        except Exception as e:
            print(f"✗ Save error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _save_csv(self, filename):
        """Save data sebagai CSV"""
        with open(filename, 'w', newline='') as f:
            fieldnames = [
                'timestamp', 'relative_time', 'sample',
                'co_m', 'eth_m', 'voc_m', 'no2', 
                'eth_gm', 'voc_gm', 'co_gm'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for data in self.current_session:
                row = {k: data.get(k, 0) for k in fieldnames}
                writer.writerow(row)
        
        print(f"✓ Data saved to CSV: {filename}")
        return True

    def _save_json(self, filename):
        """Save data sebagai JSON"""
        output = {
            'sample_name': self.session_name,
            'timestamp': datetime.now().isoformat(),
            'total_samples': len(self.current_session),
            'data': self.current_session
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Data saved to JSON: {filename}")
        return True

    def export_edge_impulse_format(self, filename, label=None):
        """
        Export data untuk Edge Impulse dengan format yang benar
        
        Args:
            filename (str): Path file output (JSON)
            label (str): Label/class untuk data (misal: "Daun Kari")
        
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        if not self.current_session:
            print("✗ No data to export")
            return False
        
        # Gunakan session_name sebagai label jika tidak diberikan
        if label is None:
            label = self.session_name if self.session_name else "Unknown"
        
        try:
            # Hitung interval sampling (dalam ms)
            if len(self.current_session) > 1:
                time_diff = self.current_session[1]['timestamp'] - self.current_session[0]['timestamp']
                interval_ms = int(time_diff)
            else:
                interval_ms = 2000  # Default 2 detik
            
            # Extract values (7 sensor channels)
            values = []
            for data in self.current_session:
                values.append([
                    float(data.get('co_m', 0)),
                    float(data.get('eth_m', 0)),
                    float(data.get('voc_m', 0)),
                    float(data.get('no2', 0)),
                    float(data.get('eth_gm', 0)),
                    float(data.get('voc_gm', 0)),
                    float(data.get('co_gm', 0))
                ])
            
            # Format Edge Impulse (sesuai spesifikasi)
            edge_impulse_data = {
                "protected": {
                    "ver": "v1",
                    "alg": "none"
                },
                "signature": "",
                "payload": {
                    "device_name": "E-Nose-System",
                    "device_type": "CUSTOM",
                    "interval_ms": interval_ms,
                    "sensors": [
                        {"name": "co_mics", "units": "ppm"},
                        {"name": "ethanol_mics", "units": "ppm"},
                        {"name": "voc_mics", "units": "ppm"},
                        {"name": "no2_grove", "units": "ppm"},
                        {"name": "ethanol_grove", "units": "ppm"},
                        {"name": "voc_grove", "units": "ppm"},
                        {"name": "co_grove", "units": "ppm"}
                    ],
                    "values": values
                }
            }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(edge_impulse_data, f, indent=2)
            
            print(f"✓ Exported Edge Impulse format: {filename}")
            print(f"   Label: {label}")
            print(f"   Samples: {len(values)}")
            print(f"   Interval: {interval_ms}ms")
            return True
            
        except Exception as e:
            print(f"✗ Export error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_feature_array(self, window_size=10):
        """
        Ambil feature array untuk inference model
        Mengambil rata-rata dari N sample terakhir
        
        Args:
            window_size (int): Jumlah sample untuk averaging
        
        Returns:
            numpy.ndarray: Array shape [1, 7] untuk input model
                          None jika data tidak cukup
        """
        if not self.current_session:
            return None
        
        # Ambil data terakhir (window)
        window = min(window_size, len(self.current_session))
        recent_data = self.current_session[-window:]
        
        # Hitung rata-rata untuk setiap sensor
        features = [
            np.mean([d.get('co_m', 0) for d in recent_data]),
            np.mean([d.get('eth_m', 0) for d in recent_data]),
            np.mean([d.get('voc_m', 0) for d in recent_data]),
            np.mean([d.get('no2', 0) for d in recent_data]),
            np.mean([d.get('eth_gm', 0) for d in recent_data]),
            np.mean([d.get('voc_gm', 0) for d in recent_data]),
            np.mean([d.get('co_gm', 0) for d in recent_data])
        ]
        
        # Return sebagai numpy array shape [1, 7]
        return np.array([features], dtype=np.float32)

    def get_statistics(self):
        """
        Dapatkan statistik dari data saat ini
        
        Returns:
            dict: Dictionary dengan statistik untuk setiap sensor
        """
        if not self.current_session:
            return None
        
        sensors = ['co_m', 'eth_m', 'voc_m', 'no2', 'eth_gm', 'voc_gm', 'co_gm']
        stats = {}
        
        for sensor in sensors:
            values = [d.get(sensor, 0) for d in self.current_session]
            stats[sensor] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'median': np.median(values)
            }
        
        return stats

    def clear_all(self):
        """Clear semua data"""
        self.current_session = []
        self.start_time = None
        print("✓ Data cleared")

    def get_sample_count(self):
        """Get jumlah sample saat ini"""
        return len(self.current_session)

    def get_duration(self):
        """
        Get durasi recording (dalam detik)
        
        Returns:
            float: Durasi dalam detik, 0 jika belum ada data
        """
        if not self.current_session or len(self.current_session) < 2:
            return 0.0
        
        start = self.current_session[0].get('relative_time', 0)
        end = self.current_session[-1].get('relative_time', 0)
        return end - start
