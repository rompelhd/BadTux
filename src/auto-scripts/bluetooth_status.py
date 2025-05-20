import subprocess

def get_bluetooth_info():
    try:
        output = subprocess.check_output(['bluetoothctl', 'show'], text=True, stderr=subprocess.STDOUT)
        active = any("Powered: yes" in line.lower() for line in output.splitlines())
        devices = []
        if active:
            output = subprocess.check_output(['bluetoothctl', 'paired-devices'], text=True, stderr=subprocess.STDOUT)
            for line in output.splitlines():
                if line.startswith("Device"):
                    mac = line.split()[1]
                    info = subprocess.check_output(['bluetoothctl', 'info', mac], text=True, stderr=subprocess.STDOUT)
                    if "Connected: yes" in info:
                        device_name = line.split(' ', 2)[2].strip()
                        devices.append(device_name)
        return {"active": active, "devices": devices}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"active": False, "devices": [], "error": "Bluetooth Detection Error"}
