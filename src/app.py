from flask import Flask, render_template, request, jsonify, Response
import random
import datetime
import sys
import os
import sqlite3
import time
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'auto-scripts'))
from get_wifi import get_wifi_name
from bluetooth_status import get_bluetooth_info

app = Flask(__name__)

DB_PATH = "/home/raspi/tamv4/tamagotchi.db"

tamagotchi_sayings = [
    "Hello human!",
    "I'm hungry...",
    "Give me commands!",
    "I'm happy :D",
    "Zzz... resting.",
]

state = {
    "open_ports": 0,
    "scanned_networks": 0,
    "seen_ips": 0,
    "seen_gateways": 0,
    "messages": [],
    "tamagotchi_msg": random.choice(tamagotchi_sayings),
    "wifi_ssid": "N/A",
    "wifi_ip": "N/A",
    "wifi_mac": "N/A",
    "bluetooth_active": False,
    "bluetooth_devices": [],
}

def add_debug_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state["messages"].insert(0, f"[{timestamp}] [debug] {message}")

def get_latest_scan_results():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute("SELECT scan_id, scan_time, interface, ssid, mac FROM wifi_scans ORDER BY scan_time DESC LIMIT 1")
        wifi_scan = c.fetchone()

        messages = []
        seen_ips = 0
        seen_gateways = 0
        open_ports = 0
        scanned_networks = 0

        if wifi_scan:
            scan_id, scan_time, interface, ssid, mac = wifi_scan
            messages.append(f"[{scan_time}] Wi-Fi: {ssid} (MAC: {mac}, {interface})")
            scanned_networks = 1

            c.execute("SELECT id, ip FROM hosts WHERE scan_id = ?", (scan_id,))
            hosts = c.fetchall()
            host_ids = {row[1]: row[0] for row in hosts}
            messages.extend([f"[{scan_time}] Host found: {ip}" for ip in host_ids.keys()])
            seen_ips = len(hosts)

            c.execute("SELECT h.ip, p.port, p.service FROM ports p JOIN hosts h ON p.host_id = h.id WHERE h.scan_id = ?", (scan_id,))
            ports = c.fetchall()
            messages.extend([f"[{scan_time}] Open port: {ip}:{port} ({service})" for ip, port, service in ports])
            open_ports = len(ports)

            c.execute("SELECT gateway FROM gateways WHERE scan_id = ?", (scan_id,))
            gateways = [row[0] for row in c.fetchall()]
            messages.extend([f"[{scan_time}] Active gateway: {gateway}" for gateway in gateways])
            seen_gateways = len(gateways)

        messages.sort(reverse=True)
        return {
            "messages": messages,
            "seen_ips": seen_ips,
            "seen_gateways": seen_gateways,
            "open_ports": open_ports,
            "scanned_networks": scanned_networks,
            "tamagotchi_msg": f"Last scan: {scanned_networks} network, {seen_ips} hosts, {seen_gateways} gateways, {open_ports} ports."
        }

def stream_scan_status():
    def generate():
        last_id = 0
        while True:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT id, timestamp, status FROM scan_status WHERE id > ? ORDER BY id DESC LIMIT 1", (last_id,))
                row = c.fetchone()
                if row:
                    last_id, timestamp, status = row
                    yield f"data: {json.dumps({'timestamp': timestamp, 'status': status})}\n\n"
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

@app.route("/", methods=["GET"])
def index():
    wifi_info = get_wifi_name()
    add_debug_message(f"Testing Wi-Fi AP: SSID={wifi_info['ssid']}, IP={wifi_info['ip']}, MAC={wifi_info['mac']}")
    add_debug_message("Testing Bluetooth connection")
    bluetooth_info = get_bluetooth_info()
    state["wifi_ssid"] = wifi_info["ssid"]
    state["wifi_ip"] = wifi_info["ip"]
    state["wifi_mac"] = wifi_info["mac"]
    state["bluetooth_active"] = bluetooth_info["active"]
    state["bluetooth_devices"] = bluetooth_info["devices"]

    db_results = get_latest_scan_results()
    state["messages"] = db_results["messages"]
    state["seen_ips"] = db_results["seen_ips"]
    state["seen_gateways"] = db_results["seen_gateways"]
    state["open_ports"] = db_results["open_ports"]
    state["scanned_networks"] = db_results["scanned_networks"]
    state["tamagotchi_msg"] = db_results["tamagotchi_msg"]

    return render_template("index.html", **state)

@app.route("/stream")
def stream():
    return stream_scan_status()

@app.route("/command", methods=["POST"])
def command():
    cmd = request.form.get("cmd", "").lower()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_debug_message(f"Processing command: {cmd}")

    if cmd == "help":
        result = "Available command: 'help' - Shows this help. Wi-Fi, host, gateway, and port scans are performed automatically every 5 minutes by a systemd service."
        state["messages"].insert(0, f"[{timestamp}] $ {cmd} -> {result}")
        state["tamagotchi_msg"] = "Here's the help!"
    else:
        result = "Only the 'help' command is allowed. Scans are automatic."
        state["messages"].insert(0, f"[{timestamp}] $ {cmd} -> {result}")
        state["tamagotchi_msg"] = "Use 'help' for commands!"

    return jsonify({
        "open_ports": state["open_ports"],
        "scanned_networks": state["scanned_networks"],
        "seen_ips": state["seen_ips"],
        "seen_gateways": state["seen_gateways"],
        "messages": state["messages"],
        "tamagotchi_msg": state["tamagotchi_msg"],
        "wifi_ssid": state["wifi_ssid"],
        "wifi_ip": state["wifi_ip"],
        "wifi_mac": state["wifi_mac"],
        "bluetooth_active": state["bluetooth_active"],
        "bluetooth_devices": state["bluetooth_devices"]
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
