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
- Telemetry: `POST /api/v1/devices/{device_id}/telemetry` (X-API-Key header)
