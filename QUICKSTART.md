# Quick Start Guide

## Prerequisites

✅ Docker Desktop installed and running  
✅ Ports 5432 and 8501 available  
✅ 2GB free disk space  

## 🚀 Start in 3 Steps

### 1. Clone & Navigate
```bash
git clone <repository-url>
cd docker_container
```

### 2. Start the Application

**Windows:**
```powershell
.\run.bat start
```

**Linux/Mac:**
```bash
docker-compose up -d
```

### 3. Access Dashboard
Open browser: **http://localhost:8501**

## 📋 Common Commands

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Rebuild after code changes
docker-compose build
docker-compose up -d

# Fresh start (removes all data)
docker-compose down -v
docker-compose up -d
```

## 🔧 Windows Helper Script

```powershell
.\run.bat start      # Start containers
.\run.bat stop       # Stop containers
.\run.bat logs       # View logs
.\run.bat status     # Check status
.\run.bat restart    # Restart containers
.\run.bat rebuild    # Rebuild everything
```

## ⏱️ First Startup

**Initial startup takes ~30-60 seconds:**
1. PostgreSQL initializes
2. Database schema created
3. Phenology data loaded
4. Dashboard starts

**Subsequent startups:** ~5 seconds (data persists)

## 🌐 Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| Dashboard | http://localhost:8501 | Web interface |
| Database | localhost:5432 | Direct DB access |

**Database Credentials:**
- Username: `postgres`
- Password: `postgres`
- Database: `environmental_data`

## 🛠️ Troubleshooting

**Dashboard not showing changes?**
```bash
docker-compose down
docker-compose build dashboard
docker-compose up -d
```

**Database issues?**
```bash
docker-compose logs database
```

**Complete reset:**
```bash
docker-compose down -v  # Removes volumes!
docker-compose up -d
```

## 📂 Optional: Custom Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Edit `.env` to change ports or credentials

3. Restart containers:
```bash
docker-compose down
docker-compose up -d
```

---

For detailed documentation, see [README.md](README.md)
