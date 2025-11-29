-- EPREL Database Schema
-- PostgreSQL 16
-- Schema for European Product Registry for Energy Labelling

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- COMMON/SHARED TABLES
-- ============================================

-- Product Groups (Categories)
CREATE TABLE product_groups (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    name_es VARCHAR(255),
    description TEXT,
    total_products INTEGER DEFAULT 0,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers/Manufacturers
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    eprel_supplier_id VARCHAR(100) UNIQUE,
    name VARCHAR(500) NOT NULL,
    trade_name VARCHAR(500),
    address TEXT,
    country VARCHAR(100),
    contact_email VARCHAR(255),
    website VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Base Products Table (common fields for all product types)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    eprel_product_id VARCHAR(100) UNIQUE NOT NULL,
    product_group_id INTEGER REFERENCES product_groups(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    
    -- Basic identification
    model_identifier VARCHAR(500),
    brand VARCHAR(255),
    
    -- Energy efficiency
    energy_class VARCHAR(10),
    energy_class_index DECIMAL(10,4),
    
    -- Status and dates
    status VARCHAR(50),
    on_market_start_date DATE,
    on_market_end_date DATE,
    registration_date DATE,
    
    -- URLs for labels and sheets
    energy_label_url TEXT,
    product_fiche_url TEXT,
    
    -- Raw JSON data for category-specific fields
    raw_data JSONB,
    
    -- Sync tracking
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_version INTEGER DEFAULT 1,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CATEGORY-SPECIFIC TABLES
-- ============================================

-- Air Conditioners
CREATE TABLE product_airconditioners (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Cooling capacity and efficiency
    cooling_capacity_kw DECIMAL(10,2),
    cooling_efficiency_class VARCHAR(10),
    cooling_seer DECIMAL(10,2),
    
    -- Heating capacity and efficiency  
    heating_capacity_kw DECIMAL(10,2),
    heating_efficiency_class VARCHAR(10),
    heating_scop DECIMAL(10,2),
    
    -- Power consumption
    power_consumption_cooling_kw DECIMAL(10,2),
    power_consumption_heating_kw DECIMAL(10,2),
    annual_energy_consumption_kwh INTEGER,
    
    -- Noise levels
    indoor_noise_level_db DECIMAL(5,1),
    outdoor_noise_level_db DECIMAL(5,1),
    
    -- Refrigerant
    refrigerant_type VARCHAR(50),
    refrigerant_gwp INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dishwashers
CREATE TABLE product_dishwashers (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Capacity
    place_settings INTEGER,
    
    -- Energy and water consumption
    energy_consumption_kwh_100cycles DECIMAL(10,2),
    water_consumption_liters_cycle DECIMAL(10,2),
    
    -- Efficiency classes
    drying_efficiency_class VARCHAR(10),
    noise_class VARCHAR(10),
    noise_level_db DECIMAL(5,1),
    
    -- Program details
    eco_program_duration_minutes INTEGER,
    
    -- Dimensions
    width_mm INTEGER,
    depth_mm INTEGER,
    height_mm INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Washing Machines
CREATE TABLE product_washingmachines (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Capacity
    rated_capacity_kg DECIMAL(5,2),
    
    -- Energy consumption
    energy_consumption_kwh_100cycles DECIMAL(10,2),
    water_consumption_liters_cycle DECIMAL(10,2),
    
    -- Efficiency classes
    spin_drying_efficiency_class VARCHAR(10),
    noise_class VARCHAR(10),
    noise_level_db DECIMAL(5,1),
    
    -- Program details
    cotton_60_full_load_duration_minutes INTEGER,
    eco_program_duration_minutes INTEGER,
    
    -- Spin speed
    max_spin_speed_rpm INTEGER,
    
    -- Dimensions
    width_mm INTEGER,
    depth_mm INTEGER,
    height_mm INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Washer Dryers
CREATE TABLE product_washerdryers (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Capacity
    wash_capacity_kg DECIMAL(5,2),
    dry_capacity_kg DECIMAL(5,2),
    
    -- Energy consumption
    energy_consumption_wash_dry_kwh_100cycles DECIMAL(10,2),
    energy_consumption_wash_only_kwh_100cycles DECIMAL(10,2),
    water_consumption_wash_dry_liters DECIMAL(10,2),
    water_consumption_wash_only_liters DECIMAL(10,2),
    
    -- Efficiency classes
    spin_drying_efficiency_class VARCHAR(10),
    noise_class_wash VARCHAR(10),
    noise_class_dry VARCHAR(10),
    noise_level_wash_db DECIMAL(5,1),
    noise_level_dry_db DECIMAL(5,1),
    
    -- Program details
    wash_dry_cycle_duration_minutes INTEGER,
    wash_only_duration_minutes INTEGER,
    
    -- Spin speed
    max_spin_speed_rpm INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tumble Dryers
CREATE TABLE product_tumbledryers (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Capacity
    rated_capacity_kg DECIMAL(5,2),
    
    -- Energy consumption
    energy_consumption_kwh_100cycles DECIMAL(10,2),
    
    -- Dryer type
    dryer_type VARCHAR(50), -- condenser, heat pump, vented
    
    -- Efficiency and performance
    condensation_efficiency_class VARCHAR(10),
    noise_class VARCHAR(10),
    noise_level_db DECIMAL(5,1),
    
    -- Program details
    cotton_drying_program_duration_minutes INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Refrigerating Appliances (Refrigerators, Freezers, Wine Storage)
CREATE TABLE product_refrigerators (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Type
    appliance_type VARCHAR(100), -- refrigerator, freezer, refrigerator-freezer, wine storage
    
    -- Capacity
    total_volume_liters INTEGER,
    refrigerator_volume_liters INTEGER,
    freezer_volume_liters INTEGER,
    chill_compartment_volume_liters INTEGER,
    
    -- Energy consumption
    annual_energy_consumption_kwh DECIMAL(10,2),
    
    -- Temperature and performance
    freezer_star_rating INTEGER,
    noise_class VARCHAR(10),
    noise_level_db DECIMAL(5,1),
    
    -- Climate class
    climate_class VARCHAR(50),
    
    -- Frost free
    frost_free BOOLEAN,
    
    -- Dimensions
    width_mm INTEGER,
    depth_mm INTEGER,
    height_mm INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Electronic Displays (TVs, Monitors)
CREATE TABLE product_displays (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Type
    display_type VARCHAR(100), -- television, monitor
    
    -- Screen specifications
    screen_diagonal_cm DECIMAL(10,2),
    screen_diagonal_inches DECIMAL(10,2),
    resolution_horizontal INTEGER,
    resolution_vertical INTEGER,
    panel_technology VARCHAR(50), -- LCD, OLED, QLED, etc.
    
    -- Energy consumption
    on_mode_power_consumption_w DECIMAL(10,2),
    on_mode_power_consumption_hdr_w DECIMAL(10,2),
    standby_power_consumption_w DECIMAL(10,3),
    off_mode_power_consumption_w DECIMAL(10,3),
    annual_energy_consumption_kwh DECIMAL(10,2),
    
    -- Energy efficiency index
    energy_efficiency_index DECIMAL(10,4),
    energy_efficiency_index_hdr DECIMAL(10,4),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Light Sources
CREATE TABLE product_lightsources (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Light specifications
    luminous_flux_lm INTEGER,
    useful_luminous_flux_lm INTEGER,
    power_consumption_w DECIMAL(10,2),
    
    -- Efficiency
    luminous_efficacy_lm_w DECIMAL(10,2),
    
    -- Color characteristics
    correlated_color_temperature_k INTEGER,
    color_rendering_index DECIMAL(5,1),
    
    -- Lifetime
    rated_life_hours INTEGER,
    lumen_maintenance_factor DECIMAL(5,2),
    
    -- Physical characteristics
    cap_base_type VARCHAR(50),
    dimmable BOOLEAN,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ovens
CREATE TABLE product_ovens (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Type
    oven_type VARCHAR(100), -- electric, gas, microwave combination
    
    -- Cavity
    cavity_volume_liters DECIMAL(10,2),
    number_of_cavities INTEGER,
    
    -- Energy consumption
    energy_consumption_conventional_kwh DECIMAL(10,2),
    energy_consumption_forced_air_kwh DECIMAL(10,2),
    
    -- Performance
    heat_distribution VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Range Hoods
CREATE TABLE product_rangehoods (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Performance
    fluid_dynamic_efficiency_class VARCHAR(10),
    lighting_efficiency_class VARCHAR(10),
    grease_filtering_efficiency_class VARCHAR(10),
    
    -- Air flow
    maximum_air_flow_rate_m3h INTEGER,
    
    -- Energy consumption
    annual_energy_consumption_kwh DECIMAL(10,2),
    
    -- Noise
    noise_level_db DECIMAL(5,1),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tyres
CREATE TABLE product_tyres (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Size
    tyre_size_designation VARCHAR(100),
    width_mm INTEGER,
    aspect_ratio INTEGER,
    rim_diameter_inches INTEGER,
    load_index INTEGER,
    speed_rating VARCHAR(10),
    
    -- Performance ratings
    fuel_efficiency_class VARCHAR(10),
    wet_grip_class VARCHAR(10),
    external_rolling_noise_class VARCHAR(10),
    external_rolling_noise_db DECIMAL(5,1),
    
    -- Type
    tyre_type VARCHAR(50), -- C1, C2, C3 (passenger, van, truck)
    snow_tyre BOOLEAN,
    ice_tyre BOOLEAN,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Water Heaters
CREATE TABLE product_waterheaters (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Type
    heater_type VARCHAR(100), -- conventional, solar, heat pump
    
    -- Capacity
    storage_volume_liters INTEGER,
    
    -- Energy consumption and efficiency
    water_heating_energy_efficiency_class VARCHAR(10),
    annual_energy_consumption_kwh DECIMAL(10,2),
    
    -- Performance
    load_profile VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Space Heaters
CREATE TABLE product_spaceheaters (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Type
    heater_type VARCHAR(100),
    
    -- Heat output
    rated_heat_output_kw DECIMAL(10,2),
    
    -- Efficiency
    seasonal_space_heating_efficiency_percent DECIMAL(10,2),
    
    -- Energy consumption
    annual_energy_consumption_kwh DECIMAL(10,2),
    
    -- Noise
    noise_level_db DECIMAL(5,1),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ventilation Units
CREATE TABLE product_ventilationunits (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Type
    unit_type VARCHAR(100), -- residential, non-residential
    
    -- Performance
    maximum_flow_rate_m3h INTEGER,
    
    -- Energy efficiency
    specific_energy_consumption_sec DECIMAL(10,2),
    
    -- Heat recovery
    thermal_efficiency_percent DECIMAL(10,2),
    
    -- Noise
    noise_level_db DECIMAL(5,1),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Professional Refrigerated Storage Cabinets
CREATE TABLE product_profrefrigeratedcabinets (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    
    -- Type
    cabinet_type VARCHAR(100),
    operating_temperature VARCHAR(50),
    
    -- Capacity
    net_volume_liters INTEGER,
    
    -- Energy consumption
    annual_energy_consumption_kwh DECIMAL(10,2),
    
    -- Energy efficiency index
    energy_efficiency_index DECIMAL(10,4),
    
    -- Noise
    noise_level_db DECIMAL(5,1),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SYNC TRACKING TABLES
-- ============================================

-- Sync Jobs
CREATE TABLE sync_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL, -- full, incremental, category
    status VARCHAR(50) NOT NULL, -- pending, running, completed, failed
    product_group_id INTEGER REFERENCES product_groups(id),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_products INTEGER DEFAULT 0,
    synced_products INTEGER DEFAULT 0,
    failed_products INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sync Progress (for resumable downloads)
CREATE TABLE sync_progress (
    id SERIAL PRIMARY KEY,
    sync_job_id INTEGER REFERENCES sync_jobs(id) ON DELETE CASCADE,
    product_group_code VARCHAR(100) NOT NULL,
    current_page INTEGER DEFAULT 0,
    total_pages INTEGER,
    last_processed_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (sync_job_id, product_group_code)
);

-- ============================================
-- INDEXES
-- ============================================

-- Products indexes
CREATE INDEX idx_products_eprel_id ON products(eprel_product_id);
CREATE INDEX idx_products_product_group ON products(product_group_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_model ON products(model_identifier);
CREATE INDEX idx_products_energy_class ON products(energy_class);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_registration_date ON products(registration_date);
CREATE INDEX idx_products_raw_data ON products USING GIN (raw_data);

-- Product groups indexes
CREATE INDEX idx_product_groups_code ON product_groups(code);

-- Suppliers indexes
CREATE INDEX idx_suppliers_eprel_id ON suppliers(eprel_supplier_id);
CREATE INDEX idx_suppliers_name ON suppliers(name);

-- Sync jobs indexes
CREATE INDEX idx_sync_jobs_status ON sync_jobs(status);
CREATE INDEX idx_sync_jobs_type ON sync_jobs(job_type);
CREATE INDEX idx_sync_progress_job ON sync_progress(sync_job_id);
CREATE INDEX idx_sync_progress_group ON sync_progress(product_group_code);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- TRIGGERS
-- ============================================

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_groups_updated_at BEFORE UPDATE ON product_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_airconditioners_updated_at BEFORE UPDATE ON product_airconditioners
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_dishwashers_updated_at BEFORE UPDATE ON product_dishwashers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_washingmachines_updated_at BEFORE UPDATE ON product_washingmachines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_washerdryers_updated_at BEFORE UPDATE ON product_washerdryers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_tumbledryers_updated_at BEFORE UPDATE ON product_tumbledryers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_refrigerators_updated_at BEFORE UPDATE ON product_refrigerators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_displays_updated_at BEFORE UPDATE ON product_displays
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_lightsources_updated_at BEFORE UPDATE ON product_lightsources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_ovens_updated_at BEFORE UPDATE ON product_ovens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_rangehoods_updated_at BEFORE UPDATE ON product_rangehoods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_tyres_updated_at BEFORE UPDATE ON product_tyres
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_waterheaters_updated_at BEFORE UPDATE ON product_waterheaters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_spaceheaters_updated_at BEFORE UPDATE ON product_spaceheaters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_ventilationunits_updated_at BEFORE UPDATE ON product_ventilationunits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_profrefrigeratedcabinets_updated_at BEFORE UPDATE ON product_profrefrigeratedcabinets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- INITIAL DATA: Product Groups
-- ============================================

INSERT INTO product_groups (code, name, name_es, description) VALUES
('airconditioners', 'Air Conditioners', 'Aires Acondicionados', 'Household air conditioning appliances'),
('dishwashers', 'Dishwashers', 'Lavavajillas', 'Household dishwashers'),
('washingmachines', 'Washing Machines', 'Lavadoras', 'Household washing machines'),
('washerdryers', 'Washer Dryers', 'Lavadoras-Secadoras', 'Combined household washer-dryer appliances'),
('tumbledryers', 'Tumble Dryers', 'Secadoras', 'Household tumble dryers'),
('refrigeratingappliances', 'Refrigerating Appliances', 'Aparatos de Refrigeración', 'Household refrigerators, freezers and combinations'),
('electronicdisplays', 'Electronic Displays', 'Pantallas Electrónicas', 'Televisions and monitors'),
('lightsources', 'Light Sources', 'Fuentes de Luz', 'LED, fluorescent and other light sources'),
('ovens', 'Ovens', 'Hornos', 'Electric and gas household ovens'),
('rangehoods', 'Range Hoods', 'Campanas Extractoras', 'Household range hoods'),
('tyres', 'Tyres', 'Neumáticos', 'Vehicle tyres'),
('waterheaters', 'Water Heaters', 'Calentadores de Agua', 'Water heating appliances'),
('spaceheaters', 'Space Heaters', 'Calentadores de Espacio', 'Space heating appliances'),
('ventilationunits', 'Ventilation Units', 'Unidades de Ventilación', 'Residential and non-residential ventilation'),
('professionalrefrigeratedstoragecabinets', 'Professional Refrigerated Storage Cabinets', 'Armarios Refrigerados Profesionales', 'Commercial refrigeration cabinets'),
('solidfuelboilers', 'Solid Fuel Boilers', 'Calderas de Combustible Sólido', 'Solid fuel heating boilers'),
('localheaterssolid', 'Local Space Heaters (Solid Fuel)', 'Calentadores Locales (Combustible Sólido)', 'Local space heaters using solid fuel'),
('localheatersgaseous', 'Local Space Heaters (Gas)', 'Calentadores Locales (Gas)', 'Local space heaters using gaseous fuel');
