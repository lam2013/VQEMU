___          __    ________        __________     ____         ____    ____      ___
\ \         / /   / ______ \      |  ________|   |    \       /    |   |  |     |   |
 \ \       / /    | |     | |     |  |_______    |     \     /     |   |  |     |   |
  \ \     / /     | |     | |     |  |_______|   |  |\  \   /  /|  |   |  |     |   |
   \ \___/ /      | |_____|  \    |  |_______    |  | \  \_/  / |  |   |  |_____|   |
    \_____/       \_________/\|   |__________|   |__|  \_____/  |__|   |____________|

giới thiệu:
    đây là phần mềm QEMU GUI được viết 100% bằng python và cũng là mã nguồn mở chuẩn GPLv3 và được người việt thực hiện. phần mềm này được thực hiện trong 2 tháng.

cách sắp xếp file/folder:
{parent folder}
    |
    |(nhánh folder)
    +---qemu
    +---logs
    |
    |(nhánh file)
    +---run.py
    +---run.exe
    +---load_config.py
    +---log_module.py
    +---find_qemu_tools.py
    +---fill_module.py
    +---qemu_advanced_module.py
    +---README.txt
    +---LICENSE
    +---icon_VQEMU.ico

tính năng:
+hỗ trợ đa dạng loại cpu,vga,sound card, wifi card, qemu system của qemu v3.10
+có giao diện đồ họa
+khởi chạy được mọi loại qemu system
+hỗ trợ tạo ổ đĩa ảo
+tính năng custom qemu
+tính năng snapshot
+tính năng FDA,FDB,FDC,FDD
+daemon storage
+cải tiến wifi
+system w

những tính năng mới:
+update card sound (Thêm danh sách sound card đa dạng: intel-hda, ac97, es1370, sb16, hda-duplex...)
+update card IO daemon storage (Tối ưu hóa quản lý tiến trình daemon, thêm tùy chọn cache mode và aio)
+Log Viewer (Tab vm_tab: View Log, Save Log, Clear Log button)
+USB Device Manager (Giao diện tích chọn để passthrough thiết bị USB từ Host vào Guest)
+update thêm tính năng machine type (Thêm tùy chọn chọn version chipset: pc-i440fx-x.x hoặc q35-x.x để tương thích OS cũ/mới)
+Custom bios
+Shared Folder Integration (Hỗ trợ VirtFS để chia sẻ thư mục Host-Guest dễ dàng mà không cần mạng)
+Performance & Acceleration (tùy chọn bật do user quyết định WHPX/HAXM/Hyper-V, nhận biết win nào có thể bật WHPX/HAXM/Hyper-V và cảnh báo những win không thể bật)
+check qemu daemon có đang chạy không, nêu các thông tin về PID, thời gian chạy, tên gì
+Guest Agent Integration (Hỗ trợ QEMU Guest Agent để Shutdown/Reboot máy ảo an toàn, đồng bộ clipboard Host-Guest)

cách chạy:
1. chạy thủ công(nếu bạn biết sơ về command):
    -yêu cầu:
        +python v3.xx
    -chạy:
        +mở console(hoặc tương tự)
        +chạy lệnh như sau:
            python -u "{parent folder}\run.py"
2.tự động:
    chạy thẳng file exe


thank for qemu
link tải binaries cho windows:https://qemu.weilnetz.de/w64/2025/qemu-w64-setup-20250826.exe
link tải cho mac:
    -homebrew:brew install qemu
    -macport:sudo port install qemu
link tải cho linux:
    -Arch: pacman -S qemu
    -Debian/Ubuntu:
        +cho giả lập full system:apt-get install qemu-system
        +cho giả lập Linux binaries: apt-get install qemu-user-static
    -Fedora: dnf install @virtualization
    -Gentoo: emerge --ask app-emulation/qemu
    -RHEL/CentOS: yum install qemu-kvm
    -SUSE: zypper install qemu
link tải open-source:https://download.qemu.org/qemu-10.1.1.tar.xz

thank for python
link tải python:https://www.python.org/downloads/

các thư viện\phần mềm đc sử dụng:
-python 3.14
-PyQt5
-PyInstaller
-qemu


nhà phát triển: VNCore lab(Nguyễn Trường Lâm)
nhà phát hành: VNCore lab(Nguyễn Trường Lâm)
email gửi yêu cầu fix bug/cho code để update: nguyenvannghia1952tg@gmail.com

***2025 Vncore lab (alias of Nguyễn Trường Lâm)***

*lưu ý: VQEMU chỉ dành cho windows. chỉ chạy đc windows 8,8.1,10,11 và tất cả đều là 64-bit