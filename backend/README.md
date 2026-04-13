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
- Latest telemetry snapshot: `GET /api/v1/snapshot`
- Telemetry: `POST /api/v1/devices/{device_id}/telemetry` (X-API-Key header)
- API catalog: `GET /api/v1/api-catalog`
- Observability dashboard: `GET /api/v1/observability`

## Sensors alignment with IoT

The backend sensor catalog is defined in `common/constants.py` (`SENSOR_CATALOG`).

- Keep `type` and `unit` aligned with the payload sent by `iot/src/main.cpp`.
- `POST /api/v1/devices/{device_id}/telemetry` only ingests known sensor types.
- If a unit is provided and does not match the catalog unit, the reading is ignored.
- Current sensors: `temperature`, `humidity_air`, `humidity_soil`.
- `GET /api/v1/snapshot` returns the latest stored DB value for each sensor (per device, or latest active device).
- Optional filter: `GET /api/v1/snapshot?device_id=<uuid>`.

## Security (XSS / SQL Injection)

- SQL injection: API queries use Django ORM parameterization (no raw SQL in app code).
- Input validation: strict serializers on auth and device naming constraints in API.
- Browser hardening: `X-Frame-Options`, `X-Content-Type-Options`, strict referrer policy, secure cookies and optional HSTS/HTTPS redirect.
- Frontend XSS mitigation: dynamic HTML values are escaped before rendering.

## API/DB visualization

- `GET /api/v1/api-catalog`: liste des routes backend.
- `GET /api/v1/observability?limit=100`: trafic API recent (in/out) + activite BDD (SELECT/INSERT/UPDATE/DELETE par requete API) + evenements BDD observes (insert/update/delete).
- `POST /api/v1/observability/clear`: vide les buffers d'observation.

Notes:
- En `DEBUG=1`, ces endpoints sont accessibles sans authentification pour faciliter le debug.
- Les donnees d'observation sont en memoire (non persistantes), videes au redemarrage.
- `db_events` capture les operations ecriture passees par Django (API), pas les ecritures faites directement dans MariaDB par un outil externe.
