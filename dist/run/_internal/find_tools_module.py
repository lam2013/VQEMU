from pathlib import Path
import sys
import shutil

def find_qemu_img(start_file=__file__, max_up=6):
    """
    Trả về Path tới qemu-img.exe (hoặc qemu-img trên Linux).
    Không in ra terminal, chỉ return kết quả hoặc None.
    """
    exe_name = "qemu-img.exe" if sys.platform == "win32" else "qemu-img"
    start = Path(start_file).resolve()
    start_dir = start.parent

    roots = [start_dir] + list(start_dir.parents[:max_up])

    for root in roots:
        qemu_dir = root / "qemu"
        if qemu_dir.exists():
            candidate = qemu_dir / "build" / exe_name
            if candidate.exists():
                return candidate
            for sub in sorted(qemu_dir.iterdir(), reverse=True):
                if sub.is_dir() and sub.name.startswith("qemu-"):
                    candidate = sub / "build" / exe_name
                    if candidate.exists():
                        return candidate

    which = shutil.which(exe_name)
    if which:
        return Path(which)

    return None

def find_qemu_system(arch="x86_64", start_file=__file__, max_up=6):
    """
    Tìm file qemu-system tương ứng với kiến trúc (x86_64, i386, arm, v.v.)
    Trả về Path nếu tìm thấy, None nếu không.
    """
    exe_name = f"qemu-system-{arch}.exe" if sys.platform == "win32" else f"qemu-system-{arch}"
    start = Path(start_file).resolve()
    start_dir = start.parent
    roots = [start_dir] + list(start_dir.parents[:max_up])

    for root in roots:
        qemu_dir = root / "qemu"
        if qemu_dir.exists():
            candidate = qemu_dir / "build" / exe_name
            if candidate.exists():
                return candidate
            for sub in sorted(qemu_dir.iterdir(), reverse=True):
                if sub.is_dir() and sub.name.startswith("qemu-"):
                    candidate = sub / "build" / exe_name
                    if candidate.exists():
                        return candidate

    which = shutil.which(exe_name)
    if which:
        return Path(which)

    return None


def find_icon(name: str, start_file=__file__, max_up: int = 6):
    """
    Tìm một file icon (ví dụ 'icon_VQEMU.png' hoặc 'icon_VQEMU.ico') bằng cách
    duyệt từ thư mục chứa `start_file` lên các thư mục cha (tối đa `max_up`).

    Trả về Path (đã resolve) nếu tìm thấy, hoặc None nếu không.
    """
    
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            meipass = Path(sys._MEIPASS)
            for rel in ["", "icons", "resources", "assets"]:
                candidate = (meipass / rel / name).resolve()
                if candidate.exists():
                    return candidate
    except Exception:
        pass

    try:
        exe_dir = Path(sys.executable).resolve().parent
        for rel in ["", "icons", "resources", "assets"]:
            candidate = (exe_dir / rel / name).resolve()
            if candidate.exists():
                return candidate
    except Exception:
        pass

    start = Path(start_file).resolve()
    start_dir = start.parent
    roots = [start_dir] + list(start_dir.parents[:max_up])
    rel_paths = ["", "icons", "resources", "assets", "qemu"]
    for root in roots:
        for rel in rel_paths:
            candidate = (root / rel / name).resolve()
            if candidate.exists():
                return candidate

    try:
        arg0_dir = Path(sys.argv[0]).resolve().parent
        candidate = (arg0_dir / name).resolve()
        if candidate.exists():
            return candidate
    except Exception:
        pass

    return None


def get_icon_vqemu_png(start_file=__file__, max_up: int = 6):
    """Return Path to icon_VQEMU.png or None if not found."""
    return find_icon("icon_VQEMU.png", start_file=start_file, max_up=max_up)


def get_icon_vqemu_ico(start_file=__file__, max_up: int = 6):
    """Return Path to icon_VQEMU.ico or None if not found."""
    return find_icon("icon_VQEMU.ico", start_file=start_file, max_up=max_up)


