@echo off
cd /d "%~dp0"
pyinstaller --onedir --noconfirm --icon="icon_VQEMU.ico" --add-data "load_config.py;." --add-data "qemu;qemu" --add-data "log_module.py;." --add-data "find_tools_module.py;." --add-data "qemu_advanced_module.py;." run.py