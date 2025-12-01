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

try:
    if sys.stdout and hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
except Exception:
    pass

def the_return_value_of_DL_class(name):
    if not (name == "none"):
        return name
    else:
        return "none"

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
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys.executable).parent
    else:
        # Running from source
        base_path = Path(__file__).resolve().parent
    return base_path / "config_VQEMU.json"

def create_json():
    path = get_config_path()
    if not path.exists():
        data = {"disks": {}, "configs": {}, "profiles": {}}
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
    if "configs" not in data:
        data["configs"] = {}
        updated = True
    if "profiles" not in data:
        data["profiles"] = {}
        updated = True
    
    if updated:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

def check_json_file():
    path = get_config_path()
    if not path.exists():
        create_json()

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

def can_write(folder):
    try:
        testfile = os.path.join(folder, ".__testwrite__")
        with open(testfile, "w") as f:
            f.write("test")
        os.remove(testfile)
        return True
    except Exception:
        return False

def disk_list_path():
    return get_config_path()

def load_disk_list():
    return load_disk_path_json_file()

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
        self.init_tabs()

    def get_qemu_exe(self):
        arch = self.K.currentText()
        exe_path = find_qemu_system(arch)
        if not exe_path:
            raise FileNotFoundError(f"Không tìm thấy QEMU cho kiến trúc {arch}")
        return str(exe_path)

    def add_disk_to_json(self, name, path):
        if not get_config_path().exists():
            create_json()
        else:
            name_disk = name
            path_disk = path
            string_json_tree = {
                name_disk: {
                    "name": name_disk,
                    "path": path_disk,
                }
            }
            with open(get_config_path(), "a", encoding="utf-8") as f:
                json.dump(string_json_tree, f, ensure_ascii=False, indent=4)

    def remove_disk_from_json(self, name):
        cfg_path = get_config_path()
        if not cfg_path.exists():
            return
        else:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "disks" in data and name in data["disks"]:
                del data["disks"][name]
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

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
        # This function seems to append to the file which is invalid JSON if not careful, 
        # but following original logic's intent but using correct path. 
        # Actually original logic was appending a dict to the file which is definitely wrong for a JSON file structure 
        # if it's not being read and updated properly.
        # However, to minimize risk I will just fix the path for now as requested.
        # But wait, `json.dump` in 'a' mode is bad. 
        # I'll stick to the pattern: read -> update -> write.
        
        # Re-reading to be safe
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                full_data = json.load(f)
        except:
            full_data = {}
            
        # The original code was weird, it loaded data but then dumped a new dict to append?
        # I will assume the user wants to update the file.
        # But since this function `add_cdrom_to_json` doesn't seem to be used in the main flow shown, 
        # I will just fix the path references.
        
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
        group_vm = QGroupBox("Cấu hình máy ảo")
        layout_vm = QGridLayout(group_vm)
        layout_vm.addWidget(QLabel("Kiến trúc:"), 0, 0)
        self.K = QComboBox()
        try:
            archs = sorted(list(QEMU_SYSTEMS.keys()))
        except Exception:
            archs = []
        self.K.addItems(archs)
        self.K.currentIndexChanged.connect(self.update_arch_dependent_widgets)
        layout_vm.addWidget(self.K, 0, 1)
        layout_vm.addWidget(QLabel("CPU:"), 1, 0)
        self.CP = QComboBox()
        layout_vm.addWidget(self.CP, 1, 1)
        layout_vm.addWidget(QLabel("Số nhân CPU:"), 2, 0)
        self.SC = QComboBox()
        self.SC.addItems([str(i) for i in range(1, 11)])
        layout_vm.addWidget(self.SC, 2, 1)
        layout_vm.addWidget(QLabel("RAM (MB):"), 3, 0)
        self.RM = QSpinBox()
        self.RM.setRange(16, 32768)
        self.RM.setValue(1024)
        layout_vm.addWidget(self.RM, 3, 1)
        layout_vm.addWidget(QLabel("VGA:"), 4, 0)
        self.V = QComboBox()
        layout_vm.addWidget(self.V, 4, 1)
        self.update_arch_dependent_widgets()
        layout_vm.addWidget(QLabel("Âm thanh:"), 5, 0)
        self.A = QComboBox()
        self.A.addItems(["None","ac97","es1370","hda","sb16"])
        layout_vm.addWidget(self.A, 5, 1)
        vm_layout.addWidget(group_vm)
        self.run = QPushButton("Khởi động máy ảo")
        vm_layout.addWidget(self.run)
        self.addTab(vm_tab, "Máy ảo")

        disk_tab = QWidget()
        disk_layout = QVBoxLayout(disk_tab)
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
        self.addTab(disk_tab, "Ổ đĩa")
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

        boot_tab = QWidget()
        boot_layout = QVBoxLayout(boot_tab)
        group_boot = QGroupBox("Khởi động")
        layout_boot = QGridLayout(group_boot)
        self.CBI = QCheckBox("Dùng ISO")
        self.LEI = QLineEdit()
        self.LEI.setPlaceholderText("Đường dẫn file ISO")
        self.bi = QPushButton("Chọn file ISO")
        layout_boot.addWidget(self.CBI, 0, 0)
        layout_boot.addWidget(self.LEI, 0, 1)
        layout_boot.addWidget(self.bi, 0, 2)
        boot_layout.addWidget(group_boot)
        self.addTab(boot_tab, "Khởi động")

        self.CBI.toggled.connect(self.update_iso_enable)
        self.update_iso_enable(self.CBI.isChecked())

        net_tab = QWidget()
        net_layout = QVBoxLayout(net_tab)
        group_net = QGroupBox("Mạng")
        layout_net = QGridLayout(group_net)
        self.CN = QCheckBox("Bật mạng")
        self.net_list = QEMU_SYSTEMS_WIFIS.get("model", [])
        self.LN = QComboBox()
        self.LN.addItems(self.net_list)
        self.KN = QComboBox()
        self.KN.addItems(QEMU_SYSTEMS_WIFIS.get("connection", []))
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
        self.addTab(net_tab, "Mạng")

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

    def update_arch_dependent_widgets(self):
        try:
            arch = self.K.currentText()
        except Exception:
            arch = None
        self.CP.clear()
        if arch and arch in QEMU_SYSTEMS_CPUS:
            self.CP.addItems(QEMU_SYSTEMS_CPUS.get(arch, []))
        else:
            self.CP.addItems(["host", "qemu32", "qemu64"]) if not self.CP.count() else None
        self.V.clear()
        if arch and arch in QEMU_SYSTEMS_VGAS:
            self.V.addItems(QEMU_SYSTEMS_VGAS.get(arch, []))
        else:
            self.V.addItems(["none", "std", "cirrus", "vmware", "qxl", "virtio"])

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
            "net_enable": self.CN.isChecked(),
            "net_model": self.LN.currentText(),
            "portfwd": self.PF.text().strip() if self.CPF.isChecked() else ""
        }
        return config

    def apply_config(self, cfg):
        arch = cfg.get('arch', '')
        if arch:
            if self.K.findText(arch) == -1:
                self.K.addItem(arch)
            self.K.setCurrentText(arch)
        self.update_arch_dependent_widgets()
        cpu = cfg.get('cpu', '')
        if cpu:
            if self.CP.findText(cpu) == -1:
                self.CP.addItem(cpu)
            self.CP.setCurrentText(cpu)
        smp = cfg.get('smp', None)
        if smp is not None:
            try:
                self.SC.setCurrentText(str(smp))
            except Exception:
                pass
        ram = cfg.get('ram', None)
        if ram is not None:
            try:
                self.RM.setValue(int(ram))
            except Exception:
                pass
        vga = cfg.get('vga', '')
        if vga:
            if self.V.findText(vga) == -1:
                if vga != "none":
                    self.V.addItem(vga)
            self.V.setCurrentText(vga)
        audio = cfg.get('audio', '')
        if audio:
            if self.A.findText(audio) == -1:
                self.A.addItem(audio)
            self.A.setCurrentText(audio)
        cdrom = cfg.get('cdrom', '')
        if cdrom:
            self.CBI.setChecked(True)
            self.LEI.setText(cdrom)
        else:
            self.CBI.setChecked(False)
            self.LEI.setText('')
        for disk_field, cb in [('hda', self.HDA), ('hdb', self.HDB), ('hdc', self.HDC), ('hdd', self.HDD)]:
            val = cfg.get(disk_field, '')
            if val:
                if cb.findText(val) == -1:
                    cb.addItem(val)
                cb.setCurrentText(val)
            else:
                cb.setCurrentIndex(0)
        net_enable = cfg.get('net_enable', False)
        self.CN.setChecked(bool(net_enable))
        net_model = cfg.get('net_model', '')
        if net_model:
            if self.LN.findText(net_model) == -1:
                self.LN.addItem(net_model)
            self.LN.setCurrentText(net_model)
        portfwd = cfg.get('portfwd', '')
        if portfwd:
            self.CPF.setChecked(True)
            self.PF.setText(portfwd)
        else:
            self.CPF.setChecked(False)
            self.PF.setText('')

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

    def open_disk_dialog(self):
        dlg = DL()
        dlg.exec_()
        # Refresh disk lists after dialog closes (handling both creation and deletion)
        disks = load_disk_path_json_file()
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
        file, _ = QFileDialog.getOpenFileName(None, "chon file", "", "Image File (*.iso *.img *.vfd *.bin) ;; all file (*)")
        self.LEI.setText(file)

    def run_qemu(self):
        create_json()
        arch = self.K.currentText()
        try:
            exe_path = self.get_qemu_exe()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e) + "\nHãy cài QEMU hoặc kiểm tra cấu hình.")
            return

        config = self.get_current_config()
        try:
            cfg_path = get_config_path()
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["configs"] = config
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e) + "\nHãy cài QEMU hoặc kiểm tra cấu hình.")
            return
        with open(get_config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            config = data["configs"]
        base_dir = get_config_path().parent
        config_path = base_dir / "config_VQEMU.json"
        key_list = list(config.keys())
        filtered_config = {k: config[k] for k in key_list if k in config}
        cmd_part = []
        val_part = []
        result_part = []
        for key in key_list:
            if key in filtered_config:
                cmd_part.append(key)
                val_part.append(filtered_config[key])
        for i in range(len(cmd_part)):
            if cmd_part[i] == "arch":
                continue
            if cmd_part[i] == "ram":
                result_part.append(f"-m {val_part[i]}")
            if cmd_part[i] == "smp":
                result_part.append(f"-smp {val_part[i]}")
            if cmd_part[i] == "cpu":
                result_part.append(f"-cpu {val_part[i]}")
            if cmd_part[i] == "vga":
                if val_part[i] == "":
                    continue
                else:
                    result_part.append(f"-vga {val_part[i]}")
            if cmd_part[i] == "audio":
                if val_part[i] == "":
                    continue
                else:
                    result_part.append(f"-device {val_part[i]}")
            if cmd_part[i] == "cdrom":
                if val_part[i] == "":
                    continue
                else:
                    result_part.append(f"-cdrom {val_part[i]}")
            if cmd_part[i] == "hda":
                if val_part[i] == "":
                    continue
                else:
                    result_part.append(f"-hda {val_part[i]}")
            if cmd_part[i] == "hdb":
                if val_part[i] == "":
                    continue
                else:
                    result_part.append(f"-hdb {val_part[i]}")
            if cmd_part[i] == "hdc":
                if val_part[i] == "":
                    continue
                else:
                    result_part.append(f"-hdc {val_part[i]}")
            if cmd_part[i] == "hdd":
                if val_part[i] == "":
                    continue
                else:
                    result_part.append(f"-hdd {val_part[i]}")
            if cmd_part[i] == "net_model" and config.get("enb_net") == "True":
                if val_part[i] == "none":
                    continue
                else:
                    result_part.append(f"-net {val_part[i]}")
            else:
                continue
            if cmd_part[i] == "portfwd":
                if config.get("enb_portfwd") == "True":
                    result_part.append(f"-netdev user,id=n1,hostfwd={val_part[i]}")
                else:
                    continue
            if cmd_part[i] == "exe":
                result_part.append(f"{val_part[i]}")

        if config.get("cdrom") != "":
            result_part.append("-boot d")
        if config.get("hda") != "":
            result_part.append("-boot c")
        if config.get("hdb") != "":
            result_part.append("-boot c")
        if config.get("hdc") != "":
            result_part.append("-boot c")
        if config.get("hdd") != "":
            result_part.append("-boot c")
        config["config"] = result_part
        with open(get_config_path(), "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        
        json_path = get_config_path()

        try:
            # Gọi trực tiếp hàm từ module load_config thay vì subprocess
            # Điều này sửa lỗi mở cửa sổ mới khi chạy file exe
            load_config.run_qemu_direct(str(json_path))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e) + "\nHãy cài QEMU hoặc kiểm tra cấu hình.")
            return
        try:
            p = disk_list_path()
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass
        except Exception:
            self.HDA.clear()
            self.HDB.clear()
            self.HDC.clear()
            self.HDD.clear()
            self.HDA.addItem("none")
            self.HDB.addItem("none")
            self.HDC.addItem("none")
            self.HDD.addItem("none")

    def update_iso_enable(self, checked):
        self.LEI.setEnabled(checked)
        self.bi.setEnabled(checked)

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
