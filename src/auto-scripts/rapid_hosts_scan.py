import os
import subprocess
import json
from datetime import datetime

def get_active_interface():
    try:
        result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True)
        interfaces = [line.split(":")[1].strip() for line in result.stdout.split("\n") if "state UP" in line]
        for iface in interfaces:
            if "eth" in iface:
                return iface, False  # Ethernet
        for iface in interfaces:
            if "wlan" in iface:
                return iface, True  # Wi-Fi
    except Exception as e:
        print(f"Error detecting interface: {e}")
    return None, False

def scan_hosts():
    """Run arp-scan on the active interface and return detected hosts."""
    interface, is_wifi = get_active_interface()
    output = []

    if not interface:
        output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No active interface found.")
        return {"messages": output, "seen_ips": 0, "hosts": [], "interface": interface}

    connection_type = "Wi-Fi" if is_wifi else "Ethernet"
    output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connection detected on {interface} ({connection_type}).")

    try:
        result = subprocess.run(["sudo", "arp-scan", "--interface", interface, "--localnet"], capture_output=True, text=True)
        hosts = [line.split()[0] for line in result.stdout.splitlines() if line.startswith("192.")]
        output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scan completed. Found {len(hosts)} devices.")
        return {"messages": output, "seen_ips": len(hosts), "hosts": hosts, "interface": interface}
    except Exception as e:
        output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error running arp-scan: {e}")
        return {"messages": output, "seen_ips": 0, "hosts": [], "interface": interface}

if __name__ == "__main__":
    result = scan_hosts()
    print(json.dumps(result, indent=2))
