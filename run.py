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
from find_tools_module import *
from pathlib import Path
import sys, io
import threading
from qemu_advanced_module import *
import load_config

# VNcore lab 2025 (alias of Nguyễn Trường Lâm)

print("VNcore lab 2025 (alias of Nguyễn Trường Lâm)")

try:
    if sys.stdout and hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
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
    base_path = Path(__file__).resolve().parent
    return base_path / "config_VQEMU.json"

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
                border: none;
                border-radius: 8px;
                margin-top: 10px;
                background: #2c313c;
                font-weight: bold;
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
                padding: 4px;
                color: #e0e0e0;
            }
            QLabel {
                font-weight: bold;
            }
        """)
        self.is_loading = False
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500)  # Debounce 500ms
        self.save_timer.timeout.connect(self._perform_save_snapshot)
        self.init_tabs()
    
    def update_system_qemu(self):
        try:
            if self.AQEW.isChecked():
                self.K.clear()
                self.K.addItems(sorted(list(QEMU_SYSTEM_W.keys())))
            else:
                self.K.clear()
                self.K.addItems(sorted(list(QEMU_SYSTEMS.keys())))
        except:
                self.K.clear
                self.K.addItems([])

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
        vm_tab = QWidget()
        vm_layout = QVBoxLayout(vm_tab)
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
        self.A.addItems(["None","ac97","es1370","hda","sb16"])
        layout_vm.addWidget(self.A, 6, 1)
        self.group_vm = group_vm
        vm_layout.addWidget(group_vm)
        self.run = QPushButton("Khởi động máy ảo")
        vm_layout.addWidget(self.CCRQT)
        vm_layout.addWidget(self.run)
        self.addTab(vm_tab, "Máy ảo")


        self.daemon_storage_tab = QWidget()
        daemon_storage_layout = QVBoxLayout(self.daemon_storage_tab)
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
        with open(get_config_path(), 'r', encoding="utf-8") as f:
            data = json.load(f)
        listdisk = data["disks"].keys()
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
        layout_DT.addWidget(self.RHD, 6 , 0)
        self.CDPDS = QCheckBox("kill DS process")
        self.CDPDS.setChecked(False)
        self.CDPDS.setEnabled(False)
        mini_layout_1.addWidget(self.CDPDS)
        self.CDPDS2 = QComboBox()
        self.update_daemon_list_kill()
        self.CDPDS2.setEnabled(False)
        mini_layout_1.addWidget(self.CDPDS2)
        self.BCTDPDS = QPushButton("kill process")
        self.BCTDPDS.setEnabled(False)
        mini_layout_1.addWidget(self.BCTDPDS)
        layout_DT.addLayout(mini_layout_1, 7, 0)
        daemon_storage_layout.addWidget(group_DT)
        self.addTab(self.daemon_storage_tab, "Daemon storage")

        self.disk_tab = QWidget()
        disk_layout = QVBoxLayout(self.disk_tab)
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
        layout_disk.addWidget(self.CLD, 5, 0, 1, 2)
        disk_layout.addWidget(group_disk)
        self.addTab(self.disk_tab, "Ổ đĩa")
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

        self.boot_tab = QWidget()
        boot_layout = QVBoxLayout(self.boot_tab)
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
        layout_boot.addWidget(self.CBI, 0, 0)
        layout_boot.addWidget(self.LEI, 0, 1)
        layout_boot.addWidget(self.bi, 0, 2)
        layout_boot.addWidget(self.CFDA, 1, 0)
        layout_boot.addWidget(self.LEDA, 1, 1)
        layout_boot.addWidget(self.BDAD, 1, 2)
        layout_boot.addWidget(self.CFDB, 2, 0)
        layout_boot.addWidget(self.LEDB, 2, 1)
        layout_boot.addWidget(self.BDBD, 2, 2)
        layout_boot.addWidget(self.LEDC, 3, 1)
        layout_boot.addWidget(self.BDCD, 3, 2)
        layout_boot.addWidget(self.LEDD, 4, 1)
        layout_boot.addWidget(self.BDDD, 4, 2)
        layout_boot.addWidget(self.CFDC, 3, 0)
        layout_boot.addWidget(self.CFDD, 4, 0)
        boot_layout.addWidget(group_boot)
        self.addTab(self.boot_tab, "Khởi động")

        self.CBI.toggled.connect(self.update_iso_enable)
        self.update_iso_enable(self.CBI.isChecked())

        self.net_tab = QWidget()
        net_layout = QVBoxLayout(self.net_tab)
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

# ... (implicitly keeping intermediate lines, but replace_file_content needs distinct chunks or one contiguous block. Since these are far apart, I should use multi_replace or 2 calls. The prompt says "Do NOT make multiple parallel calls to this tool". I will use multi_replace_file_content instead.)
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
        self.addTab(self.net_tab, "Mạng")
        self.update_arch_dependent_widgets()

        adco_tab = QWidget()
        adco_layout = QVBoxLayout(adco_tab)
        group_adco = QGroupBox("cấu hình nâng cao")
        layout_adco = QGridLayout(group_adco)
        self.CAD = QCheckBox("Bật tùy chọn daemon storage")
        self.CAD.setChecked(False)
        layout_adco.addWidget(self.CAD, 0, 0)
        self.DHD = QComboBox()
        self.DHD.addItems(QEMU_IO_DAEMON_STORAGE)
        self.DHD.setEnabled(False)
        self.label2 = QLabel("IO daemon storage:")
        layout_adco.addWidget(self.label2, 1, 0)
        layout_adco.addWidget(self.DHD, 1, 1)
        self.DSNTR = QComboBox()
        with open(get_config_path(), 'r', encoding='utf-8') as f:
            config = json.load(f)
        list_key_DSTR = config['config_DS'].keys()
        self.DSNTR.addItems(list_key_DSTR)
        self.DSNTR.setEnabled(False)
        layout_adco.addWidget(QLabel("daemon để chạy:"), 2, 0)
        layout_adco.addWidget(self.DSNTR, 2, 1)
        adco_layout.addWidget(group_adco)
        
        adco_layout.addWidget(group_adco)
        self.addTab(adco_tab, "Cấu hình nâng cao")

        prof_tab = QWidget()
        prof_layout = QVBoxLayout(prof_tab)
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
        self.addTab(prof_tab, "Cấu hình")

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


        # Initialize UI state
        self.update_custom_command_ui(self.CCRQ.isChecked())
        
        self.load_snapshot()
        self.connect_snapshot_signals()
        self.update_disk_list()
        self.update_daemon_list()

    def connect_snapshot_signals(self):
        # Connect all relevant widgets to save_snapshot
        # VM Tab
        self.K.currentIndexChanged.connect(self.save_snapshot)
        self.CP.currentIndexChanged.connect(self.save_snapshot)
        self.SC.currentIndexChanged.connect(self.save_snapshot)
        self.RM.valueChanged.connect(self.save_snapshot)
        self.V.currentIndexChanged.connect(self.save_snapshot)
        self.A.currentIndexChanged.connect(self.save_snapshot)
        self.CCRQ.toggled.connect(self.save_snapshot)
        self.CCRQT.textChanged.connect(self.save_snapshot)
        self.AQEW.toggled.connect(self.save_snapshot)
        
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
        
        # Net Tab
        self.CN.toggled.connect(self.save_snapshot)
        self.LN.currentIndexChanged.connect(self.save_snapshot)
        self.KN.currentIndexChanged.connect(self.save_snapshot)
        self.CPF.toggled.connect(self.save_snapshot)
        self.PF.textChanged.connect(self.save_snapshot)

        #advanced tab
        self.CAD.toggled.connect(self.save_snapshot)
        self.DSNTR.currentIndexChanged.connect(self.save_snapshot)
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
        self.disk_tab.setEnabled(not checked)
        self.boot_tab.setEnabled(not checked)
        self.net_tab.setEnabled(not checked)
        self.daemon_storage_tab.setEnabled(not checked)

    def update_daemon_list(self):
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
                    "exe": exe_path,
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
                    "check_advanced_tab": self.CAD.isChecked()
                }
        return config

    def apply_config(self, cfg):
        self.is_loading = True
        try:
            return self._apply_config_internal(cfg)
        finally:
            self.is_loading = False

    def _apply_config_internal(self, cfg):
        # Custom Command
        enb_cmd = cfg.get('enb_command_qemu', False)
        self.CCRQ.setChecked(enb_cmd)
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
                path_DS = Path(__file__).resolve().parent / "qemu" / "qemu-storage-daemon.exe"
                # qemu-storage-daemon.exe is the standard name
                cmd_ds = f"{path_DS} --nbd-server addr.type=inet,addr.host=127.0.0.1,addr.port=1000{idds} --blockdev driver=file,node-name=d{idds},filename={disk_path} --export type=nbd,id=ex0,node-name=d{idds},writable=on"
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
            QMessageBox.information(self, "Info", f"Đã chạy daemon: {name_ds}")

    def click_kill_daemon(self):
        key = self.CDPDS2.currentText()
        if not key:
             return
        load_config.kill_daemon_storage_direct(get_config_path(), key)
        self.update_daemon_list_kill()
        QMessageBox.information(self, "Info", f"Đã kill daemon: {key}")
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
    create_json()
    app = QApplication(sys.argv)
    qg = QG()
    qg.show()
    sys.exit(app.exec_())
#the command:pyinstaller --onedir --noconfirm --add-data "load_config.py;." --add-data "qemu;qemu" --add-data "log_module.py;." --add-data "find_tools_module.py;." --add-data "qemu_advanced_module.py;." run.py
# 2025 Vncore lab (alias of Nguyễn Trường Lâm)
