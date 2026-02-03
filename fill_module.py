import re

raw_text = """
name "diag288", desc "diag288 device for s390x platform"
"""
no_none = False
HNC = True
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