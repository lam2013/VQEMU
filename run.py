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
from qemu_advanced_module import *

try:
    if sys.stdout and hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
except Exception:
    pass



def get_data_dir():
    try:
        if getattr(sys, 'frozen', False):
            # For frozen apps, prefer APPDATA (so files persist across updates)
            if sys.platform == 'win32':
                base = Path(os.environ.get('APPDATA', Path.home()))
            else:
                base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
            p = base / 'VQEMU'
            p.mkdir(parents=True, exist_ok=True)
            return p
    except Exception:
        pass

    # development mode: keep data alongside the script
    base = Path(__file__).resolve().parent
    p = base / 'data'
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p


def disk_list_path():
    return get_data_dir() / 'disks.json'


def load_disk_list():
    p = disk_list_path()
    if p.exists():
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_disk_to_list(disk_path):
    p = disk_list_path()
    disks = load_disk_list()
    if disk_path not in disks:
        disks.append(disk_path)
        try:
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(disks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def can_write(folder):
    try:
        testfile = os.path.join(folder, ".__testwrite__")
        with open(testfile, "w") as f:
            f.write("test")
        os.remove(testfile)
        return True
    except Exception:
        return False

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showMinimized()
        elif event.key() == Qt.Key_Q and event.modifiers() & Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(event)
            
    
    def get_qemu_exe(self):
        """Tự động tìm QEMU tương ứng kiến trúc đang chọn."""
        arch = self.K.currentText()
        exe_path = find_qemu_system(arch)
        if not exe_path:
            raise FileNotFoundError(f"Không tìm thấy QEMU cho kiến trúc {arch}")
        return str(exe_path)
    

    def init_tabs(self):
        # Tab Máy ảo
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

        # Tab Ổ đĩa
        disk_tab = QWidget()
        disk_layout = QVBoxLayout(disk_tab)
        group_disk = QGroupBox("Quản lý ổ đĩa")
        layout_disk = QGridLayout(group_disk)
        layout_disk.addWidget(QLabel("HDA:"), 0, 0)
        self.HDA = QComboBox()
        self.HDA.addItem("none")
        layout_disk.addWidget(self.HDA, 0, 1)
        layout_disk.addWidget(QLabel("HDB:"), 1, 0)
        self.HDB = QComboBox()
        self.HDB.addItem("none")
        layout_disk.addWidget(self.HDB, 1, 1)
        layout_disk.addWidget(QLabel("HDC:"), 2, 0)
        self.HDC = QComboBox()
        self.HDC.addItem("none")
        layout_disk.addWidget(self.HDC, 2, 1)
        layout_disk.addWidget(QLabel("HDD:"), 3, 0)
        self.HDD = QComboBox()
        self.HDD.addItem("none")
        layout_disk.addWidget(self.HDD, 3, 1)
        self.BCD = QPushButton("Thêm/Tạo/Xóa ổ đĩa")
        layout_disk.addWidget(self.BCD, 4, 0, 1, 2)
        self.CLD = QPushButton("Xóa danh sách ổ đĩa")
        layout_disk.addWidget(self.CLD, 5, 0, 1, 2)
        disk_layout.addWidget(group_disk)
        self.addTab(disk_tab, "Ổ đĩa")

        # Tab Boot
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
        self.CBFA = QCheckBox("Floppy A")
        self.LEFA = QLineEdit()
        self.LEFA.setPlaceholderText("Floppy A")
        self.bfa = QPushButton("Chọn file")
        layout_boot.addWidget(self.CBFA, 1, 0)
        layout_boot.addWidget(self.LEFA, 1, 1)
        layout_boot.addWidget(self.bfa, 1, 2)
        self.CBFB = QCheckBox("Floppy B")
        self.LEFB = QLineEdit()
        self.LEFB.setPlaceholderText("Floppy B")
        self.bfb = QPushButton("Chọn file")
        layout_boot.addWidget(self.CBFB, 2, 0)
        layout_boot.addWidget(self.LEFB, 2, 1)
        layout_boot.addWidget(self.bfb, 2, 2)
        boot_layout.addWidget(group_boot)
        self.addTab(boot_tab, "Khởi động")

        # Kết nối signal/slot SAU khi đã tạo widget
        self.CBI.toggled.connect(self.update_iso_enable)
        self.CBFA.toggled.connect(self.update_floppy_a_enable)
        self.CBFB.toggled.connect(self.update_floppy_b_enable)
        self.update_iso_enable(self.CBI.isChecked())
        self.update_floppy_a_enable(self.CBFA.isChecked())
        self.update_floppy_b_enable(self.CBFB.isChecked())

        # Tab Mạng
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

        # Tab Profiles (Cấu hình đã lưu)
        prof_tab = QWidget()
        prof_layout = QVBoxLayout(prof_tab)
        group_prof = QGroupBox("Profiles / Cấu hình")
        layout_prof = QGridLayout(group_prof)
        self.profile_list = QListWidget()
        layout_prof.addWidget(self.profile_list, 0, 0, 4, 2)
        self.btn_prof_add = QPushButton("Thêm")
        self.btn_prof_save = QPushButton("Lưu dưới tên...")
        self.btn_prof_load = QPushButton("Load")
        self.btn_prof_delete = QPushButton("Xóa")
        self.btn_prof_rename = QPushButton("Đổi tên")
        layout_prof.addWidget(self.btn_prof_add, 0, 2)
        layout_prof.addWidget(self.btn_prof_save, 1, 2)
        layout_prof.addWidget(self.btn_prof_load, 2, 2)
        layout_prof.addWidget(self.btn_prof_delete, 3, 2)
        layout_prof.addWidget(self.btn_prof_rename, 4, 2)
        prof_layout.addWidget(group_prof)
        self.addTab(prof_tab, "Cấu hình")

        self.btn_prof_add.clicked.connect(self._ui_profile_add)
        self.btn_prof_save.clicked.connect(self._ui_profile_save)
        self.btn_prof_load.clicked.connect(self._ui_profile_load)
        self.btn_prof_delete.clicked.connect(self._ui_profile_delete)
        self.btn_prof_rename.clicked.connect(self._ui_profile_rename)
        self.refresh_profile_list()

        # Kết nối các nút, checkbox, v.v.
        self.BCD.clicked.connect(self.open_disk_dialog)
        self.CLD.clicked.connect(self.clean_disk_list)
        self.bi.clicked.connect(self.BI)
        self.bfa.clicked.connect(self.BFA)
        self.bfb.clicked.connect(self.BFB)
        self.CBI.toggled.connect(lambda checked: self.LEI.setEnabled(checked))
        self.CBFA.toggled.connect(lambda checked: self.LEFA.setEnabled(checked))
        self.CBFB.toggled.connect(lambda checked: self.LEFB.setEnabled(checked))
        self.CN.toggled.connect(lambda checked: (self.LN.setEnabled(checked), self.KN.setEnabled(checked)))
        self.CPF.toggled.connect(lambda checked: self.PF.setEnabled(checked))
        self.run.clicked.connect(self.run_qemu)

    def update_arch_dependent_widgets(self):
        """Cập nhật danh sách CPU và VGA dựa trên kiến trúc được chọn (từ qemu_advanced_module)."""
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
        base_dir = Path(__file__).resolve().parent
        pdir = base_dir / "profiles"
        return pdir

    def ensure_profiles_dir(self):
        p = self.profiles_dir()
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    def list_profiles(self):
        self.ensure_profiles_dir()
        p = self.profiles_dir()
        files = []
        for f in p.glob('*.json'):
            files.append(f.stem)
        return sorted(files)

    def refresh_profile_list(self):
        if hasattr(self, 'profile_list'):
            self.profile_list.clear()
            for name in self.list_profiles():
                self.profile_list.addItem(name)

    def save_profile_by_name(self, name):
        if not name:
            return False, 'Empty name'
        self.ensure_profiles_dir()
        p = self.profiles_dir() / f"{name}.json"
        try:
            cfg = self.get_current_config()
        except Exception as e:
            return False, str(e)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        self.refresh_profile_list()
        return True, None

    def load_profile_by_name(self, name):
        if not name:
            return False, 'Empty name'
        p = self.profiles_dir() / f"{name}.json"
        if not p.exists():
            return False, 'Profile not found'
        with open(p, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        try:
            self.apply_config(cfg)
        except Exception as e:
            return False, str(e)
        return True, None

    def delete_profile_by_name(self, name):
        p = self.profiles_dir() / f"{name}.json"
        if p.exists():
            p.unlink()
        self.refresh_profile_list()

    def rename_profile_by_name(self, old, new):
        if not old or not new:
            return False, 'Empty name'
        p_old = self.profiles_dir() / f"{old}.json"
        p_new = self.profiles_dir() / f"{new}.json"
        if not p_old.exists():
            return False, 'Original not found'
        if p_new.exists():
            return False, 'Target name exists'
        p_old.rename(p_new)
        self.refresh_profile_list()
        return True, None

    def get_current_config(self):
        """Return current GUI config as dict (same shape as config.json)."""
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
            "vga": self.V.currentText(),
            "audio": self.A.currentText() if self.A.currentText() != "None" else "",
            "cdrom": self.LEI.text().strip() if self.CBI.isChecked() else "",
            "fda": self.LEFA.text().strip() if self.CBFA.isChecked() else "",
            "fdb": self.LEFB.text().strip() if self.CBFB.isChecked() else "",
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
        """Apply a config dict to the GUI widgets."""
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
        # Media
        cdrom = cfg.get('cdrom', '')
        if cdrom:
            self.CBI.setChecked(True)
            self.LEI.setText(cdrom)
        else:
            self.CBI.setChecked(False)
            self.LEI.setText('')
        fda = cfg.get('fda', '')
        if fda:
            self.CBFA.setChecked(True)
            self.LEFA.setText(fda)
        else:
            self.CBFA.setChecked(False)
            self.LEFA.setText('')
        fdb = cfg.get('fdb', '')
        if fdb:
            self.CBFB.setChecked(True)
            self.LEFB.setText(fdb)
        else:
            self.CBFB.setChecked(False)
            self.LEFB.setText('')
        # Disks
        for disk_field, cb in [('hda', self.HDA), ('hdb', self.HDB), ('hdc', self.HDC), ('hdd', self.HDD)]:
            val = cfg.get(disk_field, '')
            if val:
                if cb.findText(val) == -1:
                    cb.addItem(val)
                cb.setCurrentText(val)
            else:
                cb.setCurrentIndex(0)
        # Network
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

    def _ui_profile_save(self):
        name, ok = QInputDialog.getText(self, "Lưu profile", "Tên file lưu:")
        if ok and name:
            ok2, err = self.save_profile_by_name(name)
            if not ok2:
                QMessageBox.critical(self, "Lỗi", f"Không lưu profile: {err}")
            else:
                QMessageBox.information(self, "OK", "Đã lưu profile.")

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

        disks = load_disk_list()
        for d in disks:
            self.HDA.addItem(d)
            self.HDB.addItem(d)
            self.HDC.addItem(d)
            self.HDD.addItem(d)

    def open_disk_dialog(self):
        dlg = DL()
        if dlg.exec_() == QDialog.Accepted:
            disk = getattr(dlg, "disk_created_path", None)
            if disk:
                for cb in [self.HDA, self.HDB, self.HDC, self.HDD]:
                    if cb.findText(disk) == -1:
                        cb.addItem(disk)
    
    
    
    def BI(self):
        file, _ = QFileDialog.getOpenFileName(None, "chon file", "", "Image File (*.iso *.img *.vfd *.bin) ;; all file (*)")
        self.LEI.setText(file)

    def BFA(self):
        file, _ = QFileDialog.getOpenFileName(None, "chon file", "", "Image File (*.iso *.img *.vfd *.bin) ;; all file (*)")
        self.LEFA.setText(file)

    def BFB(self):
        file, _ = QFileDialog.getOpenFileName(None, "chon file", "", "Image File (*.iso *.img *.vfd *.bin) ;; all file (*)")
        self.LEFB.setText(file)

    def run_qemu(self):
    # === (1) Thu thập cấu hình từ GUI ===
        arch = self.K.currentText()
        try:
            exe_path = self.get_qemu_exe()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e) + "\nHãy cài QEMU hoặc kiểm tra cấu hình.")
            return

        config = {
            "arch": arch,
            "exe": exe_path,
            "cpu": self.CP.currentText(),
            "ram": self.RM.value(),
            "smp": int(self.SC.currentText()),
            "vga": self.V.currentText(),
            "audio": self.A.currentText() if self.A.currentText() != "None" else "",
            "cdrom": self.LEI.text().strip() if self.CBI.isChecked() else "",
            "fda": self.LEFA.text().strip() if self.CBFA.isChecked() else "",
            "fdb": self.LEFB.text().strip() if self.CBFB.isChecked() else "",
            "hda": self.HDA.currentText() if self.HDA.currentText().lower() != "none" else "",
            "hdb": self.HDB.currentText() if self.HDB.currentText().lower() != "none" else "",
            "hdc": self.HDC.currentText() if self.HDC.currentText().lower() != "none" else "",
            "hdd": self.HDD.currentText() if self.HDD.currentText().lower() != "none" else "",
            "net_enable": self.CN.isChecked(),
            "net_model": self.LN.currentText(),
            "portfwd": self.PF.text().strip() if self.CPF.isChecked() else ""
        }

        # === (2) Ghi file config ===
        base_dir = Path(__file__).resolve().parent
        config_path = base_dir / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # === (3) Xác định file load_config.py ===
        load_config_path = base_dir / "load_config.py"
        if not load_config_path.exists():
            QMessageBox.critical(self, "Lỗi", f"Không tìm thấy {load_config_path}")
            return

        print(f"➡️ Gọi: {sys.executable} {load_config_path} {config_path}")

        # === (4) Gọi load_config.py an toàn ===
        try:
            log_path = base_dir / "gui_call_log.txt"
            with open(log_path, "w", encoding="utf-8") as log_file:
                popen_kwargs = dict(cwd=base_dir, stdout=log_file, stderr=subprocess.STDOUT)
                if os.name == 'nt' and hasattr(subprocess, 'CREATE_NEW_CONSOLE'):
                    popen_kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE
                python_exec = sys.executable if sys.executable.endswith("python.exe") else "python"
                subprocess.Popen(
                    [python_exec, "-X", "utf8", str(load_config_path), str(config_path)],
                    cwd=base_dir,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            QMessageBox.information(self, "Khởi động VM", "Đang khởi động QEMU, kiểm tra file gui_call_log.txt để xem tiến trình.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi khi chạy QEMU", str(e))
            print("❌ Exception:", e)



    def clean_disk_list(self):
        p = disk_list_path()
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
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

    def update_floppy_a_enable(self, checked):
        self.LEFA.setEnabled(checked)
        self.bfa.setEnabled(checked)

    def update_floppy_b_enable(self, checked):
        self.LEFB.setEnabled(checked)
        self.bfb.setEnabled(checked)

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
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.disk_path)
        browse_layout.addWidget(self.btn_browse_disk)
        layout.addWidget(QLabel("Đường dẫn ổ đĩa hiện có"))
        layout.addLayout(browse_layout)
        return w

    def create_delete_widget(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.disk_list = QComboBox()
        disks = load_disk_list()
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

    def browse_disk(self):
        file, _ = QFileDialog.getOpenFileName(self, "Chọn ổ đĩa", "", "Disk Images (*.img *.qcow2);;All Files (*)")
        if file:
            self.disk_path.setText(file)
            self.disk_created_path = file
            save_disk_to_list(file)
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
        if os.path.exists(full_path):
            QMessageBox.warning(self, "Lỗi", "File đã tồn tại.")
            return

        # Ưu tiên tìm qemu-img trong build nội bộ (dù chạy ở đâu)
        qemu_img_path = find_qemu_img()
        if not qemu_img_path or not qemu_img_path.exists():
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy qemu-img! Hãy build/cài QEMU trước.")
            return
        qemu_img = str(qemu_img_path)
        cmd = [qemu_img, "create", "-f", fmt, full_path, f"{size}M"]
        try:
            subprocess.run(cmd, check=True)
            QMessageBox.information(self, "Thành công", f"Đã tạo ổ đĩa: {full_path}")
            self.disk_created_path = full_path
            save_disk_to_list(full_path)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không tạo được ổ đĩa:\n{e}")

    def delete_disk(self):
        disk = self.disk_list.currentText()
        if not disk:
            QMessageBox.warning(self, "Lỗi", "Không có ổ đĩa nào để xóa.")
            return
        reply = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa file này?\n{disk}", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(disk):
                    os.remove(disk)
                disks = load_disk_list()
                if disk in disks:
                    disks.remove(disk)
                    try:
                        with open(disk_list_path(), "w", encoding='utf-8') as f:
                            json.dump(disks, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                QMessageBox.information(self, "Thành công", "Đã xóa ổ đĩa.")
                self.disk_list.clear()
                self.disk_list.addItems(disks)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không xóa được ổ đĩa:\n{e}")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


if __name__ == "__main__":

    app = QApplication(sys.argv)
    qg = QG()
    qg.show()
    sys.exit(app.exec_())
#the command:pyinstaller --onedir --noconfirm --add-data "load_config.py;." --add-data "qemu;qemu" --add-data "log_module.py;." --add-data "find_tools_module.py;." --add-data "qemu_advanced_module.py;." run.py