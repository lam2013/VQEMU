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


def main():

    
    print(">>> load_config.py đã được gọi thành công!")  
    print(">>> sys.argv:", sys.argv)


    if len(sys.argv) < 2:
        print("Usage: python load_config.py <config.json>")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    if not config_path.exists():
        print(f"[Lỗi] Không tìm thấy file cấu hình: {config_path}")
        sys.exit(1)

    cfg = load_config(config_path)

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

    # Log file
    log_file = Path(__file__).resolve().parent / "qemu_log.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] QEMU Command:\n")
        f.write(" ".join(cmd) + "\n\n")


    print("👉 Lệnh QEMU được tạo:")
    print(" ".join(cmd))
    print("🚀 QEMU started!")
    print(f"📝 Log ghi tại: {log_file}")

    try:
        print(">>> Running QEMU command...")
        print("CMD:", cmd)
        sys.stdout.flush()

        qemu_log_path = Path(__file__).resolve().parent / "qemu_log.txt"
        with open(qemu_log_path, "w", encoding="utf-8") as f:
            creation = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            subprocess.Popen(cmd, stdout=f, stderr=f, shell=True, creationflags=creation)



        print("🚀 QEMU started asynchronously! (non-blocking)")

    except Exception as e:
        log.error(f"Khi chạy QEMU: {e}")
        sys.exit(1)

    

    log.log("QEMU chạy thành công!")


if __name__ == "__main__":
    main()
