import json
import os
from datetime import datetime
from rapid_hosts_scan import get_active_interface

def check_gateway(ip):
    response = os.system(f"ping -c 1 -W 1 {ip} > /dev/null 2>&1")
    return response == 0

def scan_gateways():
    interface, _ = get_active_interface()
    output = [f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning possible gateways in the range 192.168.0.1 - 192.168.255.1..."]
    active_gateways = []

    for i in range(0, 256, 4):
        ips = [f"192.168.{i+j}.1" for j in range(4) if i+j <= 255]
        output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning: {', '.join(ips)}")

        for ip in ips:
            if check_gateway(ip):
                output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✔ Active subnet at: {ip}")
                active_gateways.append(ip)

        output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] -----------------------------")

    output.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scan completed. Found {len(active_gateways)} active gateways.")

    return {
        "messages": output,
        "seen_gateways": len(active_gateways),
        "active_gateways": active_gateways,
        "interface": interface
    }

if __name__ == "__main__":
    result = scan_gateways()
    print(json.dumps(result, indent=2))
