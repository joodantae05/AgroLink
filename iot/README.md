# IoT (ESP8266)

## Quick start (PlatformIO)

1) Update Wi-Fi + API values in `src/main.cpp`.
2) Build and upload with PlatformIO.
3) Monitor serial at 115200.

## Notes

- This firmware sends JSON to the backend endpoint:
  `POST /api/v1/devices/{device_id}/telemetry` using `X-API-Key`.
- Replace placeholder sensor functions with real drivers.
