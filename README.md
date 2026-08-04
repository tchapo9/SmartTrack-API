# SmartTrack API

SmartTrack est un backend basé sur FastAPI pour le suivi GPS en temps réel, la gestion des appareils, le géorepérage et les alertes.

## But de l’API

L’objectif principal de SmartTrack est de fournir une plateforme back-end capable de :

- Collecter des positions GPS envoyées par des appareils mobiles ou dispositifs IoT.
- Gérer les appareils, leur état, leur connexion et le mode perdu.
- Fournir un historique de localisation et une position actuelle par appareil.
- Détecter des entrées / sorties de zones géographiques (geofencing).
- Générer et suivre des alertes pour les utilisateurs et les administrateurs.
- Offrir des dashboards utilisateurs et administrateurs pour surveiller l’activité.

## Fonctionnalités

- Authentification JWT sécurisée
- Inscription et gestion des comptes utilisateurs
- Enregistrement et modification des appareils
- Activation, désactivation et mode perdu des appareils
- Ingestion de positions GPS en temps réel
- Historique et position actuelle des appareils
- Géofencing et alertes basées sur la localisation
- Dashboard utilisateur et administrateur
- PostgreSQL asynchrone avec SQLAlchemy
- Cache Redis pour les sessions et les données volatiles
- Prise en charge de Neon Postgres via configuration d’environnement
- Migrations Alembic pour la gestion du schéma

## Installation

1. Installer les dépendances :

```bash
pip install -r requirements.txt
```

2. Copier le fichier d’exemple d’environnement :

```bash
copy .env.example .env.local
```

3. Mettre à jour `.env.local` :

- `DATABASE_URL` pour votre PostgreSQL / Neon
- `REDIS_URL` pour votre serveur Redis
- `SECRET_KEY`, `DEBUG`, `CORS_ORIGINS`, etc.

4. Lancer l’application :

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Si vous lancez depuis Docker Compose, assurez-vous que Redis et PostgreSQL/PostGIS sont disponibles.

## Configuration recommandée

Exemple de variables essentielles dans `.env.local` :

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
DEBUG=true
```

## Endpoints principaux

### Authentification

- `POST /api/auth/register` — Création d’un compte utilisateur
- `POST /api/auth/login` — Authentification et récupération de tokens JWT
- `POST /api/auth/refresh` — Rafraîchissement d’un token d’accès
- `GET /api/auth/me` — Récupération du profil de l’utilisateur connecté
- `POST /api/auth/change-password` — Changement du mot de passe
- `POST /api/auth/logout` — Déconnexion

### Utilisateurs

- `GET /api/users/me` — Profil de l’utilisateur connecté
- `GET /api/users/devices` — Liste des appareils de l’utilisateur connecté

### Appareils

- `POST /api/devices/` — Enregistrer un nouvel appareil
- `GET /api/devices/{device_id}` — Récupérer un appareil
- `PUT /api/devices/{device_id}` — Mettre à jour un appareil
- `POST /api/devices/{device_id}/activate` — Activer un appareil
- `POST /api/devices/{device_id}/deactivate` — Désactiver un appareil
- `POST /api/devices/{device_id}/lost-mode` — Activer/désactiver le mode perdu
- `DELETE /api/devices/{device_id}` — Supprimer un appareil

### Tracking / positions

- `POST /api/tracking/location` — Envoi d’une position GPS par UUID d’appareil
- `GET /api/tracking/{device_id}/current` — Position actuelle de l’appareil
- `GET /api/tracking/{device_id}/geojson` — Trajet GeoJSON de l’appareil
- `GET /api/tracking/{device_id}/nearby` — Appareils proches d’un point donné
- `GET /api/tracking/{device_id}/statistics` — Statistiques de localisation de l’appareil

### Localisations

- `GET /api/locations/{device_id}/last` — Dernière position enregistrée
- `GET /api/locations/{device_id}/history` — Historique des positions entre deux dates

### Geofencing

- `POST /api/geofence/` — Créer une zone géographique de surveillance
- `GET /api/geofence/` — Lister les geofences de l’utilisateur
- `GET /api/geofence/{geofence_id}` — Récupérer un geofence
- `PUT /api/geofence/{geofence_id}` — Mettre à jour un geofence
- `DELETE /api/geofence/{geofence_id}` — Supprimer un geofence

### Alertes

- `GET /api/alerts/` — Lister les alertes de l’utilisateur
- `GET /api/alerts/{alert_id}` — Récupérer une alerte
- `PUT /api/alerts/{alert_id}/read` — Marquer une alerte comme lue
- `PUT /api/alerts/{alert_id}/resolve` — Résoudre une alerte

### Dashboard

- `GET /api/dashboard/overview` — Vue d’ensemble des métriques utilisateur
- `GET /api/dashboard/device/{device_id}` — Résumé d’un appareil spécifique

### Administration

- `GET /api/admin/users` — Liste des utilisateurs (admin seulement)
- `GET /api/admin/devices` — Liste des appareils (admin seulement)
- `GET /api/admin/alerts` — Liste des alertes (admin seulement)
- `DELETE /api/admin/users/{user_id}` — Supprimer un utilisateur (admin seulement)

## Documentation API

- OpenAPI : `http://localhost:8000/api/openapi.json`
- Swagger UI : `http://localhost:8000/api/docs`
- ReDoc : `http://localhost:8000/api/redoc`

## Migrations de base de données

Le projet utilise Alembic :

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

> Assurez-vous que `postgis` est activé sur PostgreSQL si vous utilisez des colonnes `Geometry`.

## Tests

```bash
pytest
```

## Notes

- Le middleware `TrustedHostMiddleware` protège l’API selon la configuration `DEBUG` et `CORS_ORIGINS`.
- La valeur `DATABASE_URL` peut être fournie par Neon pour une connexion Postgres gérée.
- Si vous utilisez Docker, démarrez d’abord Redis et PostgreSQL/PostGIS avant l’API.
