# Agrolink - Spec technique (hors partie physique)

Ce document couvre les parties non physiques du projet : ESP8266/IoT, backend web, frontend, securite et RGPD.

## 1) Architecture globale (vue logique)

Flux principal (firmware actuel) :

```
[DHT11 + sonde sol] -> [ESP8266] -> [LCD 20x4 + Serial Monitor]
                                     -> (Wi-Fi / HTTPS) -> [API Backend] -> [DB] -> [Frontend Web]
```

Rappels CDC (pages 10-14) :
- Sous-ensemble implante actuellement : temperature, humidite air, humidite sol.
- ESP8266 en C++ pour capter, afficher localement et synchroniser l'API backend.
- Web app en Python/PHP, stack Django + "Symphony" (probable Symfony).
- Base MariaDB ou MongoDB.
- Securite : protection XSS/SQLi, 2FA, zero-trust.
- RGPD : donnees traitees dans l'UE, usage limite a l'amelioration du service.

## 2) ESP8266 / IoT (firmware, format, protocole)

### 2.1 Capteurs et interfaces (POC actuel)

Objectif : fournir des mesures locales stables avec capteurs reels.
- Temperature + humidite air : DHT11 sur `D5`.
- Humidite sol : sonde analogique sur `A0` (avec calibration `SOIL_DRY` / `SOIL_WET`).
- Affichage local : LCD I2C 20x4 (`D2` SDA, `D1` SCL, adresse `0x27` ou `0x3F`).

### 2.2 Fonctionnalites firmware (C++)

Modules cles :
- Initialisation serie (`115200`) et bus I2C (`Wire.begin(D2, D1)`).
- Lecture DHT11 (temperature/humidite air).
- Lecture analogique sol + conversion en pourcentage (`map` + clamp 0..100).
- Affichage LCD sur 4 lignes + log serie detaille.
- Gestion d'erreur de lecture DHT (`isnan`).

Cadence de mesure :
- Une mesure complete toutes les 3 secondes.

### 2.3 Format des donnees (JSON telemetry)

Le firmware envoie le JSON suivant vers l'API backend :

```json
{
  "ts": "2026-04-13T10:15:00Z",
  "readings": [
    {"type": "temperature", "value": 23.4, "unit": "c"},
    {"type": "humidity_air", "value": 61.2, "unit": "%"},
    {"type": "humidity_soil", "value": 47, "unit": "%"}
  ]
}
```

Notes :
- `ts` en UTC ISO-8601.
- `type` doit etre dans le catalogue backend (`temperature`, `humidity_air`, `humidity_soil`).
- `unit` doit correspondre au catalogue backend.

### 2.4 Protocole de transmission

Mode actif :
- `POST /api/v1/devices/{device_id}/telemetry`
- Header `X-API-Key`
- TLS obligatoire (HTTPS)

## 3) Backend web (API, modele de donnees, auth/2FA, securite)

### 3.1 Stack proposee

Alignement CDC :
- Backend : Django (Python) ou Symfony (PHP).
- Base : MariaDB (recommande pour relations + securite SQL) ou MongoDB.

### 3.2 Modele de donnees (schema minimal)

Tables principales (version relationnelle) :
- `users`: id, email, password_hash, role, totp_secret, created_at, last_login_at.
- `devices`: id, owner_id, name, api_key_hash, status, last_seen_at.
- `readings`: id, device_id, sensor_type, value, unit, measured_at.
- `thresholds`: id, device_id, sensor_type, min_value, max_value, enabled.
- `alerts`: id, device_id, sensor_type, value, triggered_at, resolved_at.
- `audit_logs`: id, actor_id, action, ip, created_at.

Notes :
- Pour MongoDB, `readings` peut etre une collection time-series.
- Prevoir index sur `device_id` + `measured_at`.
- Retention : garder le detail 12 mois, aggreger ensuite (si besoin).

### 3.3 API (exemples d'endpoints)

Auth / sessions :
- `POST /api/v1/auth/login` -> email + password
- `POST /api/v1/auth/2fa/verify` -> code TOTP
- `POST /api/v1/auth/refresh` -> renouvellement token
- `POST /api/v1/auth/logout`

Devices :
- `GET /api/v1/devices`
- `POST /api/v1/devices`
- `GET /api/v1/devices/{id}`
- `PUT /api/v1/devices/{id}`
- `POST /api/v1/devices/{id}/telemetry` (device only)

Readings / Alerts :
- `GET /api/v1/readings?device_id=...&from=...&to=...&limit=...`
- `GET /api/v1/alerts?device_id=...`
- `POST /api/v1/thresholds`

### 3.4 Auth + 2FA

Flux :
1) Login email/password.
2) Si 2FA active, demander TOTP.
3) Emission JWT + refresh token (HTTP-only cookie).

Options 2FA :
- TOTP (Google Authenticator/FreeOTP).
- Codes de secours (backup codes).

### 3.5 Securite web (XSS/SQLi/Zero-trust)

Mesures minimales :
- ORM + requetes parametrees (SQLi).
- Validation stricte des inputs (schemas).
- CSP + echappement HTML (XSS).
- CSRF tokens sur endpoints sensibles.
- Rate limiting sur login + API device.
- Logs d'audit et alertes sur echec d'auth.
- Zero-trust : aucune confiance implicite, moindre privilege, ACL par device/user.

## 4) Frontend (UI, charte graphique, pages cles)

### 4.1 Charte graphique (CDC page 14)

- Police : Times New Roman.
- Couleurs :
  - Gris: #DCDFDA
  - Vert fonce: #C8D6A2
  - Vert clair: #B7CE66
  - Vert: #8FB43A
  - Vert pale: #4B5943

### 4.2 Pages cles

- Login + 2FA.
- Dashboard (cards + charts capteurs).
- Detail device (courbe par capteur, dernieres valeurs).
- Alerts (liste + filtre).
- Parametres (seuils, device, profil, 2FA).
- RGPD/Confidentialite (informations et contact).

### 4.3 Structure UI (exemple)

- Header fixe (logo + navigation).
- Zone centrale : cartes metriques + graphiques.
- Bandeau d'alertes en haut si depassement seuil.
- Tableau des mesures recentes.

### 4.4 Notes UI/UX

- Design sobre, lisible, fonds clairs.
- Couleurs vertes pour etat normal, accentuation pour alertes.
- Formats unifies (POC actuel) : `%`, `c`.

## 5) RGPD + securite (politique et checklist)

### 5.1 RGPD (principes)

- Finalite : suivi des cultures et amelioration du service.
- Donnees collecte es : identite utilisateur, devices, mesures capteurs.
- Base legale : execution du service (contrat) et interet legitime.
- Conservation : duree limitee, suppression ou anonymisation.
- Localisation : UE uniquement (hebergement + sauvegardes).
- Droits : acces, rectification, suppression, portabilite.
- DPO/Contact : email projet pour demandes RGPD.

### 5.2 Checklist securite (synthese)

- TLS obligatoire partout (frontend + API).
- Mots de passe hashes (bcrypt/argon2).
- 2FA active par defaut pour comptes admin.
- JWT courts + refresh tokens securises.
- Permissions par role (user/admin).
- Logs d'audit pour actions sensibles.
- Sauvegardes chiffre es et teste es.
- Scan OWASP basique (XSS/SQLi/CSRF).

## 6) Livrables non-physiques (POC)

- API fonctionnelle + endpoints de telemetry.
- Dashboard web avec mesures temps reel.
- Auth + 2FA.
- Document RGPD + checklist securite.
