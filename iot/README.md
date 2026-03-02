# IoT (ESP8266)

## Quick start (PlatformIO)

1) Update Wi-Fi + API values in `src/main.cpp`.
2) Build and upload with PlatformIO.
3) Monitor serial at 115200.

## Notes

- This firmware sends JSON to the backend endpoint:
  `POST /api/v1/devices/{device_id}/telemetry` using `X-API-Key`.
- The default payload includes 7 sensors: `luminosity`, `air_humidity`, `soil_humidity`, `co2`, `nutrient_index`, `pressure`, `heat`.
- Keep backend sensor catalog in sync in `backend/common/constants.py` (`SENSOR_CATALOG`).
- Replace placeholder sensor functions with real drivers.
