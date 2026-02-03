import re

raw_text = """
kc705                kc705 EVB (dc232b)
kc705-nommu          kc705 noMMU EVB (de212)
lx200                lx200 EVB (dc232b)
lx200-nommu          lx200 noMMU EVB (de212)
lx60                 lx60 EVB (dc232b)
lx60-nommu           lx60 noMMU EVB (de212)
ml605                ml605 EVB (dc232b)
ml605-nommu          ml605 noMMU EVB (de212)
none                 empty machine
sim                  sim machine (dc232b) (default)
virt                 virt machine (dc232b)
"""
no_none = True
HNC = False
# 1️⃣ Tách từng dòng, bỏ trống và comment
if HNC == True:
    if "name " in raw_text:
        names = re.findall(r'name\s+"([^"]+)"', raw_text)
        formatted = ", ".join(f'"{n}"' for n in names)
        if no_none == False:
            result = ["none"]
            for name in names:
                result.append(name)
            print(f"{result},")
        else:
            print(f"[{formatted}],")
else:
    def extract_machine_names(output):
        machines = []
        lines = output.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
            # Split by whitespace, take the first element
            parts = line.split()
            if parts:
                machines.append(parts[0])
        return machines

    # Run and print
    names = extract_machine_names(raw_text)
    print("Filtered Machine List:")
    print(f"{names},")