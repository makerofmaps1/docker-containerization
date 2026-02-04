#!/usr/bin/env python3
"""
Data loading script for PostgreSQL/PostGIS database.
Loads phenology data from CSV file.
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {'host': 'localhost',
             'database': os.getenv('POSTGRES_DB', 'environmental_data'),
             'user': os.getenv('POSTGRES_USER', 'postgres'),
             'password': os.getenv('POSTGRES_PASSWORD', 'postgres')}


def load_phenology_data(conn):
    """
    Load flower phenology observation data from CSV file
    """

    logger.info("Loading flower phenology data...")
    
    cursor = conn.cursor()
    data_path = '/data/phenology_data'
    
    if not os.path.exists(data_path):
        logger.warning(f"Phenology data path not found: {data_path}")
        return
    
    # Look for the CSV file
    csv_file = os.path.join(data_path, 'All_Clean_Combined.csv')
    
    if not os.path.exists(csv_file):
        logger.warning(f"Could not find phenology data file: {csv_file}")
        return
    
    logger.info(f"Loading phenology data from: {csv_file}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        logger.info(f"Found {len(df)} flower observations")
        
        # Prepare data for insertion
        observations = []
        for _, row in df.iterrows():
            try:
                # Parse date
                obs_date = pd.to_datetime(row['DateMMDDYYYY'])
                
                observation = (
                    row['PhotoID'],
                    int(row['Year']),
                    obs_date.date(),
                    float(row['Longitude']),
                    float(row['Latitude']),
                    float(row['Latitude']),
                    float(row['Longitude']),
                    row.get('Family', ''),
                    row['Genus species'],
                    row.get('Group', ''),
                    row.get('Duration', ''),
                    row.get('Growth habit', '')
                )
                observations.append(observation)
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                continue
        
        # Bulk insert
        if observations:
            execute_values(cursor, 
                           """
                           INSERT INTO flower_observations 
                           (photo_id, year, observation_date, location, latitude, longitude,
                           family, genus_species, plant_group, duration, growth_habit)
                           VALUES %s
                           ON CONFLICT (photo_id) DO NOTHING
                           """, 
                           [(obs[0], obs[1], obs[2], f'SRID=4326;POINT({obs[3]} {obs[4]})',  # location as WKT
                            obs[5], obs[6], obs[7], obs[8], obs[9], obs[10], obs[11])
                            for obs in observations])
            
            conn.commit()
            logger.info(f"Loaded {len(observations)} flower observations")
            
            # Log some statistics
            cursor.execute("SELECT COUNT(DISTINCT genus_species) FROM flower_observations")
            species_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT family) FROM flower_observations")
            family_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(observation_date), MAX(observation_date) FROM flower_observations")
            date_range = cursor.fetchone()
            
            logger.info(f"Statistics: {species_count} species, {family_count} families")
            logger.info(f"Date range: {date_range[0]} to {date_range[1]}")
        
    except Exception as e:
        logger.error(f"Error loading phenology data: {e}")
        conn.rollback()

def main():
    """Main data loading function"""
    logger.info("Starting data loading process...")
    
    # Small delay to ensure PostgreSQL is ready
    time.sleep(5)
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        load_phenology_data(conn)
        conn.close()
        logger.info("Data loading complete!")
    except Exception as e:
        logger.error(f"Error during data loading: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
