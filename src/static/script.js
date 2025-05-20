const penguin = document.getElementById('penguin');
const cmdInput = document.getElementById('cmd-input');
const commandForm = document.getElementById('command-form');
const stateDisplay = document.getElementById('penguin-state');
const consoleDiv = document.getElementById('console');
const tamagotchiMsg = document.getElementById('tamagotchi-msg');
const openPorts = document.getElementById('open-ports');
const scannedNetworks = document.getElementById('scanned-networks');
const seenIps = document.getElementById('seen-ips');
const seenGateways = document.getElementById('seen-gateways');
const wifiSsid = document.getElementById('wifi-ssid');
const wifiIp = document.getElementById('wifi-ip');
const wifiMac = document.getElementById('wifi-mac');
const bluetoothStatus = document.getElementById('bluetooth-status');
const bluetoothDevices = document.getElementById('bluetooth-devices');
const expressions = ['based', 'neutral'];

function removeAllExpressions() {
    penguin.classList.remove(...expressions);
}

function setExpression(expression) {
    removeAllExpressions();
    penguin.classList.add(expression);
    stateDisplay.textContent = expression.charAt(0).toUpperCase() + expression.slice(1);
}

function getRandomExpression() {
    return expressions[Math.floor(Math.random() * expressions.length)];
}

function updatePenguinExpression(command) {
    let expression;
    if (command.includes('help')) {
        expression = 'neutral';
    } else {
        expression = getRandomExpression();
    }
    setExpression(expression);
}

function updateUI(data) {
    openPorts.textContent = data.open_ports;
    scannedNetworks.textContent = data.scanned_networks;
    seenIps.textContent = data.seen_ips;
    seenGateways.textContent = data.seen_gateways;
    consoleDiv.innerHTML = data.messages.map(msg =>
        `<div class="${msg.includes('[debug]') ? 'debug' : ''}">${msg}</div>`
    ).join('');
    consoleDiv.scrollTop = consoleDiv.scrollHeight;
    tamagotchiMsg.textContent = data.tamagotchi_msg;
    wifiSsid.textContent = data.wifi_ssid;
    wifiIp.textContent = data.wifi_ip || 'N/A';
    wifiMac.textContent = data.wifi_mac || 'N/A';
    bluetoothStatus.textContent = data.bluetooth_active ? 'On' : 'Off';
    bluetoothDevices.textContent = data.bluetooth_devices.length > 0 ? data.bluetooth_devices.join(', ') : 'None';
}

function setupSSE() {
    const source = new EventSource('/stream');
    source.onmessage = function(event) {
        const data = JSON.parse(event.data);
        const message = `[${data.timestamp}] Status: ${data.status}`;
        consoleDiv.innerHTML = `<div>${message}</div>` + consoleDiv.innerHTML;
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
        tamagotchiMsg.textContent = data.status;
    };
    source.onerror = function() {
        consoleDiv.innerHTML = `<div>[${new Date().toLocaleTimeString()}] Error in status connection</div>` + consoleDiv.innerHTML;
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
    };
}

function initializePenguin() {
    updatePenguinExpression('');
}

function setupEventListeners() {
    cmdInput.placeholder = "Type 'help' for help (automatic scans by systemd service)";
    commandForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const command = cmdInput.value.toLowerCase();
        if (!command) return;
        updatePenguinExpression(command);
        try {
            const formData = new FormData(commandForm);
            const response = await fetch('http://localhost:5000/command', {
                method: 'POST',
                body: formData
            });
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            updateUI(data);
            cmdInput.value = '';
        } catch (error) {
            console.error('Error submitting command:', error);
            consoleDiv.innerHTML = `<div>[${new Date().toLocaleTimeString()}] Error processing command</div>` + consoleDiv.innerHTML;
        }
    });

    setInterval(() => {
        updatePenguinExpression('');
    }, 5000);
}

initializePenguin();
setupEventListeners();
setupSSE();
