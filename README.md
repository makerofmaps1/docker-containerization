# Docker Containerization Demo - Phenology Data Visualization Dashboard

A production-ready, multi-container application demonstrating Docker orchestration, PostgreSQL/PostGIS spatial databases, and interactive data visualization with Streamlit. This project serves as my reference for Docker containerization best practices and multi-tier application architecture.

![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Docker Skills Demonstrated](#docker-skills-demonstrated)
- [Quick Start](#quick-start)
- [Technical Deep Dive](#technical-deep-dive)
- [Project Structure](#project-structure)
- [Data Source](#data-source)
- [Key Learnings](#key-learnings)

## 🎯 Project Overview

This project demonstrates a **containerized data visualization platform** for analyzing flowering phenology data. Built with a focus on Docker best practices, it showcases:

- Multi-container orchestration with Docker Compose
- Stateful database containers with volume persistence
- Stateless application containers
- Automated database initialization
- Health checks and service dependencies
- Environment-based configuration

**Use Case:** Interactive visualization of flowering observation data, allowing users to explore phenological patterns through an intuitive web interface with cascading filters and coordinated visualizations.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                      │
│                                                      │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  Dashboard   │────────▶│  Database    │         │
│  │  (Streamlit) │  5432  │  (PostgreSQL │         │
│  │  Port: 8501  │         │   + PostGIS) │         │
│  └──────────────┘         └──────────────┘         │
│       │                          │                   │
│       │                          │                   │
│  Stateless                  Stateful                │
│  (Ephemeral)               (Persistent Volume)      │
└─────────────────────────────────────────────────────┘
```

**Two-Tier Application:**

1. **Database Container** (`postgis/postgis:15-3.3`)
   - PostgreSQL with PostGIS spatial extensions
   - Automated schema creation via SQL scripts
   - Python-based data loading from CSV
   - Named volume for data persistence

2. **Dashboard Container** (`python:3.11-slim`)
   - Streamlit web application
   - Interactive map with Folium
   - Plotly charts for temporal analysis
   - Cascading filter system

**Communication:** Containers communicate via Docker's internal network using service names (`database:5432`)

## 🐳 Docker Skills Demonstrated

### 1. Multi-Container Orchestration

**Docker Compose Configuration:**
- Service dependency management with health checks
- Container startup order (`depends_on` with `condition: service_healthy`)
- Network isolation using bridge networks
- Port mapping for external access

**Key Concept:**
```yaml
dashboard:
  depends_on:
    database:
      condition: service_healthy  # Wait for DB to be ready
```

### 2. Dockerfile Best Practices

**Layer Caching Optimization:**
```dockerfile
# Dependencies first (changes infrequently)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code last (changes frequently)
COPY . .
```

**Benefits:**
- Rebuild times reduced from minutes to seconds on code changes
- Docker reuses cached layers when dependencies unchanged
- Critical for CI/CD pipelines

**Image Size Optimization:**
- Used slim base images (`python:3.11-slim`)
- Combined RUN commands to minimize layers
- Cleaned up package lists after installation

### 3. Data Persistence Patterns

**Volume Types:**
- **Named Volume** (`postgres_data`): Managed by Docker, persists database files
- **Bind Mount** (`./Phenology_data:/data/...`): Direct host file access

**Stateful vs Stateless:**
- Database container: Stateful with volume
- Dashboard container: Stateless, ephemeral, can be recreated anytime

### 4. Health Checks & Service Readiness

**Database Health Check:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres -d environmental_data"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**Dashboard Health Check:**
```dockerfile
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
```

**Why Important:** Ensures services are genuinely ready to accept connections, not just running. Critical for production orchestrators like Kubernetes.

### 5. Database Initialization Pattern

**Automated Setup with `/docker-entrypoint-initdb.d/`:**

PostgreSQL's Docker image automatically runs scripts in this directory on **first startup**:

1. `02-load_data.sh` - Executes Python script to load Excel data (local or S3)
2. `dashboard/load_data.py` - Uses SQLAlchemy ORM to create schema and insert data

**Execution Order:** Alphabetical by filename

**Key Benefits:**
- Fully automated, reproducible deployments
- `docker-compose up` creates working system
- Idempotent - safe to run multiple times

### 6. Environment-Based Configuration

**12-Factor App Methodology:**
```yaml
environment:
  DB_HOST: database
  POSTGRES_DB: ${POSTGRES_DB:-environmental_data}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
```

**Features:**
- Configuration via environment variables
- Default values with `${VAR:-default}` syntax
- Same image works in dev/staging/prod
- Secrets management via environment

### 7. Networking & Service Discovery

**Internal Communication:**
```python
db_host = os.getenv('DB_HOST', 'database')  # Service name
connection = f'postgresql://...@{db_host}:5432/...'
```

**How It Works:**
- Docker's embedded DNS resolves service names to container IPs
- Services reference each other by name, not hardcoded IPs
- Port mapping publishes services externally: `8501:8501`

### 8. Container Lifecycle Management

**Essential Commands:**
```bash
docker-compose up -d          # Start detached
docker-compose down           # Stop and remove containers
docker-compose down -v        # Also remove volumes (fresh start)
docker-compose build          # Rebuild images
docker-compose logs -f        # Stream logs
docker-compose ps             # List running containers
docker-compose restart        # Restart services
```

**When to Rebuild vs Restart:**
- Code changes → Rebuild required
- Config changes → Restart sufficient
- Understanding reduces debugging time

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- 2GB free disk space
- Ports 5432 and 8501 available

### Setup Instructions

1. **Clone the repository:**
```bash
git clone <repository-url>
cd docker-containerization
```

2. **Configure environment (optional):**
```bash
cp .env.example .env
# Edit .env if you want to change default ports or credentials
```

3. **Start the application:**

**Windows:**
```powershell
.\run.bat start
```

**Linux/Mac:**
```bash
docker-compose up -d
```

4. **Access the dashboard:**
- Open browser to: http://localhost:8501
- Database available at: localhost:5432

5. **View logs:**
```bash
docker-compose logs -f
```

6. **Stop the application:**
```bash
docker-compose down
```

7. **Complete reset (removes data):**
```bash
docker-compose down -v
```

## ☁️ Cloud Deployment (S3 + RDS/Supabase + AWS EC2)

This setup uses S3 for the raw Excel file, a managed PostgreSQL/PostGIS database (RDS or Supabase), and an EC2 instance to host the Streamlit app.

### 1. Managed PostgreSQL (RDS or Supabase)

1. Create a Supabase project and copy the connection string (Database Settings → Connection string).
2. Enable PostGIS in the Supabase SQL editor:
```sql
create extension if not exists postgis;
create extension if not exists postgis_topology;
```
3. Set your connection string in an environment variable:
```bash
export DATABASE_URL="postgresql+psycopg2://user:password@host:5432/dbname?sslmode=require"
```

### 1b. SSH Tunnel Through EC2 (for private RDS)

If your RDS instance is private, use the provided `db-tunnel` service to forward a local port to RDS through an EC2 bastion host.

**Network requirements:**
- EC2 security group: inbound SSH (22) from your IP
- RDS security group: inbound 5432 from the EC2 security group
- EC2 outbound: allow 5432 to RDS

**Required environment variables (local or .env):**
```bash
# Dashboard connects to the tunnel container
DB_HOST=db-tunnel
DB_PORT=5432
DB_NAME=environmental_data
DB_USER=postgres
DB_PASSWORD=postgres

# Tunnel connects to RDS via EC2
EC2_HOST=ec2-x-x-x-x.compute-1.amazonaws.com
SSH_USER=ec2-user
RDS_HOST=your-rds-endpoint.amazonaws.com
RDS_PORT=5432
```

**SSH key:**
- Place your private key at `docker/tunnel/key.pem` (or change the bind mount in [docker-compose.yml](docker-compose.yml)).
- The container mounts it read-only at `/secrets/key.pem`.

**Start services:**
```bash
docker-compose up -d
```

**Notes:**
- The dashboard connects to `db-tunnel:5432`, which forwards to RDS.
- If you use Secrets Manager, make sure the secret resolves to `host=db-tunnel` or set all `DB_*` env vars so they take precedence.
- Check tunnel logs with `docker-compose logs -f db-tunnel` if the connection fails.

### 2. Load Data from S3 Using SQLAlchemy ORM

The data loader now uses a SQLAlchemy ORM model and will create the table if it does not exist.

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@host:5432/dbname?sslmode=require"
export S3_BUCKET="your-bucket"
export S3_KEY="raw-data/data.xlsx"
export AWS_REGION="us-east-1"
export AWS_SECRET_NAME="DEMO_DB_CREDS"  # optional: Secrets Manager secret name
python dashboard/load_data.py
```

Alternatively run the loader as a one-off container (recommended for CI/EC2):

```bash
# Using cloud compose
docker compose -f docker-compose.cloud.yml run --rm loader

# Using local compose (loads to local DB unless DATABASE_URL points to RDS)
docker compose run --rm loader
```

### 3. Host Streamlit on AWS EC2

1. Create an EC2 instance (t3.micro works for free tier) and open inbound port 8501 in the security group.
2. Install Docker and Docker Compose on the instance.
3. Clone this repo and set the Supabase connection string in your environment or [.env](.env).
4. Start the dashboard container only:

```bash
docker compose -f docker-compose.cloud.yml up -d
```

Open `http://<ec2-public-ip>:8501` in your browser.

**Tip:** Use [docker-compose.cloud.yml](docker-compose.cloud.yml) so the app connects to Supabase without running the local database container.

### First Startup

On first startup, the database container will:
1. Initialize PostgreSQL cluster
2. Create database and PostGIS extensions
3. Use SQLAlchemy ORM to create schema
4. Execute `dashboard/load_data.py` to import phenology data
5. This takes ~30-60 seconds

Subsequent startups are instant (data persists in volume).

## 🔧 Technical Deep Dive

### Database Design Decisions

**Why Denormalized Schema?**
- Small, bounded dataset (flower observations)
- Read-heavy workload (visualization only)
- Query performance: No joins needed for filters
- Static research data (no updates)

**When to Normalize?**
- Larger datasets with storage concerns
- Frequent updates to taxonomic data
- Multi-user data entry systems
- Need to store additional metadata about families/species

**Index Strategy:**
```sql
CREATE INDEX idx_flower_observations_family ON flower_observations(family);
CREATE INDEX idx_flower_observations_species ON flower_observations(genus_species);
CREATE INDEX idx_flower_observations_location ON flower_observations USING GIST(location);
```

**Do Indexes Help?**
- For this small dataset (~hundreds to thousands of rows): Minimal impact
- PostgreSQL often uses sequential scans for small tables
- Indexes are future-proofing and best practice
- Spatial GIST index useful if implementing proximity queries

### Streamlit Architecture

**Caching Strategy:**

```python
@st.cache_resource  # Singleton - DB connection pool
def get_db():
    return create_engine(connection_string)

@st.cache_data(ttl=600)  # Data with expiration
def load_data(_engine):
    return pd.read_sql(query, _engine)
```

**Key Differences:**
- `@st.cache_resource`: Non-serializable resources (connections, models)
- `@st.cache_data`: Data that can be copied (DataFrames, lists)
- TTL allows periodic refresh

**Multi-Page App Structure:**
- `app.py` - Home page, first Streamlit command must be `st.set_page_config`
- `pages/` - Auto-detected by Streamlit
- `1_🌸_Phenology_Analysis.py` - Number prefix controls order
- Each page runs independently when navigated to

**Cascading Filters:**
```python
# Filter 1: Family
selected_family = st.sidebar.selectbox("Family", families)

# Filter 2: Species (filtered by family)
temp_df = df[df['family'] == selected_family] if selected_family != 'All' else df
species_list = sorted(temp_df['genus_species'].unique())
selected_species = st.sidebar.selectbox("Species", species_list)
```

**Coordinated Visualizations:**
- Single color palette defined once
- Shared across map (Folium) and chart (Plotly)
- Both react to same filter selections

### Docker Build Context

**Understanding Build Context:**
```yaml
build:
  context: .
  dockerfile: database/Dockerfile
```

- Context is the directory sent to Docker daemon
- Everything in context directory is transferred
- Large contexts slow down builds
- Use `.dockerignore` to exclude unnecessary files

### PostGIS Spatial Features

**Geometry Storage:**
```sql
CREATE TABLE flower_observations (
    location GEOMETRY(Point, 4326),  -- WGS84 coordinate system
    latitude NUMERIC,
    longitude NUMERIC
);
```

**Why Both?**
- `latitude/longitude`: Easy filtering and display
- `location` geometry: Enables spatial queries
- SRID 4326: Standard for GPS coordinates

**Spatial Index:**
```sql
CREATE INDEX idx_location ON flower_observations USING GIST(location);
```

Enables fast proximity queries like "find flowers within 1km of a point" (not used in current app, but available for future features).

## 📁 Project Structure

```
docker-containerization/
│
├── docker-compose.yml          # Container orchestration
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── run.bat                    # Windows helper script
├── README.md                  # This file
├── QUICKSTART.md             # Quick reference guide
│
├── database/                  # Database Container
│   ├── Dockerfile            # PostgreSQL + PostGIS + Python
│   ├── 02-load_data.sh       # Data loading orchestration
│
├── dashboard/                 # Streamlit Container
│   ├── __init__.py           # Package marker
│   ├── app.py               # Home page
│   ├── models.py            # Database models
│   ├── load_data.py         # ORM-based data loader
│   ├── data.xlsx            # Phenology dataset
│   ├── Dockerfile           # Python + Streamlit
│   ├── requirements.txt     # Python dependencies
│   └── pages/
│       └── 1_🌸_Phenology_Analysis.py  # Main visualization
│
└── Phenology_data/           # Source Data (optional)
  └── All_Clean_Combined.csv
```

## 📊 Data Source

**Citation:**

M. Cope, E. Mikhailova, C. Post, M. Schlautman, P. McMillan,  
*Developing an integrated cloud-based spatial-temporal system for monitoring phenology*,  
Ecological Informatics, Volume 39, 2017, Pages 123-129, ISSN 1574-9541,  
https://doi.org/10.1016/j.ecoinf.2017.04.007

**Dataset:**
- Flower observations
- Multiple years of phenological data
- Taxonomic information (family, species)
- Geographic coordinates
- Temporal observations (dates)

## 🎓 Key Learnings

### Docker Containerization

1. **Multi-Container Apps**: Separate concerns into individual containers
2. **Service Dependencies**: Use health checks, not just startup order
3. **Volume Strategy**: Named volumes for state, bind mounts for code/data access
4. **Layer Caching**: Order Dockerfile commands by change frequency
5. **Health Checks**: Ensure genuine service readiness
6. **Environment Config**: 12-factor app principles for portability
7. **Service Discovery**: Use service names, let Docker handle DNS
8. **Init Patterns**: Leverage `/docker-entrypoint-initdb.d/` for automation

### Database Design

1. **Denormalization**: Appropriate for read-heavy, bounded datasets
2. **Spatial Data**: PostGIS for geographic features
3. **Indexing**: Balance between performance and overhead
4. **Initialization**: Automated, reproducible setup

### Application Architecture

1. **Caching**: Different strategies for resources vs data
2. **Stateless Frontend**: Can be recreated without data loss
3. **Stateful Backend**: Requires persistent storage
4. **Filter Cascading**: Dependent filters for better UX

### Development Workflow

1. **Container Lifecycle**: When to rebuild, restart, or recreate
2. **Debugging**: Logs, exec, and inspect commands
3. **Volumes**: Data persistence across container lifecycles
4. **Networks**: Container isolation and communication

## 🔍 Troubleshooting

**Dashboard shows old code after changes:**
```bash
docker-compose down
docker-compose build dashboard
docker-compose up -d
```

**Database won't start:**
```bash
# Check logs
docker-compose logs database

# Verify health
docker-compose ps
```

**Fresh start (removes all data):**
```bash
docker-compose down -v
docker-compose up -d
```

**Access database directly:**
```bash
docker exec -it env_data_database psql -U postgres -d environmental_data
```

## 📝 Interview Discussion Points

**"Tell me about your Docker experience"**
- "I built a multi-container application with database and web tiers, using Docker Compose for orchestration with health checks and service dependencies."

**"How do you handle data persistence?"**
- "I use named volumes for stateful services like databases, ensuring data survives container recreation, while keeping application containers stateless."

**"How do you optimize Docker builds?"**
- "I structure Dockerfiles to leverage layer caching - dependencies first, code second - which reduces rebuild times from minutes to seconds."

**"How do you manage container startup order?"**
- "I use health checks and `depends_on` conditions to ensure dependent services wait for required services to be genuinely ready, not just running."

**"How do containers communicate?"**
- "Through Docker's internal network using service names as DNS, which provides automatic service discovery without hardcoded IPs."

## 🚀 Future Enhancements

- [ ] Add nginx reverse proxy container
- [ ] Implement multi-stage Docker builds
- [ ] Add Docker secrets for credential management
- [ ] Create docker-compose.prod.yml for production
- [ ] Add CI/CD pipeline with GitHub Actions
- [ ] Implement container resource limits
- [ ] Add monitoring with Prometheus/Grafana
- [ ] Set up automated backups for database volume

## 📄 License

This project is for educational and demonstration purposes.

## 🙏 Acknowledgments

Data provided by Cope et al. (2017) via Ecological Informatics.

