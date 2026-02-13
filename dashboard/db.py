from sqlalchemy import create_engine
try:
    from dashboard.config import get_db_config
except Exception:
    from config import get_db_config


def get_engine(**kwargs):
    """Create a SQLAlchemy engine using DB config from `dashboard.config.get_db_config()`.

    The config must provide: host, port, dbname, username, password.
    """
    cfg = get_db_config() or {}

    host = cfg.get('host')
    port = cfg.get('port') or '5432'
    dbname = cfg.get('dbname') or cfg.get('database') or cfg.get('DB_NAME')
    user = cfg.get('username') or cfg.get('user') or cfg.get('DB_USER')
    password = cfg.get('password') or cfg.get('pass') or cfg.get('DB_PASSWORD')

    if not all([host, dbname, user, password]):
        raise RuntimeError('Incomplete DB config; set USE_SECRETS_MANAGER and AWS_SECRET_NAME for cloud or DB_* env vars for local')

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(url, pool_pre_ping=True, **kwargs)
