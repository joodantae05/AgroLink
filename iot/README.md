# IoT (ESP8266)

## Quick start (PlatformIO)

1) Connect:
   - DHT11 on `D5`
   - Soil sensor on `A0`
   - I2C LCD (20x4) on `D2` (SDA) and `D1` (SCL)
2) Adjust soil calibration values in `src/main.cpp`:
   - `SOIL_DRY`
   - `SOIL_WET`
3) Configure network/API in `src/main.cpp`:
   - `WIFI_SSID`
   - `WIFI_PASS`
   - `API_HOST`
   - `API_PATH`
   - `API_KEY`
4) Build/upload with PlatformIO.
5) Monitor serial at `115200`.

## Firmware behavior

- Reads:
  - Air temperature (`DHT11`)
  - Air humidity (`DHT11`)
  - Soil humidity (`A0`, converted to % with calibration)
- Displays live values on LCD 20x4.
- Logs readings to serial every 3 seconds.
- Sends HTTPS telemetry every 15 seconds to:
  - `POST /api/v1/devices/{device_id}/telemetry`
  - Header `X-API-Key`

## Backend alignment

- The backend sensor catalog must match the IoT sensor naming in `backend/common/constants.py`.
- Current sensor types used by the project:
  - `temperature` (`c`)
  - `humidity_air` (`%`)
  - `humidity_soil` (`%`)
