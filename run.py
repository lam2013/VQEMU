
import ctypes
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import subprocess
import os
import re
import json
import shutil
import tempfile
from find_tools_module import *
from pathlib import Path
import sys, io
import threading
from qemu_advanced_module import *
import load_config

try:
    if sys.stdout and hasattr(sys.stdout, "buffer"):
        if getattr(sys.stdout, "encoding", "").lower().replace("-", "") != "utf8":
            _old_stdout = sys.stdout
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
            _old_stdout.detach()  # Detach without closing the underlying buffer

    if sys.stderr and hasattr(sys.stderr, "buffer"):
        if getattr(sys.stderr, "encoding", "").lower().replace("-", "") != "utf8":
            _old_stderr = sys.stderr
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
            _old_stderr.detach()  # Detach without closing the underlying buffer

except Exception:
    pass


def force_delete_file_as_admin(file_path):
    if not os.path.exists(file_path):
        return False
    path = os.path.normpath(file_path)
    params = f'/c del /f /q "{path}"'
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", params, None, 0)
        return int(ret) > 32
    except Exception:
        return False

def get_config_path():
    def writable_base(path):
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".vqemu_write_test"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("\n")
            test_file.unlink()
            return True
        except Exception:
            return False

    candidates = []
    if sys.platform == "win32":
        localappdata = os.environ.get('LOCALAPPDATA')
        appdata = os.environ.get('APPDATA')
        if localappdata:
            candidates.append(Path(localappdata) / "VQEMU")
        if appdata and appdata != localappdata:
            candidates.append(Path(appdata) / "VQEMU")
        candidates.append(Path.home() / "AppData" / "Local" / "VQEMU")
        candidates.append(Path.home() / ".vqemu")
    else:
        candidates.append(Path.home() / ".vqemu")

    for base_path in candidates:
        if writable_base(base_path):
            return base_path / "config_VQEMU.json"

    fallback = Path(tempfile.gettempdir()) / "VQEMU"
    try:
        fallback.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return fallback / "config_VQEMU.json"

def create_json():
    path = get_config_path()
    if not path.exists():
        data = {"disks": {}, "config": {}, "profiles": {}, "snapshots": {}, "caches": {}, "config_DS": {}, "CCD": {}}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    updated = False
    if "disks" not in data:
        data["disks"] = {}
        updated = True
    if "CCD" not in data:
        data["CCD"] = {}
        updated = True
    if "config" not in data:
        data["config"] = {}
        updated = True
    if "profiles" not in data:
        data["profiles"] = {}
        updated = True
    if "snapshots" not in data:
        data["snapshots"] = {}
        updated = True
    if "caches" not in data:
        data["caches"] = {}
        updated = True
    if "config_DS" not in data:
        data["config_DS"] = {}
        updated = True
    
    if updated:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

def save_disk_path_json_file(name, path):
    try:
        json_path = get_config_path()
        if not json_path.exists():
            create_json()
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        if "disks" not in data:
            data["disks"] = {}
        if name is None:
            key = str(path)
        else:
            key = str(name)
        data["disks"][key] = str(path)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

def load_disk_path_json_file():
    try:
        json_path = get_config_path()
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    if "disks" not in data:
        data["disks"] = {}
        try:
            json_path = get_config_path()
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
    disks = data.get("disks", {})
    result = {}
    for name, info in disks.items():
        path_val = ""
        if isinstance(info, dict):
            path_val = info.get("path", "")
        else:
            path_val = str(info)
        
        if path_val and path_val.lower() != "none":
            result[name] = path_val

    try:
        list_path = list(result.values())
        list_result_ect = ["none"]
        list_result_ect.extend([str(i) for i in list_path])
        return list_result_ect
    except Exception:
        return ["none"]

def load_key_DS():
    try:
        with open(get_config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    if "config_DS" not in data:
        data["config_DS"] = {}
    keys = data["config_DS"].keys()
    return keys

def can_write(folder):
    try:
        testfile = os.path.join(folder, ".__testwrite__")
        with open(testfile, "w") as f:
            f.write("test")
        os.remove(testfile)
        return True
    except Exception:
        return False

def always_return_true():
    return True

class LogViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trình xem Log")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_log)
        btn_layout.addWidget(self.btn_refresh)
        
        self.btn_save = QPushButton("Lưu Log")
        self.btn_save.clicked.connect(self.save_log)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_clear = QPushButton("Xóa Log")
        self.btn_clear.clicked.connect(self.clear_log)
        btn_layout.addWidget(self.btn_clear)
        
        self.btn_close = QPushButton("Đóng")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
        self.log_file = self.get_latest_log()
        self.load_log()
        
        # Auto-refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_log)
        self.timer.start(100) # Refresh every 2 seconds

    def get_latest_log(self):
        if sys.platform == "win32":
            app_data = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
            log_dir = Path(app_data) / "VQEMU" / "logs"
        else:
            log_dir = Path.home() / ".vqemu" / "logs"
            
        if not log_dir.exists():
            return None
        logs = sorted(log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
        return logs[0] if logs else None

    def load_log(self):
        self.log_file = self.get_latest_log()
        if self.log_file and self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_edit.setPlainText(content)
                self.text_edit.moveCursor(QTextCursor.End)
            except Exception as e:
                self.text_edit.setPlainText(f"Error reading log: {e}")
        else:
            if sys.platform == "win32":
                app_data = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
                log_dir = Path(app_data) / "VQEMU" / "logs"
            else:
                log_dir = Path.home() / ".vqemu" / "logs"
            self.text_edit.setPlainText(f"No log file found in {log_dir}")

    def save_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu File Log", "", "Log Files (*.log);;Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            QMessageBox.information(self, "Thành công", "Đã lưu log thành công!")

    def clear_log(self):
        if self.log_file and self.log_file.exists():
            reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xóa nội dung file log hiện tại?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write("")
                self.load_log()

class USBScanThread(QThread):
    scan_finished = pyqtSignal(list)
    scan_error = pyqtSignal(str)

    def run(self):
        cmd = 'Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match "^USB" } | Select-Object FriendlyName, InstanceId | ConvertTo-Json'
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            proc = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, startupinfo=startupinfo)
            if proc.returncode == 0:
                devices = json.loads(proc.stdout)
                if not isinstance(devices, list):
                    devices = [devices]
                self.scan_finished.emit(devices)
            else:
                self.scan_error.emit(f"Process returned {proc.returncode}")
        except Exception as e:
            self.scan_error.emit(str(e))

class USBManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý thiết bị USB")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Chọn", "Tên thiết bị", "Vendor ID", "Product ID"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2c313c;
                color: #e0e0e0;
                gridline-color: #444;
                border: 1px solid #444;
            }
            QHeaderView::section {
                background-color: #3b4252;
                color: #fff;
                padding: 5px;
                border: 1px solid #444;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableCornerButton::section {
                background-color: #3b4252;
                border: 1px solid #444;
            }
            QCheckBox {
                margin-left: 10px;
            }
        """)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_scan = QPushButton("Quét thiết bị")
        self.btn_scan.clicked.connect(self.scan_devices)
        btn_layout.addWidget(self.btn_scan)
        
        self.btn_close = QPushButton("Đóng")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
        self.load_current_config()
        self.scan_devices()

    def load_current_config(self):
        # Use parent's transient list instead of reading file again
        parent = self.parent()
        if parent and hasattr(parent, 'usb_passthrough_list'):
            self.selected_devices = parent.usb_passthrough_list
        else:
            self.selected_devices = []

    def on_checkbox_changed(self, state):
        # Update parent list immediately
        self.update_parent_list()
        # Trigger parent snapshot save
        parent = self.parent()
        if parent and hasattr(parent, 'save_timer'):
            parent.save_timer.start()

    def update_parent_list(self):
        usb_list = []
        for i in range(self.table.rowCount()):
            # Access checkbox via cell widget layout
            widget = self.table.cellWidget(i, 0)
            if widget and widget.layout().count() > 0:
                chk = widget.layout().itemAt(0).widget()
                
                if chk.isChecked():
                    vid = self.table.item(i, 2).text()
                    pid = self.table.item(i, 3).text()
                    name = self.table.item(i, 1).text()
                    usb_list.append({
                        "vendorid": vid,
                        "productid": pid,
                        "name": name
                    })
        
        parent = self.parent()
        if parent:
            parent.usb_passthrough_list = usb_list

    def scan_devices(self):
        self.table.setRowCount(0)
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("Đang quét...")
        
        self.scan_thread = USBScanThread()
        self.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.scan_thread.scan_error.connect(self.on_scan_error)
        self.scan_thread.start()

    def on_scan_finished(self, devices):
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("Quét thiết bị")
        
        row = 0
        for dev in devices:
            name = dev.get("FriendlyName", "Unknown")
            instance_id = dev.get("InstanceId", "")
            
            # Regex to extract VID and PID
            match_vid = re.search(r'VID_([0-9A-Fa-f]{4})', instance_id)
            match_pid = re.search(r'PID_([0-9A-Fa-f]{4})', instance_id)
            
            if match_vid and match_pid:
                vid = "0x" + match_vid.group(1).lower()
                pid = "0x" + match_pid.group(1).lower()
                
                self.table.insertRow(row)
                
                chk = QCheckBox()
                chk.stateChanged.connect(self.on_checkbox_changed)

                for s_dev in self.selected_devices:
                    if s_dev.get("vendorid") == vid and s_dev.get("productid") == pid:
                        chk.setChecked(True)
                        break
                
                chk_widget = QWidget()
                chk_layout = QHBoxLayout(chk_widget)
                chk_layout.addWidget(chk)
                chk_layout.setAlignment(Qt.AlignCenter)
                chk_layout.setContentsMargins(0,0,0,0)
                
                self.table.setCellWidget(row, 0, chk_widget)
                self.table.setItem(row, 1, QTableWidgetItem(name))
                self.table.setItem(row, 2, QTableWidgetItem(vid))
                self.table.setItem(row, 3, QTableWidgetItem(pid))
                row += 1

    def on_scan_error(self, error):
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("Quét thiết bị")
        QMessageBox.warning(self, "Lỗi quét USB", f"Không thể quét thiết bị: {error}")



class QG(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VQEMU")
        icon_path = find_icon("icon_VQEMU.png") or find_icon("icon_VQEMU.ico")
        if icon_path:
            icon = QIcon(str(icon_path))
            self.setWindowIcon(icon)
            app_inst = QApplication.instance()
            if app_inst:
                app_inst.setWindowIcon(icon)
        self.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #23272e;
            }
            QTabBar::tab {
                background: #2c313c;
                color: #e0e0e0;
                border-radius: 12px 12px 0 0;
                min-width: 120px;
                min-height: 32px;
                margin-right: 4px;
                padding: 8px 20px;
                font-size: 16px;
            }
            QTabBar::tab:selected {
                background: #5e81ac;
                color: #fff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #434c5e;
                color: #fff;
            }
            QWidget {
                background: #23272e;
                color: #e0e0e0;
                font-size: 15px;
            }
            QGroupBox {
                border: 2px solid #3b4252;
                border-radius: 8px;
                margin-top: 20px;
                background: #2c313c;
                font-weight: bold;
                font-size: 18px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: #cacdcf;
            }
            QPushButton {
                background: #3b4252;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 15px;
            }
            QPushButton:hover {
                background: #5e81ac;
                color: #fff;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #23272e;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 6px;
                color: #e0e0e0;
                min-height: 28px;
            }
            QLabel {
                font-weight: bold;
                margin-right: 5px;
            }
        """)
        self.is_loading = False
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500)  # Debounce 500ms
        self.save_timer.timeout.connect(self._perform_save_snapshot)
        
        # Load config once
        try:
            with open(get_config_path(), 'r', encoding='utf-8') as f:
                self.cached_config = json.load(f)
        except Exception:
            self.cached_config = {"disks": {}, "config_DS": {}, "profiles": {}}
            
        self.init_tabs()
    
    def open_log_viewer(self):
        if not hasattr(self, 'log_viewer_dialog') or not self.log_viewer_dialog.isVisible():
            self.log_viewer_dialog = LogViewerDialog(self)
            self.log_viewer_dialog.show()
        else:
            self.log_viewer_dialog.raise_()
            self.log_viewer_dialog.activateWindow()

    def open_usb_manager(self):
        dlg = USBManagerDialog(self)
        dlg.exec_()

    def update_system_qemu(self):
        try:
            self.K.blockSignals(True)
            current_idx = self.K.currentIndex()
            add_w = self.AQEW.isChecked()
            for i in range(self.K.count()):
                text = self.K.itemText(i)
                if add_w and not text.endswith("w"):
                    self.K.setItemText(i, text + "w")
                elif not add_w and text.endswith("w"):
                    self.K.setItemText(i, text[:-1])
            self.K.setCurrentIndex(current_idx)
            self.K.blockSignals(False)
        except Exception:
            self.K.blockSignals(False)

    def get_qemu_exe(self):
        arch = self.K.currentText()
        exe_path = find_qemu_system(arch)
        if not exe_path:
            raise FileNotFoundError(f"Không tìm thấy QEMU cho kiến trúc {arch}")
        return str(exe_path)



    def add_cdrom_to_json(self, name, path):
        cfg_path = get_config_path()
        if not cfg_path.exists():
            create_json()
        
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "cdroms" not in data:
            data["cdroms"] = {}
        
        name_cdrom = name
        path_disk = path
        string_json_tree = {
            name_cdrom: {
                "name": name_cdrom,
                "path": path_disk,
            }
        }
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                full_data = json.load(f)
        except:
            full_data = {}
        
        with open(cfg_path, "a", encoding="utf-8") as f:
             json.dump(string_json_tree, f, ensure_ascii=False, indent=4)



    def confin_json(self, key, val=None):
        cfg_path = get_config_path()
        if not cfg_path.exists():
            cfg_path.write_text("{}", encoding="utf-8")
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        updates = {}
        data.setdefault("configs", {})
        if isinstance(key, dict):
            updates = {str(k): v for k, v in key.items()}
        else:
            if (isinstance(key, (list, tuple)) and isinstance(val, (list, tuple))):
                for k, v in zip(key, val):
                    updates[str(k)] = v
            else:
                updates[str(key)] = val
        for k, v in updates.items():
            data["configs"][k] = v
        import tempfile
        fd, tmp = tempfile.mkstemp(prefix=cfg_path.name + "_", dir=str(cfg_path.parent))
        try:
            with open(fd, "w", encoding="utf-8") as tf:
                json.dump(data, tf, ensure_ascii=False, indent=4)
            Path(tmp).replace(cfg_path)
        finally:
            if Path(tmp).exists():
                try:
                    Path(tmp).unlink()
                except Exception:
                    pass
    
    def clear_disk_list(self):
        with open(get_config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        data["disks"] = {}
        with open(get_config_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def init_tabs(self):
        vm_scroll = QScrollArea()
        vm_scroll.setWidgetResizable(True)
        vm_content = QWidget()
        vm_layout = QVBoxLayout(vm_content)
        self.CCRQ = QCheckBox("tùy chọn lệnh chạy", self)
        self.CCRQ.setEnabled(True)
        self.CCRQ.setChecked(False)
        
        self.CCRQT = QLineEdit()
        self.CCRQT.setPlaceholderText("nhập lệnh chạy")
        self.CCRQT.setDisabled(True)

        self.CCRQ.toggled.connect(self.update_custom_command_ui)
        self.AQEW = QCheckBox("Qemu nâng cao", self)
        self.AQEW.setEnabled(True)
        self.AQEW.setChecked(False)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.CCRQ)
        h_layout.addWidget(self.AQEW)
        vm_layout.addLayout(h_layout)

        group_vm = QGroupBox("Cấu hình máy ảo")
        layout_vm = QGridLayout(group_vm)
        layout_vm.addWidget(QLabel("Kiến trúc:"), 1, 0)
        self.K = QComboBox()
        try:
            self.K.addItems(sorted(list(QEMU_SYSTEMS.keys())))
        except:
            pass
        try:
            self.AQEW.toggled.connect(self.update_system_qemu)
        except Exception:
            pass
        self.K.currentIndexChanged.connect(self.update_arch_dependent_widgets)
        layout_vm.addWidget(self.K, 1, 1)
        layout_vm.addWidget(QLabel("CPU:"), 2, 0)
        self.CP = QComboBox()
        layout_vm.addWidget(self.CP, 2, 1)
        layout_vm.addWidget(QLabel("Số nhân CPU:"), 3, 0)
        self.SC = QComboBox()
        self.SC.addItems([str(i) for i in range(1, 11)])
        layout_vm.addWidget(self.SC, 3, 1)
        layout_vm.addWidget(QLabel("RAM (MB):"), 4, 0)
        self.RM = QSpinBox()
        self.RM.setRange(16, 32768)
        self.RM.setValue(1024)
        layout_vm.addWidget(self.RM, 4, 1)
        layout_vm.addWidget(QLabel("VGA:"), 5, 0)
        self.V = QComboBox()
        layout_vm.addWidget(self.V, 5, 1)

        layout_vm.addWidget(QLabel("Âm thanh:"), 6, 0)
        self.A = QComboBox()
        self.update_audio_list()
        
        layout_vm.addWidget(self.A, 6, 1)

        self.MT = QComboBox()
        self.update_machine_type()
        layout_vm.addWidget(QLabel("machine type:"), 7,0)
        layout_vm.addWidget(self.MT, 7,1)

        # Feature 8: Acceleration
        layout_vm.addWidget(QLabel("Tăng tốc (Accel):"), 8, 0)
        
        acc_widget = QWidget()
        acc_layout = QHBoxLayout(acc_widget)
        acc_layout.setContentsMargins(0,0,0,0)
        
        self.ACC = QComboBox()
        self.ACC.addItems(["tcg", "whpx", "hax", "off"])
        self.ACC.setToolTip("Chọn 'tcg' nếu không chắc chắn. 'whpx' yêu cầu Hyper-V/WHPX.")
        
        self.L_ACC_Status = QLabel("")
        
        acc_layout.addWidget(self.ACC)
        acc_layout.addWidget(self.L_ACC_Status)
        
        layout_vm.addWidget(acc_widget, 8, 1)

        self.ACC.currentIndexChanged.connect(self.validate_accelerator)

        self.WDD = QComboBox()
        
        layout_vm.addWidget(QLabel("Watchdog:"), 9, 0)
        layout_vm.addWidget(self.WDD, 9, 1)
        self.K.currentIndexChanged.connect(self.update_watchdog_list)
        self.AQEW.toggled.connect(self.update_watchdog_list)
        

        self.group_vm = group_vm
        vm_layout.addWidget(group_vm)
        self.run = QPushButton("Khởi động máy ảo")
        
        self.btn_view_log = QPushButton("")
        self.btn_view_log.setToolTip("Xem Log")
        log_icon_path = find_icon("log_icon_VEQMU.png")
        if log_icon_path:
             self.btn_view_log.setIcon(QIcon(str(log_icon_path)))
        else:
             self.btn_view_log.setText("Xem Log")
        self.btn_view_log.clicked.connect(self.open_log_viewer)
        
        self.btn_usb_manager = QPushButton("Quản lý USB")
        self.btn_usb_manager.clicked.connect(self.open_usb_manager)

        run_layout = QHBoxLayout()
        run_layout.addWidget(self.run)
        run_layout.addWidget(self.btn_view_log)
        run_layout.addWidget(self.btn_usb_manager)
        
        vm_layout.addWidget(self.CCRQT)
        vm_layout.addLayout(run_layout)
        vm_scroll.setWidget(vm_content)
        self.addTab(vm_scroll, "Máy ảo")


        self.daemon_storage_scroll = QScrollArea()
        self.daemon_storage_scroll.setWidgetResizable(True)
        self.daemon_storage_content = QWidget()
        daemon_storage_layout = QVBoxLayout(self.daemon_storage_content)
        self.CDT = QCheckBox("dùng daemon storage")
        group_DT = QGroupBox("Cấu hình daemon storage")
        layout_DT = QGridLayout(group_DT)
        self.CDT.setChecked(False)
        self.CDT.setEnabled(True)
        layout_DT.addWidget(self.CDT)
        self.label1 = QLabel("tên ổ đĩa:")
        layout_DT.addWidget(self.label1, 2, 0)
        mini_layout_1 = QHBoxLayout()
        self.HD = QComboBox()
        check_list_disk_D = []
        self.HD = QComboBox()
        check_list_disk_D = []
        # Use cached config
        listdisk = self.cached_config.get("disks", {}).keys()
        self.HD.addItems(listdisk)
        self.HD.clear()
        check_list_disk = []
        for i in listdisk:
            check_list_disk.append(str(i))
        for i in listdisk:
            self.HD.addItem(str(i))
        if self.HD.currentText() not in check_list_disk:
            self.HD.clear()
            for i in listdisk:
                self.HD.addItem(str(i))
        self.HD.setEnabled(False)
        layout_DT.addWidget(self.HD, 3, 0)
        layout_DT.addWidget(QLabel("tên process:"), 4, 0)
        self.ENPDS = QLineEdit()
        self.ENPDS.setPlaceholderText("nhập tên process cho DS")
        self.ENPDS.setEnabled(False)
        layout_DT.addWidget(self.ENPDS, 5, 0)
        self.RHD = QPushButton("chạy daemon storage")
        self.RHD.setEnabled(False)
        layout_DT.addWidget(self.RHD, 6, 0)
        self.CDPDS = QCheckBox("Dừng tiến trình DS")
        self.CDPDS.setChecked(False)
        self.CDPDS.setEnabled(False)
        mini_layout_1.addWidget(self.CDPDS)
        self.CDPDS2 = QComboBox()
        self.update_daemon_list_kill()
        self.CDPDS2.setEnabled(False)
        mini_layout_1.addWidget(self.CDPDS2)
        self.BCTDPDS = QPushButton("Dừng tiến trình")
        self.BCTDPDS.setEnabled(False)
        mini_layout_1.addWidget(self.BCTDPDS)
        layout_DT.addLayout(mini_layout_1, 7, 0)
        
        # Feature 9: Daemon Status Table
        layout_DT.addWidget(QLabel("Trạng thái Daemon:"), 8, 0)
        self.table_daemon_status = QTableWidget()
        self.table_daemon_status.setColumnCount(4)
        self.table_daemon_status.setHorizontalHeaderLabels(["Tên", "PID", "Trạng thái", "Thời gian chạy"])
        self.table_daemon_status.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_daemon_status.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_daemon_status.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_daemon_status.setStyleSheet("QTableWidget { background-color: #2c313c; color: white; border: 1px solid #444; } QHeaderView::section { background-color: #3b4252; color: white; border: 1px solid #444; }")
        layout_DT.addWidget(self.table_daemon_status, 9, 0)
        
        self.btn_refresh_daemon = QPushButton("Cập nhật trạng thái")
        layout_DT.addWidget(self.btn_refresh_daemon, 10, 0)
        daemon_storage_layout.addWidget(group_DT)
        self.daemon_storage_scroll.setWidget(self.daemon_storage_content)
        self.addTab(self.daemon_storage_scroll, "Daemon storage")

        self.disk_scroll = QScrollArea()
        self.disk_scroll.setWidgetResizable(True)
        self.disk_content = QWidget()
        disk_layout = QVBoxLayout(self.disk_content)
        group_disk = QGroupBox("Quản lý ổ đĩa")
        layout_disk = QGridLayout(group_disk)
        layout_disk.addWidget(QLabel("HDA:"), 0, 0)
        self.HDA = QComboBox()
        layout_disk.addWidget(self.HDA, 0, 1)
        layout_disk.addWidget(QLabel("HDB:"), 1, 0)
        self.HDB = QComboBox()
        layout_disk.addWidget(self.HDB, 1, 1)
        layout_disk.addWidget(QLabel("HDC:"), 2, 0)
        self.HDC = QComboBox()
        layout_disk.addWidget(self.HDC, 2, 1)
        layout_disk.addWidget(QLabel("HDD:"), 3, 0)
        self.HDD = QComboBox()
        layout_disk.addWidget(self.HDD, 3, 1)
        self.BCD = QPushButton("Thêm/Tạo/Xóa ổ đĩa")
        layout_disk.addWidget(self.BCD, 4, 0, 1, 2)
        self.CLD = QPushButton("Xóa danh sách ổ đĩa")
        self.CLD = QPushButton("Xóa danh sách ổ đĩa")
        layout_disk.addWidget(self.CLD, 5, 0, 1, 2)
        disk_layout.addWidget(group_disk)
        self.disk_scroll.setWidget(self.disk_content)
        self.addTab(self.disk_scroll, "Ổ đĩa")
        check_list_disk = []
        for i in load_disk_path_json_file():
            check_list_disk.append(str(i))
        for i in load_disk_path_json_file():
            self.HDA.addItem(str(i))
            self.HDB.addItem(str(i))
            self.HDC.addItem(str(i))
            self.HDD.addItem(str(i))
        if self.HDA.currentText() not in check_list_disk:
            self.HDA.clear()
            for i in load_disk_path_json_file():
                self.HDA.addItem(str(i))
        if self.HDB.currentText() not in check_list_disk:
            self.HDB.clear()
            for i in load_disk_path_json_file():
                self.HDB.addItem(str(i))
        if self.HDC.currentText() not in check_list_disk:
            self.HDC.clear()
            for i in load_disk_path_json_file():
                self.HDC.addItem(str(i))
        if self.HDD.currentText() not in check_list_disk:
            self.HDD.clear()
            for i in load_disk_path_json_file():
                self.HDD.addItem(str(i))
        

        self.boot_scroll = QScrollArea()
        self.boot_scroll.setWidgetResizable(True)
        self.boot_content = QWidget()
        boot_layout = QVBoxLayout(self.boot_content)
        group_boot = QGroupBox("Khởi động")
        layout_boot = QGridLayout(group_boot)
        self.CBI = QCheckBox("Dùng ISO")
        self.LEI = QLineEdit()
        self.LEI.setPlaceholderText("Đường dẫn file ISO")
        self.bi = QPushButton("Chọn file ISO")
        self.CFDA = QCheckBox("Dùng floppy A")
        self.LEDA = QLineEdit()
        self.BDAD = QPushButton("Chọn file floppy A")
        self.BDAD.setEnabled(False)
        self.LEDA.setPlaceholderText("Đường dẫn file floppy A")
        self.CFDB = QCheckBox("Dùng floppy B")
        self.LEDB = QLineEdit()
        self.BDBD = QPushButton("Chọn file floppy B")
        self.BDBD.setEnabled(False)
        self.LEDB.setPlaceholderText("Đường dẫn file floppy B")
        self.CFDC = QCheckBox("Dùng floppy C")
        self.LEDC = QLineEdit()
        self.LEDC.setPlaceholderText("Đường dẫn file floppy C")
        self.BDCD = QPushButton("Chọn file floppy C")
        self.BDCD.setEnabled(False)
        self.CFDD = QCheckBox("Dùng floppy D")
        self.LEDD = QLineEdit()
        self.LEDD.setPlaceholderText("Đường dẫn file floppy D")
        self.BDDD = QPushButton("Chọn file floppy D")
        self.BDDD.setEnabled(False)
        self.CB_BIOS = QCheckBox("Dùng BIOS")
        self.LE_BIOS = QLineEdit()
        self.LE_BIOS.setPlaceholderText("Đường dẫn file BIOS")
        self.BIOS = QPushButton("Chọn file BIOS")
        self.BIOS.setEnabled(False)
        layout_boot.addWidget(self.CBI, 0, 0)
        layout_boot.addWidget(self.LEI, 0, 1)
        layout_boot.addWidget(self.bi, 0, 2)
        layout_boot.addWidget(self.CFDA, 1, 0)
        layout_boot.addWidget(self.LEDA, 1, 1)
        layout_boot.addWidget(self.BDAD, 1, 2)
        layout_boot.addWidget(self.CFDB, 2, 0)
        layout_boot.addWidget(self.LEDB, 2, 1)
        layout_boot.addWidget(self.BDBD, 2, 2)
        layout_boot.addWidget(self.CFDC, 3, 0)
        layout_boot.addWidget(self.LEDC, 3, 1)
        layout_boot.addWidget(self.BDCD, 3, 2)
        layout_boot.addWidget(self.LEDD, 4, 1)
        layout_boot.addWidget(self.BDDD, 4, 2)
        layout_boot.addWidget(self.CFDD, 4, 0)
        
        # Custom BIOS (User added manually + my addition cleanup)
        # Note: self.CB_BIOS, self.LE_BIOS, self.BIOS are defined above by user.
        # I will reuse them but position them correctly.
        layout_boot.addWidget(self.CB_BIOS, 5, 0)
        layout_boot.addWidget(self.LE_BIOS, 5, 1)
        layout_boot.addWidget(self.BIOS, 5, 2)
        
        # Boot Order (Adding this as user may have missed it or I need to re-add)
        layout_boot.addWidget(QLabel("Boot Order:"), 6, 0)
        self.BOOT_ORDER = QComboBox()
        self.BOOT_ORDER.addItems(["Default", "CD-ROM -> HDD (-boot d c)", "HDD -> CD-ROM (-boot c d)", "HDD Only (-boot c)", "CD-ROM Only (-boot d)", "Floppy -> HDD (-boot a c)", "Network (-boot n)"])
        layout_boot.addWidget(self.BOOT_ORDER, 6, 1)
        self.BOOT_MENU = QCheckBox("Boot Menu")
        layout_boot.addWidget(self.BOOT_MENU, 6, 2)

        self.CB_BIOS.toggled.connect(lambda checked: (self.LE_BIOS.setEnabled(checked), self.BIOS.setEnabled(checked)))
        self.BIOS.clicked.connect(self.browse_bios)

        boot_layout.addWidget(group_boot)
        self.boot_scroll.setWidget(self.boot_content)
        self.addTab(self.boot_scroll, "Khởi động")

        self.CBI.toggled.connect(self.update_iso_enable)
        self.update_iso_enable(self.CBI.isChecked())

        self.net_scroll = QScrollArea()
        self.net_scroll.setWidgetResizable(True)
        self.net_content = QWidget()
        net_layout = QVBoxLayout(self.net_content)
        group_net = QGroupBox("Mạng")
        layout_net = QGridLayout(group_net)
        self.CN = QCheckBox("Bật mạng")
        self.net_list = list(QEMU_SYSTEMS_WIFIS["model"].get(self.K.currentText(), []))
        self.LN = QComboBox()
        self.LN.addItems(self.net_list)
        self.LN.setEnabled(False)
        self.KN = QComboBox()
        self.KN.addItems(list(QEMU_SYSTEMS_WIFIS.get("connection", [])))
        self.KN.setEnabled(False)
        self.CPF = QCheckBox("Mở port forward")
        self.PF = QLineEdit()
        self.PF.setPlaceholderText("hostfwd=tcp::2222-:22")
        layout_net.addWidget(self.CN, 0, 0)
        layout_net.addWidget(QLabel("Loại card mạng:"), 1, 0)
        layout_net.addWidget(self.LN, 1, 1)
        layout_net.addWidget(QLabel("Kiểu mạng:"), 2, 0)
        layout_net.addWidget(self.KN, 2, 1)
        layout_net.addWidget(self.CPF, 3, 0)
        layout_net.addWidget(self.PF, 3, 1)
        net_layout.addWidget(group_net)
        self.net_scroll.setWidget(self.net_content)
        self.addTab(self.net_scroll, "Mạng")
        self.update_arch_dependent_widgets()

        adco_scroll = QScrollArea()
        adco_scroll.setWidgetResizable(True)
        adco_content = QWidget()
        adco_layout = QVBoxLayout(adco_content)
        group_adco = QGroupBox("cấu hình nâng cao")
        layout_adco = QGridLayout(group_adco)
        self.CAD = QCheckBox("Bật tùy chọn daemon storage")
        self.CAD.setChecked(False)
        layout_adco.addWidget(self.CAD, 0, 0)
        self.DHD = QComboBox()
        list_io_ds = QEMU_IO_DAEMON_STORAGE.get(self.K.currentText(), ["none"])
        self.DHD.addItems(list_io_ds)
        self.DHD.setEnabled(False)
        self.label2 = QLabel("IO daemon storage:")
        layout_adco.addWidget(self.label2, 1, 0)
        layout_adco.addWidget(self.DHD, 1, 1)
        self.DSNTR = QComboBox()
        self.DSNTR = QComboBox()
        # Use cached config
        list_key_DSTR = self.cached_config.get("config_DS", {}).keys()
        self.DSNTR.addItems(list_key_DSTR)
        self.DSNTR.setEnabled(False)
        layout_adco.addWidget(QLabel("daemon để chạy:"), 2, 0)
        layout_adco.addWidget(self.DSNTR, 2, 1)
        adco_layout.addWidget(group_adco)

        # Feature 7: Shared Folder
        group_sf = QGroupBox("Shared Folder (Thư mục chia sẻ)")
        layout_sf = QGridLayout(group_sf)
        self.CB_SF = QCheckBox("Bật chia sẻ thư mục")
        self.CB_SF.setChecked(False)
        layout_sf.addWidget(self.CB_SF, 0, 0, 1, 3)
        
        layout_sf.addWidget(QLabel("Đường dẫn host:"), 1, 0)
        self.LE_SF_Path = QLineEdit()
        layout_sf.addWidget(self.LE_SF_Path, 1, 1)
        self.BTN_SF_Browse = QPushButton("Chọn...")
        layout_sf.addWidget(self.BTN_SF_Browse, 1, 2)
        
        layout_sf.addWidget(QLabel("Mount Tag:"), 2, 0)
        self.LE_SF_Tag = QLineEdit("shared")
        layout_sf.addWidget(self.LE_SF_Tag, 2, 1)
        
        adco_layout.addWidget(group_sf)

        # Feature 10: Guest Agent
        group_ga = QGroupBox("Tích hợp Guest Agent")
        layout_ga = QGridLayout(group_ga)
        self.CB_GuestAgent = QCheckBox("Bật QEMU Guest Agent (Tắt/Khởi động lại, Clipboard)")
        self.CB_GuestAgent.setChecked(False)
        self.CB_GuestAgent.setToolTip("Hỗ trợ QEMU Guest Agent để giao tiếp với Host.\nCần cài đặt driver virtio-serial và agent trong máy ảo.\nLệnh kích hoạt: -device virtio-serial -device virtserialport,chardev=qga0,name=org.qemu.guest_agent.0...")
        layout_ga.addWidget(self.CB_GuestAgent, 0, 0)

        adco_layout.addWidget(group_ga)

        # Feature 11: -readconfig
        group_rc = QGroupBox("Read Config")
        layout_rc = QGridLayout(group_rc)
        self.CB_RC = QCheckBox("Bật readconfig")
        self.CB_RC.setChecked(False)
        self.path_rc = QPlainTextEdit()
        self.path_rc.setPlaceholderText("Đường dẫn file config")
        self.path_rc.setEnabled(False)
        self.CB_RC.toggled.connect(self.update_readconfig_ui)
        layout_rc.addWidget(self.CB_RC, 0, 0)
        layout_rc.addWidget(self.path_rc, 0, 1)

        # Feature 12: -sandbox
        group_sb = QGroupBox("Sandbox")
        layout_sb = QGridLayout(group_sb)
        self.CB_SB = QCheckBox("Bật sandbox (lưu ý: sandbox chí hỗ trợ cho linux)")
        self.CB_SB.setChecked(False)
        layout_sb.addWidget(self.CB_SB)
        self.SB_seccomp_mode = QComboBox()
        self.SB_seccomp_mode.addItems(["on", "off"])
        self.SB_seccomp_mode.setEnabled(False)
        layout_sb.addWidget(QLabel("seccomp mode: "))
        layout_sb.addWidget(self.SB_seccomp_mode)
        self.SB_obsolete = QComboBox()
        self.SB_obsolete.addItems(["allow", "deny", "none"])
        self.SB_obsolete.setEnabled(False)
        layout_sb.addWidget(QLabel("obsolete:"))
        layout_sb.addWidget(self.SB_obsolete)
        self.SB_elevateprivileges = QComboBox()
        self.SB_elevateprivileges.addItems(["allow", "deny", "children", "none"])
        self.SB_elevateprivileges.setEnabled(False)
        layout_sb.addWidget(QLabel("elevateprivileges:"))
        layout_sb.addWidget(self.SB_elevateprivileges)
        self.SB_spawn = QComboBox()
        self.SB_spawn.addItems(["allow", "deny", "none"])
        self.SB_spawn.setEnabled(False)
        layout_sb.addWidget(QLabel("spawn: "))
        layout_sb.addWidget(self.SB_spawn)
        self.SB_resourcecontrol = QComboBox()
        self.SB_resourcecontrol.addItems(["allow", "deny", "none"])
        self.SB_resourcecontrol.setEnabled(False)
        layout_sb.addWidget(QLabel("resourcecontrol: "))
        layout_sb.addWidget(self.SB_resourcecontrol)
        
        adco_layout.addWidget(group_rc)

        # Feature 14: -watchdog-action
        wac_group = QGroupBox("Watchdog Action")
        wac_layout = QGridLayout(wac_group)
        self.WAC = QComboBox()
        self.WAC.addItems(["reset","shutdown","poweroff","inject-nmi","pause","debug","none"])
        wac_layout.addWidget(QLabel("watchdog action: "))
        wac_layout.addWidget(self.WAC)
        adco_layout.addWidget(wac_group)

        adco_layout.addWidget(group_sb)
        self.CB_SB.toggled.connect(self.update_ui_SB)
        
        adco_scroll.setWidget(adco_content)
        self.addTab(adco_scroll, "Cấu hình nâng cao")

        self.prof_scroll = QScrollArea()
        self.prof_scroll.setWidgetResizable(True)
        self.prof_content = QWidget()
        prof_layout = QVBoxLayout(self.prof_content)
        group_prof = QGroupBox("Profiles / Cấu hình")
        layout_prof = QGridLayout(group_prof)
        self.profile_list = QListWidget()
        layout_prof.addWidget(self.profile_list, 0, 0, 4, 2)
        self.btn_prof_add = QPushButton("Thêm")
        self.btn_prof_load = QPushButton("Load")
        self.btn_prof_delete = QPushButton("Xóa")
        self.btn_prof_rename = QPushButton("Đổi tên")
        layout_prof.addWidget(self.btn_prof_add, 0, 2)
        layout_prof.addWidget(self.btn_prof_load, 1, 2)
        layout_prof.addWidget(self.btn_prof_delete, 2, 2)
        layout_prof.addWidget(self.btn_prof_rename, 3, 2)
        prof_layout.addWidget(group_prof)
        self.prof_scroll.setWidget(self.prof_content)
        self.addTab(self.prof_scroll, "Cấu hình")

        self.btn_prof_add.clicked.connect(self._ui_profile_add)
        self.btn_prof_load.clicked.connect(self._ui_profile_load)
        self.btn_prof_delete.clicked.connect(self._ui_profile_delete)
        self.btn_prof_rename.clicked.connect(self._ui_profile_rename)
        self.refresh_profile_list()

        self.CFDA.toggled.connect(self.update_FDA)
        self.CFDB.toggled.connect(self.update_FDB)
        self.CFDC.toggled.connect(self.update_FDC)
        self.CFDD.toggled.connect(self.update_FDD)
        self.BDAD.clicked.connect(self.BDA)
        self.BDBD.clicked.connect(self.BDB)
        self.BDCD.clicked.connect(self.BDC)
        self.BDDD.clicked.connect(self.BDD)

        self.CDT.toggled.connect(self.update_daemon_storage_ui)
        self.CDPDS.toggled.connect(self.update_daemon_kill_process)
        self.RHD.clicked.connect(self.update_daemon_list_kill)


        self.CAD.toggled.connect(self.update_advanced_tab)
        
        self.CB_SF.toggled.connect(self.update_sf_ui)
        self.BTN_SF_Browse.clicked.connect(self.browse_shared_folder)
        self.update_sf_ui() # Initialize state

        self.BCD.clicked.connect(self.open_disk_dialog)
        self.CLD.clicked.connect(self.clear_disk_list)
        self.bi.clicked.connect(self.BI)
        self.CBI.toggled.connect(lambda checked: self.LEI.setEnabled(checked))
        self.CN.toggled.connect(lambda checked: (self.LN.setEnabled(checked), self.KN.setEnabled(checked)))
        self.CPF.toggled.connect(lambda checked: self.PF.setEnabled(checked))
        self.run.clicked.connect(self.run_qemu)
        self.run.clicked.connect(create_json)
        self.BCD.clicked.connect(create_json)
        self.btn_prof_add.clicked.connect(create_json)
        self.btn_prof_load.clicked.connect(create_json)
        self.btn_prof_delete.clicked.connect(create_json)
        self.btn_prof_rename.clicked.connect(create_json)
        self.AQEW.toggled.connect(self.update_io_ds)
        self.K.currentIndexChanged.connect(self.update_io_ds)


        # Initialize UI state
        self.update_custom_command_ui(self.CCRQ.isChecked())
        
        self.load_snapshot()
        self.connect_snapshot_signals()
        self.update_disk_list()
        self.update_daemon_list()
        self.KeyPressEvent()

    def update_readconfig_ui(self):
        checked = self.CB_RC.isChecked()
        self.path_rc.setEnabled(checked)

    def KeyPressEvent(self):
        # Thiết lập các phím tắt (Shortcuts)
        self.shortcuts = []
        
        shortcut_run = QShortcut(QKeySequence("F5"), self)
        shortcut_run.activated.connect(self.run_qemu)
        self.shortcuts.append(shortcut_run)

        shortcut_run_ctrl = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_run_ctrl.activated.connect(self.run_qemu)
        self.shortcuts.append(shortcut_run_ctrl)

        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self.save_snapshot)
        self.shortcuts.append(shortcut_save)

        shortcut_iso = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_iso.activated.connect(self.BI)
        self.shortcuts.append(shortcut_iso)

        shortcut_disk = QShortcut(QKeySequence("Ctrl+D"), self)
        shortcut_disk.activated.connect(self.open_disk_dialog)
        self.shortcuts.append(shortcut_disk)

        shortcut_usb = QShortcut(QKeySequence("Ctrl+U"), self)
        shortcut_usb.activated.connect(self.open_usb_manager)
        self.shortcuts.append(shortcut_usb)

        shortcut_log = QShortcut(QKeySequence("Ctrl+L"), self)
        shortcut_log.activated.connect(self.open_log_viewer)
        self.shortcuts.append(shortcut_log)

        shortcut_profile = QShortcut(QKeySequence("Ctrl+M"), self)
        shortcut_profile.activated.connect(self._ui_profile_add)
        self.shortcuts.append(shortcut_profile)

        shortcut_close = QShortcut(QKeySequence("Alt+F4"), self)
        shortcut_close.activated.connect(self.close)
        self.shortcuts.append(shortcut_close)

        shortcut_move_tab_to_right = QShortcut(QKeySequence("Ctrl+Right"), self)
        shortcut_move_tab_to_right.activated.connect(self.move_tab_to_right)
        self.shortcuts.append(shortcut_move_tab_to_right)

        shortcut_move_tab_to_left = QShortcut(QKeySequence("Ctrl+Left"), self)
        shortcut_move_tab_to_left.activated.connect(self.move_tab_to_left)
        self.shortcuts.append(shortcut_move_tab_to_left)

    def keyPressEvent(self, event):
        # Xử lý phím Escape để đóng ứng dụng hoặc các hành động cụ thể
        if event.key() == Qt.Key_Escape:
            self.close()
        
        else:
            super().keyPressEvent(event)

    def update_ui_SB(self):
        # Feature 12: -sandbox
        checked = self.CB_SB.isChecked()
        self.SB_obsolete.setEnabled(checked)
        self.SB_elevateprivileges.setEnabled(checked)
        self.SB_spawn.setEnabled(checked)
        self.SB_resourcecontrol.setEnabled(checked)
        self.SB_seccomp_mode.setEnabled(checked)

    def update_watchdog_list(self):
        if self.AQEW.isChecked():
            self.WDD.clear()
            self.WDD.addItems(sorted(list(QEMU_SYSTEM_WATCHDOG_W.get(self.K.currentText(), []))))
        else:
            self.WDD.clear()
            self.WDD.addItems(sorted(list(QEMU_SYSTEM_WATCHDOG.get(self.K.currentText(), []))))

    def setup_WDD(self):
        try:
            with open(get_config_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
        if self.AQEW.isChecked():
            self.WDD.clear()
            self.WDD.addItems(sorted(list(QEMU_SYSTEM_WATCHDOG_W.get(self.K.currentText(), []))))
            if "watchdog" in data:
                self.WDD.setCurrentText(data["watchdog"])
        else:
            self.WDD.clear()
            self.WDD.addItems(sorted(list(QEMU_SYSTEM_WATCHDOG.get(self.K.currentText(), []))))
            if "watchdog" in data:
                self.WDD.setCurrentText(data["watchdog"])

    def move_tab_to_right(self):
        current_index = self.currentIndex()
        next_index = (current_index + 1) % self.count()
        self.setCurrentIndex(next_index)

    def move_tab_to_left(self):
        current_index = self.currentIndex()
        prev_index = (current_index - 1 + self.count()) % self.count()
        self.setCurrentIndex(prev_index)

    def browse_bios(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Chọn File BIOS", "", "Pulse Files (*.bin *.rom *.fd);;All Files (*.*)")
        if filename:
            self.LE_BIOS.setText(filename)

    def connect_snapshot_signals(self):
        # Connect all relevant widgets to save_snapshot
        # VM Tab
        self.K.currentIndexChanged.connect(self.save_snapshot)
        self.CP.currentIndexChanged.connect(self.save_snapshot)
        self.SC.currentIndexChanged.connect(self.save_snapshot)
        self.RM.valueChanged.connect(self.save_snapshot)
        self.V.currentIndexChanged.connect(self.save_snapshot)
        self.A.currentIndexChanged.connect(self.save_snapshot)
        self.MT.currentIndexChanged.connect(self.save_snapshot)
        self.ACC.currentIndexChanged.connect(self.save_snapshot)
        self.CCRQ.toggled.connect(self.save_snapshot)
        self.CCRQT.textChanged.connect(self.save_snapshot)
        self.AQEW.toggled.connect(self.save_snapshot)
        self.WDD.currentIndexChanged.connect(self.save_snapshot)

        # Disk Tab
        self.HDA.currentIndexChanged.connect(self.save_snapshot)
        self.HDB.currentIndexChanged.connect(self.save_snapshot)
        self.HDC.currentIndexChanged.connect(self.save_snapshot)
        self.HDD.currentIndexChanged.connect(self.save_snapshot)

        #daemon storage tab
        self.CDT.toggled.connect(self.save_snapshot)
        self.HD.currentIndexChanged.connect(self.save_snapshot)
        self.DHD.currentIndexChanged.connect(self.save_snapshot)
        self.ENPDS.textChanged.connect(self.save_snapshot)
        self.RHD.clicked.connect(self.save_snapshot)
        self.RHD.clicked.connect(self.click_run_daemon)
        self.CDPDS.toggled.connect(self.save_snapshot)
        self.CDPDS2.currentIndexChanged.connect(self.save_snapshot)
        self.BCTDPDS.clicked.connect(self.save_snapshot)
        self.BCTDPDS.clicked.connect(self.click_kill_daemon)
        self.btn_refresh_daemon.clicked.connect(self.check_daemon_status)
        
        # Boot Tab
        self.CBI.toggled.connect(self.save_snapshot)
        self.LEI.textChanged.connect(self.save_snapshot)
        self.CFDA.toggled.connect(self.save_snapshot)
        self.LEDA.textChanged.connect(self.save_snapshot)
        self.CFDB.toggled.connect(self.save_snapshot)
        self.LEDB.textChanged.connect(self.save_snapshot)
        self.CFDC.toggled.connect(self.save_snapshot)
        self.LEDC.textChanged.connect(self.save_snapshot)
        self.CFDD.toggled.connect(self.save_snapshot)
        self.LEDD.textChanged.connect(self.save_snapshot)
        self.CB_BIOS.toggled.connect(self.save_snapshot)
        self.LE_BIOS.textChanged.connect(self.save_snapshot)
        self.BOOT_ORDER.currentIndexChanged.connect(self.save_snapshot)
        self.BOOT_MENU.toggled.connect(self.save_snapshot)
        
        # Net Tab
        self.CN.toggled.connect(self.save_snapshot)
        self.LN.currentIndexChanged.connect(self.save_snapshot)
        self.KN.currentIndexChanged.connect(self.save_snapshot)
        self.CPF.toggled.connect(self.save_snapshot)
        self.PF.textChanged.connect(self.save_snapshot)

        #advanced tab
        self.CAD.toggled.connect(self.save_snapshot)
        self.DSNTR.currentIndexChanged.connect(self.save_snapshot)

        # Shared Folder
        self.CB_SF.toggled.connect(self.save_snapshot)
        self.LE_SF_Path.textChanged.connect(self.save_snapshot)
        self.LE_SF_Tag.textChanged.connect(self.save_snapshot)

        # Guest Agent
        self.CB_GuestAgent.toggled.connect(self.save_snapshot)

        #readconfig
        self.CB_RC.toggled.connect(self.save_snapshot)
        self.path_rc.textChanged.connect(self.save_snapshot)

        #sandbox
        self.CB_SB.toggled.connect(self.save_snapshot)
        self.SB_resourcecontrol.currentIndexChanged.connect(self.save_snapshot)
        self.SB_obsolete.currentIndexChanged.connect(self.save_snapshot)
        self.SB_elevateprivileges.currentIndexChanged.connect(self.save_snapshot)
        self.SB_spawn.currentIndexChanged.connect(self.save_snapshot)
        self.SB_seccomp_mode.currentIndexChanged.connect(self.save_snapshot)

        #watchdog action
        self.WAC.currentIndexChanged.connect(self.save_snapshot)

    def save_snapshot(self):
        if self.is_loading:
            return
        self.save_timer.start()

    def _perform_save_snapshot(self):
        try:
            cfg_path = get_config_path()
            # No atomic write for now to keep it simple, but we debounce so it's safer.
            # Ideally we should read-modify-write carefully.
            if not cfg_path.exists():
                return

            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "snapshots" not in data:
                data["snapshots"] = {}
            
            # Save current config to 'latest' snapshot
            data["snapshots"]["latest"] = self.get_current_config()
            
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def load_snapshot(self):
        try:
            cfg_path = get_config_path()
            if not cfg_path.exists():
                return
            
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "snapshots" in data and "latest" in data["snapshots"]:
                self.apply_config(data["snapshots"]["latest"])
        except Exception:
            pass

    def update_disk_list(self):
        with open(get_config_path(), 'r', encoding="utf-8") as f:
            data = json.load(f)
        list_disk = ["none"]
        list_disk.extend(sorted(data["disks"].keys()))
        self.HDA.clear()
        self.HDB.clear()
        self.HDC.clear()
        self.HDD.clear()
        self.HD.clear()
        self.HDA.addItems(list_disk)
        self.HDB.addItems(list_disk)
        self.HDC.addItems(list_disk)
        self.HDD.addItems(list_disk)
        self.HD.addItems(list_disk)
        self.HD.removeItem(0)

    def update_machine_type(self):
        self.MT.clear()
        check_w = self.AQEW.isChecked()
        if check_w == True:
            self.list_m = QEMU_MACHINE_W.get(self.K.currentText(), ["none"])
        else:
            self.list_m = QEMU_MACHINE.get(self.K.currentText(), ["none"])
        self.MT.addItems(self.list_m)

    def validate_accelerator(self):
        acc = self.ACC.currentText()
        if acc in ["tcg", "off"]:
             self.L_ACC_Status.setText("")
             return
        
        threading.Thread(target=self._validate_accel_thread, args=(acc,), daemon=True).start()

    def _validate_accel_thread(self, acc):
        try:
            exe = self.get_qemu_exe()
            # Run check
            cmd = [exe, "-accel", acc, "-machine", "help"]
            # Use startupinfo to hide window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Run with timeout
            proc = subprocess.run(cmd, capture_output=True, timeout=3, startupinfo=startupinfo)
            if proc.returncode != 0:
                 self.L_ACC_Status.setText("❌ Không hỗ trợ")
                 self.L_ACC_Status.setStyleSheet("color: red")
                 self.L_ACC_Status.setToolTip(f"QEMU trả về mã lỗi {proc.returncode}. Có thể máy không hỗ trợ {acc} hoặc chưa bật feature.")
            else:
                 self.L_ACC_Status.setText("✅ Hỗ trợ")
                 self.L_ACC_Status.setStyleSheet("color: green")
                 self.L_ACC_Status.setToolTip("Accelerator khả dụng.")
        except Exception as e:
             self.L_ACC_Status.setText("⚠️ Lỗi kiểm tra")
             self.L_ACC_Status.setStyleSheet("color: orange")
             self.L_ACC_Status.setToolTip(str(e))


    def update_io_ds(self):
        if self.K.currentText() == "rx" or self.K.currentText() == "avr" or self.K.currentText() == "tricore" or self.K.currentText() == "rxw" or self.K.currentText() == "avrw" or self.K.currentText() == "tricorew":
            self.CAD.setChecked(False)
            self.CAD.setEnabled(False)
            self.DHD.clear()
            self.DHD.addItems(["none"])
            self.DHD.setEnabled(False)
            return
        self.CAD.setEnabled(True)
        self.DHD.clear()
        check_w = self.AQEW.isChecked()
        if check_w == True:
            list_io_ds = QEMU_IO_DAEMON_STORAGE_W.get(self.K.currentText(), ["none"])
        else:
            list_io_ds = QEMU_IO_DAEMON_STORAGE.get(self.K.currentText(), ["none"])
        self.DHD.addItems(list_io_ds)

    def update_audio_list(self):
        self.A.clear()
        check_W = self.AQEW.isChecked()
        if check_W == True:
            self.audio_list = QEMU_SYSTEMS_SOUNDS_W.get(self.K.currentText(), ["none"])
        else:
            self.audio_list = QEMU_SYSTEMS_SOUNDS.get(self.K.currentText(), ["none"])
        self.A.addItems(self.audio_list)

    def update_DSNTR(self):
        self.DSNTR.clear()
        try:
            with open(get_config_path(), 'r', encoding="utf-8") as f:
                data = json.load(f)
            list_key_DSTR = list(data.get('config_DS', {}).keys())
            self.DSNTR.addItems(sorted(list_key_DSTR))
        except Exception:
            pass

    def update_custom_command_ui(self, checked):
        # VM Tab
        self.group_vm.setEnabled(not checked)
        self.CCRQT.setEnabled(checked)
        self.CCRQT.setReadOnly(not checked)
        if checked:
            self.CCRQT.setPlaceholderText("nhập lệnh chạy")
        self.CCRQ.setEnabled(True)
            
        # Other Tabs
        self.disk_scroll.setEnabled(not checked)
        self.boot_scroll.setEnabled(not checked)
        self.net_scroll.setEnabled(not checked)
        self.daemon_storage_scroll.setEnabled(not checked)

    def update_daemon_list(self):
        # We need fresh config here to reset it
        with open(get_config_path(), 'r', encoding="utf-8") as f:
            data = json.load(f)
        del data["caches"]
        del data["config_DS"]
        del data["CCD"]
        data["caches"] = {}
        data["config_DS"] = {}
        data["CCD"] = {}
        self.CDPDS2.clear()
        self.DSNTR.clear()
        with open(get_config_path(), 'w', encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.update_DSNTR()
        

    def update_net_list_I(self):
        list_net = QEMU_SYSTEMS_WIFIS.get("model", {}).get(self.K.currentText(), [])
        self.LN.clear()
        self.LN.addItem("none")
        self.LN.addItems(sorted(list_net))

    def update_daemon_storage_ui(self):
        self.HD.setEnabled(self.CDT.isChecked())
        self.RHD.setEnabled(self.CDT.isChecked())
        self.CDPDS.setEnabled(self.CDT.isChecked())
        self.ENPDS.setEnabled(self.CDT.isChecked())

    def update_daemon_kill_process(self):
        self.BCTDPDS.setEnabled(self.CDPDS.isChecked())
        self.CDPDS2.setEnabled(self.CDPDS.isChecked())
    
    def update_daemon_list_kill(self):
        try:
            with open(get_config_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            self.CDPDS2.clear()
            self.CDPDS2.addItems(data["caches"].keys())
        except Exception:
            pass

    def update_advanced_tab(self):
        self.DSNTR.setEnabled(self.CAD.isChecked())
        self.DHD.setEnabled(self.CAD.isChecked())

    def update_sf_ui(self):
        enabled = self.CB_SF.isChecked()
        self.LE_SF_Path.setEnabled(enabled)
        self.BTN_SF_Browse.setEnabled(enabled)
        self.LE_SF_Tag.setEnabled(enabled)

    def browse_shared_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chia sẻ")
        if folder:
            self.LE_SF_Path.setText(folder)


    def update_FDA(self):
        self.LEDA.setEnabled(self.CFDA.isChecked())
        self.BDAD.setEnabled(self.CFDA.isChecked())

    def update_FDB(self):
        self.LEDB.setEnabled(self.CFDB.isChecked())
        self.BDBD.setEnabled(self.CFDB.isChecked())

    def update_FDC(self):
        self.LEDC.setEnabled(self.CFDC.isChecked())
        self.BDCD.setEnabled(self.CFDC.isChecked())

    def update_FDD(self):
        self.LEDD.setEnabled(self.CFDD.isChecked())
        self.BDDD.setEnabled(self.CFDD.isChecked())

    def update_arch_dependent_widgets(self):
        try:
            arch = self.K.currentText()
        except Exception:
            arch = None
        self.CP.clear()
        if arch and arch in QEMU_SYSTEMS_CPUS:
            self.CP.addItems(QEMU_SYSTEMS_CPUS.get(arch, []))
        if arch and arch in QEMU_SYSTEMS_CPUS_W:
            self.CP.addItems(QEMU_SYSTEMS_CPUS_W.get(arch, []))
        else:
            self.CP.addItems(["host", "qemu32", "qemu64"]) if not self.CP.count() else None
        self.V.clear()
        if arch and arch in QEMU_SYSTEMS_VGAS:
            self.V.addItems(QEMU_SYSTEMS_VGAS.get(arch, []))
        if arch and arch in QEMU_SYSTEMS_VGAS_W:
            self.V.addItems(QEMU_SYSTEMS_VGAS_W.get(arch, []))
        else:
            self.V.addItems(["none", "std", "cirrus", "vmware", "qxl", "virtio"])
        self.update_net_list_I()
        self.update_audio_list()
        self.update_machine_type()

    def profiles_dir(self):
        return get_config_path()

    def ensure_profiles_dir(self):
        p = self.profiles_dir()
        try:
            with open(p, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except FileNotFoundError:
            cfg = {'profiles': {}}
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        return

    def list_profiles(self):
        self.ensure_profiles_dir()
        p = self.profiles_dir()
        with open(p, 'r', encoding="utf-8") as f:
            cfg = json.load(f)
        return sorted(cfg['profiles'].keys())

    def refresh_profile_list(self):
        if hasattr(self, 'profile_list'):
            self.profile_list.clear()
            for name in self.list_profiles():
                self.profile_list.addItem(name)

    def save_profile_by_name(self, name):
        if not name:
            return False, 'Empty name'
        p = self.profiles_dir()
        with open(p, 'r', encoding="utf-8") as f:
            cfg = json.load(f)
        try:
            self.apply_config(cfg)
            cfg['profiles'][name] = self.get_current_config()
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.refresh_profile_list()
        except Exception as e:
            return False, str(e)
        return True, None

    def load_profile_by_name(self, name):
        if not name:
            return False, 'Empty name'
        p = self.profiles_dir()
        with open(p, 'r', encoding="utf-8") as f:
            cfg = json.load(f)
        if cfg.get('enb_command_qemu'):
            self.CCRQ.setChecked(True)
            self.CCRQT.setText(cfg.get('command_qemu'))
        else:
            self.CCRQ.setChecked(False)
            self.CCRQT.setText('')
        try:
            self.apply_config(cfg['profiles'][name])
        except Exception as e:
            return False, str(e)
        return True, None

    def delete_profile_by_name(self, name):
        p = self.profiles_dir()
        with open(p, 'r', encoding="utf-8") as f:
            cfg = json.load(f)
        try:
            del cfg['profiles'][name]
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.refresh_profile_list()
        except Exception as e:
            return False, str(e)
        return True, None

    def rename_profile_by_name(self, old, new):
        if not old or not new:
            return False, 'Empty name'
        p = self.profiles_dir()
        with open(p, 'r', encoding="utf-8") as f:
            cfg = json.load(f)
        try:
            cfg['profiles'][new] = cfg['profiles'].pop(old)
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.refresh_profile_list()
        except Exception as e:
            return False, str(e)
        return True, None

    def get_current_config(self):
        arch = self.K.currentText()
        try:
            exe_path = self.get_qemu_exe()
        except Exception:
            exe_path = ""
        else:
            if self.CCRQ.isChecked():
                config = {
                    "enb_command_qemu": True,
                    "command_qemu": self.CCRQT.text().strip()
                }
            else:
                config = {
                    "arch": arch,
                    "machine_type": self.MT.currentText(),
                    "accel": self.ACC.currentText(),
                    "cpu": self.CP.currentText(),
                    "ram": self.RM.value(),
                    "smp": int(self.SC.currentText()),
                    "vga": self.V.currentText() if self.V.currentText().lower() != "none" else "",
                    "audio": self.A.currentText() if self.A.currentText() != "None" else "",
                    "cdrom": self.LEI.text().strip() if self.CBI.isChecked() else "",
                    "hda": self.HDA.currentText() if self.HDA.currentText().lower() != "none" else "",
                    "hdb": self.HDB.currentText() if self.HDB.currentText().lower() != "none" else "",
                    "hdc": self.HDC.currentText() if self.HDC.currentText().lower() != "none" else "",
                    "hdd": self.HDD.currentText() if self.HDD.currentText().lower() != "none" else "",
                    "fda": self.LEDA.text().strip() if self.CFDA.isChecked() else "",
                    "fdb": self.LEDB.text().strip() if self.CFDB.isChecked() else "",
                    "fcd": self.LEDC.text().strip() if self.CFDC.isChecked() else "",
                    "fdd": self.LEDD.text().strip() if self.CFDD.isChecked() else "",
                    "net_enable": self.CN.isChecked(),
                    "net_model": self.LN.currentText(),
                    "net_type": self.KN.currentText(),
                    "portfwd": self.PF.text().strip() if self.CPF.isChecked() else "",
                    "AQEW": self.AQEW.isChecked(),
                    "enb_command_qemu": False,
                    "command_qemu": "",
                    "daemon_storage": self.CDT.isChecked(),
                    "daemon_storage_path": self.HD.currentText() if self.HD.currentText().lower() != "none" else "",
                    "daemon_kill_process": self.CDPDS.isChecked(),
                    "daemon_kill_process_name": self.CDPDS2.currentText() if self.CDPDS2.currentText().lower() != "none" or self.CDPDS2.currentText().lower() != "" else "none",
                    "daemon_edit_name": self.ENPDS.text() if self.ENPDS.text().lower() != "" else "",
                    "IO_daemon_storage": self.DHD.currentText(),
                    "daemon_current": self.DSNTR.currentText(),
                    "check_advanced_tab": self.CAD.isChecked(),
                    "shared_folder_enable": self.CB_SF.isChecked(),
                    "shared_folder_path": self.LE_SF_Path.text(),
                    "shared_folder_tag": self.LE_SF_Tag.text(),
                    "bios_enable": self.CB_BIOS.isChecked(),
                    "bios_path": self.LE_BIOS.text().strip() if self.CB_BIOS.isChecked() else "",
                    "boot_order": self.BOOT_ORDER.currentText(),
                    "boot_menu": self.BOOT_MENU.isChecked(),
                    "guest_agent_enable": self.CB_GuestAgent.isChecked(),
                    "readconfig_enable": self.CB_RC.isChecked(),
                    "readconfig_path": self.path_rc.toPlainText(),
                    "sandbox": {
                        "check": self.CB_SB.isChecked(),
                        "obsolete": self.SB_obsolete.currentText(),
                        "elevateprivileges": self.SB_elevateprivileges.currentText(),
                        "spawn": self.SB_spawn.currentText(),
                        "resourcecontrol": self.SB_resourcecontrol.currentText(),
                        "seccomp mode": self.SB_seccomp_mode.currentText(),
                    },
                    "watchdog": self.WDD.currentText(),
                    "watchdog-action": self.WAC.currentText(),
                }
                
                # Use in-memory list if available, else load from file
                if hasattr(self, 'usb_passthrough_list'):
                    config["usb_passthrough"] = self.usb_passthrough_list
                else:
                    try:
                        with open(get_config_path(), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        config["usb_passthrough"] = data.get("config", {}).get("usb_passthrough", [])
                        # Initialize list if missing
                        self.usb_passthrough_list = config["usb_passthrough"]
                    except:
                        config["usb_passthrough"] = []
                        self.usb_passthrough_list = []
                    
        return config

    def apply_config(self, cfg):
        self.is_loading = True
        try:
            # Block signals to prevent snowballing updates during load
            self.K.blockSignals(True)
            self.CP.blockSignals(True)
            self.SC.blockSignals(True)
            self.RM.blockSignals(True)
            self.V.blockSignals(True)
            self.RM.blockSignals(True)
            self.V.blockSignals(True)
            self.A.blockSignals(True)
            self.MT.blockSignals(True)
            self.ACC.blockSignals(True)
            self.CB_BIOS.blockSignals(True)
            self.LE_BIOS.blockSignals(True)
            self.BOOT_ORDER.blockSignals(True)
            self.BOOT_MENU.blockSignals(True)
            
            self.CB_SF.blockSignals(True)
            self.LE_SF_Path.blockSignals(True)
            self.LE_SF_Tag.blockSignals(True)
            self.CB_GuestAgent.blockSignals(True)
            
            
            try:
                result = self._apply_config_internal(cfg)
                
                # Manually trigger necessary updates after loading
                self.update_arch_dependent_widgets()
                
                # Restore USB Passthrough in memory
                if "usb_passthrough" in cfg:
                    self.usb_passthrough_list = cfg["usb_passthrough"]

                return result
            finally:
                # Restore signals
                self.K.blockSignals(False)
                self.CP.blockSignals(False)
                self.SC.blockSignals(False)
                self.RM.blockSignals(False)
                self.V.blockSignals(False)
                self.A.blockSignals(False)
                self.MT.blockSignals(False)
                self.ACC.blockSignals(False)
                self.CB_BIOS.blockSignals(False)
                self.LE_BIOS.blockSignals(False)
                self.BOOT_ORDER.blockSignals(False)
                self.BOOT_MENU.blockSignals(False)

                self.CB_SF.blockSignals(False)
                self.LE_SF_Path.blockSignals(False)
                self.LE_SF_Tag.blockSignals(False)
                self.CB_GuestAgent.blockSignals(False)

        finally:
            self.is_loading = False

    def _apply_config_internal(self, cfg):
        # Custom Command
        enb_cmd = cfg.get('enb_command_qemu', False)
        self.CCRQ.setChecked(enb_cmd)
        
        # Restore USB Passthrough if present in snapshot/profile
        if "usb_passthrough" in cfg:
            try:
                path = get_config_path()
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if "config" not in data:
                        data["config"] = {}
                    
                    data["config"]["usb_passthrough"] = cfg["usb_passthrough"]
                    
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
            except:
                pass

        if enb_cmd:
            self.CCRQT.setText(cfg.get('command_qemu', ''))
            return

        AQEW = cfg.get('AQEW', False)
        self.AQEW.setChecked(AQEW)
        
        # Arch
        arch = cfg.get('arch', '')
        if arch:
            if self.K.findText(arch) == -1:
                self.K.addItem(arch)
            self.K.setCurrentText(arch)
        self.update_arch_dependent_widgets()
        
        # CPU
        cpu = cfg.get('cpu', '')
        if cpu:
            if self.CP.findText(cpu) == -1:
                self.CP.addItem(cpu)
            self.CP.setCurrentText(cpu)
            
        # SMP
        smp = cfg.get('smp', None)
        if smp is not None:
            try:
                self.SC.setCurrentText(str(smp))
            except Exception:
                pass
                
        # RAM
        ram = cfg.get('ram', None)
        if ram is not None:
            try:
                self.RM.setValue(int(ram))
            except Exception:
                pass
                
        # VGA
        vga = cfg.get('vga', '')
        if vga:
            if self.V.findText(vga) == -1:
                if vga != "none":
                    self.V.addItem(vga)
            self.V.setCurrentText(vga)
            
        # Machine Type
        mt = cfg.get('machine_type', '')
        if mt:
            if self.MT.findText(mt) == -1:
                self.MT.addItem(mt)
            self.MT.setCurrentText(mt)
            
        # Accel
        acc = cfg.get('accel', '')
        if acc:
            if self.ACC.findText(acc) == -1:
                self.ACC.addItem(acc)
            self.ACC.setCurrentText(acc)
            
        # Watchdog
        watchdog = cfg.get('watchdog', '')
        if watchdog:
            if self.WDD.findText(watchdog) == -1:
                self.setup_WDD()
            self.WDD.setCurrentText(watchdog)

            
        # Audio
        audio = cfg.get('audio', '')
        if audio:
            if self.A.findText(audio) == -1:
                self.A.addItem(audio)
            self.A.setCurrentText(audio)
            
        # CDROM
        cdrom = cfg.get('cdrom', '')
        if cdrom:
            self.CBI.setChecked(True)
            self.LEI.setText(cdrom)
        else:
            self.CBI.setChecked(False)
            self.LEI.setText('')
            
        # Disks
        for disk_field, cb in [('hda', self.HDA), ('hdb', self.HDB), ('hdc', self.HDC), ('hdd', self.HDD)]:
            val = cfg.get(disk_field, '')
            if val:
                if cb.findText(val) == -1:
                    cb.addItem(val)
                cb.setCurrentText(val)
        
        # Floppies
        fda = cfg.get('fda', '')
        if fda:
            self.CFDA.setChecked(True)
            self.LEDA.setText(fda)
        else:
            self.CFDA.setChecked(False)
            self.LEDA.setText('')
            
        # BIOS & Boot
        self.CB_BIOS.setChecked(cfg.get('bios_enable', False))
        self.LE_BIOS.setText(cfg.get('bios_path', ''))
        self.BOOT_ORDER.setCurrentText(cfg.get('boot_order', 'Default'))
        self.BOOT_MENU.setChecked(cfg.get('boot_menu', False))
            
        fdb = cfg.get('fdb', '')
        if fdb:
            self.CFDB.setChecked(True)
            self.LEDB.setText(fdb)
        else:
            self.CFDB.setChecked(False)
            self.LEDB.setText('')
            
        fcd = cfg.get('fcd', '')
        if fcd:
            self.CFDC.setChecked(True)
            self.LEDC.setText(fcd)
        else:
            self.CFDC.setChecked(False)
            self.LEDC.setText('')
            
        fdd = cfg.get('fdd', '')
        if fdd:
            self.CFDD.setChecked(True)
            self.LEDD.setText(fdd)
        else:
            self.CFDD.setChecked(False)
            self.LEDD.setText('')
            
        # Network
        net_enable = cfg.get('net_enable', False)
        self.CN.setChecked(net_enable)
        
        net_model = cfg.get('net_model', '')
        if net_model:
            if self.LN.findText(net_model) == -1:
                self.LN.addItem(net_model)
            self.LN.setCurrentText(net_model)
            
        net_type = cfg.get('net_type', '')
        if net_type:
            if self.KN.findText(net_type) == -1:
                self.KN.addItem(net_type)
            self.KN.setCurrentText(net_type)
            
        portfwd = cfg.get('portfwd', '')
        if portfwd:
            self.CPF.setChecked(True)
            self.PF.setText(portfwd)
        else:
            self.CPF.setChecked(False)
            self.PF.setText('')

        # daemon storage
        daemon_storage = cfg.get('daemon_storage', False)
        self.CDT.setChecked(daemon_storage)
        daemon_storage_path = cfg.get('daemon_storage_path', '')
        if daemon_storage_path:
            if self.HD.findText(daemon_storage_path) == -1:
                self.HD.addItem(daemon_storage_path)
            self.HD.setCurrentText(daemon_storage_path)
        daemon_kill_process = cfg.get('daemon_kill_process', False)
        self.CDPDS.setChecked(daemon_kill_process)
        daemon_kill_process_CB = cfg.get('daemon_kill_process_name', '')
        if daemon_kill_process_CB:
            if self.CDPDS2.findText(daemon_kill_process_CB) == -1:
                self.CDPDS2.addItem(daemon_kill_process_CB)
            self.CDPDS2.setCurrentText(daemon_kill_process_CB)
        daemon_edit_name = cfg.get('daemon_edit_name', '')
        if daemon_edit_name:
            self.ENPDS.setText(daemon_edit_name)
        self.DHD.setCurrentText(cfg.get('IO_daemon_storage', ''))

        # advanced tab
        daemon_current = cfg.get('daemon_current', '')
        if daemon_current:
            if self.DSNTR.findText(daemon_current) == -1:
                self.DSNTR.addItem(daemon_current)
            self.DSNTR.setCurrentText(daemon_current)
        check_advanced_tab = cfg.get('check_advanced_tab', False)
        self.CAD.setChecked(check_advanced_tab)

        # Shared Folder
        self.CB_SF.setChecked(cfg.get('shared_folder_enable', False))
        self.LE_SF_Path.setText(cfg.get('shared_folder_path', ''))
        self.LE_SF_Tag.setText(cfg.get('shared_folder_tag', 'shared'))
        self.update_sf_ui()

        # Guest Agent
        self.CB_GuestAgent.setChecked(cfg.get('guest_agent_enable', False))

        # readconfig
        self.CB_RC.setChecked(cfg.get('readconfig_enable', False))
        self.path_rc.setPlainText(cfg.get('readconfig_path', ''))

        # sandbox
        sandbox_cfg = cfg.get('sandbox', {})
        self.CB_SB.setChecked(sandbox_cfg.get('check', False))

        # watchdog
        WAC_cfg = cfg.get('watchdog-action', '')
        if WAC_cfg:
            if self.WAC.findText(WAC_cfg) == -1:
                self.WAC.addItem(WAC_cfg)
            self.WAC.setCurrentText(WAC_cfg)
        
        # Helper function to safely set combobox text
        def set_combobox_text(combobox, text):
            if text:
                if combobox.findText(text) == -1:
                    combobox.addItem(text)
                combobox.setCurrentText(text)

        set_combobox_text(self.SB_obsolete, sandbox_cfg.get('obsolete', ''))
        set_combobox_text(self.SB_elevateprivileges, sandbox_cfg.get('elevateprivileges', ''))
        set_combobox_text(self.SB_spawn, sandbox_cfg.get('spawn', ''))
        set_combobox_text(self.SB_resourcecontrol, sandbox_cfg.get('resourcecontrol', ''))
        set_combobox_text(self.SB_seccomp_mode, sandbox_cfg.get('seccomp mode', ''))



    def _ui_profile_add(self):
        name, ok = QInputDialog.getText(self, "Thêm profile", "Tên profile:")
        if ok and name:
            ok2, err = self.save_profile_by_name(name)
            if not ok2:
                QMessageBox.critical(self, "Lỗi", f"Không lưu profile: {err}")

    def _ui_profile_load(self):
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Chọn profile", "Vui lòng chọn profile để load.")
            return
        name = item.text()
        ok2, err = self.load_profile_by_name(name)
        if not ok2:
            QMessageBox.critical(self, "Lỗi", f"Không load profile: {err}")
        else:
            QMessageBox.information(self, "OK", "Đã load profile.")

    def _ui_profile_delete(self):
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Chọn profile", "Vui lòng chọn profile để xóa.")
            return
        name = item.text()
        reply = QMessageBox.question(self, "Xác nhận", f"Xóa profile {name}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.delete_profile_by_name(name)

    def _ui_profile_rename(self):
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Chọn profile", "Vui lòng chọn profile để đổi tên.")
            return
        old = item.text()
        new, ok = QInputDialog.getText(self, "Đổi tên profile", "Tên mới:", text=old)
        if ok and new and new != old:
            ok2, err = self.rename_profile_by_name(old, new)
            if not ok2:
                QMessageBox.critical(self, "Lỗi", f"Không đổi tên: {err}")
        disks = load_disk_path_json_file()
        for d in disks:
            self.HDA.addItem(d)
            self.HDB.addItem(d)
            self.HDC.addItem(d)
            self.HDD.addItem(d)

    def ui_command_qemu(self):
        self.update_custom_command_ui(self.CCRQ.isChecked())

    def open_disk_dialog(self):
        dlg = DL()
        dlg.exec_()
        disks = load_disk_path_json_file()
        self.update_disk_list()
        for cb in [self.HDA, self.HDB, self.HDC, self.HDD]:
            current_val = cb.currentText()
            cb.clear()
            cb.addItems(disks)
            # Try to restore selection
            if cb.findText(current_val) != -1:
                cb.setCurrentText(current_val)
            else:
                cb.setCurrentIndex(0)
    
    def BI(self):
        file, _ = QFileDialog.getOpenFileName(None, "chọn file", "", "Image File (*.iso *.vfd *.bin) ;; all file (*)")
        self.LEI.setText(file)

    def BDA(self):
        file, _ = QFileDialog.getOpenFileName(None, "chọn file", "", "Image File (*.img *.vfd *.bin) ;; all file (*)")
        self.LEDA.setText(file)

    def BDB(self):
        file, _ = QFileDialog.getOpenFileName(None, "chọn file", "", "Image File (*.img *.vfd *.bin) ;; all file (*)")
        self.LEDB.setText(file)
    
    def BDC(self):
        file, _ = QFileDialog.getOpenFileName(None, "chọn file", "", "Image File (*.img *.vfd *.bin) ;; all file (*)")
        self.LEDC.setText(file)

    def BDD(self):
        file, _ = QFileDialog.getOpenFileName(None, "chọn file", "", "Image File (*.img *.vfd *.bin) ;; all file (*)")
        self.LEDD.setText(file)

    def run_qemu(self):
        create_json()
        arch = self.K.currentText()
        try:
            exe_path = self.get_qemu_exe()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e) + "\nHãy cài QEMU hoặc kiểm tra cấu hình.")
            return
        config = self.get_current_config()
        base_dir = get_config_path().parent
        config_path = base_dir / "config_VQEMU.json"
        key_list = list(config.keys())
        filtered_config = {k: config[k] for k in key_list if k in config}

        with open(get_config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if self.CCRQ.isChecked() == False:
            data["config"] = self.get_current_config()
        else:
            if self.CCRQ.isChecked():
                data["config"]["enb_command_qemu"] = True
                data["config"]["command_qemu"] = self.CCRQT.text()
        with open(get_config_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        json_path = get_config_path()

        try:
            # Gọi trực tiếp hàm từ module load_config thay vì subprocess
            # Điều này sửa lỗi mở cửa sổ mới khi chạy file exe
            load_config.run_qemu_direct(str(json_path))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e) + "\nHãy cài QEMU hoặc kiểm tra cấu hình.")
            return
    
    def run_daemon_storage(self):
        create_json()
        with open(get_config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        idds = len(list(data["caches"].keys()))
        name_ds_check = list(data["config_DS"].keys())
        if self.CDT.isChecked() == False:
            data["config"]["daemon_storage"] = False
            return None
        if self.DHD.currentText() == "":
            QMessageBox.critical(self, "Lỗi", "Hãy chọn loại kết nối IO (IO daemon storage) trước.")
            return None
        if self.HD.currentText() == "" or self.HD.currentText() == "none":
            QMessageBox.critical(self, "Lỗi", "Hãy chọn ổ cứng hoặc nạp ổ cứng qua tab ổ cứng để chạy")
            return None 
        else:
            if self.CDT.isChecked():
                addr_nbd_path = Path(__file__).resolve().parent
                # Ensure forward slashes for QEMU options to avoid escaping issues on Windows
                addr_nbd = addr_nbd_path.as_posix()
                disk_path = self.HD.currentText() if self.HD.currentText() != "none" else ""
                path_DS = find_qemu_storage_daemon()
                if not path_DS:
                    QMessageBox.critical(self, "Lỗi", "Không tìm thấy qemu-storage-daemon. Hãy cài đặt QEMU.")
                    return None
                
                # qemu-storage-daemon.exe is the standard name
                cmd_ds = f'"{path_DS}" --nbd-server addr.type=inet,addr.host=127.0.0.1,addr.port=1000{idds} --blockdev driver=file,node-name=d{idds},filename="{disk_path}" --export type=nbd,id=ex0,node-name=d{idds},writable=on'
                part_cmd_run_qemu = f"-blockdev export=d{idds},driver=nbd,server.type=inet,server.host=127.0.0.1,node-name=nbd{idds},server.port=1000{idds}"
                
                with open(get_config_path(), "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "config_DS" not in data:
                    data["config_DS"] = {}
                
                name_ds = self.ENPDS.text()
                data["config_DS"][name_ds] = {
                        "cmd_ds": cmd_ds,
                        "part_cmd_run_qemu": part_cmd_run_qemu,
                        "id": idds,
                        "node-name": f"d{idds}",
                        "check_list": name_ds,
                        "path_disk": self.HD.currentText(),
                    }
                data["CCD"][name_ds] = {
                    "check_used" : True,
                    "path_disk_used": self.HD.currentText(),
                }
                if name_ds == "":
                    QMessageBox.critical(self, "Lỗi", "Tên ổ đĩa không được để trống.")
                    return None
                if name_ds in name_ds_check:
                    name_ds_check_caches = list(data["caches"].keys())
                    if name_ds in name_ds_check_caches:
                        QMessageBox.critical(self, "Lỗi", "Tên ổ đĩa đã tồn tại.")
                        return None
                    else:
                        pass
                data["config_DS"][name_ds] = {
                        "cmd_ds": cmd_ds,
                        "part_cmd_run_qemu": part_cmd_run_qemu,
                        "id": idds,
                        "node-name": f"d{idds}",
                        "check_list": name_ds,
                        "path_disk": self.HD.currentText(),
                    }
                data["CCD"][name_ds] = {
                    "check_used" : True,
                    "path_disk_used": self.HD.currentText(),
                }
                
                with open(get_config_path(), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                return name_ds

    def click_run_daemon(self):
        name_ds = self.run_daemon_storage()
        if name_ds:
            load_config.run_daemon_storage_direct(get_config_path(), name_ds)
            self.update_daemon_list_kill()
            self.update_DSNTR()
            QMessageBox.information(self, "Thông báo", f"Đã chạy daemon: {name_ds}")

    def click_kill_daemon(self):
        key = self.CDPDS2.currentText()
        if not key:
             return
        load_config.kill_daemon_storage_direct(get_config_path(), key)
        self.update_daemon_list_kill()
        QMessageBox.information(self, "Thông báo", f"Đã dừng daemon: {key}")
        try:
            with open(get_config_path(), 'r', encoding="utf-8") as f:
                data = json.load(f)
            del data["caches"][key]
            key = key.split(":")[0]
            del data["config_DS"][key]
            del data["CCD"][key]
            self.CDPDS2.clear()
            self.CDPDS2.addItems(load_key_DS())
            self.DSNTR.clear()
            self.DSNTR.addItems(load_key_DS())
            with open(get_config_path(), 'w', encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(e)

    def update_iso_enable(self, checked):
        self.LEI.setEnabled(checked)
        self.bi.setEnabled(checked)

    def check_daemon_status(self):
        self.table_daemon_status.setRowCount(0)
        self.btn_refresh_daemon.setText("Đang kiểm tra...")
        self.btn_refresh_daemon.setEnabled(False)
        
        # Read caches
        try:
            with open(get_config_path(), 'r', encoding="utf-8") as f:
                data = json.load(f)
            caches = data.get("caches", {})
        except:
            caches = {}

        if not caches:
            self.btn_refresh_daemon.setText("Cập nhật trạng thái")
            self.btn_refresh_daemon.setEnabled(True)
            return

        import csv
        
        row = 0
        for key, pid in caches.items():
            # Key format usually 'Name:PID' but pid value is also stored
            # Let's trust the key for name if possible, but the 'pid' value is the OS PID
            
            proc_name = key.split(":")[0] if ":" in key else key
            pid_str = str(pid)

            status = "Stopped"
            time_run = "N/A"
            
            # Check using tasklist
            # tasklist /FI "PID eq 1234" /FO CSV /NH
            cmd = f'tasklist /FI "PID eq {pid_str}" /FO CSV /NH'
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                output = subprocess.check_output(cmd, startupinfo=startupinfo).decode("utf-8", errors="ignore")
                
                # Check if PID is in output
                if f'"{pid_str}"' in output:
                    status = "Running"
                    # Not easy to get start time from tasklist without verbose or wmic
                    # Let's try wmic for start time if running
                    # wmic process where ProcessId=1234 get CreationDate
                    try: 
                        cmd_wmic = f'wmic process where ProcessId={pid_str} get CreationDate'
                        out_wmic = subprocess.check_output(cmd_wmic, startupinfo=startupinfo).decode("utf-8", errors="ignore")
                        # Output like: CreationDate \n 202310...
                        dates = [line.strip() for line in out_wmic.splitlines() if line.strip() and "CreationDate" not in line]
                        if dates:
                            # Parse generic WMI date format YYYYMMDDHHMMSS.mmmmm
                            d = dates[0].split('.')[0]
                            if len(d) == 14:
                                dt = datetime.strptime(d, "%Y%m%d%H%M%S")
                                time_run = dt.strftime("%H:%M:%S %d/%m")
                    except:
                        pass
                else:
                    status = "Stopped (Not Found)"
            except:
                status = "Error Check"

            self.table_daemon_status.insertRow(row)
            self.table_daemon_status.setItem(row, 0, QTableWidgetItem(proc_name))
            self.table_daemon_status.setItem(row, 1, QTableWidgetItem(pid_str))
            
            item_status = QTableWidgetItem(status)
            if "Running" in status:
                item_status.setForeground(QColor("green"))
            else:
                item_status.setForeground(QColor("red"))
            self.table_daemon_status.setItem(row, 2, item_status)
            self.table_daemon_status.setItem(row, 3, QTableWidgetItem(time_run))
            row += 1
            
        self.btn_refresh_daemon.setText("Cập nhật trạng thái")
        self.btn_refresh_daemon.setEnabled(True)

    def closeEvent(self, event):
        load_config.kill_all_daemons(get_config_path())
        event.accept()

class DL(QDialog):
    def __init__(self):
        super().__init__()
        self.disk_created_path = None
        self.setWindowTitle("Trình quản lý ổ đĩa")
        self.resize(400, 200)
        self.mode_select = QComboBox()
        self.mode_select.addItems(["New", "Open", "Delete"])
        self.stack = QStackedWidget()
        self.new_widget = self.create_new_widget()
        self.open_widget = self.create_open_widget()
        self.delete_widget = self.create_delete_widget()
        self.stack.addWidget(self.new_widget)
        self.stack.addWidget(self.open_widget)
        self.stack.addWidget(self.delete_widget)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Chọn chế độ ổ đĩa:"))
        layout.addWidget(self.mode_select)
        layout.addWidget(self.stack)
        self.mode_select.currentIndexChanged.connect(self.stack.setCurrentIndex)

    def create_new_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.disk_name = QLineEdit()
        self.disk_name.setPlaceholderText("Tên file ổ đĩa")
        self.disk_format = QComboBox()
        self.disk_format.addItem("qcow2 (format qcow2)")
        self.disk_format.setItemData(0, "qcow2")
        self.disk_format.addItem("img (format raw)")
        self.disk_format.setItemData(1, "img")
        self.disk_size = QSpinBox()
        self.disk_size.setRange(12, 10000000)
        self.disk_size.setValue(1024)
        self.disk_size.setSuffix(" MB")
        self.save_folder = QLineEdit()
        self.save_folder.setPlaceholderText("Thư mục lưu ổ đĩa")
        self.btn_choose_folder = QPushButton("Chọn thư mục")
        self.btn_choose_folder.clicked.connect(self.choose_folder)
        self.btn_create = QPushButton("Tạo ổ đĩa")
        self.btn_create.clicked.connect(self.create_disk)
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.save_folder)
        folder_layout.addWidget(self.btn_choose_folder)
        layout.addWidget(QLabel("Tên file ổ đĩa:"))
        layout.addWidget(self.disk_name)
        layout.addWidget(QLabel("Định dạng ổ đĩa:"))
        layout.addWidget(self.disk_format)
        layout.addWidget(QLabel("Dung lượng ổ đĩa:"))
        layout.addWidget(self.disk_size)
        layout.addWidget(QLabel("Thư mục lưu:"))
        layout.addLayout(folder_layout)
        layout.addWidget(self.btn_create)
        return w

    def create_open_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.disk_path = QLineEdit()
        self.disk_path.setPlaceholderText("Đường dẫn file ổ đĩa")
        self.btn_browse_disk = QPushButton("Chọn file ổ đĩa")
        self.btn_browse_disk.clicked.connect(self.browse_disk)
        self.btn_apcess = QPushButton("Nạp ổ đĩa")
        self.btn_apcess.setCheckable(True)
        self.btn_apcess.clicked.connect(self.load_existing_disk)
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.disk_path)
        browse_layout.addWidget(self.btn_browse_disk)
        layout.addWidget(QLabel("Đường dẫn ổ đĩa hiện có"))
        layout.addLayout(browse_layout)
        layout.addWidget(self.btn_apcess)
        return w

    def create_delete_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.disk_list = QComboBox()
        disks = load_disk_path_json_file()
        if "none" in disks:
            disks.remove("none")
        self.disk_list.addItems(disks)
        self.btn_delete = QPushButton("Xóa ổ đĩa đã chọn")
        self.btn_delete.clicked.connect(self.delete_disk)
        layout.addWidget(QLabel("Chọn ổ đĩa để xóa:"))
        layout.addWidget(self.disk_list)
        layout.addWidget(self.btn_delete)
        return w

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu ổ đĩa")
        if folder:
            self.save_folder.setText(folder)

    def load_existing_disk(self):
        if self.disk_path.text():
            self.disk_created_path = self.disk_path.text()
            save_disk_path_json_file(None, self.disk_created_path)
            self.accept()

    def browse_disk(self):
        file, _ = QFileDialog.getOpenFileName(self, "Chọn ổ đĩa", "", "Disk Images (*.img *.qcow2);;All Files (*)")
        if file:
            self.disk_path.setText(file)
            self.disk_created_path = file
            if self.btn_apcess.isChecked():
                save_disk_path_json_file(None, file)
                self.accept()

    def create_disk(self):
        folder = self.save_folder.text()
        name = self.disk_name.text()
        if self.disk_format.currentIndex() == 1:
            fmt = "raw"
        else:
            fmt = self.disk_format.currentData()
        size = self.disk_size.value()
        if not folder or not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đủ tên và thư mục lưu.")
            return
        if re.match(r'^[A-Za-z]:$', folder):
            folder = folder + os.sep
        folder = os.path.abspath(folder)
        try:
            program_drive = Path(__file__).resolve().drive
            target_drive = Path(folder).resolve().drive
        except Exception:
            program_drive = None
            target_drive = None

        if program_drive and target_drive and program_drive.lower() != target_drive.lower() and not is_admin():
            reply = QMessageBox.question(
                self,
                "Quyền yêu cầu",
                "Bạn đang tạo ổ đĩa trên phân vùng khác (ví dụ D:).\nBạn có muốn khởi động lại chương trình với quyền quản trị (Run as Administrator) để tiếp tục?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    params = f'"{Path(__file__).resolve()}"'
                    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                    if int(ret) <= 32:
                        QMessageBox.critical(self, "Lỗi", "Không thể khởi động lại với quyền admin.")
                    else:
                        QMessageBox.information(self, "Khởi động lại", "Đang khởi động lại chương trình với quyền quản trị. Vui lòng thực hiện thao tác sau khi cửa sổ mới mở.")
                        QApplication.quit()
                        sys.exit(0)
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Không thể yêu cầu quyền admin: {e}")
                    return
            else:
                return

        if not can_write(folder):
            QMessageBox.critical(self, "Lỗi quyền", "Bạn không có quyền ghi vào thư mục này. Vui lòng chạy chương trình với quyền admin hoặc chọn thư mục khác.")
            return
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '.', '-', '_')).rstrip()
        ext = fmt if fmt != 'raw' else 'img'
        full_path = os.path.join(folder, f"{safe_name}.{ext}")

        path_json = get_config_path()
        if os.path.exists(full_path):
            try:
                with open(path_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "disks" not in data:
                    data["disks"] = {}
                data["disks"][full_path] = full_path
                with open(path_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            except Exception:
                pass
            return

        qemu_img_path = find_qemu_img()
        if not qemu_img_path or not qemu_img_path.exists():
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy qemu-img! Hãy build/cài QEMU trước.")
            return
        qemu_img = str(qemu_img_path)
        cmd = [qemu_img, "create", "-f", fmt, full_path, f"{size}M"]
        try:
            subprocess.run(cmd, check=True)
            
            if save_disk_path_json_file(None, full_path):
                QMessageBox.information(self, "Thành công", f"Đã tạo ổ đĩa: {full_path}")
                self.disk_created_path = full_path
                self.accept()
            else:
                QMessageBox.warning(self, "Cảnh báo", f"Đã tạo ổ đĩa: {full_path}\nNhưng không lưu được vào danh sách cấu hình.")
                self.disk_created_path = full_path
                self.accept()

        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi chạy qemu-img:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không tạo được ổ đĩa:\n{e}")

    def KeyPressEvent(self, event):
        key_code = event.key()
        if key_code == Qt.Key_Right:
            self.disk_list.setCurrentIndex(self.disk_list.currentIndex() + 1)
        elif key_code == Qt.Key_Left:
            self.disk_list.setCurrentIndex(self.disk_list.currentIndex() - 1)
        elif key_code in (Qt.Key_Alt + Qt.Key_F4):
            self.close()


    def delete_disk(self):
        disk_path = self.disk_list.currentText()
        if not disk_path:
            QMessageBox.warning(self, "Lỗi", "Không có ổ đĩa nào để xóa.")
            return

        reply = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa file này?\n{disk_path}", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        file_deleted = False
        if os.path.exists(disk_path):
            try:
                os.remove(disk_path)
                file_deleted = True
            except PermissionError:
                ask = QMessageBox.question(self, "Cần quyền Admin", "Không thể xóa file (Access Denied). Bạn có muốn dùng quyền Admin để xóa cưỡng chế?", QMessageBox.Yes | QMessageBox.No)
                if ask == QMessageBox.Yes:
                    if force_delete_file_as_admin(disk_path):
                        QMessageBox.information(self, "Thông báo", "Đã gửi lệnh xóa với quyền Admin. File sẽ bị xóa trong giây lát.")
                        file_deleted = True
                    else:
                        QMessageBox.critical(self, "Lỗi", "Không thể kích hoạt quyền Admin.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi xóa file: {e}")

        if not os.path.exists(disk_path):
             file_deleted = True   
        if file_deleted:
            disks = load_disk_path_json_file()
            
            idx = self.disk_list.findText(disk_path)
            if idx != -1:
                self.disk_list.removeItem(idx)
                try:

                    json_path = get_config_path()
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    disks = data.get("disks", {})
                    
                    keys_to_remove = []
                    for k, v in disks.items():
                        
                        val_str = ""
                        if isinstance(v, dict):
                            val_str = v.get("path", "")
                        else:
                            val_str = str(v)
                        
                        if val_str == disk_path or k == disk_path:
                            keys_to_remove.append(k)
                    
                    for k in keys_to_remove:
                        del disks[k]
                        
                    data["disks"] = disks
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Lỗi khi cập nhật ổ đĩa: {e}")
            
            QMessageBox.information(self, "Thành công", "Đã cập nhật danh sách ổ đĩa.")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if __name__ == "__main__":
    import traceback
    
    try:
        create_json()
        print("VNcore lab 2025 (alias of Nguyễn Trường Lâm)")
        app = QApplication(sys.argv)
        qg = QG()
        qg.show()
        sys.exit(app.exec_())
    except Exception as e:
        traceback.print_exc()
        input("Press Enter to exit...")
#the command:pyinstaller --onedir --noconfirm --icon="icon_VQEMU.ico" --add-data "load_config.py;." --add-data "qemu;qemu" --add-data "log_module.py;." --add-data "find_tools_module.py;." --add-data "qemu_advanced_module.py;." run.py
# 2025 Vncore lab (alias of Nguyễn Trường Lâm)
