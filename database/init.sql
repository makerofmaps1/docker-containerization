-- Create database and enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Flower Phenology Observations Table
-- Here we will use a non-normalized, monolithic table for simplicity and performance
--    1. data set is less than 10,000 rows
--    2. we are making a read-heavy application with no writes
--    3. optimize for query performance and simplicity over strict normalization
--    4. static data that will not change
--    5. simlicity of database design
CREATE TABLE IF NOT EXISTS flower_observations (
    observation_id SERIAL PRIMARY KEY,
    photo_id VARCHAR(255) UNIQUE NOT NULL,
    year INTEGER NOT NULL,
    observation_date DATE NOT NULL,
    location GEOMETRY(Point, 4326),  -- Created from lat/lon
    latitude NUMERIC,
    longitude NUMERIC,
    family VARCHAR(255),
    genus_species VARCHAR(255) NOT NULL,
    plant_group VARCHAR(100),  -- e.g., 'Dicot', 'Monocot'
    duration VARCHAR(100),  -- e.g., 'Annual', 'Perennial'
    growth_habit VARCHAR(100),  -- e.g., 'Tree', 'Forb Herb', 'Shrub'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes probably don't provide much benefit for this small dataset
-- But included here for demonstration purposes
CREATE INDEX idx_flower_observations_date ON flower_observations(observation_date);
CREATE INDEX idx_flower_observations_year ON flower_observations(year);
CREATE INDEX idx_flower_observations_species ON flower_observations(genus_species);
CREATE INDEX idx_flower_observations_spatial ON flower_observations USING GIST(location);
CREATE INDEX idx_flower_observations_family ON flower_observations(family);

-- Grant permissions
-- Keep it simple for this project
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
