# Slotlist Reboot

An ArmA 3 mission planning and slotlist management system with Django backend and Vue.js frontend.

## Quick Start with Docker Compose

### Prerequisites
- Docker and Docker Compose
- Steam API Key ([Get one here](https://steamcommunity.com/dev/apikey))

### Development Setup

**Quick Start (Recommended)**:
```bash
git clone <repository-url>
cd slotlist-reboot
```

Put a Steam auth key in a file `.env`

```
CONFIG_STEAM_API_SECRET=
```

Run the services:

`docker compose up`
