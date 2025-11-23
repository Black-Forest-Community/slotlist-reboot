# Production Deployment

This directory contains the production deployment configuration for the Slotlist application.

## Prerequisites

- Docker and Docker Compose v2.0+
- Domain name configured (optional, but recommended)
- SSL certificates (optional, for HTTPS)
- Steam API key

## Quick Start

### 1. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cd deployment
cp .env.example .env
```

Edit `.env` and set all required values:

- **Database credentials**: Change `DB_PASSWORD` to a strong password
- **Django secret key**: Generate a new secret key
- **JWT secret**: Generate a new JWT secret
- **Steam API key**: Add your Steam API key from https://steamcommunity.com/dev/apikey
- **Domain configuration**: Set your domain name in `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, etc.

### 2. Start the Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

This will start:
- PostgreSQL database (internal network only)
- Django backend with Gunicorn (internal network only)
- Nginx frontend serving the Vue.js app and proxying API requests (exposed on ports 80/443)

### 3. Verify the Deployment

Check that all services are running:

```bash
docker-compose -f docker-compose.prod.yml ps
```

Check the logs:

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

Access the application:
- Frontend: http://your-domain.com (or http://localhost if testing locally)
- API: http://your-domain.com/api/
- Health check: http://your-domain.com/health

## SSL/HTTPS Configuration

### Option 1: Using Let's Encrypt with Certbot

1. Install certbot on your host machine:
```bash
sudo apt-get install certbot
```

2. Obtain SSL certificates:
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

3. Create SSL directory and copy certificates:
```bash
mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*.pem
```

4. Uncomment the HTTPS server block in `nginx/default.conf`

5. Update `.env` to redirect HTTP to HTTPS (uncomment the redirect in `nginx/default.conf`)

6. Restart the frontend service:
```bash
docker-compose -f docker-compose.prod.yml restart frontend
```

### Option 2: Using a Reverse Proxy (Recommended)

For production deployments, it's recommended to use a reverse proxy like:
- Traefik (with automatic Let's Encrypt)
- Nginx Proxy Manager
- Caddy (with automatic HTTPS)

These handle SSL termination and can be placed in front of this application.

## Service Architecture

```
                    ┌─────────────────┐
                    │   Nginx (80)    │
                    │   Frontend      │
                    └────────┬────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
         ┌─────────▼────────┐  ┌──────▼──────────┐
         │  Vue.js Static   │  │  Django API     │
         │  Files (SPA)     │  │  (Gunicorn)     │
         └──────────────────┘  └────────┬────────┘
                                        │
                                ┌───────▼────────┐
                                │  PostgreSQL    │
                                │   Database     │
                                └────────────────┘
```

- **Nginx** serves the Vue.js frontend and proxies `/api/` requests to the backend
- **Django backend** runs with Gunicorn WSGI server
- **PostgreSQL** database is only accessible from within the Docker network

## Configuration Files

### docker-compose.prod.yml
Main production Docker Compose configuration with:
- Production-ready service definitions
- Health checks for all services
- Restart policies (`unless-stopped`)
- Internal network for service communication
- Environment variable configuration

### nginx/nginx.conf
Main Nginx configuration with:
- Performance optimizations (gzip, keepalive)
- Security settings (server_tokens off)
- Rate limiting zones
- Multiple worker processes

### nginx/default.conf
Virtual host configuration with:
- Static file serving for Vue.js SPA
- API proxy configuration to Django backend
- Optional HTTPS/SSL configuration
- Security headers
- Static asset caching

### .env.example
Template for production environment variables

## Maintenance

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f db
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart services
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backup Database

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres slotlist > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres slotlist < backup_20231120_120000.sql
```

### Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes database)
docker-compose -f docker-compose.prod.yml down -v
```

## Security Considerations

1. **Environment Variables**: Never commit the `.env` file to version control
2. **Secrets**: Use strong, randomly generated secrets for Django and JWT
3. **Database**: The database is only accessible from within the Docker network
4. **SSL/TLS**: Always use HTTPS in production with valid certificates
5. **CORS**: Configure `CORS_ALLOWED_ORIGINS` to only allow your domain
6. **Rate Limiting**: Nginx is configured with rate limiting for API endpoints
7. **Updates**: Keep Docker images and dependencies up to date

## Troubleshooting

### Services Won't Start

Check logs for specific errors:
```bash
docker-compose -f docker-compose.prod.yml logs
```

Common issues:
- Port 80/443 already in use: Stop other web servers or change `FRONTEND_PORT`
- Database connection failed: Check `DB_*` environment variables
- Backend unhealthy: Check `CONFIG_*` environment variables

### Cannot Access Application

1. Check if services are running:
```bash
docker-compose -f docker-compose.prod.yml ps
```

2. Check firewall rules:
```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

3. Check Nginx logs:
```bash
docker-compose -f docker-compose.prod.yml logs frontend
```

### Database Issues

Access the database shell:
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U postgres slotlist
```

Reset database (WARNING: deletes all data):
```bash
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

## Performance Tuning

### Nginx

Edit `nginx/nginx.conf` to adjust:
- `worker_processes`: Set to number of CPU cores
- `worker_connections`: Increase for high traffic
- `gzip_comp_level`: Balance between CPU usage and compression

### Gunicorn

The backend Dockerfile uses Gunicorn with default settings. For production tuning:

1. Create a custom Gunicorn configuration file
2. Mount it in `docker-compose.prod.yml`
3. Adjust workers, threads, and timeout based on your needs

Recommended starting point:
- Workers: (2 × CPU cores) + 1
- Threads: 2-4 per worker
- Timeout: 30-60 seconds

### PostgreSQL

For high-traffic deployments, consider:
- Adjusting PostgreSQL configuration (shared_buffers, work_mem, etc.)
- Using connection pooling (PgBouncer)
- Setting up read replicas

## Monitoring

Consider adding monitoring and alerting:
- **Logs**: Use a log aggregation service (ELK stack, Loki, etc.)
- **Metrics**: Prometheus + Grafana for metrics
- **Uptime**: UptimeRobot or similar for availability monitoring
- **APM**: Application Performance Monitoring (New Relic, DataDog, etc.)

## Support

For issues specific to this deployment:
1. Check the logs
2. Review this README
3. Check the main project README
4. Open an issue on GitHub
