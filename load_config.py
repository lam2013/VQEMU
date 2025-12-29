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
    cmd = [str(exe_path)]

    cmd_part = ["arch", "ram", "smp", "cpu", "vga", "audio", "cdrom", "hda", "hdb", "hdc", "hdd", "fda", "fdb", "fdc", "fdd", "net_model", "portfwd", "exe"]
    val_part = [cfg.get(part, "") for part in cmd_part]
    result_part = []

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
            if val_part[i] == "":
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
            path_json = Path(__file__).parent / "config_VQEMU.json"
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

    if cfg.get("enb_command_qemu"):
        cmd.clear()
        import shlex
        custom_cmd = cfg.get("command_qemu", "")
        try:
            cmd.extend(shlex.split(custom_cmd, posix=False))
        except:
            cmd.extend(custom_cmd.split())
        return cmd
    
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
    log.log("🚀 QEMU started!")
    
    try:
        log.log(">>> Running QEMU command...")
        # Capture output to diagnose errors
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log.log("QEMU Output:\n" + result.stdout)
        log.log("QEMU chạy thành công!")
    except subprocess.CalledProcessError as e:
        log.error(f"Khi chạy QEMU (Exit Code {e.returncode}):")
        log.error(f"STDOUT: {e.stdout}")
        log.error(f"STDERR: {e.stderr}")
    except Exception as e:
        log.error(f"Khi chạy QEMU (Lỗi khác): {e}")

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
        
        path_config = Path(__file__).resolve().parent / "config_VQEMU.json"
        
        # Check if process crashed immediately
        try:
            time.sleep(1)
            if proc.poll() is not None:
                log.error(f"Daemon process exited immediately with code {proc.returncode}")
                return
        except Exception:
            pass
            
        pid = proc.pid
        data["config_DS"][name_ds]["pid"] = pid
        log.log(f"Daemon started with PID: {pid}")

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
        log.step(f"Kill process {pid} ({name_ds})")
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
            log.log(f"Killing {name_ds} (PID: {pid})...")
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
        print("Usage: python load_config.py <config.json>")
        sys.exit(1)

    config_path = sys.argv[1]
    run_qemu_direct(config_path)

if __name__ == "__main__":
    main()
