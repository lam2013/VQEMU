from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtCore import QVersionNumber
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QVBoxLayout
from typing import override
from threading import *
from datetime import datetime
from log_module import Logger
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import re
import json
import shutil
import ctypes
import tempfile
from find_tools_module import *
from pathlib import Path
import sys, io
import threading
from qemu_advanced_module import *
import load_config
from log_module import *
import struct

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

def get_qss():
    with open(Path(os.path.dirname(__file__)) / "qss_style.qss", "r", encoding="utf-8") as f:
        return f.read()

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
        data = {"disks": {}, "config": {}, "profiles": {}, "snapshots": {}, "caches": {}, "config_DS": {}, "CCD": {}, "display_options": {}, "multi_options": {}, "qemu-edid": {}}
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
    if "display_options" not in data:
        data["display_options"] = {}
        updated = True
    if "multi_options" not in data:
        data["multi_options"] = {}
        updated = True
    if "qemu-edid" not in data:
        data["qemu-edid"] = {}
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
        self.update_parent_list()
        parent = self.parent()
        if parent and hasattr(parent, 'save_timer'):
            parent.save_timer.start()

    def update_parent_list(self):
        usb_list = []
        for i in range(self.table.rowCount()):
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

class multi_option_call(QTabWidget):
    """
    class multi options call là một class chuyên:
        tạo các option có thể gọi liên tục trong một câu lệnh của qemu
    được thêm vào bản v1.9
    """
    closed_signal = pyqtSignal()

    def __init__(self, parent=None):
        self.option_name = ""
        super().__init__(parent)
        if parent:
            self.setWindowFlags(Qt.Window)
        self.setWindowTitle("multi option call menu / gọi nhiều option menu")
        self.setStyleSheet(f"""{get_qss()}""")
        self.resize(400, 600)
        icon_path = find_icon("icon_VQEMU.png") or find_icon("icon_VQEMU.ico")
        if icon_path:
            icon = QIcon(str(icon_path))
            self.setWindowIcon(icon)
            app_inst = QApplication.instance()
            if app_inst:
                app_inst.setWindowIcon(icon)
        self.init_tab()

    def closeEvent(self, event):
        self.closed_signal.emit()
        super().closeEvent(event)
    
    def check_tab(self, option_name: str = ""):
        with open(get_config_path(), "r", encoding='utf-8') as f:
            data = json.load(f)
            config = data["multi_options"]
        types = config.get(option_name).get("type")
        if types == "fw_cfg":
            return 0
        else:
            return -1

    def on_reoption(self, option_name=""):
        """
        Hàm này được tự động gọi khi nhấn nút 'thay đổi thông số option' (self.btn_moc_reoption) từ cửa sổ chính.
        :param option_name: Tên của Item hiện tại đang được chọn trong list (nếu không chọn sẽ là chuỗi rỗng "")
        """
        self.option_name = option_name
        self.reoption = True
        self.set_current_data(option_name)
    
    def set_current_data(self, option_name: str = ""):
        if not (hasattr(self, "reoption") and self.reoption):
            return
        if not option_name:
            return
        with open(get_config_path(), "r", encoding='utf-8') as f:
            data = json.load(f)
            config = data["multi_options"]
        option_data = config.get(option_name)
        if not option_data:
            return
        # Điền tên option vào NameOption
        if hasattr(self, "NameOption"):
            self.NameOption.setText(option_name)
        idx_tab = self.check_tab(option_name)
        if idx_tab >= 0:
            self.setCurrentIndex(idx_tab)
            if idx_tab == 0:
                has_line = option_data.get("Line")
                if hasattr(self, "fw_cfg_comboBox"):
                    # index 0 = file path, index 1 = string
                    self.fw_cfg_comboBox.setCurrentIndex(0 if has_line else 1)
                # Sau khi setCurrentIndex, fw_cfg_update_widget sẽ tạo widget phù hợp
                if has_line:
                    if hasattr(self, "LineEdit"):
                        self.LineEdit.setText(has_line)
                else:
                    if hasattr(self, "TextEdit"):
                        self.TextEdit.setText(option_data.get("Text", ""))

    def init_tab(self):
        # fw_cfg option
        self.saveoption = QPushButton("lưu tùy chọn / save option")
        self.NameOption = QLineEdit()
        self.NameOption.setPlaceholderText("nhập tên cho option")
        self.saveoption.clicked.connect(self.save_config)
        self.fw_cfg_scrollarea = QScrollArea()
        self.fw_cfg_scrollarea.setWidgetResizable(True)
        fw_cfg_content = QWidget()
        group_fw_cfg = QGroupBox("fw_cfg menu")
        self.layout_fw_cfg = QVBoxLayout(group_fw_cfg)
        fw_cfg_layout = QGridLayout(fw_cfg_content)
        fw_cfg_layout.addWidget(group_fw_cfg)
        self.layout_fw_cfg.addWidget(self.NameOption)
        self.fw_cfg_comboBox = QComboBox()
        self.fw_cfg_comboBox.addItems(["file path / đường dẫn file", "string / chuỗi văn bản"])
        self.layout_fw_cfg.addWidget(self.fw_cfg_comboBox)
        self.fw_cfg_update_widget()
        self.fw_cfg_comboBox.currentIndexChanged.connect(self.fw_cfg_update_widget)
        self.layout_fw_cfg.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fw_cfg_scrollarea.setWidget(fw_cfg_content)
        fw_cfg_layout.addWidget(self.saveoption)
        self.addTab(self.fw_cfg_scrollarea, "fw_cfg")

        self.set_current_data(self.option_name)

    def clean_fw_cfg(self):
        if hasattr(self, "LineEdit") and self.LineEdit is not None:
            self.layout_fw_cfg.removeWidget(self.LineEdit)
            self.LineEdit.setParent(None)
            self.LineEdit.deleteLater()
            del self.LineEdit

        if hasattr(self, "TextEdit") and self.TextEdit is not None:
            self.layout_fw_cfg.removeWidget(self.TextEdit)
            self.TextEdit.setParent(None)
            self.TextEdit.deleteLater()
            del self.TextEdit

    def fw_cfg_update_widget(self):
        mode = self.fw_cfg_comboBox.currentText()
        if "path" in mode:
            if hasattr(self, "TextEdit"):
                self.clean_fw_cfg()
            if not hasattr(self, "LineEdit"):
                self.LineEdit = QLineEdit()
                self.LineEdit.setPlaceholderText("nhập đường dẫn file")
                self.layout_fw_cfg.addWidget(self.LineEdit)
        elif "string" in mode:
            if hasattr(self, "LineEdit"):
                self.clean_fw_cfg()
            if not hasattr(self, "TextEdit"):
                self.TextEdit = QTextEdit()
                self.TextEdit.setPlaceholderText("nhập mã nguồn vào đây")
                self.layout_fw_cfg.addWidget(self.TextEdit)

    def check_fw_cfg_available(self):
        if not self.NameOption.text().strip():
            return False
        mode = self.fw_cfg_comboBox.currentText()
        if "path" in mode:
            if hasattr(self, "LineEdit") and self.LineEdit is not None:
                val = self.LineEdit.text().strip()
                if val and Path(val).exists():
                    return True
            return False
        else:
            if hasattr(self, "TextEdit") and self.TextEdit is not None:
                val = self.TextEdit.toPlainText().strip()
                if val:
                    return True
            return False

    def save_config(self):
        mode = self.fw_cfg_comboBox.currentText()
        if not self.NameOption.text().strip():
            QMessageBox.warning(self, "option fw_cfg", "Chưa nhập tên cho option")
            return
        with open(get_config_path(), 'r', encoding="utf-8") as f:
            data = json.load(f)
            mocc = data["multi_options"]
        if self.NameOption.text().strip() in mocc:
            QMessageBox.warning(self, "option fw_cfg", "Tên option đã tồn tại")
            return

        if "path" in mode:
            if not hasattr(self, "LineEdit") or not self.LineEdit.text().strip():
                QMessageBox.warning(self, "option fw_cfg", "Chưa nhập đường dẫn file fw_cfg")
                return
            if not Path(self.LineEdit.text().strip()).exists():
                QMessageBox.warning(self, "option fw_cfg", "Đường dẫn file không tồn tại")
                return
        else:
            if not hasattr(self, "TextEdit") or not self.TextEdit.toPlainText().strip():
                QMessageBox.warning(self, "option fw_cfg", "Chưa nhập mã nguồn fw_cfg")
                return

        idx = self.currentIndex()
        if idx == 0:
            config_path = get_config_path()
            try:
                with open(config_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {}

            if "multi_options" not in data:
                data["multi_options"] = {}
            if hasattr(self, "reoption") and self.reoption != True:
                data["multi_options"][self.option_name] = {
                    "type": "fw_cfg",
                    "mode": self.fw_cfg_comboBox.currentText(),
                    "Line": self.LineEdit.text().strip() if hasattr(self, "LineEdit") and self.LineEdit else False,
                    "Text": self.TextEdit.toPlainText().strip() if hasattr(self, "TextEdit") and self.TextEdit else False,
                }
            else:
                data["multi_options"][self.NameOption.text().strip()] = {
                    "type": "fw_cfg",
                    "mode": self.fw_cfg_comboBox.currentText(),
                    "Line": self.LineEdit.text().strip() if hasattr(self, "LineEdit") and self.LineEdit else False,
                    "Text": self.TextEdit.toPlainText().strip() if hasattr(self, "TextEdit") and self.TextEdit else False,
                }

            with open(config_path, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "Thành công", f"Đã lưu option '{self.NameOption.text().strip()}'")
            self.close()

class Edid_dialog(QDialog):
    """Edid Dialog:
        widget hỗ trợ việc tạo file edid thông qua qemu-edid
    được thêm vào bản v1.9"""
    closed_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        if parent:
            self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Edid / Cấu hình Display")
        self.setStyleSheet(f"""{get_qss()}""")
        self.resize(700, 600)
        icon_path = find_icon("icon_VQEMU.png") or find_icon("icon_VQEMU.ico")
        if icon_path:
            icon = QIcon(str(icon_path))
            self.setWindowIcon(icon)
            app_inst = QApplication.instance()
            if app_inst:
                app_inst.setWindowIcon(icon)
        self.init_tab()
    
    def init_tab(self):
        main_layout = QVBoxLayout(self)
        self.menu = QScrollArea()
        self.menu_content = QWidget()
        self.menu_layout = QVBoxLayout(self.menu_content)
        group_menu = QGroupBox("menu edid")
        self.layout_menu = QGridLayout(group_menu)
        self.name_output_file = QLineEdit()
        self.folder_output_file = QLineEdit()
        self.btn_folder_output_file = QPushButton("Chọn đường dẫn")
        self.layout_menu.addWidget(QLabel("Nhập tên file"), 0, 0)
        self.layout_menu.addWidget(self.name_output_file, 0, 1)
        self.layout_menu.addWidget(QLabel("Chọn thư mục"), 1, 0)
        self.layout_menu.addWidget(self.folder_output_file, 1, 1)
        self.layout_menu.addWidget(self.btn_folder_output_file, 1, 2)
        self.name_output_file.setPlaceholderText("nhập tên file")
        self.folder_output_file.setPlaceholderText("Chọn nơi chứa file")
        self.btn_folder_output_file.clicked.connect(self.btn_folder_output_file_clicked)
        self.monitor_vendor = QLineEdit()
        self.monitor_vendor.setEnabled(False)
        self.chk_monitor_vendor = QCheckBox("bật vendor monitor")
        self.chk_monitor_vendor.toggled.connect(lambda:self.monitor_vendor.setEnabled(self.chk_monitor_vendor.isChecked()))
        self.monitor_vendor.setPlaceholderText("nhập vendor ID")
        self.layout_menu.addWidget(self.chk_monitor_vendor, 2, 0, 1, 3)
        self.layout_menu.addWidget(self.monitor_vendor, 3, 0, 1, 2)
        self.name_monitor = QLineEdit()
        self.layout_menu.addWidget(self.name_monitor, 4, 0, 1, 3)
        self.name_monitor.setPlaceholderText("nhập tên monitor (mặc định là none)")
        self.serial_monitor = QLineEdit()
        self.serial_monitor.setPlaceholderText("nhập số serial(mặc định là không có serial)")
        self.layout_menu.addWidget(self.serial_monitor, 5, 0, 1, 3)
        self.dpi_monitor = QSpinBox()
        self.dpi_monitor.setRange(28, 390)
        self.dpi_monitor.setValue(96)
        self.layout_menu.addWidget(QLabel("dpi monitor"), 6, 0)
        self.layout_menu.addWidget(self.dpi_monitor, 6, 1)
        self.xres = QSpinBox()
        self.xres.setRange(5, 5120)
        self.xres.setValue(1920)
        self.xres.setSuffix("px")
        self.layout_menu.addWidget(QLabel("xres"), 7, 0)
        self.layout_menu.addWidget(self.xres, 7, 1)
        self.yres = QSpinBox()
        self.yres.setRange(10, 2160)
        self.yres.setValue(1080)
        self.yres.setSuffix("px")
        self.layout_menu.addWidget(QLabel("yres"), 8, 0)
        self.layout_menu.addWidget(self.yres, 8, 1)
        self.max_xres = QSpinBox()
        self.max_xres.setRange(5, 5120)
        self.max_xres.setValue(1920)
        self.max_xres.setSuffix("px")
        self.max_xres.setEnabled(False)
        self.btn_max_xres = QCheckBox()
        self.btn_max_xres.setText("bật giới hạn chiều rộng tối đa")
        self.btn_max_xres.clicked.connect(lambda : self.max_xres.setEnabled(self.btn_max_xres.isChecked()))
        self.layout_menu.addWidget(self.btn_max_xres, 9, 0)
        self.layout_menu.addWidget(self.max_xres, 9, 1)
        self.max_yres = QSpinBox()
        self.max_yres.setRange(10, 2160)
        self.max_yres.setValue(1080)
        self.max_yres.setSuffix("px")
        self.max_yres.setEnabled(False)
        self.btn_max_yres = QCheckBox()
        self.btn_max_yres.setText("bật giới hạn chiều cao tối đa")
        self.btn_max_yres.clicked.connect(lambda : self.max_yres.setEnabled(self.btn_max_yres.isChecked()))
        self.layout_menu.addWidget(self.btn_max_yres, 10, 0)
        self.layout_menu.addWidget(self.max_yres, 10, 1)
        self.btn_build = QPushButton("build")
        self.layout_menu.addWidget(self.btn_build, 11, 0, 1, 2)
        self.btn_build.clicked.connect(self.btn_build_clicked)

        self.menu_layout.addWidget(group_menu)
        self.menu.setWidget(self.menu_content)
        self.menu.setWidgetResizable(True)
        main_layout.addWidget(self.menu)

    def btn_folder_output_file_clicked(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục")
        if folder_path:
            self.folder_output_file.setText(folder_path)

    def check_avilable_config(self):
        if not self.folder_output_file.text():
            QMessageBox.warning(self, "warning", "vui lòng nhập đường dẫn file")
            return False
        if not self.name_output_file.text():
            QMessageBox.warning(self, "warning", "vui lòng tên file output")
            return False
        strs = f"{self.folder_output_file.text()}/{self.name_output_file.text()}"
        if os.path.exists(strs):
            QMessageBox.warning(self, "warning", f"địa chỉ {strs} đã tồn tại")
            return False
        if os.path.isdir(self.folder_output_file.text()) == False:
            QMessageBox.warning(self, "warning", f"địa chỉ {self.folder_output_file.text()} không hợp lệ")
            return False
        return True

    def check_avilable_vendor(self):
        if self.chk_monitor_vendor.isChecked() == False:
            print("ok2")
            return True
        for i in str(self.monitor_vendor.text()):
            if str(i).isupper() == False:
                QMessageBox.warning(self, "warning", "vui lòng chỉ nhập chữ in hoa")
                return False
            if str(i).isalpha() == False:
                QMessageBox.warning(self, "warning", "vui lòng chỉ nhập chữ cái")
                return False
        if len(str(self.monitor_vendor.text())) == 3:
            print("ok")
            return True
        else:
            QMessageBox.warning(self, "warning", """Vendor ID không hợp lệ, một vendor ID phải tuân theo 3 điều:
            - chỉ có 3 kí tự
            - chỉ là chữ cái, không chữ số, kí tự đặc biệt
            - tất cả chữ đều là chữ in hoa
            """)
            return False

    def count_option(self):
        with open(get_config_path(), "r", encoding="utf-8") as f:
            config: dict = json.load(f)
            config_Edid: dict = config.get("qemu-edid")
        a = 0
        for i in config_Edid.keys():
            a += 1
        return a

    def config_option_edid(self):
        if not self.check_avilable_config():
            return
        option = {
            "name": self.name_monitor.text() if self.name_monitor.text() else None,
            "located" : f"{self.folder_output_file.text()}/{self.name_output_file.text()}.bin",
            "vendor": self.monitor_vendor.text() if self.chk_monitor_vendor.isChecked() and self.check_avilable_vendor() else "NON",
            "serial": self.serial_monitor.text() if self.serial_monitor.text() else None,
            "dpi": self.dpi_monitor.value(),
            "xres": self.xres.value(),
            "yres": self.yres.value(),
            "max_xres": self.max_xres.value() if self.btn_max_xres.isChecked() else None,
            "max_yres": self.max_yres.value() if self.btn_max_yres.isChecked() else None
        }
        with open(get_config_path(), "r", encoding="utf-8") as f:
            config: dict = json.load(f)
            config_Edid: dict = config.get("qemu-edid")
            config_Edid[f"EDID-{self.count_option()}"] = option
        with open(get_config_path(), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def option_config(self):
        strs = f"{self.folder_output_file.text()}/{self.name_output_file.text()}.bin"
        cmd = f"{find_qemu_edid()} -o {strs}"
        if self.chk_monitor_vendor.isChecked() and self.monitor_vendor.text() != "":
            cmd += f" -v {self.monitor_vendor.text()}"
        if self.serial_monitor.text() != "":
            cmd += f" -s {self.serial_monitor.text()}"
        if self.dpi_monitor.value():
            cmd += f" -d {self.dpi_monitor.value()}"
        if self.xres.value():
            cmd += f" -x {self.xres.value()}"
        if self.yres.value():
            cmd += f" -y {self.yres.value()}"
        if self.btn_max_xres.isChecked() and self.max_xres.value():
            cmd += f" -X {self.max_xres.value()}"
        if self.btn_max_yres.isChecked() and self.max_yres.value():
            cmd += f" -Y {self.max_yres.value()}"
        if self.name_monitor.text() != "":
            cmd += f" -n {self.name_monitor.text()}"
        return cmd

    def closeEvent(self, event):
        try:
            self.closed_signal.emit()
        except Exception:
            pass
        super().closeEvent(event)

    def btn_build_clicked(self):
        if not (self.check_avilable_config() and self.check_avilable_vendor()):
            return
        cmd = self.option_config()
        log = Logger()
        def edid_process(proc):
            try:
                for line in proc.stdout:
                    if line:
                        log.log(f"[EDID] {line.strip()}")
                proc.wait()
                log.log(f"edid đã thoát với mã {proc.returncode}")
            except Exception as e:
                log.error(f"Lỗi giám sát tiến trình: {e}")
        try:
            log.log(f"build edid {self.name_output_file.text()} ({datetime.now().strftime('%Y/%m/%d %H-%M-%S')})")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", text=True, errors="replace", creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            t = Thread(target=edid_process, args=(proc,), daemon=True)
            t.start()
            log.log(f"build edid {self.name_output_file.text()} thành công ({datetime.now().strftime('%Y/%m/%d %H-%M-%S')})")
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "warning", f"đã xảy ra lỗi: {e}")


class QG(QTabWidget):
    moc_reoption_signal = pyqtSignal(str)

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
                min-width: 190px;
                min-height: 32px;
                margin-right: 4px;
                padding: 8px 24px;
                font-size: 16px;
                outline: None;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
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

        self.none_Watchdog = False  # khởi tạo trước khi dùng
        self.WDD = QComboBox()
        self.Checkbox_enable_watchdog_device = QCheckBox()
        self.Checkbox_enable_watchdog_device.setChecked(False)
        self.Checkbox_enable_watchdog_device.setText("bật watchdog device")
        layout_vm.addWidget(QLabel("Watchdog:"), 9, 0)
        layout_vm.addWidget(self.WDD, 9, 1)
        layout_vm.addWidget(self.Checkbox_enable_watchdog_device, 9, 2)
        self.K.currentIndexChanged.connect(self.update_watchdog_list)
        self.AQEW.toggled.connect(self.update_watchdog_list)
        self.Checkbox_enable_watchdog_device.toggled.connect(self.update_watchdog)
        self.WDD.currentIndexChanged.connect(self.update_watcdog_action)
        

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
        self.check_disk_available()

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

        #Feature 15: -nographics
        NGG = QGroupBox("nographics")
        layout_NGG = QGridLayout(NGG)
        self.CB_NGG = QCheckBox("Bật nographics (chạy QEMU mà không cần giao diện đồ họa, chỉ dùng terminal)")
        self.CB_NGG.setChecked(False)
        layout_NGG.addWidget(self.CB_NGG)
        adco_layout.addWidget(NGG)
        
        #Feature 16: display options
        display_group = QGroupBox("tùy chọn display")
        self.display_layout = QGridLayout(display_group)
        self.CB_Display = QCheckBox("Bật tùy chọn display")
        self.CB_Display.setChecked(False)
        self.display_layout.addWidget(self.CB_Display, 0, 0)
        self.Mode_of_display = QComboBox()
        self.Mode_of_display.addItems(["sdl", "gtk", "spice-app", "curses", "egl-headless", "dbus", "none"])
        self.Mode_of_display.setEnabled(False)
        self.CB_Display.toggled.connect(self.update_display_options_ui)
        self.display_layout.addWidget(QLabel("Mode of display:"), 1, 0)
        self.display_layout.addWidget(self.Mode_of_display, 1, 1)
        self.update_option_diplay() # Initialize display options UI
        self.CB_Display.toggled.connect(self.update_option_diplay)
        self.Mode_of_display.currentTextChanged.connect(self.update_option_diplay)
        self.update_UI_display_options()
        self.CB_Display.toggled.connect(self.update_UI_display_options)
        self.Mode_of_display.currentTextChanged.connect(self.update_UI_display_options)
        adco_layout.addWidget(display_group)

        #Feature 17: spice
        spice_display_group = QGroupBox("tùy chọn spice")
        self.spice_layout = QGridLayout(spice_display_group)
        self.CB_Spice = QCheckBox("bật/tắt tùy chọn spice")
        self.CB_Spice.setChecked(False)
        self.spice_layout.addWidget(self.CB_Spice, 0 ,0)
        self.Mode_of_spice = QComboBox()
        self.Mode_of_spice.addItems(["cơ bản", "nâng cao"])
        self.Mode_of_spice.setEnabled(False)
        self.spice_layout.addWidget(self.Mode_of_spice)
        self.layout_option_spice = QVBoxLayout()
        adco_layout.addWidget(spice_display_group)
        self.update_option_display_spice()
        self.CB_Spice.toggled.connect(self.update_option_display_spice)
        self.Mode_of_spice.currentIndexChanged.connect(self.update_option_display_spice)
        self.Mode_of_spice.currentIndexChanged.connect(self.update_CB_Spice)
        self.CB_Spice.toggled.connect(self.update_Mode_of_spice_UI)
        self.CB_Spice.toggled.connect(self.update_CB_Spice)
        adco_layout.addWidget(spice_display_group)

        #i38 advanced options

        i386_advanced_optons_group = QGroupBox("i386 advanced options")
        self.i386_advanced_options_layout = QGridLayout(i386_advanced_optons_group)
        self.i386_advanced_options_layout.addWidget(QLabel("tùy chọn đặc biệt của i386:"))
        self.win2k_hack = QCheckBox("bật win2k-hack")
        self.i386_advanced_options_layout.addWidget(QLabel("win2k_hack"))
        self.i386_advanced_options_layout.addWidget(self.win2k_hack)
        self.no_fd_bootcheck = QCheckBox("bật no-fd-bootcheck")
        self.i386_advanced_options_layout.addWidget(QLabel("no-fd-bootcheck"))
        self.i386_advanced_options_layout.addWidget(self.no_fd_bootcheck)
        self.K.currentIndexChanged.connect(self.update_i386_advanced_optons)
        self.update_i386_advanced_optons()

        adco_layout.addWidget(i386_advanced_optons_group)

        #keyboard layout

        keyboard_layout_group = QGroupBox("keyboard layout")
        self.kll = QGridLayout(keyboard_layout_group)
        self.kll.addWidget(QLabel("keyboard layout option"))
        self.keyboardlayoutcheckbox = QCheckBox()
        self.keyboardlayoutcheckbox.setText("bật keyboard layout")
        self.keyboardlayoutlineedit = QLineEdit()
        self.keyboardlayoutlineedit.setPlaceholderText("VD: en, fr, vn,...")
        self.keyboardlayoutlineedit.setEnabled(False)
        self.keyboardlayoutcheckbox.toggled.connect(lambda: self.keyboardlayoutlineedit.setEnabled(self.keyboardlayoutcheckbox.isChecked()))
        self.kll.addWidget(self.keyboardlayoutcheckbox)
        self.kll.addWidget(self.keyboardlayoutlineedit)
        adco_layout.addWidget(keyboard_layout_group)

        #edid
        edid_vga = QGroupBox("Extended Display Identification Data vga")
        self.ev = QGridLayout(edid_vga)
        self.enable_edid = QCheckBox("bật edid vga")
        self.enable_edid.toggled.connect(self.edid_path)
        self.enable_edid_path = QCheckBox()
        self.enable_edid_path.setText("chọn đường dẫn edid")
        self.enable_edid_path.clicked.connect(self.edid_path)
        self.ev.addWidget(self.enable_edid, 0, 0)
        self.ev.addWidget(self.enable_edid_path, 0, 1)
        self.xres = QSpinBox()
        self.xres.setRange(5, 5120)
        self.xres.setValue(1920)
        self.xres.setSuffix("px")
        self.xres.setEnabled(False)
        self.ev.addWidget(QLabel("chiều rộng màng hình"))
        self.ev.addWidget(self.xres)
        self.yres = QSpinBox()
        self.yres.setRange(10, 2160)
        self.yres.setValue(1080)
        self.yres.setSuffix("px")
        self.yres.setEnabled(False)
        self.ev.addWidget(QLabel("chiều cao màng hình"))
        self.ev.addWidget(self.yres)
        self.max_xres = QSpinBox()
        self.max_xres.setRange(5, 5120)
        self.max_xres.setValue(1920)
        self.max_xres.setSuffix("px")
        self.max_xres.setEnabled(False)
        self.btn_max_xres = QCheckBox()
        self.btn_max_xres.setText("bật giới hạn chiều rộng tối đa")
        self.btn_max_xres.clicked.connect(lambda : self.max_xres.setEnabled(self.btn_max_xres.isChecked()))
        self.btn_max_xres.setEnabled(False)
        self.ev.addWidget(self.btn_max_xres)
        self.ev.addWidget(self.max_xres)
        self.max_yres = QSpinBox()
        self.max_yres.setRange(10, 2160)
        self.max_yres.setValue(1080)
        self.max_yres.setSuffix("px")
        self.max_yres.setEnabled(False)
        self.btn_max_yres = QCheckBox()
        self.btn_max_yres.setText("bật giới hạn chiều cao tối đa")
        self.btn_max_yres.clicked.connect(lambda : self.max_yres.setEnabled(self.btn_max_yres.isChecked()))
        self.btn_max_yres.setEnabled(False)
        self.ev.addWidget(self.btn_max_yres)
        self.ev.addWidget(self.max_yres)
        self.refresh_hz = QSpinBox()
        self.refresh_hz.setRange(10, 590)
        self.refresh_hz.setValue(60)
        self.refresh_hz.setSuffix("hz")
        self.refresh_hz.setEnabled(False)
        self.ev.addWidget(QLabel("tần số hz"))
        self.ev.addWidget(self.refresh_hz)
        self.srceen_raw_width = QSpinBox()
        self.srceen_raw_width.setRange(10, 813)
        self.srceen_raw_width.setValue(530)
        self.srceen_raw_width.setSuffix("mm")
        self.srceen_raw_width.setEnabled(False)
        self.btn_srceen_raw_width = QCheckBox("bật giới hạn chiều dài vật lý của màng hình ảo")
        self.btn_srceen_raw_width.clicked.connect(lambda : self.srceen_raw_width.setEnabled(self.btn_srceen_raw_width.isChecked()))
        self.btn_srceen_raw_width.setEnabled(False)
        self.ev.addWidget(self.btn_srceen_raw_width)
        self.ev.addWidget(self.srceen_raw_width)
        self.srceen_raw_height = QSpinBox()
        self.srceen_raw_height.setRange(5, 516)
        self.srceen_raw_height.setValue(320)
        self.srceen_raw_height.setSuffix("mm")
        self.srceen_raw_height.setEnabled(False)
        self.btn_srceen_raw_height = QCheckBox()
        self.btn_srceen_raw_height.setText("bật giới hạn chiều cao vật lý của màng hình ảo")
        self.btn_srceen_raw_height.clicked.connect(lambda : self.srceen_raw_height.setEnabled(self.btn_srceen_raw_height.isChecked()))
        self.btn_srceen_raw_height.setEnabled(False)
        self.ev.addWidget(self.btn_srceen_raw_height)
        self.ev.addWidget(self.srceen_raw_height)
        vboxlayout_edid1 = QVBoxLayout()
        self.btn_edid_path = QPushButton("chọn đường dẫn file edid")
        self.lineedit_edid_path = QLineEdit()
        self.lineedit_edid_path.setEnabled(False)
        self.lineedit_edid_path.setPlaceholderText("địa chỉ file edid (.bin)")
        self.btn_edid_path.setEnabled(False)
        self.btn_edid_path.clicked.connect(self.set_path_edid)
        vboxlayout_edid1.addWidget(self.btn_edid_path)
        vboxlayout_edid1.addWidget(self.lineedit_edid_path)
        self.ev.addLayout(vboxlayout_edid1, 16, 0)
        adco_layout.addWidget(edid_vga)

        adco_scroll.setWidget(adco_content)
        self.adco_scroll = adco_scroll
        self.addTab(adco_scroll, "Cấu hình nâng cao")

        # multi options call

        self.moc_scroll = QScrollArea()
        self.moc_scroll.setWidgetResizable(True)
        self.moc_content = QWidget()
        moc_layout = QVBoxLayout(self.moc_content)
        group_moc = QGroupBox("multi option call / gọi nhiều tùy chọn")
        layout_moc = QGridLayout(group_moc)
        self.moc_list = QListWidget()
        layout_moc.addWidget(self.moc_list, 0, 0, 4, 2)
        self.btn_moc_create_option = QPushButton("tạo option")
        self.btn_moc_reoption = QPushButton("thay đổi thông số option")
        self.btn_moc_delete_option = QPushButton("xóa option")
        layout_moc.addWidget(self.btn_moc_create_option, 0, 2)
        layout_moc.addWidget(self.btn_moc_reoption, 1, 2)
        layout_moc.addWidget(self.btn_moc_delete_option, 2, 2)
        moc_layout.addWidget(group_moc)
        self.moc_scroll.setWidget(self.moc_content)
        self.addTab(self.moc_scroll, "Multi Options Call")
        self.btn_moc_create_option.clicked.connect(self.open_moc_dialog)
        self.btn_moc_reoption.clicked.connect(self.on_btn_moc_reoption_clicked)
        self.btn_moc_delete_option.clicked.connect(self.delete_moc_option)
        self.moc_list.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.moc_list.itemChanged.connect(self.rename_moc_option)

        # edid menu
        self.em_menu = QScrollArea()
        self.em_menu.setWidgetResizable(True)
        self.em_content = QWidget()
        em_layout = QVBoxLayout(self.em_content)
        group_em = QGroupBox("Edid / Cấu hình Display")
        layout_em = QGridLayout(group_em)
        self.Hlayout_em1 = QVBoxLayout()
        Hlayout_em2 = QVBoxLayout()
        self.em_comboBox = QComboBox()
        self.Hlayout_em1.addWidget(self.em_comboBox)
        self.Vlayout_info = QVBoxLayout()
        self.Hlayout_em1.addLayout(self.Vlayout_info)
        self.em_create_btn = QPushButton("Tạo file edid")
        self.em_import_btn = QPushButton("import file edid")
        self.em_delete_btn = QPushButton("xóa file edid")
        self.em_create_btn.clicked.connect(self.open_edid_dialog)
        self.em_delete_btn.clicked.connect(self.delete_edid)
        Hlayout_em2.addWidget(self.em_create_btn)
        Hlayout_em2.addWidget(self.em_import_btn)
        Hlayout_em2.addWidget(self.em_delete_btn)
        layout_em.addLayout(self.Hlayout_em1, 0, 0, Qt.AlignmentFlag.AlignTop)
        layout_em.addLayout(Hlayout_em2, 0, 1, Qt.AlignmentFlag.AlignTop)
        em_layout.addWidget(group_em)
        self.em_menu.setWidget(self.em_content)
        self.addTab(self.em_menu, "Cấu hình EDID")

        #network advanced
        self.netad_scroll = QScrollArea()
        self.netad_scroll.setWidgetResizable(True)
        self.netad_content = QWidget()
        netad_layout = QVBoxLayout(self.netad_content)
        netad_group = QGroupBox("cấu hình network nâng cao")
        layout_netad = QGridLayout(netad_group)
        self.enable_netad = QCheckBox("bật network advanced")
        layout_netad.addWidget(self.enable_netad)
        self.frame_netad = QFrame()
        self.frame_netad.setEnabled(False)
        self.enable_netad.toggled.connect(lambda: self.frame_netad.setEnabled(self.enable_netad.isChecked()))
        self.netad_mode = QComboBox()
        self.netad_mode.addItems(["user"])
        layout_netad.addWidget(self.netad_mode)
        layout_netad.addWidget(self.frame_netad)
        self.Vlayout1 = QVBoxLayout(self.frame_netad)
        self.frame_netad.setEnabled(False)
        self.enable_netad.toggled.connect(lambda: self.frame_netad.setEnabled(self.enable_netad.isChecked()))
        self.netad_mode.currentTextChanged.connect(self.netad_update)
        self.netad_update()
        netad_layout.addWidget(netad_group)
        self.netad_scroll.setWidget(self.netad_content)
        self.addTab(self.netad_scroll, "network advanced")

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
        qtime_Check_disk = QTimer()
        qtime_Check_disk.setSingleShot(True)
        qtime_Check_disk.setInterval(100)
        qtime_Check_disk.timeout.connect(self.check_disk_available)
        qtime_Check_disk.start()

    def clean_netad_widget(self):
        for i in reversed(range(self.Vlayout1.count())):
            self.Vlayout1.itemAt(i).widget().deleteLater()

    def netad_update(self):
        self.clean_netad_widget()
        if self.netad_mode.currentText() == "user":
            self.id_netad = QLineEdit()
            self.id_netad.setPlaceholderText("ID network")
            self.id_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.id_netad)
            self.ipv4_enable = QCheckBox("IPV4 (optional)")
            self.ipv4_enable.toggled.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.ipv4_enable)
            self.net_addr_netad = QLineEdit()
            self.net_addr_netad.setPlaceholderText("địa chỉ net (optional)(VD: 192.168.1.0[/24])")
            self.net_addr_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.net_addr_netad)
            self.net_host_netad = QLineEdit()
            self.net_host_netad.setPlaceholderText("địa chỉ net host (optional)(VD: 192.168.1)")
            self.net_host_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.net_host_netad)
            self.ipv6_enable = QCheckBox("IPV6 (optional)")
            self.ipv6_enable.toggled.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.ipv6_enable)
            self.ipv6_addr_netad = QLineEdit()
            self.ipv6_addr_netad.setPlaceholderText("địa chỉ ipv6 (optional) (VD: fec0::/64)")
            self.ipv6_addr_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.ipv6_addr_netad)
            self.ipv6_host_netad = QLineEdit()
            self.ipv6_host_netad.setPlaceholderText("địa chỉ ipv6 host (optional) (VD: fec0::1)")
            self.ipv6_host_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.ipv6_host_netad)
            self.restrict_netad = QCheckBox("restrict (optional)")
            self.restrict_netad.toggled.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.restrict_netad)
            self.hostname_netad = QLineEdit()
            self.hostname_netad.setPlaceholderText("hostname (optional)")
            self.hostname_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.hostname_netad)
            self.dhcpstart_netad = QLineEdit()
            self.dhcpstart_netad.setPlaceholderText("dhcpstart (optional)(VD:10.0.2.15)")
            self.dhcpstart_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.dhcpstart_netad)
            self.dns_netad = QLineEdit()
            self.dns_netad.setPlaceholderText("địa chỉ dns server (optional)(VD: 10.0.2.3)")
            self.dns_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.dns_netad)
            self.ipv6_dns = QLineEdit()
            self.ipv6_dns.setPlaceholderText("địa chỉ dns server cho ipv6 (optional)(VD: fec0::3)")
            self.ipv6_dns.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.ipv6_dns)
            self.dnssearch_netad = QLineEdit()
            self.dnssearch_netad.setPlaceholderText("tìm kiếm domain (optional)")
            self.dnssearch_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.dnssearch_netad)
            self.domainname_netad = QLineEdit()
            self.domainname_netad.setPlaceholderText("tên domain (optional)")
            self.domainname_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.domainname_netad)
            self.tftp_netad = QLineEdit()
            self.tftp_netad.setPlaceholderText("tftp server (optional)")
            self.tftp_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.tftp_netad)
            self.tftpname_netad = QLineEdit()
            self.tftpname_netad.setPlaceholderText("tên tftp server (optional)")
            self.tftpname_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.tftpname_netad)
            self.bootfile_netad = QLineEdit()
            self.bootfile_netad.setPlaceholderText("tệp boot (optional)(VD: pxelinux.0)")
            self.bootfile_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.bootfile_netad)
            self.hostfwd_netad = QLineEdit()
            self.hostfwd_netad.setPlaceholderText("host forward rule (optional)")
            self.hostfwd_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.hostfwd_netad)
            self.guestfwd_netad = QLineEdit()
            self.guestfwd_netad.setPlaceholderText("guest forward rule (optional)")
            self.guestfwd_netad.textChanged.connect(self.save_snapshot_netad)
            self.Vlayout1.addWidget(self.guestfwd_netad)

    def set_path_edid(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Chọn file EDID", "", "EDID Files (*.bin);;All Files (*)")
        if filename:
            self.lineedit_edid_path.setText(filename)

    def config_netad(self):
        if self.netad_mode.currentText() == "user":
            return {"id_netad": self.id_netad.text() if self.id_netad.text() != "" else "N/A",
                    "ipv4_enable": self.ipv4_enable.isChecked(),
                    "net_host_netad": self.net_host_netad.text() if self.net_host_netad.text() != "" else "N/A",
                    "net_addr_netad": self.net_addr_netad.text() if self.net_addr_netad.text() != "" else "N/A",
                    "ipv6_enable": self.ipv6_enable.isChecked(),
                    "ipv6_addr_netad": self.ipv6_addr_netad.text() if self.ipv6_addr_netad.text() != "" else "N/A",
                    "ipv6_host_netad": self.ipv6_host_netad.text() if self.ipv6_host_netad.text() != "" else "N/A",
                    "restrict_netad": self.restrict_netad.isChecked(),
                    "hostname_netad": self.hostname_netad.text() if self.hostname_netad.text() != "" else "N/A",
                    "dns_netad": self.dns_netad.text() if self.dns_netad.text() != "" else "N/A",
                    "dnssearch_netad": self.dnssearch_netad.text() if self.dnssearch_netad.text() != "" else "N/A",
                    "domainname_netad": self.domainname_netad.text() if self.domainname_netad.text() != "" else "N/A",
                    "tftp_netad": self.tftp_netad.text() if self.tftp_netad.text() != "" else "N/A",
                    "tftpname_netad": self.tftpname_netad.text() if self.tftpname_netad.text() != "" else "N/A",
                    "bootfile_netad": self.bootfile_netad.text() if self.bootfile_netad.text() != "" else "N/A",
                    "hostfwd_netad": self.hostfwd_netad.text() if self.hostfwd_netad.text() != "" else "N/A",
                    "guestfwd_netad": self.guestfwd_netad.text() if self.guestfwd_netad.text() != "" else "N/A"}

    def save_snapshot_netad(self):
        if self.netad_mode.currentText() == "user":
            for i in ["id_netad", "ipv4_enable", "net_host_netad", "net_addr_netad", "ipv6_enable", "ipv6_addr_netad", "ipv6_host_netad", "restrict_netad", "hostname_netad", "dns_netad", "dnssearch_netad", "domainname_netad", "tftp_netad", "tftpname_netad", "bootfile_netad", "hostfwd_netad", "guestfwd_netad"]:
                if not hasattr(self, i):
                    QMessageBox.critical(self, "lỗi netad", f"""
                    gặp sự cố trong việc check attribute {i} của netad
                    gọi hàm netad_update để khởi tạo lại UI""")
                    self.netad_update()
                    return
            self.id_netad.textChanged.connect(self.save_snapshot)
            self.ipv4_enable.toggled.connect(self.save_snapshot)
            self.net_addr_netad.textChanged.connect(self.save_snapshot)
            self.net_host_netad.textChanged.connect(self.save_snapshot)
            self.ipv6_enable.toggled.connect(self.save_snapshot)
            self.ipv6_addr_netad.textChanged.connect(self.save_snapshot)
            self.ipv6_host_netad.textChanged.connect(self.save_snapshot)
            self.restrict_netad.toggled.connect(self.save_snapshot)
            self.hostname_netad.textChanged.connect(self.save_snapshot)
            self.dns_netad.textChanged.connect(self.save_snapshot)
            self.dnssearch_netad.textChanged.connect(self.save_snapshot)
            self.domainname_netad.textChanged.connect(self.save_snapshot)
            self.tftp_netad.textChanged.connect(self.save_snapshot)
            self.tftpname_netad.textChanged.connect(self.save_snapshot)
            self.bootfile_netad.textChanged.connect(self.save_snapshot)
            self.hostfwd_netad.textChanged.connect(self.save_snapshot)
            self.guestfwd_netad.textChanged.connect(self.save_snapshot)

    def load_snapshot_netad(self, cfg: dict[str, any] = {}):
        self.netad_mode.setCurrentText(cfg.get("netad_mode", ""))
        self.enable_netad.setChecked(cfg.get("enable_netad", False))
        # Nếu signal của netad_mode đang bị block (trong apply_config), cần gọi thủ công
        # để đảm bảo widget được tạo sẵn trước khi load data vào
        if self.netad_mode.signalsBlocked():
            self.netad_update()
        if self.netad_mode.currentText() == "user":

            for i in ["id_netad", "ipv4_enable", "net_host_netad", "net_addr_netad", "ipv6_enable", "ipv6_addr_netad", "ipv6_host_netad", "restrict_netad", "hostname_netad", "dns_netad", "dnssearch_netad", "domainname_netad", "tftp_netad", "tftpname_netad", "bootfile_netad", "hostfwd_netad", "guestfwd_netad"]:
                if not hasattr(self, i):
                    QMessageBox.critical(self, "lỗi netad", f"""
                    gặp sự cố trong việc check attribute {i} của netad
                    gọi hàm netad_update để khởi tạo lại UI""")
                    self.netad_update()
                    return
            data = cfg.get("netad", {})
            self.id_netad.setText(data.get("id_netad", "N/A") if data.get("id_netad", "N/A") != "N/A" else "")
            self.ipv4_enable.setChecked(data.get("ipv4_enable", False))
            self.net_host_netad.setText(data.get("net_host_netad", "N/A") if data.get("net_host_netad", "N/A") != "N/A" else "")
            self.net_addr_netad.setText(data.get("net_addr_netad", "N/A") if data.get("net_addr_netad", "N/A") != "N/A" else "")
            self.ipv6_enable.setChecked(data.get("ipv6_enable", False))
            self.ipv6_addr_netad.setText(data.get("ipv6_addr_netad", "N/A") if data.get("ipv6_addr_netad", "N/A") != "N/A" else "")
            self.ipv6_host_netad.setText(data.get("ipv6_host_netad", "N/A") if data.get("ipv6_host_netad", "N/A") != "N/A" else "")
            self.restrict_netad.setChecked(data.get("restrict_netad", False))
            self.hostname_netad.setText(data.get("hostname_netad", "N/A") if data.get("hostname_netad", "N/A") != "N/A" else "")
            self.dns_netad.setText(data.get("dns_netad", "N/A") if data.get("dns_netad", "N/A") != "N/A" else "")
            self.dnssearch_netad.setText(data.get("dnssearch_netad", "N/A") if data.get("dnssearch_netad", "N/A") != "N/A" else "")
            self.domainname_netad.setText(data.get("domainname_netad", "N/A") if data.get("domainname_netad", "N/A") != "N/A" else "")
            self.tftp_netad.setText(data.get("tftp_netad", "N/A") if data.get("tftp_netad", "N/A") != "N/A" else "")
            self.tftpname_netad.setText(data.get("tftpname_netad", "N/A") if data.get("tftpname_netad", "N/A") != "N/A" else "")
            self.bootfile_netad.setText(data.get("bootfile_netad", "N/A") if data.get("bootfile_netad", "N/A") != "N/A" else "")
            self.hostfwd_netad.setText(data.get("hostfwd_netad", "N/A") if data.get("hostfwd_netad", "N/A") != "N/A" else "")
            self.guestfwd_netad.setText(data.get("guestfwd_netad", "N/A") if data.get("guestfwd_netad", "N/A") != "N/A" else "")
                
    def edid_path(self):
        if self.enable_edid.isChecked() and self.enable_edid_path.isChecked():
            self.xres.setEnabled(not self.enable_edid_path.isChecked())
            self.yres.setEnabled(not self.enable_edid_path.isChecked())
            self.max_xres.setEnabled(not self.enable_edid_path.isChecked())
            self.max_yres.setEnabled(not self.enable_edid_path.isChecked())
            self.refresh_hz.setEnabled(not self.enable_edid_path.isChecked())
            self.srceen_raw_width.setEnabled(not self.enable_edid_path.isChecked())
            self.srceen_raw_height.setEnabled(not self.enable_edid_path.isChecked())
            self.btn_srceen_raw_height.setEnabled(not self.enable_edid_path.isChecked())
            self.btn_srceen_raw_width.setEnabled(not self.enable_edid_path.isChecked())
            self.btn_max_xres.setEnabled(not self.enable_edid_path.isChecked())
            self.btn_max_yres.setEnabled(not self.enable_edid_path.isChecked())
            self.btn_edid_path.setEnabled(True)
            self.lineedit_edid_path.setEnabled(True)
            self.enable_edid_path.setEnabled(self.enable_edid.isChecked())
        elif self.enable_edid.isChecked():
            self.xres.setEnabled(self.enable_edid.isChecked())
            self.yres.setEnabled(self.enable_edid.isChecked())
            self.max_xres.setEnabled(self.enable_edid.isChecked())
            self.max_yres.setEnabled(self.enable_edid.isChecked())
            self.refresh_hz.setEnabled(self.enable_edid.isChecked())
            self.srceen_raw_width.setEnabled(self.enable_edid.isChecked())
            self.srceen_raw_height.setEnabled(self.enable_edid.isChecked())
            self.btn_srceen_raw_height.setEnabled(self.enable_edid.isChecked())
            self.btn_srceen_raw_width.setEnabled(self.enable_edid.isChecked())
            self.btn_max_xres.setEnabled(self.enable_edid.isChecked())
            self.btn_max_yres.setEnabled(self.enable_edid.isChecked())
            self.btn_edid_path.setEnabled(False)
            self.lineedit_edid_path.setEnabled(False)
            self.enable_edid_path.setEnabled(True)
        else:
            self.xres.setEnabled(self.enable_edid_path.isChecked())
            self.yres.setEnabled(self.enable_edid_path.isChecked())
            self.max_xres.setEnabled(self.enable_edid_path.isChecked())
            self.max_yres.setEnabled(self.enable_edid_path.isChecked())
            self.refresh_hz.setEnabled(self.enable_edid_path.isChecked())
            self.srceen_raw_width.setEnabled(self.enable_edid_path.isChecked())
            self.srceen_raw_height.setEnabled(self.enable_edid_path.isChecked())
            self.btn_srceen_raw_height.setEnabled(self.enable_edid_path.isChecked())
            self.btn_srceen_raw_width.setEnabled(self.enable_edid_path.isChecked())
            self.btn_max_xres.setEnabled(self.enable_edid_path.isChecked())
            self.btn_max_yres.setEnabled(self.enable_edid_path.isChecked())
            self.btn_edid_path.setEnabled(False)
            self.lineedit_edid_path.setEnabled(False)
            self.enable_edid_path.setEnabled(False)

    def update_i386_advanced_optons(self):
        if self.K.currentText() == "i386":
            self.win2k_hack.setEnabled(True)
            self.no_fd_bootcheck.setEnabled(True)
        else:
            self.win2k_hack.setEnabled(False)
            self.no_fd_bootcheck.setEnabled(False)

    def update_readconfig_ui(self):
        checked = self.CB_RC.isChecked()
        self.path_rc.setEnabled(checked)

    def update_Mode_of_spice_UI(self):
        self.Mode_of_spice.setEnabled(self.CB_Spice.isChecked())

    def update_watcdog_action(self):
        self.none_Watchdog = False
        if self.WDD.currentText() == "none" or not self.WDD.isEnabled():
            self.WAC.setEnabled(False)
            self.none_Watchdog = True
        else:
            self.WAC.setEnabled(True)

    def update_watchdog(self):
        check = self.Checkbox_enable_watchdog_device.isChecked()
        self.WDD.setEnabled(check)
        self.WAC.setEnabled(check)
        self.update_watcdog_action()

    def update_display_options_ui(self):
        checked = self.CB_Display.isChecked()
        self.Mode_of_display.setEnabled(checked)

    def update_UI_spice_options(self):
        enabled = self.CB_Spice.isChecked()
        if not enabled:
            self.clean_layout_option_spice()
        if enabled:
            if self.Mode_of_spice.currentText() == "cơ bản":
                self.CB_option1_port_spice.setEnabled(True)
                self.CB_option2_tls_port_spice.setEnabled(True)
                self.option3_ipv4_spice.setEnabled(True)
                self.option4_ipv6_spice.setEnabled(True)
                self.option5_disable_ticketing_spice.setEnabled(True)
                self.CB_option6_secret_password_spice.setEnabled(True)
                self.option7_disable_copy_paste_spice.setEnabled(True)
                self.option8_agent_mouse_spice.setEnabled(True)

    def update_port_spice(self):
        self.option1_port_spice.setEnabled(self.CB_option1_port_spice.isChecked())
    
    def update_tls_port_spice(self):
        self.option2_tls_port_spice.setEnabled(self.CB_option2_tls_port_spice.isChecked())

    def update_secret_password_spice(self):
        self.option6_secret_password_spice.setEnabled(self.CB_option6_secret_password_spice.isChecked())    

    def update_option_display_spice(self):
        if hasattr(self, 'layout_option_spice') and self.layout_option_spice is not None:
            self.clean_layout_option_spice()
            try:
                for i in range(self.spice_layout.count()):
                    item = self.spice_layout.itemAt(i)
                    if item and item.layout() is self.layout_option_spice:
                        self.spice_layout.removeItem(item)
                        break
            except:
                pass
        self.option1_layout_spice_basic = QHBoxLayout()
        self.option1_port_spice = QLineEdit()
        self.option1_port_spice.setPlaceholderText("VD: 5900")
        self.option1_port_spice.setEnabled(False)
        self.CB_option1_port_spice = QCheckBox("Bật port")
        self.CB_option1_port_spice.setChecked(False)
        self.CB_option1_port_spice.setEnabled(False) #UI
        self.CB_option1_port_spice.toggled.connect(self.update_port_spice)
        self.option1_layout_spice_basic.addWidget(QLabel("Port:"))
        self.option1_layout_spice_basic.addWidget(self.option1_port_spice)
        self.option1_layout_spice_basic.addWidget(self.CB_option1_port_spice)
        self.option2_layout_spice_basic = QHBoxLayout()
        self.option2_tls_port_spice = QLineEdit()
        self.option2_tls_port_spice.setPlaceholderText("VD: 5901")
        self.option2_tls_port_spice.setEnabled(False)
        self.CB_option2_tls_port_spice = QCheckBox("Bật TLS port")
        self.CB_option2_tls_port_spice.setChecked(False)
        self.CB_option2_tls_port_spice.setEnabled(False) #UI
        self.CB_option2_tls_port_spice.toggled.connect(self.update_tls_port_spice)
        self.option2_layout_spice_basic.addWidget(QLabel("TLS Port:"))
        self.option2_layout_spice_basic.addWidget(self.option2_tls_port_spice)
        self.option2_layout_spice_basic.addWidget(self.CB_option2_tls_port_spice)
        self.option3_layout_spice_basic = QHBoxLayout()
        self.option3_ipv4_spice = QCheckBox("cho phép kết nối IPv4")
        self.option3_ipv4_spice.setChecked(False)
        self.option3_ipv4_spice.setEnabled(False) #UI
        self.option3_layout_spice_basic.addWidget(self.option3_ipv4_spice)
        self.option4_layout_spice_basic = QHBoxLayout()
        self.option4_ipv6_spice = QCheckBox("cho phép kết nối IPv6")
        self.option4_ipv6_spice.setChecked(False)
        self.option4_ipv6_spice.setEnabled(False) #UI
        self.option4_layout_spice_basic.addWidget(self.option4_ipv6_spice)
        self.option5_layout_spice_basic = QHBoxLayout()
        self.option5_disable_ticketing_spice = QCheckBox("vô hiệu hóa ticketing")
        self.option5_disable_ticketing_spice.setChecked(False)
        self.option5_disable_ticketing_spice.setEnabled(False) #UI
        self.option5_layout_spice_basic.addWidget(self.option5_disable_ticketing_spice)
        self.option6_layout_spice_basic = QHBoxLayout()
        self.option6_secret_password_spice = QLineEdit()
        self.option6_secret_password_spice.setPlaceholderText("Đặt mật khẩu cho kết nối spice")
        self.option6_secret_password_spice.setEnabled(False)
        self.CB_option6_secret_password_spice = QCheckBox("Bật mật khẩu")
        self.CB_option6_secret_password_spice.setChecked(False)
        self.CB_option6_secret_password_spice.setEnabled(False) #UI
        self.CB_option6_secret_password_spice.toggled.connect(self.update_secret_password_spice)
        self.option6_layout_spice_basic.addWidget(self.CB_option6_secret_password_spice)
        self.option6_layout_spice_basic.addWidget(self.option6_secret_password_spice)
        self.option7_layout_spice_basic = QHBoxLayout()
        self.option7_disable_copy_paste_spice = QCheckBox("vô hiệu hóa copy-paste")
        self.option7_disable_copy_paste_spice.setChecked(False)
        self.option7_disable_copy_paste_spice.setEnabled(False) #UI
        self.option7_layout_spice_basic.addWidget(self.option7_disable_copy_paste_spice)
        self.option8_layout_spice_basic = QHBoxLayout()
        self.option8_agent_mouse_spice = QCheckBox("bật agent mouse")
        self.option8_agent_mouse_spice.setChecked(False)
        self.option8_agent_mouse_spice.setEnabled(False) #UI
        self.option8_layout_spice_basic.addWidget(self.option8_agent_mouse_spice)
        if self.Mode_of_spice.currentText() == "cơ bản":
            self.clean_layout_option_spice()
            self.layout_option_spice_basic = QVBoxLayout()
            self.layout_option_spice_basic.addLayout(self.option1_layout_spice_basic)
            self.layout_option_spice_basic.addLayout(self.option2_layout_spice_basic)
            self.layout_option_spice_basic.addLayout(self.option3_layout_spice_basic)
            self.layout_option_spice_basic.addLayout(self.option4_layout_spice_basic)
            self.layout_option_spice_basic.addLayout(self.option5_layout_spice_basic)
            self.layout_option_spice_basic.addLayout(self.option6_layout_spice_basic)
            self.layout_option_spice_basic.addLayout(self.option7_layout_spice_basic)
            self.layout_option_spice_basic.addLayout(self.option8_layout_spice_basic)
            self.spice_layout.addLayout(self.layout_option_spice_basic, 2, 0, 1, 2)
        if self.Mode_of_spice.currentText() == "nâng cao":
            self.clean_layout_option_spice()
            self.layout_option_spice_advanced = QVBoxLayout()
            self.layout_option_spice_advanced.addLayout(self.option1_layout_spice_basic)
            self.layout_option_spice_advanced.addLayout(self.option2_layout_spice_basic)
            self.layout_option_spice_advanced.addLayout(self.option3_layout_spice_basic)
            self.layout_option_spice_advanced.addLayout(self.option4_layout_spice_basic)
            self.layout_option_spice_advanced.addLayout(self.option5_layout_spice_basic)
            self.layout_option_spice_advanced.addLayout(self.option6_layout_spice_basic)
            self.layout_option_spice_advanced.addLayout(self.option7_layout_spice_basic)
            self.layout_option_spice_advanced.addLayout(self.option8_layout_spice_basic)
            self.layout_option1_spice_advanced = QHBoxLayout()
            self.option1_x509_dir = QLineEdit()
            self.option1_x509_dir.setPlaceholderText("Đường dẫn thư mục chứa chứng chỉ x509")
            self.option1_x509_dir.setEnabled(False)
            self.CB_option1_x509_dir = QCheckBox("Bật chứng chỉ x509")
            self.CB_option1_x509_dir.setChecked(False)
            self.CB_option1_x509_dir.setEnabled(False) #UIX
            self.CB_option1_x509_dir.toggled.connect(self.update_x509_dir)
            self.layout_option1_spice_advanced.addWidget(QLabel("Thư mục x509:"))
            self.layout_option1_spice_advanced.addWidget(self.option1_x509_dir)
            self.layout_option1_spice_advanced.addWidget(self.CB_option1_x509_dir)
            self.layout_option_spice_advanced.addLayout(self.layout_option1_spice_advanced)
            self.layout_option2_spice_advanced = QHBoxLayout()
            self.option2_x509_key_file = QLineEdit()
            self.option2_x509_key_file.setPlaceholderText("Đường dẫn file khóa riêng x509")
            self.option2_x509_key_file.setEnabled(False)
            self.CB_option2_x509_key_file = QCheckBox("Bật khóa riêng x509")
            self.CB_option2_x509_key_file.setChecked(False)
            self.CB_option2_x509_key_file.setEnabled(False) #UIX
            self.CB_option2_x509_key_file.toggled.connect(self.update_x509_key_file)
            self.layout_option2_spice_advanced.addWidget(QLabel("Khóa riêng x509:"))
            self.layout_option2_spice_advanced.addWidget(self.option2_x509_key_file)
            self.layout_option2_spice_advanced.addWidget(self.CB_option2_x509_key_file)
            self.layout_option_spice_advanced.addLayout(self.layout_option2_spice_advanced)
            self.layout_option3_spice_advanced = QHBoxLayout()
            self.option3_x509_key_password = QLineEdit()
            self.option3_x509_key_password.setPlaceholderText("Mật khẩu khóa riêng x509")
            self.option3_x509_key_password.setEnabled(False)
            self.CB_option3_x509_key_password = QCheckBox("Bật mật khẩu khóa riêng x509")
            self.CB_option3_x509_key_password.setChecked(False)
            self.CB_option3_x509_key_password.setEnabled(False) #UIX
            self.CB_option3_x509_key_password.toggled.connect(self.update_x509_key_password)
            self.layout_option3_spice_advanced.addWidget(QLabel("Mật khẩu khóa riêng x509:"))
            self.layout_option3_spice_advanced.addWidget(self.option3_x509_key_password)
            self.layout_option3_spice_advanced.addWidget(self.CB_option3_x509_key_password)
            self.layout_option_spice_advanced.addLayout(self.layout_option3_spice_advanced)
            self.layout_option4_spice_advanced = QHBoxLayout()
            self.option4_x509_cert_file = QLineEdit()
            self.option4_x509_cert_file.setPlaceholderText("Đường dẫn file chứng chỉ x509")
            self.option4_x509_cert_file.setEnabled(False)
            self.CB_option4_x509_cert_file = QCheckBox("Bật chứng chỉ x509")
            self.CB_option4_x509_cert_file.setChecked(False)
            self.CB_option4_x509_cert_file.setEnabled(False) #UIX
            self.CB_option4_x509_cert_file.toggled.connect(self.update_x509_cert_file)
            self.layout_option4_spice_advanced.addWidget(QLabel("Chứng chỉ x509:"))
            self.layout_option4_spice_advanced.addWidget(self.option4_x509_cert_file)
            self.layout_option4_spice_advanced.addWidget(self.CB_option4_x509_cert_file)
            self.layout_option_spice_advanced.addLayout(self.layout_option4_spice_advanced)
            self.layout_option5_spice_advanced = QHBoxLayout()
            self.option6_x509_cacert_file = QLineEdit()
            self.option6_x509_cacert_file.setPlaceholderText("Đường dẫn file chứng chỉ CA x509")
            self.option6_x509_cacert_file.setEnabled(False)
            self.CB_option6_x509_cacert_file = QCheckBox("Bật chứng chỉ CA x509")
            self.CB_option6_x509_cacert_file.setChecked(False)
            self.CB_option6_x509_cacert_file.setEnabled(False) #UIX
            self.CB_option6_x509_cacert_file.toggled.connect(self.update_x509_cacert_file)
            self.layout_option5_spice_advanced.addWidget(QLabel("Chứng chỉ CA x509:"))
            self.layout_option5_spice_advanced.addWidget(self.option6_x509_cacert_file)
            self.layout_option5_spice_advanced.addWidget(self.CB_option6_x509_cacert_file)
            self.layout_option_spice_advanced.addLayout(self.layout_option5_spice_advanced)
            self.layout_option6_spice_advanced = QHBoxLayout()
            self.option6_addr_spice = QLineEdit()
            self.option6_addr_spice.setPlaceholderText("Địa chỉ bind của spice (VD: 127.0.0.1:5900)")
            self.option6_addr_spice.setEnabled(False)
            self.CB_option6_addr_spice = QCheckBox("Bật địa chỉ bind của spice")
            self.CB_option6_addr_spice.setChecked(False)
            self.CB_option6_addr_spice.setEnabled(False) #UIX
            self.CB_option6_addr_spice.toggled.connect(self.update_addr_spice)
            self.layout_option6_spice_advanced.addWidget(QLabel("Địa chỉ bind của spice:"))
            self.layout_option6_spice_advanced.addWidget(self.option6_addr_spice)
            self.layout_option6_spice_advanced.addWidget(self.CB_option6_addr_spice)
            self.layout_option_spice_advanced.addLayout(self.layout_option6_spice_advanced)
            self.layout_option7_spice_advanced = QHBoxLayout()
            self.option7_x509_dh_key_file = QLineEdit()
            self.option7_x509_dh_key_file.setPlaceholderText("Đường dẫn file khóa Diffie-Hellman")
            self.option7_x509_dh_key_file.setEnabled(False)
            self.CB_option7_x509_dh_key_file = QCheckBox("Bật khóa Diffie-Hellman")
            self.CB_option7_x509_dh_key_file.setChecked(False)
            self.CB_option7_x509_dh_key_file.setEnabled(False) #UI
            self.CB_option7_x509_dh_key_file.toggled.connect(self.update_x509_dh_key_file)
            self.layout_option7_spice_advanced.addWidget(QLabel("Khóa Diffie-Hellman:"))
            self.layout_option7_spice_advanced.addWidget(self.option7_x509_dh_key_file)
            self.layout_option7_spice_advanced.addWidget(self.CB_option7_x509_dh_key_file)
            self.layout_option_spice_advanced.addLayout(self.layout_option7_spice_advanced)
            self.layout_option7_spice_advanced = QHBoxLayout()
            self.option7_unix = QCheckBox("Bật Unix")
            self.option7_unix.setChecked(False)
            self.option7_unix.setEnabled(False) #UI
            self.layout_option7_spice_advanced.addWidget(self.option7_unix)
            self.layout_option_spice_advanced.addLayout(self.layout_option7_spice_advanced)
            self.layout_option8_spice_advanced = QHBoxLayout()
            self.option8_tls_cipher = QLineEdit()
            self.option8_tls_cipher.setPlaceholderText("Ciphers TLS tùy chỉnh (VD: HIGH:!aNULL:!MD5)")
            self.option8_tls_cipher.setEnabled(False)
            self.option8_CB_tls_cipher = QCheckBox("Bật ciphers TLS tùy chỉnh")
            self.option8_CB_tls_cipher.setChecked(False)
            self.option8_CB_tls_cipher.setEnabled(False) #UI
            self.option8_CB_tls_cipher.toggled.connect(self.update_tls_cipher)
            self.layout_option8_spice_advanced.addWidget(QLabel("Ciphers TLS:"))
            self.layout_option8_spice_advanced.addWidget(self.option8_tls_cipher)
            self.layout_option8_spice_advanced.addWidget(self.option8_CB_tls_cipher)
            self.layout_option_spice_advanced.addLayout(self.layout_option8_spice_advanced)
            self.layout_option9_spice_advanced = QHBoxLayout()
            self.option9_tls_channel = QComboBox()
            self.option9_tls_channel.addItems(["main", "display","cursor", "input", "playback", "record"])
            self.CB_option9_tls_channel = QCheckBox("Bật kênh TLS tùy chỉnh")
            self.CB_option9_tls_channel.setChecked(False)
            self.CB_option9_tls_channel.setEnabled(False) #UI
            self.CB_option9_tls_channel.toggled.connect(self.update_tls_channel)
            self.layout_option9_spice_advanced.addWidget(QLabel("Kênh TLS:"))
            self.layout_option9_spice_advanced.addWidget(self.option9_tls_channel)
            self.layout_option9_spice_advanced.addWidget(self.CB_option9_tls_channel)
            self.layout_option_spice_advanced.addLayout(self.layout_option9_spice_advanced)
            self.layout_option10_spice_advanced = QHBoxLayout()
            self.option10_plaintext_channel = QComboBox()
            self.option10_plaintext_channel.addItems(["main", "display","cursor", "input", "playback", "record"])
            self.option10_plaintext_channel.setEnabled(False)
            self.CB_option10_plaintext_channel = QCheckBox("Bật kênh plaintext tùy chỉnh")
            self.CB_option10_plaintext_channel.setChecked(False)
            self.CB_option10_plaintext_channel.setEnabled(False) #UI
            self.CB_option10_plaintext_channel.toggled.connect(self.update_plaintext_channel)
            self.layout_option10_spice_advanced.addWidget(QLabel("Kênh Plaintext:"))
            self.layout_option10_spice_advanced.addWidget(self.option10_plaintext_channel)
            self.layout_option10_spice_advanced.addWidget(self.CB_option10_plaintext_channel)
            self.layout_option_spice_advanced.addLayout(self.layout_option10_spice_advanced)
            self.layout_option11_spice_advanced = QHBoxLayout()
            self.option11_sasl = QCheckBox("Bật SASL")
            self.option11_sasl.setChecked(False)
            self.option11_sasl.setEnabled(False) #UI
            self.layout_option11_spice_advanced.addWidget(self.option11_sasl)
            self.layout_option_spice_advanced.addLayout(self.layout_option11_spice_advanced)
            self.layout_option12_spice_advanced = QHBoxLayout()
            self.option12_image_compression = QComboBox()
            self.option12_image_compression.addItems(["auto_glz", "auto_lz", "quic", "glz", "lz", "off"])
            self.option12_CB_image_compression = QCheckBox("Bật nén hình ảnh")
            self.option12_CB_image_compression.setChecked(False)
            self.option12_CB_image_compression.setEnabled(False) #UI
            self.option12_CB_image_compression.toggled.connect(self.update_image_compression)
            self.layout_option12_spice_advanced.addWidget(QLabel("Nén hình ảnh:"))
            self.layout_option12_spice_advanced.addWidget(self.option12_image_compression)
            self.layout_option12_spice_advanced.addWidget(self.option12_CB_image_compression)
            self.layout_option_spice_advanced.addLayout(self.layout_option12_spice_advanced)
            self.layout_option13_spice_advenced = QHBoxLayout()
            self.option13_jpeg_wan_compression = QComboBox()
            self.option13_jpeg_wan_compression.addItems(["auto", "never", "always"])
            self.option13_CB_jpeg_wan_compression = QCheckBox("Bật nén JPEG WAN")
            self.option13_CB_jpeg_wan_compression.setChecked(False)
            self.option13_CB_jpeg_wan_compression.setEnabled(False) #UI
            self.option13_CB_jpeg_wan_compression.toggled.connect(self.update_jpeg_wan_compression)
            self.layout_option13_spice_advenced.addWidget(QLabel("Nén JPEG WAN:"))
            self.layout_option13_spice_advenced.addWidget(self.option13_jpeg_wan_compression)
            self.layout_option13_spice_advenced.addWidget(self.option13_CB_jpeg_wan_compression)
            self.layout_option_spice_advanced.addLayout(self.layout_option13_spice_advenced)
            self.layout_option14_spice_advanced = QHBoxLayout()
            self.option14_zlib_glz_wan_compression = QComboBox()
            self.option14_zlib_glz_wan_compression.addItems(["auto", "never", "always"])
            self.option14_CB_zlib_glz_wan_compression = QCheckBox("Bật nén ZLIB/GLZ WAN")
            self.option14_CB_zlib_glz_wan_compression.setChecked(False)
            self.option14_CB_zlib_glz_wan_compression.setEnabled(False) #UI
            self.option14_CB_zlib_glz_wan_compression.toggled.connect(self.update_zlib_glz_wan_compression)
            self.layout_option14_spice_advanced.addWidget(QLabel("Nén ZLIB/GLZ WAN:"))
            self.layout_option14_spice_advanced.addWidget(self.option14_zlib_glz_wan_compression)
            self.layout_option14_spice_advanced.addWidget(self.option14_CB_zlib_glz_wan_compression)
            self.layout_option_spice_advanced.addLayout(self.layout_option14_spice_advanced)
            self.layout_option15_spice_aadvanced = QHBoxLayout()
            self.option15_streaming_video = QComboBox()
            self.option15_streaming_video.addItems(["off", "all", "filter"])
            self.option15_streaming_video.setEnabled(False)
            self.option15_CB_streaming_video = QCheckBox("Bật streaming video")
            self.option15_CB_streaming_video.setChecked(False)
            self.option15_CB_streaming_video.setEnabled(False) #UI
            self.option15_CB_streaming_video.toggled.connect(self.update_streaming_video)
            self.layout_option15_spice_aadvanced.addWidget(QLabel("Streaming video:"))
            self.layout_option15_spice_aadvanced.addWidget(self.option15_streaming_video)
            self.layout_option15_spice_aadvanced.addWidget(self.option15_CB_streaming_video)
            self.layout_option_spice_advanced.addLayout(self.layout_option15_spice_aadvanced)
            self.layout_option16_spice_advanced = QHBoxLayout()
            self.option16_disable_agent_file_xfer = QCheckBox("vô hiệu hóa chuyển file qua agent")
            self.option16_disable_agent_file_xfer.setChecked(False)
            self.option16_disable_agent_file_xfer.setEnabled(False) #UI
            self.layout_option16_spice_advanced.addWidget(self.option16_disable_agent_file_xfer)
            self.layout_option_spice_advanced.addLayout(self.layout_option16_spice_advanced)
            self.layout_option17_spice_advanced = QHBoxLayout()
            self.option17_playback_compression = QCheckBox()
            self.option17_playback_compression.setText("Bật nén playback")
            self.option17_playback_compression.setChecked(False)
            self.option17_playback_compression.setEnabled(False) #UI
            self.layout_option17_spice_advanced.addWidget(self.option17_playback_compression)
            self.layout_option_spice_advanced.addLayout(self.layout_option17_spice_advanced)
            self.layout_option18_spice_advanced = QHBoxLayout()
            self.option18_seamless_migration = QCheckBox("Bật seamless migration")
            self.option18_seamless_migration.setChecked(False)
            self.option18_seamless_migration.setEnabled(False) #UI
            self.layout_option18_spice_advanced.addWidget(self.option18_seamless_migration)
            self.layout_option_spice_advanced.addLayout(self.layout_option18_spice_advanced)
            self.layout_option19_spice_advanced = QHBoxLayout()
            self.option19_video_codec = QLineEdit()
            self.option19_video_codec.setPlaceholderText("Codec video tùy chỉnh (VD: h264)")
            self.option19_video_codec.setEnabled(False)
            self.CB_option19_video_codec = QCheckBox("Bật codec video tùy chỉnh")
            self.CB_option19_video_codec.setChecked(False)
            self.CB_option19_video_codec.setEnabled(False) #UI
            self.CB_option19_video_codec.toggled.connect(self.update_video_codec)
            self.layout_option19_spice_advanced.addWidget(QLabel("Codec video:"))
            self.layout_option19_spice_advanced.addWidget(self.option19_video_codec)
            self.layout_option19_spice_advanced.addWidget(self.CB_option19_video_codec)
            self.layout_option_spice_advanced.addLayout(self.layout_option19_spice_advanced)
            self.layout_option20_spice_advanced = QHBoxLayout()
            self.option20_max_refresh_rate = QSpinBox()
            self.option20_max_refresh_rate.setRange(0, 99999)
            self.option20_max_refresh_rate.setValue(100)
            self.option20_max_refresh_rate.setEnabled(False)
            self.CB_option20_max_refresh_rate = QCheckBox("Bật tốc độ refresh tối đa")
            self.CB_option20_max_refresh_rate.setChecked(False)
            self.CB_option20_max_refresh_rate.setEnabled(False) #UI
            self.CB_option20_max_refresh_rate.toggled.connect(self.update_max_refresh_rate)
            self.layout_option20_spice_advanced.addWidget(QLabel("Tốc độ refresh tối đa:"))
            self.layout_option20_spice_advanced.addWidget(self.option20_max_refresh_rate)
            self.layout_option20_spice_advanced.addWidget(self.CB_option20_max_refresh_rate)
            self.layout_option_spice_advanced.addLayout(self.layout_option20_spice_advanced)
            self.layout_option21_spice_advanced = QHBoxLayout()
            self.option21_gl = QCheckBox("Bật GL")
            self.option21_gl.setChecked(False)
            self.option21_gl.setEnabled(False) #UI
            self.layout_option21_spice_advanced.addWidget(self.option21_gl)
            self.layout_option_spice_advanced.addLayout(self.layout_option21_spice_advanced)
            self.layout_option22_spice_advanced = QHBoxLayout()
            self.option22_render_node = QLineEdit()
            self.option22_render_node.setPlaceholderText("Render node tùy chỉnh (VD: /dev/dri/renderD128)")
            self.option22_render_node.setEnabled(False)
            self.CB_option22_render_node = QCheckBox("Bật render node tùy chỉnh")
            self.CB_option22_render_node.setChecked(False)
            self.CB_option22_render_node.setEnabled(False) #UI
            self.CB_option22_render_node.toggled.connect(self.update_render_node)
            self.layout_option22_spice_advanced.addWidget(QLabel("Render node:"))
            self.layout_option22_spice_advanced.addWidget(self.option22_render_node)
            self.layout_option22_spice_advanced.addWidget(self.CB_option22_render_node)
            self.layout_option_spice_advanced.addLayout(self.layout_option22_spice_advanced)
            self.spice_layout.addLayout(self.layout_option_spice_advanced, 2, 0, 1, 2)
        self.save_snapshot_spice_options()

    def update_x509_dir(self):
        self.option1_x509_dir.setEnabled(self.CB_option1_x509_dir.isChecked())

    def update_x509_key_file(self):
        self.option2_x509_key_file.setEnabled(self.CB_option2_x509_key_file.isChecked())
    
    def update_x509_key_password(self):
        self.option3_x509_key_password.setEnabled(self.CB_option3_x509_key_password.isChecked())

    def update_x509_cert_file(self):
        self.option4_x509_cert_file.setEnabled(self.CB_option4_x509_cert_file.isChecked())
    
    def update_x509_cacert_file(self):
        self.option6_x509_cacert_file.setEnabled(self.CB_option6_x509_cacert_file.isChecked())

    def update_x509_dh_key_file(self):
        self.option7_x509_dh_key_file.setEnabled(self.CB_option7_x509_dh_key_file.isChecked())

    def update_addr_spice(self):
        self.option6_addr_spice.setEnabled(self.CB_option6_addr_spice.isChecked())

    def update_tls_cipher(self):
        self.option8_tls_cipher.setEnabled(self.option8_CB_tls_cipher.isChecked())
    
    def update_tls_channel(self):
        self.option9_tls_channel.setEnabled(self.CB_option9_tls_channel.isChecked())

    def update_plaintext_channel(self):
        self.option10_plaintext_channel.setEnabled(self.CB_option10_plaintext_channel.isChecked())

    def update_password_secret_spice(self):
        self.option6_secret_password_spice.setEnabled(self.CB_option6_secret_password_spice.isChecked())

    def update_image_compression(self):
        self.option12_image_compression.setEnabled(self.option12_CB_image_compression.isChecked())
    
    def update_jpeg_wan_compression(self):
        self.option13_jpeg_wan_compression.setEnabled(self.option13_CB_jpeg_wan_compression.isChecked())

    def update_zlib_glz_wan_compression(self):
        self.option14_zlib_glz_wan_compression.setEnabled(self.option14_CB_zlib_glz_wan_compression.isChecked())

    def update_streaming_video(self):
        self.option15_streaming_video.setEnabled(self.option15_CB_streaming_video.isChecked())

    def update_video_codec(self):
        self.option19_video_codec.setEnabled(self.CB_option19_video_codec.isChecked())
    
    def update_max_refresh_rate(self):
        self.option20_max_refresh_rate.setEnabled(self.CB_option20_max_refresh_rate.isChecked())

    def update_render_node(self):
        self.option22_render_node.setEnabled(self.CB_option22_render_node.isChecked())

    def update_CB_Spice(self):
        check = self.CB_Spice.isChecked()
        self.Mode_of_spice.setEnabled(check)
        self.save_snapshot()
        if self.Mode_of_spice.currentText() == "cơ bản":
            self.CB_option1_port_spice.setEnabled(check)
            self.CB_option2_tls_port_spice.setEnabled(check)
            self.option3_ipv4_spice.setEnabled(check)
            self.option4_ipv6_spice.setEnabled(check)
            self.option5_disable_ticketing_spice.setEnabled(check)
            self.CB_option6_secret_password_spice.setEnabled(check)
            self.option7_disable_copy_paste_spice.setEnabled(check)
            self.option8_agent_mouse_spice.setEnabled(check)
        if self.Mode_of_spice.currentText() == "nâng cao":
            self.CB_option1_port_spice.setEnabled(check)
            self.CB_option2_tls_port_spice.setEnabled(check)
            self.option3_ipv4_spice.setEnabled(check)
            self.option4_ipv6_spice.setEnabled(check)
            self.option5_disable_ticketing_spice.setEnabled(check)
            self.CB_option6_secret_password_spice.setEnabled(check)
            self.CB_option6_addr_spice.setEnabled(check)
            self.option7_disable_copy_paste_spice.setEnabled(check)
            self.option8_agent_mouse_spice.setEnabled(check)
            self.CB_option1_x509_dir.setEnabled(check)
            self.CB_option2_x509_key_file.setEnabled(check)
            self.CB_option3_x509_key_password.setEnabled(check)
            self.CB_option4_x509_cert_file.setEnabled(check)
            self.CB_option6_x509_cacert_file.setEnabled(check)
            self.CB_option7_x509_dh_key_file.setEnabled(check)
            self.option7_unix.setEnabled(check)
            self.option8_CB_tls_cipher.setEnabled(check)
            self.CB_option9_tls_channel.setEnabled(check)
            self.CB_option10_plaintext_channel.setEnabled(check)
            self.option11_sasl.setEnabled(check)
            self.option12_CB_image_compression.setEnabled(check)
            self.option13_CB_jpeg_wan_compression.setEnabled(check)
            self.option14_CB_zlib_glz_wan_compression.setEnabled(check)
            self.option15_CB_streaming_video.setEnabled(check)
            self.option16_disable_agent_file_xfer.setEnabled(check)
            self.option17_playback_compression.setEnabled(check)
            self.option18_seamless_migration.setEnabled(check)
            self.CB_option19_video_codec.setEnabled(check)
            self.CB_option20_max_refresh_rate.setEnabled(check)
            self.option21_gl.setEnabled(check)
            self.CB_option22_render_node.setEnabled(check)

    def update_x509(self):
        check = self.CB_option2_tls_port_spice.isChecked()
        self.option1_x509_dir.setEnabled(check)
        self.option2_x509_key_file.setEnabled(check)
        self.option3_x509_key_password.setEnabled(check)
        self.option4_x509_cert_file.setEnabled(check)
        self.option6_x509_cacert_file.setEnabled(check)
        self.option7_x509_dh_key_file.setEnabled(check)

    def clean_layout_option_spice(self):
        if hasattr(self, 'layout_option_spice_basic'):
            while self.layout_option_spice_basic.count():
                item = self.layout_option_spice_basic.takeAt(0)
                if item is None:
                    continue
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    # Recursively clean nested layouts
                    layout = item.layout()
                    if layout is not None:
                        self._recursive_clear_layout(layout)
        if hasattr(self, 'layout_option_spice_advanced'):
            while self.layout_option_spice_advanced.count():
                item = self.layout_option_spice_advanced.takeAt(0)
                if item is None:
                    continue
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    # Recursively clean nested layouts
                    layout = item.layout()
                    if layout is not None:
                        self._recursive_clear_layout(layout)

    def update_option_diplay(self):
        """ update tùy chọn display theo mode of display đã chọn """
        # Remove old layout_options from display_layout to prevent overlap
        if hasattr(self, 'layout_options') and self.layout_options is not None:
            self.clean_layout_options()
            # Remove the layout_options from the grid layout by finding it
            try:
                for i in range(self.display_layout.count()):
                    item = self.display_layout.itemAt(i)
                    if item and item.layout() is self.layout_options:
                        self.display_layout.removeItem(item)
                        break
            except:
                pass
        
        self.layout_options = QVBoxLayout()
        self.option1_gl2 = QComboBox()
        self.option1_gl2.addItems(["on", "off", "core", "es", "none"])
        self.option1_gl2.setEnabled(False)
        self.options1_readnode = QLineEdit()
        self.options1_readnode.setPlaceholderText("Đường dẫn readnode cho egl-headless")
        self.options1_readnode.setEnabled(False)
        self.checkbox_options1_readnode = QCheckBox("Bật readnode")
        self.checkbox_options1_readnode.setChecked(False)
        self.checkbox_options1_readnode.setEnabled(False) #UI
        self.option1_gl = QCheckBox("Bật/tắt gl")
        self.option1_gl.setChecked(False)
        self.option1_gl.setEnabled(False) #UI
        if self.Mode_of_display.currentText() == "sdl":
            self.clean_layout_options()
            self.layout_options1sdl = QHBoxLayout()
            self.layout_options1sdl.addWidget(QLabel("gl:"))
            self.layout_options1sdl.addWidget(self.option1_gl2)
            self.layout_options.addLayout(self.layout_options1sdl)
            self.layout_options2sdl = QHBoxLayout()
            self.option2_grap_mod = QLineEdit()
            self.option2_grap_mod.setPlaceholderText("VD: rctrl (tham khảo tài liệu qemu)")
            self.option2_grap_mod.setEnabled(False)
            self.checkbox_option2_grap_mod = QCheckBox("Bật grap_mod")
            self.checkbox_option2_grap_mod.setChecked(False)
            self.checkbox_option2_grap_mod.setEnabled(False) #UI
            self.checkbox_option2_grap_mod.toggled.connect(self.update_grap_mod)
            self.layout_options2sdl.addWidget(QLabel("grap_mod:"))
            self.layout_options2sdl.addWidget(self.option2_grap_mod)
            self.layout_options2sdl.addWidget(self.checkbox_option2_grap_mod)
            self.layout_options.addLayout(self.layout_options2sdl)
            self.layout_options3sdl = QHBoxLayout()
            self.option3_show_cursor = QCheckBox("Hiển thị con trỏ chuột")
            self.option3_show_cursor.setChecked(True)
            self.option3_show_cursor.setEnabled(False) #UI
            self.layout_options3sdl.addWidget(self.option3_show_cursor)
            self.layout_options.addLayout(self.layout_options3sdl)
            self.layout_options4sdl = QHBoxLayout()
            self.options4_windows_close = QCheckBox("Cho phép đóng cửa sổ QEMU")
            self.options4_windows_close.setChecked(True)
            self.options4_windows_close.setEnabled(False) #UI
            self.layout_options4sdl.addWidget(self.options4_windows_close)
            self.layout_options.addLayout(self.layout_options4sdl)
        if self.Mode_of_display.currentText() == "spice-app":
            self.clean_layout_options()
            self.layout_options1sp = QHBoxLayout()
            self.layout_options1sp.addWidget(QLabel("gl:"))
            self.layout_options1sp.addWidget(self.option1_gl)
            self.layout_options.addLayout(self.layout_options1sp)
        if self.Mode_of_display.currentText() == "gtk":
            self.clean_layout_options()
            self.layout_options1gtk = QVBoxLayout()
            self.option1_full_srceen = QCheckBox("Bật/tắt fullscreen")
            self.option1_full_srceen.setChecked(False)
            self.option1_full_srceen.setEnabled(False) #UI
            self.layout_options1gtk.addWidget(QLabel("Fullscreen:"))
            self.layout_options1gtk.addWidget(self.option1_full_srceen)
            self.layout_options2gtk = QVBoxLayout()
            self.option2_gl = QCheckBox("Bật/tắt gl")
            self.option2_gl.setChecked(False)
            self.option2_gl.setEnabled(False) #UI
            self.layout_options2gtk.addWidget(QLabel("gl:"))
            self.layout_options2gtk.addWidget(self.option2_gl)
            self.layout_options.addLayout(self.layout_options1gtk)
            self.layout_options.addLayout(self.layout_options2gtk)
            self.layout_options3gtk = QVBoxLayout()
            self.option3_show_tab = QCheckBox("Hiển thị tab khi có nhiều cửa sổ")
            self.option3_show_tab.setChecked(True)
            self.option3_show_tab.setEnabled(False) #UI
            self.layout_options3gtk.addWidget(self.option3_show_tab)
            self.layout_options.addLayout(self.layout_options3gtk)
            self.layout_options4gtk = QVBoxLayout()
            self.options4_show_curser  = QCheckBox("Hiển thị con trỏ chuột")
            self.options4_show_curser.setChecked(True)
            self.layout_options4gtk.addWidget(self.options4_show_curser)
            self.layout_options.addLayout(self.layout_options4gtk)
            self.layout_options5gtk = QVBoxLayout()
            self.options5_windows_close = QCheckBox("Cho phép đóng cửa sổ QEMU")
            self.options5_windows_close.setChecked(True)
            self.options5_windows_close.setEnabled(False) #UI
            self.layout_options5gtk.addWidget(self.options5_windows_close)
            self.layout_options.addLayout(self.layout_options5gtk)
            self.layout_options6gtk = QVBoxLayout()
            self.option6_show_menubar = QCheckBox("Hiển thị menubar")
            self.option6_show_menubar.setChecked(True)
            self.option6_show_menubar.setEnabled(False) #UI
            self.layout_options6gtk.addWidget(self.option6_show_menubar)
            self.layout_options.addLayout(self.layout_options6gtk)
            self.layout_options7gtk = QVBoxLayout()
            self.options7_zoom_to_fit = QCheckBox("Bật zoom to fit")
            self.options7_zoom_to_fit.setChecked(False)
            self.options7_zoom_to_fit.setEnabled(False) #UI
            self.layout_options7gtk.addWidget(self.options7_zoom_to_fit)
            self.layout_options.addLayout(self.layout_options7gtk)
        if self.Mode_of_display.currentText() == "curses":
            self.clean_layout_options()
            self.layout_options1cur = QVBoxLayout()
            self.options1_charset = QLineEdit()
            self.options1_charset.setPlaceholderText("VD: UTF-8")
            self.layout_options1cur.addWidget(QLabel("charset:"))
            self.options1_charset.setEnabled(False)
            self.options1_charset_checkbox = QCheckBox("Bật charset")
            self.options1_charset_checkbox.setChecked(False)
            self.options1_charset_checkbox.setEnabled(False) #UI
            self.options1_charset_checkbox.toggled.connect(self.update_charset)
            self.layout_options1cur.addWidget(self.options1_charset_checkbox)
            self.layout_options1cur.addWidget(self.options1_charset)
            self.layout_options.addLayout(self.layout_options1cur)
        if self.Mode_of_display.currentText() == "egl-headless":
            self.clean_layout_options()
            self.layout_options1egl = QVBoxLayout()
            self.options1_readnode = QLineEdit()
            self.layout_options1egl.addWidget(QLabel("readnode:"))
            self.layout_options1egl.addWidget(self.options1_readnode)
            self.checkbox_options1_readnode.toggled.connect(self.update_readnode1)
            self.layout_options1egl.addWidget(self.checkbox_options1_readnode)
            self.layout_options.addLayout(self.layout_options1egl)
        if self.Mode_of_display.currentText() == "dbus":
            self.clean_layout_options()
            self.layout_options1dbus = QVBoxLayout()
            self.options1_addr = QLineEdit()
            self.checkbox_options1_addr = QCheckBox("Bật DBus address")
            self.checkbox_options1_addr.setChecked(False)
            self.checkbox_options1_addr.setEnabled(False) #UI
            self.checkbox_options1_addr.toggled.connect(self.update_dbus_address)
            self.options1_addr.setPlaceholderText("vd: tcp:host=127.0.0.1,port=12345")
            self.options1_addr.setEnabled(False)
            self.layout_options1dbus.addWidget(QLabel("DBus address:"))
            self.layout_options1dbus.addWidget(self.options1_addr)
            self.layout_options1dbus.addWidget(self.checkbox_options1_addr)
            self.layout_options.addLayout(self.layout_options1dbus)
            self.layout_options2dbus = QVBoxLayout()
            self.layout_options2dbus.addWidget(QLabel("gl:"))
            self.layout_options2dbus.addWidget(self.option1_gl2)
            self.layout_options.addLayout(self.layout_options2dbus)
            self.layout_options3dbus = QVBoxLayout()
            self.layout_options3dbus.addWidget(QLabel("readnode:"))
            self.layout_options3dbus.addWidget(self.options1_readnode)
            self.layout_options3dbus.addWidget(self.checkbox_options1_readnode)
            self.checkbox_options1_readnode.toggled.connect(self.update_readnode1)
        if self.Mode_of_display.currentText() == "none":
            self.clean_layout_options()
        
        # Add the layout_options to display_layout
        self.display_layout.addLayout(self.layout_options, 2, 0, 1, 2)
        self.save_snapshot_display_options()

    def update_UI_display_options(self):
        check_display_options = self.CB_Display.isChecked()
        if self.Mode_of_display.currentText() == "sdl":
            self.checkbox_option2_grap_mod.setEnabled(check_display_options)
            self.option3_show_cursor.setEnabled(check_display_options)
            self.options4_windows_close.setEnabled(check_display_options)
            self.option1_gl2.setEnabled(check_display_options)
        if self.Mode_of_display.currentText() == "spice-app":
            self.option1_gl.setEnabled(check_display_options)
        if self.Mode_of_display.currentText() == "gtk":
            self.option1_full_srceen.setEnabled(check_display_options)
            self.option2_gl.setEnabled(check_display_options)
            self.option3_show_tab.setEnabled(check_display_options)
            self.options4_show_curser.setEnabled(check_display_options)
            self.options5_windows_close.setEnabled(check_display_options)
            self.option6_show_menubar.setEnabled(check_display_options)
            self.options7_zoom_to_fit.setEnabled(check_display_options)
        if self.Mode_of_display.currentText() == "curses":
            self.options1_charset_checkbox.setEnabled(check_display_options)
        if self.Mode_of_display.currentText() == "egl-headless":
            self.checkbox_options1_readnode.setEnabled(check_display_options)
        if self.Mode_of_display.currentText() == "dbus":
            self.checkbox_options1_addr.setEnabled(check_display_options)
            self.option1_gl2.setEnabled(check_display_options)
            self.checkbox_options1_readnode.setEnabled(check_display_options)

    def save_snapshot_display_options(self):
        """Connect display option signals to save snapshot when values change"""
        # Note: Display options are automatically saved via save_snapshot() -> get_current_config() -> update_config_display_options()
        # which saves them to the snapshots.latest section in the JSON file
        # This function ensures that when display options change, we trigger a save
        try:
            if not hasattr(self, '_display_signals_connected'):
                self._display_signals_connected = True
                self.CB_Display.toggled.connect(lambda: self.save_snapshot())
                self.Mode_of_display.currentTextChanged.connect(lambda: self.save_snapshot())
        except:
            pass
        
        # Connect mode-specific signals based on current mode
        if self.Mode_of_display.currentText() == "sdl":
            for attr in ['option1_gl2', 'checkbox_option2_grap_mod', 'option2_grap_mod', 'option3_show_cursor', 'options4_windows_close']:
                if hasattr(self, attr):
                    try:
                        widget = getattr(self, attr)
                        if isinstance(widget, QComboBox):
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.currentIndexChanged.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                        elif isinstance(widget, QLineEdit):
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.textChanged.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                        else:
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.toggled.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                    except:
                        pass
        
        elif self.Mode_of_display.currentText() == "spice-app":
            if hasattr(self, 'option1_gl'):
                try:
                    if not hasattr(self, '_signal_connected_option1_gl'):
                        self.option1_gl.toggled.connect(lambda: self.save_snapshot())
                        setattr(self, '_signal_connected_option1_gl', True)
                except:
                    pass
        
        elif self.Mode_of_display.currentText() == "gtk":
            for attr in ['option1_full_srceen', 'option2_gl', 'option3_show_tab', 'options4_show_curser', 
                        'options5_windows_close', 'option6_show_menubar', 'options7_zoom_to_fit']:
                if hasattr(self, attr):
                    try:
                        if not hasattr(self, f'_signal_connected_{attr}'):
                            getattr(self, attr).toggled.connect(lambda: self.save_snapshot())
                            setattr(self, f'_signal_connected_{attr}', True)
                    except:
                        pass
                self.option6_show_menubar.toggled.connect(lambda: self.save_snapshot())
            if hasattr(self, 'options7_zoom_to_fit'):
                self.options7_zoom_to_fit.toggled.connect(lambda: self.save_snapshot())
        
        elif self.Mode_of_display.currentText() == "curses":
            try:
                if hasattr(self, 'options1_charset_checkbox'):
                    self.options1_charset_checkbox.toggled.disconnect()
            except: pass
            try:
                if hasattr(self, 'options1_charset'):
                    self.options1_charset.textChanged.disconnect()
            except: pass
            if hasattr(self, 'options1_charset_checkbox'):
                self.options1_charset_checkbox.toggled.connect(lambda: self.save_snapshot())
            if hasattr(self, 'options1_charset'):
                self.options1_charset.textChanged.connect(lambda: self.save_snapshot())
        
        elif self.Mode_of_display.currentText() == "egl-headless":
            try:
                if hasattr(self, 'checkbox_options1_readnode'):
                    self.checkbox_options1_readnode.toggled.disconnect()
            except: pass
            try:
                if hasattr(self, 'options1_readnode'):
                    self.options1_readnode.textChanged.disconnect()
            except: pass
            if hasattr(self, 'checkbox_options1_readnode'):
                self.checkbox_options1_readnode.toggled.connect(lambda: self.save_snapshot())
            if hasattr(self, 'options1_readnode'):
                self.options1_readnode.textChanged.connect(lambda: self.save_snapshot())
        
        elif self.Mode_of_display.currentText() == "dbus":
            for attr in ['checkbox_options1_addr', 'options1_addr', 'option1_gl2', 'checkbox_options1_readnode', 'options1_readnode']:
                try:
                    if hasattr(self, attr):
                        widget = getattr(self, attr)
                        if isinstance(widget, QCheckBox):
                            widget.toggled.disconnect()
                        elif isinstance(widget, (QLineEdit, QComboBox)):
                            if isinstance(widget, QLineEdit):
                                widget.textChanged.disconnect()
                            else:
                                widget.currentIndexChanged.disconnect()
                except: pass
            
            if hasattr(self, 'checkbox_options1_addr'):
                self.checkbox_options1_addr.toggled.connect(lambda: self.save_snapshot())
            if hasattr(self, 'options1_addr'):
                self.options1_addr.textChanged.connect(lambda: self.save_snapshot())
            if hasattr(self, 'option1_gl2'):
                self.option1_gl2.currentIndexChanged.connect(lambda: self.save_snapshot())
            if hasattr(self, 'checkbox_options1_readnode'):
                self.checkbox_options1_readnode.toggled.connect(lambda: self.save_snapshot())
            if hasattr(self, 'options1_readnode'):
                self.options1_readnode.textChanged.connect(lambda: self.save_snapshot())

    def save_snapshot_spice_options(self):
        """Connect spice option signals to save snapshot when values change"""
        # Note: Spice options are automatically saved via save_snapshot() -> get_current_config() -> update_config_spice_options()
        # which saves them to the snapshots.latest section in the JSON file
        # This function ensures that when spice options change, we trigger a save
        try:
            if not hasattr(self, '_spice_signals_connected'):
                self._spice_signals_connected = True
                self.CB_Spice.toggled.connect(lambda: self.save_snapshot())
                self.Mode_of_spice.currentTextChanged.connect(lambda: self.save_snapshot())
        except:
            pass
        
        # Connect mode-specific signals based on current mode
        if self.Mode_of_spice.currentText() == "cơ bản":
            for attr in ['CB_option1_port_spice', 'option1_port_spice', 'CB_option2_tls_port_spice', 'option2_tls_port_spice',
                        'option3_ipv4_spice', 'option4_ipv6_spice', 'option5_disable_ticketing_spice', 
                        'CB_option6_secret_password_spice', 'option6_secret_password_spice', 'option7_disable_copy_paste_spice', 
                        'option8_agent_mouse_spice']:
                if hasattr(self, attr):
                    try:
                        widget = getattr(self, attr)
                        if isinstance(widget, QComboBox):
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.currentIndexChanged.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                        elif isinstance(widget, QLineEdit):
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.textChanged.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                        elif isinstance(widget, QSpinBox):
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.valueChanged.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                        else:
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.toggled.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                    except:
                        pass
        
        elif self.Mode_of_spice.currentText() == "nâng cao":
            # Include all advanced mode controls
            for attr in ['CB_option1_port_spice', 'option1_port_spice', 'CB_option2_tls_port_spice', 'option2_tls_port_spice',
                        'option3_ipv4_spice', 'option4_ipv6_spice', 'option5_disable_ticketing_spice', 
                        'CB_option6_secret_password_spice', 'option6_secret_password_spice', 'CB_option6_addr_spice', 'option6_addr_spice',
                        'option7_disable_copy_paste_spice', 'option8_agent_mouse_spice', 'option7_unix',
                        # x509 options
                        'CB_option1_x509_dir', 'option1_x509_dir', 'CB_option2_x509_key_file', 'option2_x509_key_file',
                        'CB_option3_x509_key_password', 'option3_x509_key_password', 'CB_option4_x509_cert_file', 'option4_x509_cert_file',
                        'CB_option6_x509_cacert_file', 'option6_x509_cacert_file', 'CB_option7_x509_dh_key_file', 'option7_x509_dh_key_file',
                        # TLS options
                        'option8_CB_tls_cipher', 'option8_tls_cipher', 'CB_option9_tls_channel', 'option9_tls_channel',
                        'CB_option10_plaintext_channel', 'option10_plaintext_channel', 'option11_sasl',
                        # Compression options
                        'option12_CB_image_compression', 'option12_image_compression', 'option13_CB_jpeg_wan_compression', 'option13_jpeg_wan_compression',
                        'option14_CB_zlib_glz_wan_compression', 'option14_zlib_glz_wan_compression', 'option15_CB_streaming_video', 'option15_streaming_video',
                        # Other advanced options
                        'option16_disable_agent_file_xfer', 'option17_playback_compression', 'option18_seamless_migration',
                        'CB_option19_video_codec', 'option19_video_codec', 'CB_option20_max_refresh_rate', 'option20_max_refresh_rate',
                        'option21_gl', 'CB_option22_render_node', 'option22_render_node']:
                if hasattr(self, attr):
                    try:
                        widget = getattr(self, attr)
                        if isinstance(widget, QComboBox):
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.currentIndexChanged.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                        elif isinstance(widget, QLineEdit):
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.textChanged.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                        elif isinstance(widget, QSpinBox):
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.valueChanged.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                        else:
                            if not hasattr(self, f'_signal_connected_{attr}'):
                                widget.toggled.connect(lambda: self.save_snapshot())
                                setattr(self, f'_signal_connected_{attr}', True)
                    except:
                        pass

    def clean_layout_options(self):
        """Properly clean up and remove all widgets from layout_options"""
        if hasattr(self, 'layout_options'):
            while self.layout_options.count():
                item = self.layout_options.takeAt(0)
                if item is None:
                    continue
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    # Recursively clean nested layouts
                    layout = item.layout()
                    if layout is not None:
                        self._recursive_clear_layout(layout)
    
    def _recursive_clear_layout(self, layout):
        """Recursively clear all widgets and nested layouts"""
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                nested_layout = item.layout()
                if nested_layout is not None:
                    self._recursive_clear_layout(nested_layout)

    def update_dbus_address(self):
        self.options1_addr.setEnabled(self.checkbox_options1_addr.isChecked())

    def update_charset(self):
        self.options1_charset.setEnabled(self.options1_charset_checkbox.isChecked())
    def update_readnode1(self):
        self.options1_readnode.setEnabled(self.checkbox_options1_readnode.isChecked())
    def update_grap_mod(self):
        self.option2_grap_mod.setEnabled(self.checkbox_option2_grap_mod.isChecked())

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

        shortcut_advanced_tab = QShortcut(QKeySequence("Ctrl+A"), self)
        shortcut_advanced_tab.activated.connect(lambda: self.setCurrentWidget(self.findChild(QScrollArea, "Cấu hình nâng cao")))
        self.shortcuts.append(shortcut_advanced_tab)

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
        self.Checkbox_enable_watchdog_device.toggled.connect(self.save_snapshot)

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

        #nographics
        self.CB_NGG.toggled.connect(self.save_snapshot)

        #display options
        self.CB_Display.toggled.connect(self.save_snapshot)
        self.Mode_of_display.currentIndexChanged.connect(self.save_snapshot)
        self.QTime_save_snapshot_display_options = QTimer()
        self.QTime_save_snapshot_display_options.setSingleShot(True)
        self.QTime_save_snapshot_display_options.setInterval(20) # 20ms debounce
        self.QTime_save_snapshot_display_options.timeout.connect(self.save_snapshot_display_options)

        #spice options
        self.CB_Spice.toggled.connect(self.save_snapshot)
        self.CB_Spice.toggled.connect(self.save_snapshot_spice_options)
        self.Mode_of_spice.currentIndexChanged.connect(self.save_snapshot)
        self.Mode_of_spice.currentIndexChanged.connect(self.save_snapshot_spice_options)
        self.QTime_save_snapshot_spice_options = QTimer()
        self.QTime_save_snapshot_spice_options.setSingleShot(True)
        self.QTime_save_snapshot_spice_options.setInterval(20) # 20ms debounce
        self.QTime_save_snapshot_spice_options.timeout.connect(self.save_snapshot_spice_options)

        #i386 advanced options
        self.win2k_hack.toggled.connect(self.save_snapshot)
        self.no_fd_bootcheck.toggled.connect(self.save_snapshot)

        #keyboard layout
        self.keyboardlayoutlineedit.textChanged.connect(self.save_snapshot)
        self.keyboardlayoutcheckbox.toggled.connect(self.save_snapshot)

        # edid vga
        self.xres.valueChanged.connect(self.save_snapshot)
        self.yres.valueChanged.connect(self.save_snapshot)
        self.max_xres.valueChanged.connect(self.save_snapshot)
        self.max_yres.valueChanged.connect(self.save_snapshot)
        self.refresh_hz.valueChanged.connect(self.save_snapshot)
        self.srceen_raw_width.valueChanged.connect(self.save_snapshot)
        self.srceen_raw_height.valueChanged.connect(self.save_snapshot)
        self.enable_edid.toggled.connect(self.save_snapshot)
        self.enable_edid_path.toggled.connect(self.save_snapshot)
        self.lineedit_edid_path.textChanged.connect(self.save_snapshot)
        self.btn_edid_path.clicked.connect(self.save_snapshot)
        self.btn_max_xres.clicked.connect(self.save_snapshot)
        self.btn_max_yres.clicked.connect(self.save_snapshot)

        #multi option call
        self.moc_list.itemChanged.connect(self.save_snapshot)
        self.btn_moc_create_option.clicked.connect(self.save_snapshot)
        self.btn_moc_delete_option.clicked.connect(self.save_snapshot)
        self.btn_moc_reoption.clicked.connect(self.save_snapshot)

        #edid menu
        self.em_create_btn.clicked.connect(self.save_snapshot)
        self.em_delete_btn.clicked.connect(self.save_snapshot)
        self.em_import_btn.clicked.connect(self.save_snapshot)
        self.em_comboBox.currentIndexChanged.connect(self.save_snapshot)

        #netad
        self.netad_mode.currentIndexChanged.connect(self.save_snapshot)
        self.enable_netad.toggled.connect(self.save_snapshot)

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

    def check_disk_available(self):
        cfg = get_config_path()
        with open(cfg, 'r', encoding="utf-8") as f:
            data = json.load(f)
        
        disk_list = data["disks"].keys()
        for disk in disk_list:
            if not Path(disk).exists():
                del data["disks"][disk]

        self.update_disk_list()

        with open(cfg, 'w', encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

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
                 self.L_ACC_Status.setText("Khong ho tro")
                 self.L_ACC_Status.setStyleSheet("color: red")
                 self.L_ACC_Status.setToolTip(f"QEMU tra ve ma loi {proc.returncode}. Co the may khong ho tro {acc} hoac chua bat feature.")
            else:
                 self.L_ACC_Status.setText("Ho tro")
                 self.L_ACC_Status.setStyleSheet("color: green")
                 self.L_ACC_Status.setToolTip("Accelerator kha dung.")
        except Exception as e:
             self.L_ACC_Status.setText("Loi kiem tra")
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
        self.boot_scroll.setEnabled(not checked)
        self.net_scroll.setEnabled(not checked)
        self.daemon_storage_scroll.setEnabled(not checked)
        self.adco_scroll.setEnabled(not checked)

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

    def maunal_set_config(self, cfg: dict = {}):
        # xóa attr lỗi
        cfg.pop('vga-enable-edid', None)
        cfg.pop('multi_options', None)
        # khởi tạo lại attr
        cfg['vga-enable-edid'] = self.enable_edid.isChecked()
        cfg['multi_options'] = self.check_moc()
        return cfg

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
                    "checkbox_watchdog": self.Checkbox_enable_watchdog_device.isChecked(),
                    "none_watchdog_device": self.none_Watchdog,
                    "nographics": self.CB_NGG.isChecked(),
                    "index_of_current_tab": self.currentIndex(),
                    "win2k-hack": self.win2k_hack.isChecked(),
                    "no-fd-bootcheck": self.no_fd_bootcheck.isChecked(),
                    "klc": self.keyboardlayoutcheckbox.isChecked(),
                    "keyboard_layout": self.keyboardlayoutlineedit.text() if self.keyboardlayoutcheckbox.isChecked() else None,
                    "multi_options": self.check_moc(),
                    "edid-path-vga": self.enable_edid_path.isChecked(),
                    "enable_netad": self.enable_netad.isChecked(),
                    "netad_mode": self.netad_mode.currentText(),
                    "netad": {},
                }
                config = self.update_config_display_options(config)
                config = self.update_config_spice_option(config)
                config = self.edid_vga_config(config)
                config = self.maunal_set_config(config)
                config["netad"] = self.config_netad()
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

    def edid_vga_config(self, dict: dict = {}):
        if self.enable_edid.isChecked():       
            di = {
                "edid-vga": {
                    "xres": self.xres.value(),
                    "yres": self.yres.value(),
                    "max_xres": self.max_xres.value() if self.btn_max_xres.isChecked() else None,
                    "max_yres": self.max_yres.value() if self.btn_max_yres.isChecked() else None,
                    "refresh-hz": self.refresh_hz.value(),
                    "srw": self.srceen_raw_width.value() if self.btn_srceen_raw_width.isChecked() else None,
                    "srh": self.srceen_raw_height.value() if self.btn_srceen_raw_height.isChecked() else None,
                    "path": self.lineedit_edid_path.text().strip(),
                }
            }
        else:
            di = {
                "edid-vga": {
                    "xres": self.xres.value(),
                    "yres": self.yres.value(),
                    "max_xres": self.max_xres.value() if self.btn_max_xres.isChecked() else None,
                    "max_yres": self.max_yres.value() if self.btn_max_yres.isChecked() else None,
                    "refresh-hz": self.refresh_hz.value(),
                    "srw": self.srceen_raw_width.value() if self.btn_srceen_raw_width.isChecked() else None,
                    "srh": self.srceen_raw_height.value() if self.btn_srceen_raw_height.isChecked() else None,
                    "path": self.lineedit_edid_path.text().strip(),
                }
            }
        dict.update(di)
        return dict
        

    def update_config_display_options(self, config):
        if self.CCRQ.isChecked():
            return config
        if not self.CB_Display.isChecked():
            return config
        
        mode = self.Mode_of_display.currentText()
        config["display_options"] = {
            "mode": mode,
            "Enable": str(self.CB_Display.isChecked()),
            "options": {}
        }
        
        options_dict = {}
        if mode == "sdl":
            options_dict["sdl"] = {
                "gl2": str(self.option1_gl2.currentIndex()) if hasattr(self, 'option1_gl2') else "0",
                "grap_mod": str(self.option2_grap_mod.text()) if hasattr(self, 'option2_grap_mod') else "",
                "check_grap_mod": str(self.checkbox_option2_grap_mod.isChecked()) if hasattr(self, 'checkbox_option2_grap_mod') else "False",
                "show_cursor": str(self.option3_show_cursor.isChecked()) if hasattr(self, 'option3_show_cursor') else "True",
                "windows_close": str(self.options4_windows_close.isChecked()) if hasattr(self, 'options4_windows_close') else "True",
            }
        elif mode == "spice-app":
            options_dict["spice-app"] = {
                "gl": str(self.option1_gl.isChecked()) if hasattr(self, 'option1_gl') else "False",
            }
        elif mode == "gtk":
            options_dict["gtk"] = {
                "fullscreen": str(self.option1_full_srceen.isChecked()) if hasattr(self, 'option1_full_srceen') else "False",
                "gl": str(self.option2_gl.isChecked()) if hasattr(self, 'option2_gl') else "False",
                "show_tab": str(self.option3_show_tab.isChecked()) if hasattr(self, 'option3_show_tab') else "False",
                "show_curser": str(self.options4_show_curser.isChecked()) if hasattr(self, 'options4_show_curser') else "True",
                "windows_close": str(self.options5_windows_close.isChecked()) if hasattr(self, 'options5_windows_close') else "True",
                "show_menubar": str(self.option6_show_menubar.isChecked()) if hasattr(self, 'option6_show_menubar') else "True",
                "zoom_to_fit": str(self.options7_zoom_to_fit.isChecked()) if hasattr(self, 'options7_zoom_to_fit') else "False",
            }
        elif mode == "curses":
            options_dict["curses"] = {
                "charset": str(self.options1_charset.text()) if hasattr(self, 'options1_charset') else "",
                "charset_enable": str(self.options1_charset_checkbox.isChecked()) if hasattr(self, 'options1_charset_checkbox') else "False",
            }
        elif mode == "egl-headless":
            options_dict["egl-headless"] = {
                "readnode": str(self.options1_readnode.text()) if hasattr(self, 'options1_readnode') else "",
                "readnode_enable": str(self.checkbox_options1_readnode.isChecked()) if hasattr(self, 'checkbox_options1_readnode') else "False",
            }
        elif mode == "dbus":
            options_dict["dbus"] = {
                "addr": str(self.options1_addr.text()) if hasattr(self, 'options1_addr') else "",
                "addr_enable": str(self.checkbox_options1_addr.isChecked()) if hasattr(self, 'checkbox_options1_addr') else "False",
                "gl2": str(self.option1_gl2.currentIndex()) if hasattr(self, 'option1_gl2') else "0",
                "readnode": str(self.options1_readnode.text()) if hasattr(self, 'options1_readnode') else "",
                "readnode_enable": str(self.checkbox_options1_readnode.isChecked()) if hasattr(self, 'checkbox_options1_readnode') else "False",
            }
        
        config["display_options"]["options"] = options_dict
        return config

    def update_config_spice_option(self, config):
        if self.CCRQ.isChecked():
            return config
        if not self.CB_Spice.isChecked():
            return config
        
        mode = self.Mode_of_spice.currentText()
        config["spice_option"] = {
            "mode": mode,
            "Enable": str(self.CB_Spice.isChecked()),
            "options": {}
        }
        
        options_dict = {}
        if mode == "cơ bản":
            options_dict["basic"] = {
                "port":{
                    "enable": str(self.CB_option1_port_spice.isChecked()) if hasattr(self, 'CB_option1_port_spice') else "False",
                    "value": str(self.option1_port_spice.text()) if hasattr(self, 'option1_port_spice') else "",
                },
                "tls-port":{
                    "enable": str(self.CB_option2_tls_port_spice.isChecked()) if hasattr(self, 'CB_option2_tls_port_spice') else "False",
                    "value": str(self.option2_tls_port_spice.text()) if hasattr(self, 'option2_tls_port_spice') else "",
                },
                "ipv4": str(self.option3_ipv4_spice.isChecked()) if hasattr(self, 'option3_ipv4_spice') else "False",
                "ipv6": str(self.option4_ipv6_spice.isChecked()) if hasattr(self, 'option4_ipv6_spice') else "False",
                "disable_ticketing": str(self.option5_disable_ticketing_spice.isChecked()) if hasattr(self, 'option5_disable_ticketing_spice') else "False",
                "password_secret":{
                    "enable": str(self.CB_option6_secret_password_spice.isChecked()) if hasattr(self, 'CB_option6_secret_password_spice') else "False",
                    "value": str(self.option6_secret_password_spice.text()) if hasattr(self, 'option6_secret_password_spice') else "",
                },
                "disable_copy_paste": str(self.option7_disable_copy_paste_spice.isChecked()) if hasattr(self, 'option7_disable_copy_paste_spice') else "False",
                "agent_mouse": str(self.option8_agent_mouse_spice.isChecked()) if hasattr(self, "option8_agent_mouse_spice") else "False",
            }
        if mode == "nâng cao":
            options_dict["advanced"] = {
                "port":{
                    "enable": str(self.CB_option1_port_spice.isChecked()) if hasattr(self, 'CB_option1_port_spice') else "False",
                    "value": str(self.option1_port_spice.text()) if hasattr(self, 'option1_port_spice') else "",
                },
                "tls-port":{
                    "enable": str(self.CB_option2_tls_port_spice.isChecked()) if hasattr(self, 'CB_option2_tls_port_spice') else "False",
                    "value": str(self.option2_tls_port_spice.text()) if hasattr(self, 'option2_tls_port_spice') else "",
                },
                "ipv4": str(self.option3_ipv4_spice.isChecked()) if hasattr(self, 'option3_ipv4_spice') else "False",
                "ipv6": str(self.option4_ipv6_spice.isChecked()) if hasattr(self, 'option4_ipv6_spice') else "False",
                "disable_ticketing": str(self.option5_disable_ticketing_spice.isChecked()) if hasattr(self, 'checkbox_option3_disable_ticketing_spice') else "False",
                "password_secrect":{
                    "enable": str(self.CB_option6_secret_password_spice.isChecked()) if hasattr(self, 'CB_option6_secret_password_spice') else "False",
                    "value": str(self.option6_secret_password_spice.text()) if hasattr(self, 'option6_secret_password_spice') else "",
                },
                "disable_copy_paste": str(self.option7_disable_copy_paste_spice.isChecked()) if hasattr(self, 'option7_disable_copy_paste_spice') else "False",
                "x509":{
                    "enable": str(self.CB_option2_tls_port_spice.isChecked()) if hasattr(self, 'CB_option2_tls_port_spice') else "False",
                    "x509_dir":{
                        "enable": str(self.CB_option1_x509_dir.isChecked()) if hasattr(self, 'CB_option1_x509_dir') else "False",
                        "value": str(self.option1_x509_dir.text()) if hasattr(self, 'option1_x509_dir') else "",
                    },
                    "x509_key_file":{
                        "enable": str(self.CB_option2_x509_key_file.isChecked()) if hasattr(self, 'CB_option2_x509_key_file') else "False",
                        "value": str(self.option2_x509_key_file.text()) if hasattr(self, 'option2_x509_key_file') else "",
                    },
                    "x509_cert_file":{
                        "enable": str(self.CB_option4_x509_cert_file.isChecked()) if hasattr(self, 'CB_option4_x509_cert_file') else "False",
                        "value": str(self.option4_x509_cert_file.text()) if hasattr(self, 'option4_x509_cert_file') else "",
                    },
                    "x509_key_password":{
                        "enable": str(self.CB_option3_x509_key_password.isChecked()) if hasattr(self, 'CB_option3_x509_key_password') else "False",
                        "value": str(self.option3_x509_key_password.text()) if hasattr(self, 'option3_x509_key_password') else "",
                    },
                    "x509_cacert_file":{
                        "enable": str(self.CB_option6_x509_cacert_file.isChecked()) if hasattr(self, 'CB_option6_x509_cacert_file') else "False",
                        "value": str(self.option6_x509_cacert_file.text()) if hasattr(self, 'option6_x509_cacert_file') else "",
                    },
                    "x509_dh_key_file":{
                        "enable": str(self.CB_option7_x509_dh_key_file.isChecked()) if hasattr(self, "CB_option7_x509_dh_key_file") else "False",
                        "value": str(self.option7_x509_dh_key_file.text()) if hasattr(self, "option7_x509_dh_key_file") else "",
                    },
                },
                "addr": {
                    "enable": str(self.CB_option6_addr_spice.isChecked()) if hasattr(self, "CB_option6_addr_spice") else "False",
                    "value": str(self.option6_addr_spice.text()) if hasattr(self, "option6_addr_spice") else "",
                },
                "unix": str(self.option7_unix.isChecked()) if hasattr(self, "option7_unix") else "False",
                "tls_ciphers":{
                    "enable": str(self.option8_CB_tls_cipher.isChecked()) if hasattr(self, "option8_CB_tls_cipher") else "False",
                    "value": str(self.option8_tls_cipher.text()) if hasattr(self, "option8_tls_cipher") else "",
                },
                "tls_channel": {
                    "enable": str(self.CB_option9_tls_channel.isChecked()) if hasattr(self, "CB_option9_tls_channel") else "False",
                    "value": str(self.option9_tls_channel.currentText()) if hasattr(self, "option9_tls_channel") else "",
                },
                "plaintext_channel": {
                    "enable": str(self.CB_option10_plaintext_channel.isChecked()) if hasattr(self, "CB_option10_plaintext_channel") else "False",
                    "value": str(self.option10_plaintext_channel.currentText()) if hasattr(self, "option10_plaintext_channel") else "",
                },
                "sasl": str(self.option11_sasl.isChecked()) if hasattr(self, "option11_sasl") else "False",
                "image_compression":{
                    "enable": str(self.option12_CB_image_compression.isChecked()) if hasattr(self, "option12_CB_image_compression") else "False",
                    "value": str(self.option12_image_compression.currentText()) if hasattr(self, "option12_image_compression") else "",
                },
                "jpeg_wan_compression":{
                    "enable": str(self.option13_CB_jpeg_wan_compression.isChecked()) if hasattr(self, "option13_CB_jpeg_wan_compression") else "False",
                    "value": str(self.option13_jpeg_wan_compression.currentText()) if hasattr(self, "option13_jpeg_wan_compression") else ""
                },
                "zlib_glz_wan_compression":{
                    "enable": str(self.option14_CB_zlib_glz_wan_compression.isChecked()) if hasattr(self, "option14_CB_zlib_glz_wan_compression") else "False",
                    "value": str(self.option14_zlib_glz_wan_compression.currentText()) if hasattr(self, "option14_zlib_glz_wan_compression") else "",
                },
                "streaming_video":{
                    "enable": str(self.option15_CB_streaming_video.isChecked()) if hasattr(self, "option15_CB_streaming_video") else "False",
                    "value": str(self.option15_streaming_video.currentText()) if hasattr(self, "option15_streaming_video") else ""
                },
                "disable_agent_file_xfer": str(self.option16_disable_agent_file_xfer.isChecked()) if hasattr(self, "option16_disable_agent_file_xfer") else "False",
                "agent_mouse": str(self.option8_agent_mouse_spice.isChecked()) if hasattr(self, "option8_agent_mouse_spice") else "False",
                "playback_compression": str(self.option17_playback_compression.isChecked()) if hasattr(self, "option17_playback_compression") else "False",
                "seamless_migration": str(self.option18_seamless_migration.isChecked()) if hasattr(self, "option18_seamless_migration") else "False",
                "video_codec": {
                    "enable": str(self.CB_option19_video_codec.isChecked()) if hasattr(self, "CB_option19_video_codec") else "False",
                    "value": str(self.option19_video_codec.text()) if hasattr(self, "option19_video_codec") else "",
                },
                "max_refresh_rate": {
                    "enable": str(self.CB_option20_max_refresh_rate.isChecked()) if hasattr(self, "CB_option20_max_refresh_rate") else "False",
                    'value': str(self.option20_max_refresh_rate.value()) if hasattr(self, "option20_max_refresh_rate") else "0",
                },
                "gl": str(self.option21_gl.isChecked()) if hasattr(self, "option21_gl") else "False",
                "rendernode": {
                    "enable": str(self.CB_option22_render_node.isChecked()) if hasattr(self, "CB_option22_render_node") else "False",
                    "value": str(self.option22_render_node.text()) if hasattr(self, "option22_render_node") else "",
                }
            }
        config["spice_option"]["options"] = options_dict
        return config
            
    def apply_config_display_options(self, cfg=None):
        try:
            if cfg is None:
                cfg = {}
            display_options = cfg.get("display_options", {})
            if not display_options:
                self.CB_Display.setChecked(False)
                return
            mode = display_options.get("mode", "")
            options = display_options.get("options", {})
            if not mode:
                self.CB_Display.setChecked(False)
                return
            
            # First, set the mode which should trigger update_option_diplay to create widgets
            self.CB_Display.setChecked(True)
            self.Mode_of_display.setCurrentText(mode)
            
            # Manually call update_option_diplay to ensure widgets are created
            # (in case signals are blocked)
            if not hasattr(self, 'layout_options') or not hasattr(self, 'option1_gl2'):
                self.update_option_diplay()
            
            # Now apply the specific options for this mode
            if mode == "sdl":
                if hasattr(self, 'option1_gl2'):
                    self.option1_gl2.setCurrentIndex(int(options.get("sdl", {}).get("gl2", 0)))
                if hasattr(self, 'option2_grap_mod'):
                    self.option2_grap_mod.setText(str(options.get("sdl", {}).get("grap_mod", "")))
                if hasattr(self, 'checkbox_option2_grap_mod'):
                    self.checkbox_option2_grap_mod.setChecked(str(options.get("sdl", {}).get("check_grap_mod", "False")) == "True")
                if hasattr(self, 'option3_show_cursor'):
                    self.option3_show_cursor.setChecked(str(options.get("sdl", {}).get("show_cursor", "True")) == "True")
                if hasattr(self, 'options4_windows_close'):
                    self.options4_windows_close.setChecked(str(options.get("sdl", {}).get("windows_close", "True")) == "True")
            elif mode == "spice-app":
                if hasattr(self, 'option1_gl'):
                    self.option1_gl.setChecked(str(options.get("spice-app", {}).get("gl", "False")) == "True")
            elif mode == "gtk":
                if hasattr(self, 'option1_full_srceen'):
                    self.option1_full_srceen.setChecked(str(options.get("gtk", {}).get("fullscreen", "False")) == "True")
                if hasattr(self, 'option2_gl'):
                    self.option2_gl.setChecked(str(options.get("gtk", {}).get("gl", "False")) == "True")
                if hasattr(self, 'option3_show_tab'):
                    self.option3_show_tab.setChecked(str(options.get("gtk", {}).get("show_tab", "True")) == "True")
                if hasattr(self, 'options4_show_curser'):
                    self.options4_show_curser.setChecked(str(options.get("gtk", {}).get("show_curser", "True")) == "True")
                if hasattr(self, 'options5_windows_close'):
                    self.options5_windows_close.setChecked(str(options.get("gtk", {}).get("windows_close", "True")) == "True")
                if hasattr(self, 'option6_show_menubar'):
                    self.option6_show_menubar.setChecked(str(options.get("gtk", {}).get("show_menubar", "True")) == "True")
                if hasattr(self, 'options7_zoom_to_fit'):
                    self.options7_zoom_to_fit.setChecked(str(options.get("gtk", {}).get("zoom_to_fit", "False")) == "True")
            elif mode == "curses":
                if hasattr(self, 'options1_charset'):
                    self.options1_charset.setText(str(options.get("curses", {}).get("charset", "")))
                if hasattr(self, 'options1_charset_checkbox'):
                    self.options1_charset_checkbox.setChecked(str(options.get("curses", {}).get("charset_enable", "False")) == "True")
            elif mode == "egl-headless":
                if hasattr(self, 'options1_readnode'):
                    self.options1_readnode.setText(str(options.get("egl-headless", {}).get("readnode", "")))
                if hasattr(self, 'checkbox_options1_readnode'):
                    self.checkbox_options1_readnode.setChecked(str(options.get("egl-headless", {}).get("readnode_enable", "False")) == "True")
            elif mode == "dbus":
                if hasattr(self, 'options1_addr'):
                    self.options1_addr.setText(str(options.get("dbus", {}).get("addr", "")))
                if hasattr(self, 'checkbox_options1_addr'):
                    self.checkbox_options1_addr.setChecked(str(options.get("dbus", {}).get("addr_enable", "False")) == "True")
                if hasattr(self, 'option1_gl2'):
                    self.option1_gl2.setCurrentIndex(int(options.get("dbus", {}).get("gl2", 0)))
                if hasattr(self, 'options1_readnode'):
                    self.options1_readnode.setText(str(options.get("dbus", {}).get("readnode", "")))
                if hasattr(self, 'checkbox_options1_readnode'):
                    self.checkbox_options1_readnode.setChecked(str(options.get("dbus", {}).get("readnode_enable", "False")) == "True")
        except Exception:
            pass

    def apply_spice_option(self, cfg=None):
        try:
            if cfg is None:
                cfg = {}
            spice_option = cfg.get("spice_option", {})
            if not spice_option:
                self.CB_Spice.setChecked(False)
                return
            mode = spice_option.get("mode", "")
            option = spice_option.get("options", {})
            if not mode:
                self.CB_Spice.setChecked(False)
                return
            
            self.CB_Spice.setChecked(True)
            self.Mode_of_spice.setCurrentText(mode)

            if not hasattr(self, 'layout_option_spice') or not hasattr(self,"layout_option_spice_advanced") or not hasattr(self, "layout_option_spice_basic"):
                self.update_UI_spice_options()

            if mode == "cơ bản":
                basic = option.get("basic", {})
                if hasattr(self, "option1_port_spice"):
                    self.option1_port_spice.setText(str(basic.get("port", {}).get("value", "")))
                if hasattr(self, "CB_option1_port_spice"):
                    self.CB_option1_port_spice.setChecked(bool(basic.get("port", {}).get("enable", "False")) == "True")
                    self.update_port_spice()
                if hasattr(self, "option2_tls_port_spice"):
                    self.option2_tls_port_spice.setText(str(basic.get("tls-port",{}).get("value","")))
                if hasattr(self, "CB_option2_tls_port_spice"):
                    self.CB_option2_tls_port_spice.setChecked(bool(basic.get("tls-port",{}).get("enable", "False")) == "True")
                    self.update_tls_port_spice()
                if hasattr(self, "option5_disable_ticketing_spice"):
                    self.option5_disable_ticketing_spice.setChecked(bool(basic.get("disable_ticketing", "False")) == "True")
                if hasattr(self, "CB_option6_secret_password_spice"):
                    self.CB_option6_secret_password_spice.setChecked(bool(basic.get("password_secret", {}).get("enable", "False")) == "True")
                    self.update_password_secret_spice()
                if hasattr(self, "option6_secret_password_spice"):
                    self.option6_secret_password_spice.setText(str(basic.get("password_secret", {}).get("value", "")))
                if hasattr(self, "option7_disable_copy_paste_spice"):
                    self.option7_disable_copy_paste_spice.setChecked(bool(basic.get("disable_copy_paste", "False")) == "True")
                if hasattr(self, "option3_ipv4_spice"):
                    self.option3_ipv4_spice.setChecked(bool(basic.get("ipv4", "False")) == "True")
                if hasattr(self, "option4_ipv6_spice"):
                    self.option4_ipv6_spice.setChecked(bool(basic.get("ipv6", "False")))
                if hasattr(self, "option8_agent_mouse_spice"):
                    self.option8_agent_mouse_spice.setChecked(bool(basic.get("agent_mouse", "False")) == "True")
            if mode == "nâng cao":
                advanced = option.get("advanced", {})
                # Basic options in advanced mode
                if hasattr(self, "option1_port_spice"):
                    self.option1_port_spice.setText(str(advanced.get("port", {}).get("value", "")))
                if hasattr(self, "CB_option1_port_spice"):
                    self.CB_option1_port_spice.setChecked(bool(advanced.get("port", {}).get("enable", "False")) == "True")
                    self.update_port_spice()
                if hasattr(self, "option2_tls_port_spice"):
                    self.option2_tls_port_spice.setText(str(advanced.get("tls-port",{}).get("value","")))
                if hasattr(self, "CB_option2_tls_port_spice"):
                    self.CB_option2_tls_port_spice.setChecked(bool(advanced.get("tls-port",{}).get("enable", "False")) == "True")
                    self.update_tls_port_spice()
                if hasattr(self, "option3_ipv4_spice"):
                    self.option3_ipv4_spice.setChecked(bool(advanced.get("ipv4", "False")))
                if hasattr(self, "option4_ipv6_spice"):
                    self.option4_ipv6_spice.setChecked(bool(advanced.get("ipv6", "False")))
                if hasattr(self, "option5_disable_ticketing_spice"):
                    self.option5_disable_ticketing_spice.setChecked(bool(advanced.get("disable_ticketing", "False")))
                if hasattr(self, "CB_option6_secret_password_spice"):
                    self.CB_option6_secret_password_spice.setChecked(bool(advanced.get("password_secret", {}).get("enable", "False")) == "True")
                    self.update_password_secret_spice()
                if hasattr(self, "option6_secret_password_spice"):
                    self.option6_secret_password_spice.setText(str(advanced.get("password_secret", {}).get("value", "")))
                if hasattr(self, "option7_disable_copy_paste_spice"):
                    self.option7_disable_copy_paste_spice.setChecked(bool(advanced.get("disable_copy_paste", "False")) == "True")
                if hasattr(self, "option8_agent_mouse_spice"):
                    self.option8_agent_mouse_spice.setChecked(bool(advanced.get("agent_mouse", "False")) == "True")
                # X509 options
                x509_options = advanced.get("x509", {})
                if x509_options.get("enable"):
                    if hasattr(self, "CB_option1_x509_dir"):
                        self.CB_option1_x509_dir.setChecked(bool(x509_options.get("x509_dir", {}).get("enable", "False")) == "True")
                        self.update_x509_dir()
                    if hasattr(self, "option1_x509_dir"):
                        self.option1_x509_dir.setText(str(x509_options.get("x509_dir", {}).get("value", "")))
                    if hasattr(self, "CB_option2_x509_key_file"):
                        self.CB_option2_x509_key_file.setChecked(bool(x509_options.get("x509_key_file", {}).get("enable", "False")) == "True")
                        self.update_x509_key_file()
                    if hasattr(self,"option2_x509_key_file"):
                        self.option2_x509_key_file.setText(str(x509_options.get("x509_key_file", {}).get("value", "")))
                    if hasattr(self, "CB_option3_x509_key_password"):
                        self.CB_option3_x509_key_password.setChecked(bool(x509_options.get("x509_key_password",{}).get("enable", "False")) == "True")
                        self.update_x509_key_password()
                    if hasattr(self, "option3_x509_key_password"):
                        self.option3_x509_key_password.setText(str(x509_options.get("x509_key_password", {}).get("value", "")))
                    if hasattr(self, "CB_option4_x509_cert_file"):
                        self.CB_option4_x509_cert_file.setChecked(bool(x509_options.get("x509_cert_file",{}).get("enable", "False")) == "True")
                        self.update_x509_cert_file()
                    if hasattr(self, "option4_x509_cert_file"):
                        self.option4_x509_cert_file.setText(str(x509_options.get("x509_cert_file", {}).get("value", "")))
                    if hasattr(self, "CB_option6_x509_cacert_file"):
                        self.CB_option6_x509_cacert_file.setChecked(bool(x509_options.get("x509_cacert_file",{}).get("enable", "False")) == "True")
                        self.update_x509_cacert_file()
                    if hasattr(self, "option6_x509_cacert_file"):
                        self.option6_x509_cacert_file.setText(str(x509_options.get("x509_cacert_file", {}).get("value", "")))
                    if hasattr(self, "CB_option7_x509_dh_key_file"):
                        self.CB_option7_x509_dh_key_file.setChecked(bool(x509_options.get("x509_dh_key_file",{}).get("enable", "False")) == "True")
                        self.update_x509_dh_key_file()
                    if hasattr(self, "option7_x509_dh_key_file"):
                        self.option7_x509_dh_key_file.setText(str(x509_options.get("x509_dh_key_file", {}).get("value", "")))
                # Address option
                if hasattr(self, "CB_option6_addr_spice"):
                    self.CB_option6_addr_spice.setChecked(bool(advanced.get("addr", {}).get("enable", "False")) == "True")
                    self.update_addr_spice()
                if hasattr(self, "option6_addr_spice"):
                    self.option6_addr_spice.setText(str(advanced.get("addr", {}).get("value", "")))
                # Unix socket
                if hasattr(self, "option7_unix"):
                    self.option7_unix.setChecked(bool(advanced.get("unix", "False")) == "True")
                # TLS Ciphers
                if hasattr(self, "option8_CB_tls_cipher"):
                    self.option8_CB_tls_cipher.setChecked(bool(advanced.get("tls_ciphers", {}).get("enable", "False")) == "True")
                    self.update_tls_cipher()
                if hasattr(self, "option8_tls_cipher"):
                    self.option8_tls_cipher.setText(str(advanced.get("tls_ciphers", {}).get("value", "")))
                # TLS Channel
                if hasattr(self, "CB_option9_tls_channel"):
                    self.CB_option9_tls_channel.setChecked(bool(advanced.get("tls_channel", {}).get("enable", "False")) == "True")
                    self.update_tls_channel()
                if hasattr(self, "option9_tls_channel"):
                    self.option9_tls_channel.setCurrentText(str(advanced.get("tls_channel", {}).get("value", "main")))
                # Plaintext Channel
                if hasattr(self, "CB_option10_plaintext_channel"):
                    self.CB_option10_plaintext_channel.setChecked(bool(advanced.get("plaintext_channel", {}).get("enable", "False")) == "True")
                    self.update_plaintext_channel()
                if hasattr(self, "option10_plaintext_channel"):
                    self.option10_plaintext_channel.setCurrentText(str(advanced.get("plaintext_channel", {}).get("value", "main")))
                # SASL
                if hasattr(self, "option11_sasl"):
                    self.option11_sasl.setChecked(bool(advanced.get("sasl", "False")) == "True")
                # Image Compression
                if hasattr(self, "option12_CB_image_compression"):
                    self.option12_CB_image_compression.setChecked(bool(advanced.get("image_compression", {}).get("enable", "False")) == "True")
                    self.update_image_compression()
                if hasattr(self, "option12_image_compression"):
                    self.option12_image_compression.setCurrentText(str(advanced.get("image_compression", {}).get("value", "auto_glz")))
                # JPEG WAN Compression
                if hasattr(self, "option13_CB_jpeg_wan_compression"):
                    self.option13_CB_jpeg_wan_compression.setChecked(bool(advanced.get("jpeg_wan_compression", {}).get("enable", "False")) == "True")
                    self.update_jpeg_wan_compression()
                if hasattr(self, "option13_jpeg_wan_compression"):
                    self.option13_jpeg_wan_compression.setCurrentText(str(advanced.get("jpeg_wan_compression", {}).get("value", "auto")))
                # ZLIB/GLZ WAN Compression
                if hasattr(self, "option14_CB_zlib_glz_wan_compression"):
                    self.option14_CB_zlib_glz_wan_compression.setChecked(bool(advanced.get("zlib_glz_wan_compression", {}).get("enable", "False")) == "True")
                    self.update_zlib_glz_wan_compression()
                if hasattr(self, "option14_zlib_glz_wan_compression"):
                    self.option14_zlib_glz_wan_compression.setCurrentText(str(advanced.get("zlib_glz_wan_compression", {}).get("value", "auto")))
                # Streaming Video
                if hasattr(self, "option15_CB_streaming_video"):
                    self.option15_CB_streaming_video.setChecked(bool(advanced.get("streaming_video", {}).get("enable", "False")) == "True")
                    self.update_streaming_video()
                if hasattr(self, "option15_streaming_video"):
                    self.option15_streaming_video.setCurrentText(str(advanced.get("streaming_video", {}).get("value", "off")))
                # Agent File Transfer
                if hasattr(self, "option16_disable_agent_file_xfer"):
                    self.option16_disable_agent_file_xfer.setChecked(bool(advanced.get("disable_agent_file_xfer", "False")) == "True")
                # Playback Compression
                if hasattr(self, "option17_playback_compression"):
                    self.option17_playback_compression.setChecked(bool(advanced.get("playback_compression", "False")) == "True")
                # Seamless Migration
                if hasattr(self, "option18_seamless_migration"):
                    self.option18_seamless_migration.setChecked(bool(advanced.get("seamless_migration", "False")) == "True")
                # Video Codec
                if hasattr(self, "CB_option19_video_codec"):
                    self.CB_option19_video_codec.setChecked(bool(advanced.get("video_codec", {}).get("enable", "False")) == "True")
                    self.update_video_codec()
                if hasattr(self, "option19_video_codec"):
                    self.option19_video_codec.setText(str(advanced.get("video_codec", {}).get("value", "")))
                # Max Refresh Rate
                if hasattr(self, "CB_option20_max_refresh_rate"):
                    self.CB_option20_max_refresh_rate.setChecked(bool(advanced.get("max_refresh_rate", {}).get("enable", "False")) == "True")
                    self.update_max_refresh_rate()
                if hasattr(self, "option20_max_refresh_rate"):
                    self.option20_max_refresh_rate.setValue(int(advanced.get("max_refresh_rate", {}).get("value", "100")))
                # GL
                if hasattr(self, "option21_gl"):
                    self.option21_gl.setChecked(bool(advanced.get("gl", "False")) == "True")
                # Render Node
                if hasattr(self, "CB_option22_render_node"):
                    self.CB_option22_render_node.setChecked(bool(advanced.get("rendernode", {}).get("enable", "False")) == "True")
                    self.update_render_node()
                if hasattr(self, "option22_render_node"):
                    self.option22_render_node.setText(str(advanced.get("rendernode", {}).get("value", "")))
                    self.update_x509_cert_file()
        except Exception:
            pass

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
            self.netad_mode.blockSignals(True)
            self.enable_netad.blockSignals(True)
            
            
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
                self.netad_mode.blockSignals(False)
                self.enable_netad.blockSignals(False)

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
        WDD_cfg = cfg.get('watchdog', '')
        if WDD_cfg:
            if self.WDD.findText(WDD_cfg) == -1:
                self.WDD.addItem(WDD_cfg)
            self.WDD.setCurrentText(WDD_cfg)
        Checkbox_watchdog = cfg.get('checkbox_watchdog','')
        if Checkbox_watchdog:
            self.Checkbox_enable_watchdog_device.setChecked(Checkbox_watchdog)

        #nographics
        self.CB_NGG.setChecked(cfg.get('nographics', False))

        # i386 advanced options
        self.win2k_hack.setChecked(cfg.get('win2k-hack', False))
        self.no_fd_bootcheck.setChecked(cfg.get("no_fd_bootcheck", False))

        # keyboardlayout
        self.keyboardlayoutcheckbox.setChecked(cfg.get('klc', False))
        self.keyboardlayoutlineedit.setEnabled(cfg.get("klc", False))
        self.keyboardlayoutlineedit.setText(cfg.get("keyboard_layout", "")) if cfg.get("keyboard_layout", "None") == "None" else self.keyboardlayoutlineedit.setText("")

        # multi options
        self.moc_list.clear()
        self.load_snapshot_moc()

        # edid
        edid_cfg = cfg.get('edid-vga', {})
        self.enable_edid_path.setChecked(cfg.get('edid-path-vga', False))
        self.enable_edid.setChecked(cfg.get('edid-vga-check', False))
        self.xres.setValue(edid_cfg.get('xres', 1920))
        self.yres.setValue(edid_cfg.get('yres', 1080))
        self.max_xres.setValue(edid_cfg.get('max_xres', 1920))
        self.max_yres.setValue(edid_cfg.get('max_yres', 1080))
        self.refresh_hz.setValue(edid_cfg.get('refresh-hz', 60))
        self.srceen_raw_width.setValue(edid_cfg.get('srw', 1920))
        self.srceen_raw_height.setValue(edid_cfg.get('srh', 1080))
        self.lineedit_edid_path.setText(edid_cfg.get('path', ''))
        self.edid_path()

        # edid menu
        self.em_comboBox.clear()
        with open(get_config_path(), "r", encoding='utf-8') as f:
            data: dict[str, any] = json.load(f)
        for i in data.keys():
            for j in data[i].get("name"):
                self.em_comboBox.addItem(j)
        self.set_current_info_edid()

        # netad
        self.load_snapshot_netad(cfg)

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
        self.apply_config_display_options(cfg)
        self.apply_spice_option(cfg)
        # nếu bạn nhìn thấy dòng này, chúng mừng, cho việc ngồi rẵng lướt 4628 dòng code của tôi :)

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

    def rename_moc_option(self, item):
        old_name = item.data(Qt.UserRole)
        new_name = item.text().strip()

        # Neu old_name chua duoc khoi tao trong UserRole
        if old_name is None:
            old_name = ""

        # Truong hop 1: Ten khong thay doi
        if old_name == new_name:
            return

        # Truong hop 2: Ten moi bi rong
        if not new_name:
            self.moc_list.blockSignals(True)
            item.setText(old_name)
            self.moc_list.blockSignals(False)
            return

        # Truong hop 3: Ten moi da ton tai trong danh sach
        for i in range(self.moc_list.count()):
            other_item = self.moc_list.item(i)
            if other_item is not item and other_item.text().strip() == new_name:
                QMessageBox.critical(self, "Lỗi", f"Tên '{new_name}' đã tồn tại!")
                self.moc_list.blockSignals(True)
                item.setText(old_name)
                self.moc_list.blockSignals(False)
                return

        # Truong hop 4: Cap nhat ten moi vao file config
        try:
            cfg_path = get_config_path()
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            config = data.get("multi_options", {})
            if old_name in config:
                config[new_name] = config.pop(old_name)
            else:
                config[new_name] = {}
            data["multi_options"] = config

            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self.save_snapshot()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật cấu hình: {e}")
            self.moc_list.blockSignals(True)
            item.setText(old_name)
            self.moc_list.blockSignals(False)
            return

        self.moc_list.blockSignals(True)
        item.setText(new_name)
        item.setData(Qt.UserRole, new_name)
        self.moc_list.blockSignals(False)

    def check_moc(self):
        if self.moc_list.count() > 0:
            return True
        else:
            return False

    def load_snapshot_moc(self):
        try:
            with open(get_config_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
                config = data.get("multi_options", {})
            for key in config:
                item = QListWidgetItem(key)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setData(Qt.UserRole, key)
                self.moc_list.addItem(item)
        except Exception:
            pass

    def open_moc_dialog(self):
        if not hasattr(self, 'moc_dialog') or not self.moc_dialog.isVisible():
            self.moc_dialog = multi_option_call(self)
            self.moc_dialog.closed_signal.connect(self.on_moc_closed)
            self.moc_reoption_signal.connect(self.moc_dialog.on_reoption)
            self.moc_dialog.show()
        else:
            self.moc_dialog.raise_()
            self.moc_dialog.activateWindow()

    def on_btn_moc_reoption_clicked(self):
        current_item = self.moc_list.currentItem()
        selected_name = current_item.text().strip() if current_item else ""
        self.open_moc_dialog()
        self.moc_reoption_signal.emit(selected_name)

    def delete_moc_option(self):
        current_row = self.moc_list.currentRow()
        if current_row >= 0:
            current_item = self.moc_list.takeItem(current_row)
            with open(get_config_path(), "r", encoding='utf-8') as f:
                data = json.load(f)
                config = data["multi_options"]
            key = current_item.data(Qt.UserRole)
            del config[key]
            with open(get_config_path(), "w", encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.save_snapshot()
            del current_item, config, data, key

    def on_moc_closed(self):
        # cái hàm thực thi các dòng lệnh sau khi multi options call đóng
        with open(get_config_path(), "r", encoding='utf-8') as f:
            data = json.load(f)
            config = data["multi_options"]
        self.moc_list.clear()
        # nevermind về việc phải xử lí mỗi khi moc nó đống :)
        for key in config:
            item = QListWidgetItem(key)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setData(Qt.UserRole, key)
            self.moc_list.addItem(item)

    def on_edid_closed(self):
        def count(cfg: dict = {}):
            a: int = 0
            for i in cfg:
                a += 1
            return a
        with open(get_config_path(), "r", encoding='utf-8') as f:
            data = json.load(f)
            data_edid = data.get("qemu-edid", {})
            count = count(data_edid)
        self.em_comboBox.clear()
        for key in data_edid:
            self.em_comboBox.addItem(data_edid[key].get("name") or key)
        self.em_comboBox.setCurrentIndex(max(0, count - 1))
        self.set_current_info_edid()
    
    def set_current_info_edid(self):
        #ready stage
        with open(get_config_path(), "r", encoding='utf-8') as f:
            data = json.load(f)
            data_edid: dict[str, any] = data.get("qemu-edid", {})
        current_data: dict = data_edid.get(f"EDID-{self.em_comboBox.currentIndex()}")
        #clean Vlayout_info
        for i in reversed(range(self.Vlayout_info.count())):
            self.Vlayout_info.itemAt(i).widget().deleteLater()
        #add info
        self.Vlayout_info.addWidget(QLabel(f"Tên: {self.em_comboBox.currentText()}"))
        self.Vlayout_info.addWidget(QLabel(f"Vị trí file: {current_data.get("located", "unknown")}"))
        self.Vlayout_info.addWidget(QLabel(f"vendor ID: {current_data.get("vendor", "NON")}"))
        self.Vlayout_info.addWidget(QLabel(f"serial: {current_data.get("serial")}"))
        self.Vlayout_info.addWidget(QLabel(f"dpi: {current_data.get("dpi")}"))
        self.Vlayout_info.addWidget(QLabel(f"xres: {current_data.get("xres")}"))
        self.Vlayout_info.addWidget(QLabel(f"yres: {current_data.get("yres")}"))
        self.Vlayout_info.addWidget(QLabel(f"max xres: {current_data.get("max_xres")}"))
        self.Vlayout_info.addWidget(QLabel(f"max yres: {current_data.get("max_yres")}"))

    def delete_edid(self):
        with open(get_config_path(), "r", encoding='utf-8') as f:
            data = json.load(f)
            data_edid: dict[str, any] = data.get("qemu-edid", {})
        current_index = self.em_comboBox.currentIndex()
        current_data: dict = data_edid.get(f"EDID-{current_index}")
        current_name = self.em_comboBox.currentText()
        if current_data is None:
            return
        try:
            os.remove(current_data.get("located"))
        except Exception:
            pass
        del data_edid[f"EDID-{current_index}"]
        with open(get_config_path(), "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.save_snapshot()
        self.on_edid_close()
        QMessageBox.information(self, "qemu-edid", f"Xoá thành công file {current_name}.bin")
        del current_name

    def open_edid_dialog(self):
        if not hasattr(self, 'edid_dialog') or not self.edid_dialog.isVisible():
            self.edid_dialog = Edid_dialog(self)
            self.edid_dialog.closed_signal.connect(self.on_edid_closed)
            self.edid_dialog.show()
        else:
            self.edid_dialog.raise_()
            self.edid_dialog.activateWindow()
    
    def import_edid(self):
        file, _ = QFileDialog.getOpenFileName(None, "chọn file", "", "Image File (*.bin) ;; all file (*)")
        data = self.get_data_Edid(file)
        if data is None:
            return
        with open(get_config_path(), "r", encoding='utf-8') as f:
            data_config = json.load(f)
            data_edid = data_config.get("qemu-edid", {})
        new_index = len(data_edid)
        new_name = f"EDID-{new_index}"
        data_edid[new_name] = data
        data_config["qemu-edid"] = data_edid
        with open(get_config_path(), "w", encoding='utf-8') as f:
            json.dump(data_config, f, ensure_ascii=False, indent=4)
        self.save_snapshot()
        self.on_edid_close()
        QMessageBox.information(self, "qemu-edid", f"Import thành công file {Path(file).name}")
        del data_config, data_edid, new_index, new_name
    
    def get_data_Edid(self, input: str):
        with open(input, "rb") as f:
            data = f.read()
        if len(data) < 128:
            QMessageBox.critical(self, "lỗi EDID import", f"File {Path(input).name} quá ngắn")
            return None
        header = data[:8]
        if header != b'\x00\xff\xff\xff\xff\xff\xff\x00':
            QMessageBox.critical(self, "lỗi EDID import", f"File {Path(input).name} không phải là EDID")
            return None
        vendor_raw = struct.unpack(">H", data[8:10])[0]
        char1 = chr(((vendor_raw >> 10) & 0x1F) + 64)
        char2 = chr(((vendor_raw >> 5) & 0x1F) + 64)
        char3 = chr((vendor_raw & 0x1F) + 64)
        vendor_id = f"{char1}{char2}{char3}"
        
        pixel_clock = struct.unpack("<H", data[54:56])[0]
        xres, yres = "Unknown", "Unknown"
        if pixel_clock > 0:
            # Width in pixels: Byte 56 + 4 bits cao của Byte 58
            h_active = data[56] + ((data[58] >> 4) << 8)
            # Height in pixels: Byte 59 + 4 bits cao của Byte 61
            v_active = data[59] + ((data[61] >> 4) << 8)
            xres = str(h_active)
            yres = str(v_active)
        
        monitor_name = "Generic EDID"
        for offset in (54, 72, 90, 108):
            # Check block header cho Display Name (00 00 00 FC)
            if data[offset:offset+4] == b'\x00\x00\x00\xfc':
            # Text nằm ở 13 bytes tiếp theo
                name_bytes = data[offset+5 : offset+18]
                monitor_name = name_bytes.decode('ascii', errors='ignore').split('\n')[0].strip()
                break
        
        w_cm = data[21]
        h_cm = data[22]
        dpi = "N/A"
        if isinstance(xres, int) and w_cm > 0:
            w_inches = w_cm / 2.54
            dpi = round(xres / w_inches)
        
        # 3. Max Resolution (Standard Timing - Byte 38..53)
        max_xres = max_yres = "Unknown"
        max_x_val = 0
       
        for i in range(38, 54, 2):
            b1, b2 = data[i], data[i+1]
            if b1 != 0x01 or b2 != 0x01: # Unused slot check
                cur_x = (b1 + 31) * 8
                aspect_ratio = (b2 >> 6) & 0x03
                
                # Tính Y dựa trên Aspect Ratio
                if aspect_ratio == 0: cur_y = int(cur_x * 10 / 16)   # 16:10
                elif aspect_ratio == 1: cur_y = int(cur_x * 3 / 4)   # 4:3
                elif aspect_ratio == 2: cur_y = int(cur_x * 4 / 5)   # 5:4
                else: cur_y = int(cur_x * 9 / 16)                   # 16:9

                if cur_x > max_x_val:
                    max_x_val = cur_x
                    max_xres, max_yres = cur_x, cur_y

        # Nếu không tìm thấy Standard Timing, lấy Max = Preferred
        if max_xres == "Unknown":
            max_xres, max_yres = xres, yres

        serial = "N/A"
        
        for offset in (54, 72, 90, 108):
            header = data[offset:offset+4]
            # Serial Number (0xFF)
            if header == b'\x00\x00\x00\xff':
                serial = data[offset+5:offset+18].decode('ascii', errors='ignore').split('\n')[0].strip()
        
        config = {
            "name": monitor_name,
            "vendor": vendor_id,
            "xres": xres,
            "yres": yres,
            "dpi": dpi,
            "max_xres": max_xres,
            "max_yres": max_yres,
            "serial": serial
        }
        return config

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
        data["config"] = self.get_current_config()
        with open(get_config_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        json_path = get_config_path()
        if (not self.CB_option1_port_spice.isChecked() and not self.CB_option2_tls_port_spice.isChecked()) and self.CB_Spice.isChecked():
            QMessageBox.warning(self, "lỗi khi khởi động QEMU", "Spice option bắt buộc phải có một trong hai option là port hoặc tls port")
            return
        if self.id_netad.text() == "":
            QMessageBox.critical(self, "Lỗi", "Vui lòng nhập id netad")
            return
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
                                dt = dt.strptime(d, "%Y%m%d%H%M%S")
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
        if hasattr(self, 'moc_dialog') and self.moc_dialog is not None:
            self.moc_dialog.close()
        if hasattr(self, 'log_viewer_dialog') and self.log_viewer_dialog is not None:
            self.log_viewer_dialog.close()
        if hasattr(self, "edid_dialog") and self.edid_dialog is not None:
            self.edid_dialog.close()
        load_config.kill_all_daemons(get_config_path())
        event.accept()

class DL(QDialog):
    def __init__(self):
        super().__init__()
        self.disk_created_path = None
        self.setWindowTitle("Trình quản lý ổ đĩa")
        self.resize(600, 600)
        self.mode_select = QComboBox()
        self.mode_select.addItems(["New", "Open", "Delete", "Resize"])
        self.stack = QStackedWidget()
        self.new_widget = self.create_new_widget()
        self.open_widget = self.create_open_widget()
        self.delete_widget = self.create_delete_widget()
        self.resize_widget = self.create_resize_widget()
        self.stack.addWidget(self.new_widget)
        self.stack.addWidget(self.open_widget)
        self.stack.addWidget(self.delete_widget)
        self.stack.addWidget(self.resize_widget)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Chọn chế độ ổ đĩa:"))
        layout.addWidget(self.mode_select)
        layout.addWidget(self.stack)
        self.mode_select.currentIndexChanged.connect(self.stack.setCurrentIndex)
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

    def create_resize_widget(self):
        resize_w = QWidget()
        layout = QVBoxLayout(resize_w)
        self.format_checkbox = QCheckBox()
        self.format_checkbox.setText("bật chọn format option cụ thể")
        self.format_checkbox.setChecked(False)
        self.format_comboBox = QComboBox()
        self.format_comboBox.addItems(QEMU_FORMAT_OPTIONS)
        self.format_comboBox.setEnabled(False)
        self.format_checkbox.toggled.connect(lambda: self.format_comboBox.setEnabled(self.format_checkbox.isChecked()))
        self.image_opts_check = QCheckBox()
        self.image_opts_check.setText("bật tùy chọn resize nâng cao")
        self.image_opts_check.setChecked(False)
        self.image_opts_lineEdit = QLineEdit()
        self.image_opts_lineEdit.setPlaceholderText("Các options nâng cao")
        self.image_opts_lineEdit.setEnabled(False)
        self.image_opts_check.toggled.connect(lambda: self.image_opts_lineEdit.setEnabled(self.image_opts_check.isChecked()))
        self.shrink_checkbox = QCheckBox()
        self.shrink_checkbox.setText("bật tùy chọn shrink")
        self.shrink_checkbox.setChecked(False)
        self.preallocated_checkbox = QCheckBox()
        self.preallocated_checkbox.setText("bật tùy chọn preallocated")
        self.preallocated_checkbox.setChecked(False)
        self.preallocated_combobox = QComboBox()
        self.preallocated_combobox.addItems(["off", "metadata", "falloc", "full"])
        self.preallocated_combobox.setEnabled(False)
        self.preallocated_checkbox.toggled.connect(lambda: self.preallocated_combobox.setEnabled(self.preallocated_checkbox.isChecked()))
        self.quiet_mod_resize = QCheckBox()
        self.quiet_mod_resize.setText("bật tùy chọn quiet")
        self.quiet_mod_resize.setChecked(False)
        self.file_path_mod_resize = QComboBox()
        self.file_path_mod_resize.addItems(load_disk_path_json_file())
        self.size_resize_mode = QComboBox()
        self.size_resize_mode.addItems(["+", "-"])
        self.size_resize_value = QComboBox()
        self.size_resize_value.addItems(QEMU_DISK_SIZE_FORMAT)
        self.size_resize = QSpinBox()
        self.size_resize.setRange(1, 2147483647)
        self.size_resize.setSuffix(self.size_resize_value.currentText())
        self.size_resize_value.currentIndexChanged.connect(lambda: self.size_resize.setSuffix(self.size_resize_value.currentText()))
        self.btn_run_resize = QPushButton()
        self.btn_run_resize.setText("resize ổ đĩa")
        self.btn_run_resize.clicked.connect(self.run_resize)
        layout.addWidget(self.format_checkbox)
        layout.addWidget(self.format_comboBox)
        layout.addWidget(self.image_opts_check)
        layout.addWidget(self.image_opts_lineEdit)
        layout.addWidget(self.shrink_checkbox)
        layout.addWidget(self.preallocated_checkbox)
        layout.addWidget(self.preallocated_combobox)
        layout.addWidget(self.quiet_mod_resize)
        layout.addWidget(QLabel("địa chỉ file ổ đĩa:"))
        layout.addWidget(self.file_path_mod_resize)
        layout.addWidget(QLabel("kích thước ổ đĩa (thêm hoặc bớt): "))
        layout.addWidget(self.size_resize_mode)
        layout.addWidget(self.size_resize)
        layout.addWidget(self.btn_run_resize)
        return resize_w

    def format_combox_update(self):
        self.format_comboBox.setEnabled(self.format_checkbox.isChecked())

    def run_resize(self):
        disk_path = self.file_path_mod_resize.text()
        path = Path(disk_path).resolve()
        mode = self.size_resize_mode.currentText()
        value = self.size_resize.value()
        format = self.size_resize_value.currentText()
        qemu_img_path = find_qemu_img()
        cmd_options = []
        if self.format_checkbox.isChecked():
            cmd_options.append(f"-f {self.format_comboBox.currentText()}")
        if self.image_opts_check.isChecked():
            cmd_options.append(f"--image-opts {self.image_opts_lineEdit.text()}")
        if self.shrink_checkbox.isChecked():
            cmd_options.append(f"--shrink")
        if self.preallocated_checkbox.isChecked():
            cmd_options.append(f"--preallocation={self.preallocated_combobox.currentText()}")
        if self.quiet_mod_resize.isChecked():
            cmd_options.append(f"--quiet")
        if qemu_img_path is None:
            return QMessageBox.information(self, "Thông báo", "Không tìm thấy qemu-img!")
        with open(get_config_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
        disk_path_json = data["disks"].keys()
        if disk_path not in disk_path_json and not path.exists() and not str(path) in disk_path:
            return QMessageBox.information(self, "Thông báo", "Không tìm thấy file ổ đĩa!")
        if not can_write(path):
            return QMessageBox.information(self, "Thông báo", "Không thể ghi vào file ổ đĩa!")
        if not disk_path or not path:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đủ tên và thư mục lưu.")
            return
        if re.match(r'^[A-Za-z]:$', disk_path):
            disk_path = disk_path + os.sep
        disk_path = os.path.abspath(disk_path)
        try:
            program_drive = Path(__file__).resolve().drive
            target_drive = Path(disk_path).resolve().drive
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
            match format:
                case "B":
                    form = 'b'
                case "KB":
                    form = 'K'
                case "MB":
                    form = 'M'
                case "GB":
                    form = 'G'
                case "TB":
                    form = 'T'
                case _:
                    return QMessageBox.information(self, "Thông báo", "Định dạng ổ đĩa không hợp lệ!")
            cmd = [qemu_img_path, "resize", cmd_options, str(disk_path), f"{mode}{value}{form}"]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                QMessageBox.information(self, "Thông báo", "Resize ổ đĩa thành công!")
            except subprocess.CalledProcessError as e:
                return QMessageBox.critical(self, "Lỗi", f"Lỗi khi resize ổ đĩa: {e}")
            except Exception as e:
                return QMessageBox.critical(self, "Lỗi", f"Lỗi khi resize ổ đĩa: {e}")
    def create_new_widget(self):
        s = QScrollArea()
        s.setWidgetResizable(True)
        w = QWidget()
        layout = QVBoxLayout(w)
        self.disk_name = QLineEdit()
        self.disk_name.setPlaceholderText("Tên file ổ đĩa")
        self.disk_format = QComboBox()
        self.disk_format.addItems(QEMU_FORMAT_OPTIONS)
        self.disk_size = QSpinBox()
        self.disk_size.setRange(1, 2147483647)
        self.disk_size.setValue(1024)
        self.disk_size_value = QComboBox()
        self.disk_size_value.addItems(["MB", "GB", "TB", "KB", "B"])
        self.update_size_disk_format()
        self.disk_size_value.currentIndexChanged.connect(self.update_size_disk_format)
        self.save_folder = QLineEdit()
        self.save_folder.setPlaceholderText("Thư mục lưu ổ đĩa")
        self.btn_choose_folder = QPushButton("Chọn thư mục")
        self.btn_choose_folder.clicked.connect(self.choose_folder)
        self.btn_create = QPushButton("Tạo ổ đĩa")
        self.btn_create.clicked.connect(self.create_disk)
        self.format_disk = QComboBox()
        self.format_disk.setEnabled(False)
        self.custom_format_disks = QLineEdit()
        self.custom_format_disks.setEnabled(False)
        self.custom_format_disks.setPlaceholderText("định dạng file custom")
        self.format_disk.currentIndexChanged.connect(self.custom_format_disk)
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.save_folder)
        folder_layout.addWidget(self.btn_choose_folder)
        self.disk_format.currentIndexChanged.connect(self.format_disk_update)
        self.format_disk.currentTextChanged.connect(self.custom_format_disk)
        self.quiet_mod = QCheckBox("bật chế độ im lặng")
        layout.addWidget(QLabel("Tên file ổ đĩa:"))
        layout.addWidget(self.disk_name)
        layout.addWidget(QLabel("Định dạng ổ đĩa:"))
        layout.addWidget(self.disk_format)
        layout.addWidget(QLabel("Dung lượng ổ đĩa:"))
        layout.addWidget(self.disk_size_value)
        layout.addWidget(self.disk_size)
        layout.addWidget(QLabel("Thư mục lưu:"))
        layout.addLayout(folder_layout)
        layout.addWidget(QLabel("Định dạng đuôi file custom:"))
        layout.addWidget(self.format_disk)
        layout.addWidget(self.custom_format_disks)
        layout.addWidget(self.quiet_mod)
        layout.addWidget(self.btn_create)
        s.setWidget(w)
        return s
    def custom_format_disk(self):
        if self.format_disk.currentText() == "custom":
            self.custom_format_disks.setEnabled(True)
            self.custom_format_disks.setText(".")
        else:
            self.custom_format_disks.setEnabled(False)
            self.custom_format_disks.setText("")
    def format_disk_update(self):
        if self.disk_format.currentText() == "qcow2":
            self.format_disk.setEnabled(True)
            self.format_disk.clear()
            self.format_disk.addItems([".qcow2", ".img"])
        elif self.disk_format.currentText() == "raw":
            self.format_disk.setEnabled(True)
            self.format_disk.clear()
            self.format_disk.addItems([".raw", ".img"])
        elif self.disk_format.currentText() == "parallels":
            self.format_disk.setEnabled(True)
            self.format_disk.clear()
            self.format_disk.addItems(".pvm", ".hdd")
        elif self.disk_format.currentText() == "bochs":
            self.format_disk.setEnabled(True)
            self.format_disk.clear()
            self.format_disk.addItems([".img", ".bximage", "custom"])
        elif self.disk_format.currentText() == "file":
            self.format_disk.setEnabled(True)
            self.format_disk.clear()
            self.format_disk.addItems([".img", ".raw"])
        elif self.disk_format.currentText() == "luks":
            self.format_disk.setEnabled(True)
            self.format_disk.clear()
            self.format_disk.addItems([".img", ".luks", "custom"])
        else:
            self.format_disk.setEnabled(False)
            self.format_disk.clear()
    def get_suffix_file(self):
        if not self.disk_format.currentText() in ["qcow2", "raw", "parallels", "bochs", "file", "luks"]:
            form = self.disk_format.currentText()
            match form:
                case "qcow":
                    suffix = ".qcow"
                case "qed":
                    suffix = ".qed"
                case "vmdk":
                    suffix = ".vmdk"
                case "vdi":
                    suffix = ".vdi"
                case "vhdx":
                    suffix = ".vhdx"
                case "cloop":
                    suffix = ".cloop"
                case "dmg":
                    suffix = ".dmg"
        else:
            suffix = self.format_disk.currentText()
            if suffix == "custom":
                suffix = self.custom_format_disks.text()
        return suffix
    def create_open_widget(self):
        s = QScrollArea()
        s.setWidgetResizable(True)
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
        s.setWidget(w)
        return s

    def create_delete_widget(self):
        s = QScrollArea()
        s.setWidgetResizable(True)
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
        s.setWidget(w)
        return s

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu ổ đĩa")
        if folder:
            self.save_folder.setText(folder)

    def load_existing_disk(self):
        if self.disk_path.text():
            self.disk_created_path = self.disk_path.text()
            save_disk_path_json_file(None, self.disk_created_path)
            self.accept()

    def update_size_disk_format(self):
        self.disk_size.setSuffix(self.disk_size_value.currentText())

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
        size = self.disk_size.value()
        format_size = self.disk_size_value.currentText()
        fmt = self.disk_format.currentText()
        suf = self.get_suffix_file()
        
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
        ext = suf
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
        if format_size == "MB":
            fs = "M"
        elif format_size == "GB":
            fs = "G"
        elif format_size == "KB":
            fs = "K"
        elif format_size == "B":
            fs = "b"
        elif format_size == "TB":
            fs = "T"
        cmd = [qemu_img, "create", "-f", fmt, full_path, f"{size}{fs}"]
        if self.quiet_mod.isChecked():
            cmd.append("-q")
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
#the command:pyinstaller --onedir --noconfirm --icon="icon_VQEMU.ico" --add-data "load_config.py;." --add-data "qemu;qemu" --add-data "log_module.py;." --add-data "find_tools_module.py;." --add-data "qemu_advanced_module.py;." --add-data "qss_style.qss;." run.py
# 2025 Vncore lab (alias of Nguyễn Trường Lâm)
# thằng nào copy mà còn đổi tên thì làm tuất
