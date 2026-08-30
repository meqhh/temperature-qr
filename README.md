# Temperature QR Server

A simple WebSocket + HTTP server (Python, `aiohttp`) that displays temperature and humidity data from a DHT11 sensor on an ESP32, and publishes it as a QR code that updates in real time on a web page.

## Folder Structure

```
backend/
├── server.py           # Main server (HTTP + WebSocket)
├── requirements.txt    # Python dependencies
└── static/
    └── index.html       # Frontend (temperature, humidity, QR code display)
```

## How It Works

```
ESP32 (WebSocket client)
        │
        │  {"type": "data", "suhu": 27.5, "kelembapan": 60.2}
        ▼
 server.py (WebSocket server, endpoint /ws)
        │
        │  broadcasts to all connected browsers
        ▼
 Browser / index.html (WebSocket client)
        │
        │  re-renders QR code with the latest data
        ▼
   Updated QR code
```

The server distinguishes client types via their first message (`hello`):

| Role       | First message                                    | Purpose                                       |
|------------|----------------------------------------------------|------------------------------------------------|
| `device`   | `{"type": "hello", "role": "device"}`             | Sends sensor data periodically                  |
| `frontend` | `{"type": "hello", "role": "frontend"}`           | Receives broadcast data for display             |

## Installation

Make sure Python 3.9+ is installed, then:

```bash
cd backend
pip install -r requirements.txt
```

## Running the Server

```bash
python server.py
```

The server runs on `http://0.0.0.0:8080`, accessible via:

- **From the same machine:** `http://localhost:8080` or `http://127.0.0.1:8080`
- **From another device on the same network (phone, other laptop):** `http://<server-computer-IP>:8080`

How to find your computer's IP:
- Windows: `ipconfig` → look for "IPv4 Address"
- macOS/Linux: `ifconfig` or `ip addr`

## WebSocket Message Format

### Device → Server

```json
{ "type": "hello", "role": "device" }
```

```json
{ "type": "data", "suhu": 27.5, "kelembapan": 60.2 }
```

### Server → Frontend

```json
{
  "type": "update",
  "suhu": 27.5,
  "kelembapan": 60.2,
  "timestamp": "2026-08-30T14:22:05"
}
```

## Endpoints

| Endpoint     | Method    | Description                                    |
|--------------|-----------|--------------------------------------------------|
| `/`          | GET       | Serves the frontend page (`index.html`)          |
| `/ws`        | WebSocket | Realtime connection for both device and frontend |
| `/static/*`  | GET       | Serves additional static files (CSS/JS/etc.)      |

## Troubleshooting

| Issue                                          | Likely Cause                                                          |
|--------------------------------------------------|--------------------------------------------------------------------------|
| QR code isn't updating                         | Device isn't connected, or sent the wrong `role` in its `hello` message |
| Browser can't reach the server                 | Firewall is blocking port 8080, or the IP address is wrong               |
| `ConnectionRefusedError` on the device          | Server isn't running, or the IP/port in the device code is incorrect     |
| Sensor data never reaches the frontend          | Device hasn't sent a `hello` message with `role: device` first          |

## Future Improvements

- Add data history storage (e.g. SQLite or CSV file) in `server.py`.
- Add simple authentication (token) in the `hello` message so not just any client can send data.
- Deploy with `systemd` (Linux) or `nssm` (Windows) so the server starts automatically on boot.
- Make the default port (8080) configurable via an environment variable.

## License

Free to use and modify for personal or educational purposes.