# File: src/database/db.py

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Define the database URL (SQLite in this case)
DATABASE_URL = "sqlite:///database.db"

# Create the engine and base class for models
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()

# Define a model for weather data
class WeatherData(Base):
    __tablename__ = "weather_data"
    id = Column(Integer, primary_key=True)
    location = Column(String(50))
    temperature = Column(Float)
    description = Column(String(100))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Define a model for market data
class MarketData(Base):
    __tablename__ = "market_data"
    id = Column(Integer, primary_key=True)
    crop = Column(String(50))
    price = Column(Float)
    date = Column(DateTime, default=datetime.datetime.utcnow)

# Define a model for crop data
class CropData(Base):
    __tablename__ = "crop_data"
    id = Column(Integer, primary_key=True)
    crop_name = Column(String(50))
    climate_suitability = Column(Text)
    growth_cycle = Column(String(50))

# Define a model to store user inputs
class UserInput(Base):
    __tablename__ = "user_inputs"
    id = Column(Integer, primary_key=True)
    location = Column(String(50))
    greenhouse_size = Column(Float)
    water_availability = Column(Float)
    fertilizer_type = Column(String(50))
    preferred_crops = Column(String(200))  # Comma-separated list if multiple
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Create a SessionLocal class to manage database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to initialize the database (i.e., create all tables)
def init_db():
    Base.metadata.create_all(bind=engine)
