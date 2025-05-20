import subprocess

def get_wifi_name():
    try:
        # Get SSID
        output = subprocess.check_output(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'], text=True, stderr=subprocess.STDOUT)
        ssid = "No Wi-Fi Connected"
        for line in output.splitlines():
            if line.startswith("yes:"):
                ssid = line.split(":")[1].strip()
                break

        ip = ""
        mac = ""
        if ssid != "No Wi-Fi Connected":
            # Find the active interface
            output = subprocess.check_output(['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE', 'device'], text=True, stderr=subprocess.STDOUT)
            wifi_interface = None
            for line in output.splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and parts[1] == "wifi" and parts[2] == "connected":
                    wifi_interface = parts[0]
                    break
            if wifi_interface:
                # Get IP and MAC
                output = subprocess.check_output(['ip', 'addr', 'show', wifi_interface], text=True, stderr=subprocess.STDOUT)
                for line in output.splitlines():
                    if "inet " in line:
                        ip = line.split()[1].split("/")[0]
                    if "link/ether" in line:
                        mac = line.split()[1]

        return {"ssid": ssid, "ip": ip, "mac": mac}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"ssid": "Wi-Fi Detection Error", "ip": "", "mac": ""}
