from geoalchemy2 import Geometry
from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class FlowerObservation(Base):
    __tablename__ = "flower_observations"

    observation_id = Column(Integer, primary_key=True)
    photo_id = Column(String(255), unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    observation_date = Column(Date, nullable=False)
    location = Column(Geometry(geometry_type="POINT", srid=4326))
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    family = Column(String(255))
    genus_species = Column(String(255), nullable=False)
    plant_group = Column(String(100))
    duration = Column(String(100))
    growth_habit = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
