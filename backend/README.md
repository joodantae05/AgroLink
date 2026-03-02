# Backend (Django + MariaDB)

## Setup with Docker

1) Copy env file:

```
cp .env.example .env
```

2) Run containers:

```
docker compose up --build
```

3) Create admin user:

```
docker compose exec backend python manage.py createsuperuser
```

## Local setup (no Docker)

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## API quick test

- Login: `POST /api/v1/auth/login`
- 2FA verify: `POST /api/v1/auth/2fa/verify`
- Devices: `GET /api/v1/devices`
- Sensors catalog: `GET /api/v1/sensors`
- Telemetry: `POST /api/v1/devices/{device_id}/telemetry` (X-API-Key header)

## Sensors alignment with IoT

The backend sensor catalog is defined in `common/constants.py` (`SENSOR_CATALOG`).

- Keep `type` and `unit` aligned with the payload sent by `iot/src/main.cpp`.
- `POST /api/v1/devices/{device_id}/telemetry` only ingests known sensor types.
- If a unit is provided and does not match the catalog unit, the reading is ignored.
- Current sensors: `luminosity`, `air_humidity`, `soil_humidity`, `co2`, `nutrient_index`, `pressure`, `heat`.

## Security (XSS / SQL Injection)

- SQL injection: API queries use Django ORM parameterization (no raw SQL in app code).
- Input validation: strict serializers on auth and device naming constraints in API.
- Browser hardening: `X-Frame-Options`, `X-Content-Type-Options`, strict referrer policy, secure cookies and optional HSTS/HTTPS redirect.
- Frontend XSS mitigation: dynamic HTML values are escaped before rendering.
