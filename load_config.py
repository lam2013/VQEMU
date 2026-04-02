import sys
import json
import subprocess
import os
import shutil
from pathlib import Path
from datetime import datetime
from find_tools_module import *
from log_module import *
import signal
import time
log = Logger()

def get_config_path():
    if sys.platform == "win32":
        app_data = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
        base_path = Path(app_data) / "VQEMU"
    else:
        base_path = Path.home() / ".vqemu"
        
    try:
        base_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
        
    return base_path / "config_VQEMU.json"


def load_config(config_path: str):
    """Đọc file JSON cấu hình."""
    log.step(f"Đang đọc file config: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.log("Đọc file config thành công!")
        return data
    except Exception as e:
        log.error(f"Lỗi khi đọc file config: {e}")
        return None




def build_qemu_cmd(cfg: dict, data: dict = None):
    """Ghép lệnh QEMU từ config."""
    arch = cfg.get("arch", "x86_64")
    exe_path = find_qemu_system(arch)
    if not exe_path:
        raise FileNotFoundError(f"Không tìm thấy QEMU cho kiến trúc {arch}. Hãy cài đặt QEMU.")
    cmd = [str(exe_path)]
    path_json = get_config_path()

    cmd_part = ["arch", "ram", "smp", "cpu", "vga", "audio", "cdrom", "hda", "hdb", "hdc", "hdd", "fda", "fdb", "fdc", "fdd", "net_model", "portfwd", "exe"]
    val_part = [cfg.get(part, "") for part in cmd_part]
    result_part = []

    # Machine Type
    machine_type = cfg.get("machine_type", "")
    if machine_type and machine_type != "none":
        result_part.extend(["-machine", str(machine_type)])

    # Accelerator
    accel = cfg.get("accel", "")
    if accel and accel != "off":
         result_part.extend(["-accel", str(accel)])



    # Custom BIOS
    if cfg.get("bios_enable") and cfg.get("bios_path"):
        if cfg.get("bios_path") != "":
            result_part.extend(["-bios", str(cfg.get("bios_path"))])

    # Boot Order
    boot_order = cfg.get("boot_order", "")
    if "-boot" in boot_order:
        try:
            import re
            match = re.search(r'\(-boot\s+(.*?)\)', boot_order)
            if match:
                order = match.group(1).replace(" ", "")
                result_part.extend(["-boot", f"order={order}"])
        except:
            pass
    
    if cfg.get("boot_menu"):
        # Check if we already have a -boot argument to append menu=on
        found_boot = False
        for i in range(len(result_part)):
            if result_part[i] == "-boot" and i + 1 < len(result_part):
                if "order=" in result_part[i+1]:
                    result_part[i+1] += ",menu=on"
                    found_boot = True
                    break
        if not found_boot:
             result_part.extend(["-boot", "menu=on"])

    # Shared Folder
    if cfg.get("shared_folder_enable") and cfg.get("shared_folder_path"):
        path = cfg.get("shared_folder_path")
        tag = cfg.get("shared_folder_tag", "shared")
        # -virtfs local,path=path,mount_tag=tag,security_model=none
        result_part.extend(["-virtfs", f"local,path={path},mount_tag={tag},security_model=none"])

    # Guest Agent (Feature 10)
    if cfg.get("guest_agent_enable"):
        # QEMU Guest Agent
        # Use named pipe for Windows host
        pipe_name = "qga" 
        result_part.extend(["-chardev", f"socket,path=\\\\.\\pipe\\{pipe_name},server,nowait,id=qga0"])
        result_part.extend(["-device", "virtio-serial"])
        result_part.extend(["-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0"])
        # Hint for clipboard: Ideally requires spice-vdagent running in guest and spicevmc chardev, 
        # but spicevmc requires -spice. We only add QGA here to avoid breaking boot without -spice.
        # If user wants clipboard, they might need to ensure valid display/agent setup.
        # However, adding the device for spice (without chardev) is harmless? 
        # -device virtserialport,chardev=spicechannel0,name=com.redhat.spice.0 -> needs chardev
        # So we skip it to be safe.


    for i in range(len(cmd_part)):
        if cmd_part[i] == "arch":
            continue
        if cmd_part[i] == "exe": # Skip adding exe at end, we use start
            continue
        if cmd_part[i] == "ram":
            result_part.extend(["-m", str(val_part[i])])
        if cmd_part[i] == "smp":
            result_part.extend(["-smp", str(val_part[i])])
        if cmd_part[i] == "cpu":
            result_part.extend(["-cpu", str(val_part[i])])
        if cmd_part[i] == "vga":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-vga", str(val_part[i])])
        if cmd_part[i] == "audio":
            if val_part[i] == "" or val_part[i] == "none":
                continue
            else:
                result_part.extend(["-device", str(val_part[i])])
        if cmd_part[i] == "cdrom":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-cdrom", str(val_part[i])])
        if cmd_part[i] == "hda":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-hda", str(val_part[i])])
        if cmd_part[i] == "hdb":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-hdb", str(val_part[i])])
        if cmd_part[i] == "hdc":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-hdc", str(val_part[i])])
        if cmd_part[i] == "hdd":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-hdd", str(val_part[i])])
        if cmd_part[i] == "fda":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-fda", str(val_part[i])])
        if cmd_part[i] == "fdb":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-fdb", str(val_part[i])])
        if cmd_part[i] == "fdc":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-fdc", str(val_part[i])])
        if cmd_part[i] == "fdd":
            if val_part[i] == "":
                continue
            else:
                result_part.extend(["-fdd", str(val_part[i])])
        if cmd_part[i] == "net_model" and cfg.get("enb_net") == "True":
            if val_part[i] == "none":
                continue
            else:
                result_part.extend(["-net", str(val_part[i])])
        else:
            continue
        if cmd_part[i] == "portfwd":
            if cfg.get("enb_portfwd") == "True":
                result_part.extend(["-netdev", f"user,id=n1,hostfwd={val_part[i]}"])
            else:
                continue
 
    if cfg.get("cdrom") != "":
        result_part.extend(["-boot", "d"])
    if cfg.get("hda") != "":
        result_part.extend(["-boot", "c"])
    if cfg.get("hdb") != "":
        result_part.extend(["-boot", "c"])
    if cfg.get("hdc") != "":
        result_part.extend(["-boot", "c"])
    if cfg.get("hdd") != "":
        result_part.extend(["-boot", "c"])

    # Add daemon storage parts
    if data and "caches" in data:
        caches = data["caches"]
        config_DS = data.get("config_DS", {})
        # User requirement: add lines for running daemon processes
        for key, info in caches.items():
            path_json = get_config_path()
            with open(path_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("config", {}).get("daemon_current", "")
            if name and name in config_DS:
                part = config_DS[name].get("part_cmd_run_qemu", "")
                name_io = data.get("config", {}).get("IO_daemon_storage", "")
                idds = data.get("config_DS", {}).get(name, {}).get("id", "")
                if name_io == "virtio-blk":
                    part += f" -device virtio-blk-device,drive=nbd{idds}"
                if name_io == "virtio-blk-pci":
                    part += f" -device virtio-blk-pci,drive=nbd{idds}"
                if name_io == "ide":
                    part += f" -device ide-hd,drive=nbd{idds}"
                if name_io == "ahci":
                    part += f" -device ahci,drive=nbd{idds}"
                if name_io == "nvme":
                    part += f" -device nvme,drive=nbd{idds}"
                if name_io == "usb-storage":
                    part += f" -device usb-storage,drive=nbd{idds}"
                if name_io == "floppy":
                    part += f" -device floppy,drive=nbd{idds}"
                if name_io == "virtio-blk-device":
                    part += f" -device virtio-blk-device,drive=nbd{idds}"
                if name_io == "virtio-blk-ccw":
                    part += f" -device virtio-blk-ccw,drive=nbd{idds}"
                if name_io == "virtio-scsi":
                    part += f" -device virtio-scsi-pci,drive=nbd{idds}"
                if part:
                    import shlex
                    try:
                        part_args = shlex.split(part, posix=False)
                    except:
                        part_args = part.split()
                    result_part.extend(part_args)



    # Add USB Passthrough parts
    usb_passthrough = cfg.get("usb_passthrough", [])
    if usb_passthrough:
        # Enable XHCI controller
        result_part.extend(["-device", "qemu-xhci,id=xhci"])
        for dev in usb_passthrough:
            vid = dev.get("vendorid")
            pid = dev.get("productid")
            if vid and pid:
                result_part.extend(["-device", f"usb-host,bus=xhci.0,vendorid={vid},productid={pid}"])

    if cfg.get("enb_command_qemu"):
        cmd.clear()
        import shlex
        custom_cmd = cfg.get("command_qemu", "")
        try:
            cmd.extend(shlex.split(custom_cmd, posix=False))
        except:
            cmd.extend(custom_cmd.split())
        return cmd

    # Feature 11: -readconfig
    if cfg.get("readconfig_enable") and cfg.get("readconfig_path"):
        result_part.extend(["-readconfig", str(cfg.get("readconfig_path"))])
    
    # Feature 12: -sandbox
    sandbox_cfg = cfg.get("sandbox", {})
    string_sanbox = ""
    if sandbox_cfg.get("check", ''):
        string_sandbox += "-sandbox on"
        if sandbox_cfg.get("obsolete", '') != "none":
            string_sandbox += f",obsolete={sandbox_cfg.get("obsolete", '')}"
        if sandbox_cfg.get("elevateprivileges", '') != "none":
            string_sandbox += f",elevateprivileges={sandbox_cfg.get("elevateprivileges", '')}"
        if sandbox_cfg.get("spawn", '') != "none":
            string_sandbox += f",spawn={sandbox_cfg.get("spawn", '')}"
        if sandbox_cfg.get("resourcecontrol", '') != "none":
            string_sandbox += f",resourcecontrol={sandbox_cfg.get("resourcecontrol", '')}"
        if sandbox_cfg.get("seccomp mode", '') != "off":
            string_sandbox += f",strict=yes"
        cmd += string_sandbox

    # Feature 13: watchdog
    watchdog = cfg.get("watchdog", "")
    if watchdog != "none":
        cmd += ["-device", str(watchdog)]
        # Feature 14: Watchdog-action
        watchdog_action = cfg.get("watchdog-action", "")
        cmd += ["-watchdog-action", str(watchdog_action)]

    # Prepend the executable
    with open(path_json, 'r', encoding="utf-8") as f:
        data = json.load(f)
    if data['config']['check_advanced_tab'] == True:
        final_cmd = cmd + result_part
        return final_cmd
    else:
        final_cmd = cmd + result_part
        return final_cmd


def run_qemu_direct(config_path):
    """Hàm chạy QEMU trực tiếp (dùng cho run.py gọi)."""
    config_path = Path(config_path)
    if not config_path.exists():
        log.error(f"Không tìm thấy file cấu hình: {config_path}")
        return

    log.step("Bắt đầu quy trình chạy QEMU")
    data = load_config(config_path)
    if not data:
        return
    
    cfg = data.get("config", {})

    # Suy ra arch nếu chưa có
    if "arch" not in cfg:
        exe = cfg.get("exe", "")
        if "x86_64" in exe:
            cfg["arch"] = "x86_64"
        elif "i386" in exe or "x86" in exe:
            cfg["arch"] = "i386"
        elif "arm" in exe:
            cfg["arch"] = "arm"
        else:
            cfg["arch"] = "x86_64"

    cmd = build_qemu_cmd(cfg, data)
    
    log.log("👉 Lệnh QEMU được tạo:")
    log.log(" ".join(cmd))
    log.log("🚀 QEMU đã bắt đầu!")
    
    import threading

    def monitor_process(proc):
        try:
            for line in proc.stdout:
                if line:
                    log.log(f"[QEMU] {line.strip()}")
            proc.wait()
            log.log(f"QEMU đã thoát với mã {proc.returncode}")
        except Exception as e:
            log.error(f"Lỗi giám sát tiến trình: {e}")

    try:
        log.log(">>> Đang chạy lệnh QEMU (Nền)...")
        # Use Popen to allow real-time logging and non-blocking UI
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr to stdout
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        # Start monitoring thread
        t = threading.Thread(target=monitor_process, args=(proc,), daemon=True)
        t.start()
        
    except Exception as e:
        log.error(f"Khi chạy QEMU (Lỗi khởi tạo): {e}")

def run_daemon_storage_direct(config_path, name_ds):
    """Chạy daemon storage với name_ds được chỉ định trong config."""
    config_path = Path(config_path)
    if not config_path.exists():
        log.error("Không tìm thấy config file")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log.error(f"Lỗi đọc config: {e}")
        return

    if "config_DS" not in data or name_ds not in data["config_DS"]:
        log.error(f"Không tìm thấy cấu hình Daemon Storage: {name_ds}")
        return

    ds_conf = data["config_DS"][name_ds]
    cmd_str = ds_conf.get("cmd_ds", "")
    if not cmd_str:
        log.error("cmd_ds trống")
        return
    
    # Xử lý đường dẫn exe
    import shlex
    try:
        args = shlex.split(cmd_str, posix=False)
    except:
        args = cmd_str.split()
        
    if not args:
        return

    exe_candidate = args[0]
    if "qemu-storage-daemon" in exe_candidate or "qemu-daemon-storage" in exe_candidate:
        found_exe = find_qemu_storage_daemon()
        if found_exe:
            args[0] = str(found_exe)
    
    log.step(f"Chạy Daemon Storage: {name_ds}")
    log.log(f"CMD: {args}")

    try:
        # Chạy background
        proc = subprocess.Popen(args, close_fds = False if sys.platform == "win32" else True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        
        path_config = get_config_path()
        
        # Check if process crashed immediately
        try:
            time.sleep(1)
            if proc.poll() is not None:
                log.error(f"Daemon đã thoát ngay lập tức với mã {proc.returncode}")
                return
        except Exception:
            pass
            
        pid = proc.pid
        data["config_DS"][name_ds]["pid"] = pid
        log.log(f"Daemon đã bắt đầu với PID: {pid}")

        if "caches" not in data:
            data["caches"] = {}
        
        # Format key: name:PID
        cache_key = f"{name_ds}:{pid}"
        data["caches"][cache_key] = {
            "name": name_ds,
            "pid": pid,
            "start_time": time.time()
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
    except Exception as e:
        log.error(f"Lỗi khi start daemon: {e}")

def kill_daemon_storage_direct(config_path, cache_key):
    """Kill daemon storage process dựa trên key trong caches."""
    config_path = Path(config_path)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    caches = data.get("caches", {})
    if cache_key not in caches:
        log.error(f"Không tìm thấy process key {cache_key} trong caches")
        return

    info = caches[cache_key]
    pid = info.get("pid")
    name_ds = info.get("name") 

    if pid:
        log.step(f"Dừng tiến trình {pid} ({name_ds})")
        try:
             # Windows kill force
            subprocess.run(f"taskkill /F /PID {pid}", shell=True)
            log.log("Đã gửi lệnh kill.")
        except Exception as e:
            log.error(f"Lỗi kill: {e}")
    
    # Clean up caches
    del caches[cache_key]
    
    # Loại bỏ thông tin đĩa đang dùng
    if "CCD" in data and name_ds in data["CCD"]:
        del data["CCD"][name_ds]
        
    data["caches"] = caches
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def kill_all_daemons(config_path):
    """Kill tất cả daemon storage đang chạy và xóa cache."""
    config_path = Path(config_path)
    if not config_path.exists():
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    caches = data.get("caches", {})
    if not caches:
        return

    log.step("Đang dọn dẹp tất cả daemon storage...")
    
    for cache_key, info in caches.items():
        pid = info.get("pid")
        name_ds = info.get("name")
        if pid:
            log.log(f"Đang dừng {name_ds} (PID: {pid})...")
            try:
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    # Clear lists
    data["caches"] = {}
    data["config_DS"] = {}
    data["CCD"] = {}

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    log.log("Đã dọn dẹp xong daemon storage.")


def main():
    print(">>> load_config.py đã được gọi thành công!")  
    print(">>> sys.argv:", sys.argv)

    if len(sys.argv) < 2:
        print("Cách dùng: python load_config.py <config.json>")
        sys.exit(1)

    config_path = sys.argv[1]
    run_qemu_direct(config_path)

if __name__ == "__main__":
    main()
