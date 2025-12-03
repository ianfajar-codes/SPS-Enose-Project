"""
Frontend Production - Connect to Backend Rust
Run this after 'cargo run dummy' is running
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.window import MainWindow

def main():
    print("=" * 60)
    print("🚀 Electronic Nose - Frontend GUI")
    print("=" * 60)
    print("📡 Ready to connect to backend at 127.0.0.1:8080")
    print("💡 Make sure backend is running: cargo run dummy")
    print("=" * 60)
    print()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    print("✓ GUI started")
    print("👉 Click '🔌 Connect' button to connect to backend")
    print()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
