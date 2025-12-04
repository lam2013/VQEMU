import sys
import json
import subprocess
import os
import shutil
from pathlib import Path
from datetime import datetime
from find_tools_module import *
from log_module import *
log = Logger()


def load_config(config_path: str):
    """Đọc file JSON cấu hình."""
    log.step(f"Đang đọc file config: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.log("Đọc file config thành công!")
        return data["config"]
    except Exception as e:
        log.error(f"Lỗi khi đọc file config: {e}")
        return None




def build_qemu_cmd(cfg: dict):
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
        if cmd_part[i] == "fda":
            if val_part[i] == "":
                continue
            else:
                result_part.append(f"-fda {val_part[i]}")
        if cmd_part[i] == "fdb":
            if val_part[i] == "":
                continue
            else:
                result_part.append(f"-fdb {val_part[i]}")
        if cmd_part[i] == "fdc":
            if val_part[i] == "":
                continue
            else:
                result_part.append(f"-fdc {val_part[i]}")
        if cmd_part[i] == "fdd":
            if val_part[i] == "":
                continue
            else:
                result_part.append(f"-fdd {val_part[i]}")
        if cmd_part[i] == "net_model" and cfg.get("enb_net") == "True":
            if val_part[i] == "none":
                continue
            else:
                result_part.append(f"-net {val_part[i]}")
        else:
            continue
        if cmd_part[i] == "portfwd":
            if cfg.get("enb_portfwd") == "True":
                result_part.append(f"-netdev user,id=n1,hostfwd={val_part[i]}")
            else:
                continue
        if cmd_part[i] == "exe":
            result_part.append(f"{val_part[i]}")

        if cfg.get("cdrom") != "":
            result_part.append("-boot d")
        if cfg.get("hda") != "":
            result_part.append("-boot c")
        if cfg.get("hdb") != "":
            result_part.append("-boot c")
        if cfg.get("hdc") != "":
            result_part.append("-boot c")
        if cfg.get("hdd") != "":
            result_part.append("-boot c")
        return result_part
    if cfg.get("enb_command_qemu"):
        cmd.clear()
        import shlex
        custom_cmd = cfg.get("command_qemu", "")
        try:
            cmd.extend(shlex.split(custom_cmd, posix=False))
        except:
            cmd.extend(custom_cmd.split())
        return cmd
    return cmd


def run_qemu_direct(config_path):
    """Hàm chạy QEMU trực tiếp (dùng cho run.py gọi)."""
    config_path = Path(config_path)
    if not config_path.exists():
        log.error(f"Không tìm thấy file cấu hình: {config_path}")
        return

    log.step("Bắt đầu quy trình chạy QEMU")
    cfg = load_config(config_path)
    if not cfg:
        return

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

    cmd = build_qemu_cmd(cfg)
    
    log.log("👉 Lệnh QEMU được tạo:")
    log.log(" ".join(cmd))
    log.log("🚀 QEMU started!")
    
    try:
        log.log(">>> Running QEMU command...")
        # log.log(f"CMD: {cmd}") 
        # subprocess.run blocks until QEMU closes
        subprocess.run(cmd, check=True)
        log.log("QEMU chạy thành công!")
    except Exception as e:
        log.error(f"Khi chạy QEMU: {e}")

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
