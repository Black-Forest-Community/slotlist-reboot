# Deployment Configuration

This directory contains the production deployment configuration for slotlist-reboot.

## Features

- **Traefik Reverse Proxy**: Automatic HTTPS with Let's Encrypt
- **Domain Routing**:
  - `slotlist.online` → Frontend
  - `api.slotlist.online` → Backend API
  - `traefik.slotlist.online` → Traefik Dashboard (optional)
- **Persistent Volumes**:
  - PostgreSQL database
  - Media files (user uploads)
  - Static files
  - SSL certificates
- **Automatic HTTP to HTTPS redirect**
- **Container restart policies**
- **Watchtower**: Automatic container updates every 15 minutes

## Prerequisites

1. Docker and Docker Compose installed
2. Domain names pointing to your server:
   - `slotlist.online` → Server IP
   - `api.slotlist.online` → Server IP
   - `traefik.slotlist.online` → Server IP (optional)
3. Ports 80 and 443 open in firewall

## Setup

1. **Copy environment file**:

   ```bash
   cp .env.example .env
   ```
2. **Configure environment variables** in `.env`:

   - Set secure passwords for `DB_PASSWORD`, `DJANGO_SECRET_KEY`, and `CONFIG_JWT_SECRET`
   - Add your Steam API key (`CONFIG_STEAM_API_KEY`)
   - Set your email for Let's Encrypt (`ACME_EMAIL`)
   - Optional: Set Traefik dashboard password (`TRAEFIK_AUTH`)

   **Important**: Ensure the user running Docker has proper permissions:

   ```bash
   # On the server, add your user to the docker group
   sudo usermod -aG docker $USER
   # Then log out and back in, or run:
   newgrp docker
   ```
3. **Generate secure secrets**:

   ```bash
   # Django secret key (50+ characters)
   python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

   # JWT secret (32+ characters)
   openssl rand -hex 32

   # Database password
   openssl rand -base64 32

   # Traefik dashboard auth (replace 'your_password')
   htpasswd -nb admin your_password | sed -e s/\\$/\\$\\$/g
   ```
4. **Start services**:

   ```bash
   docker-compose up -d
   ```
5. **Check logs**:

   ```bash
   docker-compose logs -f
   ```

## SSL Certificates

Let's Encrypt certificates are automatically obtained and renewed by Traefik. The first startup may take a minute while certificates are being requested.

Certificates are stored in the `traefik_letsencrypt` volume at `/letsencrypt/acme.json`.

## Volumes

Persistent data is stored in Docker volumes:

- `postgres_data`: PostgreSQL database
- `media_files`: User-uploaded files (mission images, etc.)
- `static_files`: Django static files (CSS, JS, admin interface)
- `traefik_letsencrypt`: SSL certificates

### Backup Volumes

```bash
# Backup database
docker-compose exec db pg_dump -U postgres slotlist > backup_$(date +%Y%m%d).sql

# Backup media files
docker run --rm -v deployment_media_files:/data -v $(pwd):/backup ubuntu tar czf /backup/media_backup_$(date +%Y%m%d).tar.gz /data

# Restore database
docker-compose exec -T db psql -U postgres slotlist < backup.sql

# Restore media files
docker run --rm -v deployment_media_files:/data -v $(pwd):/backup ubuntu tar xzf /backup/media_backup.tar.gz -C /
```

## Traefik Dashboard

Access the Traefik dashboard at `https://traefik.slotlist.online` with the credentials set in `TRAEFIK_AUTH` (default: admin/admin).

To disable the dashboard, remove or comment out the traefik-related labels in the `traefik` service.

## Monitoring

Check service health:

```bash
docker-compose ps
```

View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f traefik
```

## Updates

### Manual Updates

Update to the latest images manually:

```bash
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### SSL Certificate Issues

If Let's Encrypt rate limits are hit, certificates will be retried. Check Traefik logs:

```bash
docker-compose logs traefik | grep acme
```

### Backend Not Accessible

Check backend health:

```bash
docker-compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/status').read())"
```

### Media Files Not Persisting

Ensure the media volume is mounted:

```bash
docker volume inspect deployment_media_files
```

## Security Notes

1. **Change all default passwords** in `.env`
2. **Keep `.env` file secure** - never commit to git
3. **Enable firewall** - only ports 80 and 443 should be open
4. **Regular backups** - backup database and media files regularly
5. **Update regularly** - keep Docker images updated

## Network Architecture

```
Internet (HTTPS)
    ↓
Traefik (443) → Let's Encrypt
    ↓
    ├─→ slotlist.online → Frontend (port 80)
    ├─→ api.slotlist.online → Backend (port 8000)
    └─→ traefik.slotlist.online → Dashboard
```

All services communicate on the `slotlist-network` Docker network.
