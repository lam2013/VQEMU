
import os
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, name="qemu_gui", log_dir=None):
        base = Path(__file__).resolve().parent
        log_dir = Path(log_dir) if log_dir else base / "logs"
        log_dir.mkdir(exist_ok=True)
        self.log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self._write_header()

    def _write_header(self):
        self.log(f"=== QEMU GUI Log started at {datetime.now()} ===")

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def step(self, label):
        self.log(f"--- STEP: {label} ---")

    def warn(self, msg):
        self.log(f"[⚠️ WARNING] {msg}")

    def error(self, msg):
        self.log(f"[❌ ERROR] {msg}")
        self.log(f"=== QEMU GUI Log ended at {datetime.now()} ===")