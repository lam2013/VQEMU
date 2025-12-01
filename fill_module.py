import re

raw_text = """
name "e1000", bus PCI, alias "e1000-82540em", desc "Intel Gigabit Ethernet"
name "e1000-82544gc", bus PCI, desc "Intel Gigabit Ethernet"
name "e1000-82545em", bus PCI, desc "Intel Gigabit Ethernet"
name "i82550", bus PCI, desc "Intel i82550 Ethernet"
name "i82551", bus PCI, desc "Intel i82551 Ethernet"
name "i82557a", bus PCI, desc "Intel i82557A Ethernet"
name "i82557b", bus PCI, desc "Intel i82557B Ethernet"
name "i82557c", bus PCI, desc "Intel i82557C Ethernet"
name "i82558a", bus PCI, desc "Intel i82558A Ethernet"
name "i82558b", bus PCI, desc "Intel i82558B Ethernet"
name "i82559a", bus PCI, desc "Intel i82559A Ethernet"
name "i82559b", bus PCI, desc "Intel i82559B Ethernet"
name "i82559c", bus PCI, desc "Intel i82559C Ethernet"
name "i82559er", bus PCI, desc "Intel i82559ER Ethernet"
name "i82562", bus PCI, desc "Intel i82562 Ethernet"
name "i82801", bus PCI, desc "Intel i82801 Ethernet"
name "igb", bus PCI, desc "Intel 82576 Gigabit Ethernet Controller"
name "pcnet", bus PCI
name "usb-net", bus usb-bus
name "virtio-net-device", bus virtio-bus
name "virtio-net-pci", bus PCI, alias "virtio-net"
name "virtio-net-pci-non-transitional", bus PCI
name "virtio-net-pci-transitional", bus PCI
name "vmxnet3", bus PCI, desc "VMWare Paravirtualized Ethernet v3"
"""

# 1️⃣ Tách từng dòng, bỏ trống và comment
if "name" in raw_text:
    raw_text.replace("name", "")
lines = raw_text.splitlines()

cpu_names = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    # 2️⃣ Lấy cụm đầu tiên trước dấu space hoặc '#'
    match = re.match(r'^"?([A-Za-z0-9._+-]+)"?', line)
    if match:
        name = match.group(1)
        if name not in cpu_names:
            cpu_names.append(name)

# 3️⃣ Xuất ra dạng list Python
formatted = ", ".join(f'"{n}"' for n in cpu_names)
print(f"[{formatted}],")