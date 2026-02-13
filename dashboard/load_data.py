#!/usr/bin/env python3
"""
Data loading script for PostgreSQL/PostGIS database.
Loads phenology data from an Excel file.
"""

import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import logging
import time

import boto3
from geoalchemy2 import WKTElement
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

try:
    from dashboard.models import Base, FlowerObservation
except Exception:
    from models import Base, FlowerObservation

try:
    from dashboard.db import get_engine
except Exception:
    from db import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def resolve_data_file():
    data_file = os.getenv("PHENOLOGY_DATA_FILE")
    if data_file:
        return Path(data_file)

    s3_bucket = os.getenv("S3_BUCKET")
    s3_key = os.getenv("S3_KEY")
    if s3_bucket and s3_key:
        return download_from_s3(s3_bucket, s3_key)

    data_path = os.getenv("PHENOLOGY_DATA_PATH")
    if data_path:
        return Path(data_path) / "data.xlsx"

    return Path(__file__).resolve().parent / "data.xlsx"


def download_from_s3(bucket, key):
    cache_dir = os.getenv("PHENOLOGY_CACHE_DIR")
    if cache_dir:
        destination_dir = Path(cache_dir)
    else:
        destination_dir = Path(tempfile.gettempdir())

    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_file = destination_dir / "phenology_demo_data.xlsx"

    region = os.getenv("AWS_REGION")
    client = boto3.client("s3", region_name=region) if region else boto3.client("s3")
    logger.info(f"Downloading s3://{bucket}/{key} to {destination_file}")
    client.download_file(bucket, key, str(destination_file))
    return destination_file

def load_phenology_data(engine):
    """
    Load flower phenology observation data from Excel file.
    """

    logger.info("Loading flower phenology data...")

    data_file = resolve_data_file()

    if not data_file.exists():
        logger.warning(f"Phenology data file not found: {data_file}")
        return

    logger.info(f"Loading phenology data from: {data_file}")

    try:
        df = pd.read_excel(data_file)

        logger.info(f"Found {len(df)} flower observations")

        observations = []
        for _, row in df.iterrows():
            try:
                obs_date = pd.to_datetime(row["DateMMDDYYYY"]).date()
                latitude = float(row["Latitude"])
                longitude = float(row["Longitude"])

                observations.append(
                    {
                        "photo_id": row["PhotoID"],
                        "year": int(row["Year"]),
                        "observation_date": obs_date,
                        "location": WKTElement(f"POINT({longitude} {latitude})", srid=4326),
                        "latitude": latitude,
                        "longitude": longitude,
                        "family": row.get("Family", ""),
                        "genus_species": row["Genus species"],
                        "plant_group": row.get("Group", ""),
                        "duration": row.get("Duration", ""),
                        "growth_habit": row.get("Growth habit", ""),
                    }
                )
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                continue

        if observations:
            Session = sessionmaker(bind=engine)
            with Session() as session:
                stmt = insert(FlowerObservation).values(observations)
                stmt = stmt.on_conflict_do_nothing(index_elements=["photo_id"])
                session.execute(stmt)
                session.commit()

                logger.info(f"Loaded {len(observations)} flower observations")

                species_count = session.scalar(
                    select(func.count(func.distinct(FlowerObservation.genus_species)))
                )
                family_count = session.scalar(
                    select(func.count(func.distinct(FlowerObservation.family)))
                )
                date_range = session.execute(
                    select(
                        func.min(FlowerObservation.observation_date),
                        func.max(FlowerObservation.observation_date),
                    )
                ).one()

                logger.info(f"Statistics: {species_count} species, {family_count} families")
                logger.info(f"Date range: {date_range[0]} to {date_range[1]}")

    except Exception as e:
        logger.error(f"Error loading phenology data: {e}")
        logger.exception("Error loading phenology data")


def main():
    """Main data loading function"""
    logger.info("Starting data loading process...")

    time.sleep(5)

    try:
        engine = get_engine()

        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))

        Base.metadata.create_all(engine)
        load_phenology_data(engine)
        engine.dispose()
        logger.info("Data loading complete!")
    except Exception as e:
        logger.error(f"Error during data loading: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
