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
        return data
    except Exception as e:
        log.error(f"Lỗi khi đọc file config: {e}")
        return None




def build_qemu_cmd(cfg: dict):
    """Ghép lệnh QEMU từ config."""
    arch = cfg.get("arch", "x86_64")
    exe_path = find_qemu_system(arch)
    cmd = [str(exe_path)]

    # Tham số cơ bản
    if cfg.get("cpu"):
        cmd += ["-cpu", cfg["cpu"]]
    if cfg.get("ram"):
        cmd += ["-m", str(cfg["ram"])]
    if cfg.get("smp"):
        cmd += ["-smp", str(cfg["smp"])]
    if cfg.get("vga") and cfg["vga"].lower() != "none":
        cmd += ["-vga", cfg["vga"]]
    if cfg.get("audio") and cfg["audio"].lower() != "none":
        cmd += ["-device", cfg["audio"]]

    # CD, floppy
    if cfg.get("cdrom"):
        cmd += ["-cdrom", cfg["cdrom"], "-boot", "d"]


    if cfg.get("fda"):
        cmd += ["-fda", cfg["fda"]]
    if cfg.get("fdb"):
        cmd += ["-fdb", cfg["fdb"]]

    # Ổ cứng
    for hdx in ["hda", "hdb", "hdc", "hdd"]:
        if cfg.get(hdx):
            cmd += [f"-{hdx}", cfg[hdx], "-boot", "c"]

    # Mạng
    if cfg.get("net_enable"):
        model = cfg.get("net_model", "e1000")
        cmd += ["-net", f"nic,model={model}"]
        if cfg.get("portfwd"):
            pf = cfg["portfwd"]
            if pf.startswith("hostfwd="):
                cmd += ["-netdev", f"user,id=n1,{pf}", "-device", f"{model},netdev=n1"]
            else:
                cmd += ["-net", "user"]
        else:
            cmd += ["-net", "user"]
    else:
        cmd += ["-boot", "menu=on"]
    log.step("Tạo lệnh QEMU")
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
