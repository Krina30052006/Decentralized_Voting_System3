import re
import os

path = r"blockchain/full_deploy.txt"
if os.path.exists(path):
    with open(path, "rb") as f:
        data = f.read()
    
    # Handle UTF-16 (common for PS redirects) or UTF-8
    try:
        text = data.decode("utf-16") if b"\xff\xfe" in data[:2] else data.decode("utf-8")
    except:
        text = data.decode("latin-1")
    
    match = re.search(r"0x[a-fA-F0-9]{40}", text)
    if match:
        print(match.group(0))
    else:
        print("NOT_FOUND")
else:
    print("FILE_NOT_FOUND")
