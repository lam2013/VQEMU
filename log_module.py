
import os
import sys
import io
from datetime import datetime
from pathlib import Path

# Ensure stdout/stderr use UTF-8 on Windows
try:
    if sys.stdout and hasattr(sys.stdout, "buffer"):
        if getattr(sys.stdout, "encoding", "").lower().replace("-", "") != "utf8":
            _old_stdout = sys.stdout
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
            _old_stdout.detach()
    if sys.stderr and hasattr(sys.stderr, "buffer"):
        if getattr(sys.stderr, "encoding", "").lower().replace("-", "") != "utf8":
            _old_stderr = sys.stderr
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
            _old_stderr.detach()
except Exception:
    pass

class Logger:
    def __init__(self, name="qemu_gui", log_dir=None):
        if log_dir is None:
            if sys.platform == "win32":
                app_data = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
                log_dir = Path(app_data) / "VQEMU" / "logs"
            else:
                log_dir = Path.home() / ".vqemu" / "logs"
        else:
            log_dir = Path(log_dir)

        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            import tempfile
            log_dir = Path(tempfile.gettempdir()) / "VQEMU" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self._write_header()

    def _write_header(self):
        self.log(f"=== QEMU GUI Log started at {datetime.now()} ===")
        
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}"
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("utf-8", errors="backslashreplace").decode("ascii", errors="replace"))
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def step(self, label):
        self.log(f"--- STEP: {label} ---")

    def warn(self, msg):
        self.log(f"[⚠️ WARNING] {msg}")

    def error(self, msg):
        self.log(f"[❌ ERROR] {msg}")
        self.log(f"=== QEMU GUI Log ended at {datetime.now()} ===")