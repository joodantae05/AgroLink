# Agrolink - Spec technique (hors partie physique)

Ce document couvre les parties non physiques du projet : ESP8266/IoT, backend web, frontend, securite et RGPD.

## 1) Architecture globale (vue logique)

Flux principal :

```
[Capteurs] -> [ESP8266] -> (Wi-Fi / HTTPS) -> [API Backend] -> [DB] -> [Frontend Web]
```

Rappels CDC (pages 10-14) :
- Capteurs retenus pour ce projet : humidite, temperature, pression et acidite du sol (pH).
- ESP8266 en C++ pour capter et transmettre.
- Web app en Python/PHP, stack Django + "Symphony" (probable Symfony).
- Base MariaDB ou MongoDB.
- Securite : protection XSS/SQLi, 2FA, zero-trust.
- RGPD : donnees traitees dans l'UE, usage limite a l'amelioration du service.

## 2) ESP8266 / IoT (firmware, format, protocole)

### 2.1 Capteurs et interfaces (POC)

Objectif : fournir des mesures propres et exploitables, sans choix definitif de model.
- Humidite : capteur 1-wire/I2C (ex. DHT22/SHT).
- Temperature : capteur 1-wire/I2C (ex. DHT22/SHT).
- Pression : capteur I2C (ex. BMP280/BME280).
- Acidite du sol : sonde pH analogique (avec calibration 2 points).

### 2.2 Fonctionnalites firmware (C++)

Modules cles :
- Boot + config Wi-Fi.
- Drivers capteurs + calibration basique.
- Planificateur de mesures (intervalle fixe).
- Packaging des donnees (JSON).
- Transmission HTTPS + retries.
- Buffer local (ring buffer) en cas d'absence reseau.
- Time sync (NTP) pour horodatage.
- OTA (optionnel si temps dispo).

Exemple d'intervalle de mesure :
- Toutes les 5 min pour POC.
- Envoi par lot toutes les 5-10 mesures si batterie ou reseau fragile.

### 2.3 Format des donnees (JSON)

Exemple de payload JSON (ASCII) :

```json
{
  "device_id": "agrolink-esp-001",
  "ts": "2025-02-01T10:15:00Z",
  "readings": [
    {"type": "humidity", "value": 61.2, "unit": "%"},
    {"type": "temperature", "value": 23.4, "unit": "c"},
    {"type": "pressure", "value": 1009.2, "unit": "hpa"},
    {"type": "soil_ph", "value": 6.4, "unit": "ph"}
  ]
}
```

Notes :
- `ts` en UTC ISO-8601.
- `type` enumere les types de capteurs.
- `unit` stabilise l'interpretation cote backend.

### 2.4 Protocole de transmission

Choix simple et robuste : HTTPS POST.
- Endpoint : `POST /api/v1/devices/{device_id}/telemetry`
- Authentification device : token long terme (API key) ou JWT device.
- TLS obligatoire, pas de HTTP.

Fiabilite :
- 3 retries avec backoff.
- En cas d'echec, stocker jusqu'a N mesures dans un buffer local.
- Champ `battery` optionnel si alimentation autonome.

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
- Formats unifies : `%`, `c`, `hpa`, `ph`.

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
