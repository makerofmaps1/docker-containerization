from sqlalchemy import text
from dashboard.db import get_engine

def main():
    try:
        engine = get_engine()
    except Exception as e:
        print('Failed to create engine:', e)
        return

    try:
        with engine.connect() as conn:
            print('SELECT 1 ->', conn.execute(text('SELECT 1')).scalar())
            print('current_database() ->', conn.execute(text('SELECT current_database()')).scalar())
    except Exception as e:
        print('DB query failed:', e)

if __name__ == '__main__':
    main()
