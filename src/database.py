"""
Database operations for EPREL data synchronization.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from contextlib import contextmanager

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values, Json, RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class Database:
    """
    Database handler for EPREL data.
    
    Provides methods for storing and retrieving EPREL product data,
    managing sync jobs, and handling category-specific data.
    """
    
    # Mapping of product groups to their specific tables
    CATEGORY_TABLES = {
        'airconditioners': 'product_airconditioners',
        'dishwashers': 'product_dishwashers',
        'washingmachines': 'product_washingmachines',
        'washerdryers': 'product_washerdryers',
        'tumbledryers': 'product_tumbledryers',
        'refrigeratingappliances': 'product_refrigerators',
        'electronicdisplays': 'product_displays',
        'lightsources': 'product_lightsources',
        'ovens': 'product_ovens',
        'rangehoods': 'product_rangehoods',
        'tyres': 'product_tyres',
        'waterheaters': 'product_waterheaters',
        'spaceheaters': 'product_spaceheaters',
        'ventilationunits': 'product_ventilationunits',
        'professionalrefrigeratedstoragecabinets': 'product_profrefrigeratedcabinets',
    }
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize database connection.
        
        Args:
            host: Database host (defaults to POSTGRES_HOST env var)
            port: Database port (defaults to POSTGRES_PORT env var)
            database: Database name (defaults to POSTGRES_DB env var)
            user: Database user (defaults to POSTGRES_USER env var)
            password: Database password (defaults to POSTGRES_PASSWORD env var)
        """
        self.host = host or os.getenv('POSTGRES_HOST', 'localhost')
        self.port = port or int(os.getenv('POSTGRES_PORT', '5432'))
        self.database = database or os.getenv('POSTGRES_DB', 'eprel')
        self.user = user or os.getenv('POSTGRES_USER', 'eprel_user')
        self.password = password or os.getenv('POSTGRES_PASSWORD', 'eprel_password')
        
        self._connection = None
    
    def connect(self):
        """Establish database connection."""
        try:
            self._connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            self._connection.autocommit = False
            logger.info(f"Connected to database {self.database} at {self.host}:{self.port}")
        except psycopg2.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def disconnect(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnected from database")
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            yield self._connection
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise DatabaseError(f"Transaction failed: {e}")
    
    @contextmanager
    def cursor(self, dict_cursor: bool = False):
        """Context manager for database cursor."""
        cursor_factory = RealDictCursor if dict_cursor else None
        cur = self._connection.cursor(cursor_factory=cursor_factory)
        try:
            yield cur
        finally:
            cur.close()
    
    # ==========================================
    # Product Group Operations
    # ==========================================
    
    def get_product_group_id(self, code: str) -> Optional[int]:
        """Get product group ID by code."""
        with self.cursor() as cur:
            cur.execute(
                "SELECT id FROM product_groups WHERE code = %s",
                (code,)
            )
            result = cur.fetchone()
            return result[0] if result else None
    
    def get_all_product_groups(self) -> List[Dict[str, Any]]:
        """Get all product groups."""
        with self.cursor(dict_cursor=True) as cur:
            cur.execute("SELECT * FROM product_groups ORDER BY name")
            return list(cur.fetchall())
    
    def update_product_group_count(self, code: str, count: int):
        """Update total products count for a product group."""
        with self.transaction():
            with self.cursor() as cur:
                cur.execute(
                    """
                    UPDATE product_groups 
                    SET total_products = %s, last_sync_at = CURRENT_TIMESTAMP
                    WHERE code = %s
                    """,
                    (count, code)
                )
    
    # ==========================================
    # Supplier Operations
    # ==========================================
    
    def upsert_supplier(self, supplier_data: Dict[str, Any]) -> int:
        """Insert or update a supplier and return its ID."""
        eprel_id = supplier_data.get('supplierId') or supplier_data.get('id')
        name = supplier_data.get('supplierName') or supplier_data.get('name', 'Unknown')
        
        with self.cursor() as cur:
            cur.execute(
                """
                INSERT INTO suppliers (eprel_supplier_id, name, trade_name, address, country)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (eprel_supplier_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    trade_name = EXCLUDED.trade_name,
                    address = EXCLUDED.address,
                    country = EXCLUDED.country
                RETURNING id
                """,
                (
                    str(eprel_id) if eprel_id else None,
                    name,
                    supplier_data.get('tradeName'),
                    supplier_data.get('address'),
                    supplier_data.get('country'),
                )
            )
            return cur.fetchone()[0]
    
    # ==========================================
    # Product Operations
    # ==========================================
    
    def upsert_product(self, product_data: Dict[str, Any], product_group_code: str) -> int:
        """
        Insert or update a product and return its ID.
        
        Args:
            product_data: Product data from EPREL API
            product_group_code: Product group code
            
        Returns:
            Product ID
        """
        eprel_id = str(product_data.get('productId') or product_data.get('id', ''))
        
        # Get product group ID
        product_group_id = self.get_product_group_id(product_group_code)
        
        # Handle supplier
        supplier_id = None
        supplier_data = product_data.get('supplier', {})
        if supplier_data or product_data.get('supplierId'):
            if not supplier_data:
                supplier_data = {
                    'id': product_data.get('supplierId'),
                    'name': product_data.get('supplierName', 'Unknown'),
                }
            supplier_id = self.upsert_supplier(supplier_data)
        
        # Parse dates
        registration_date = self._parse_date(product_data.get('registrationDate'))
        on_market_start = self._parse_date(product_data.get('onMarketStartDate'))
        on_market_end = self._parse_date(product_data.get('onMarketEndDate'))
        
        with self.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (
                    eprel_product_id, product_group_id, supplier_id,
                    model_identifier, brand,
                    energy_class, energy_class_index,
                    status, on_market_start_date, on_market_end_date, registration_date,
                    energy_label_url, product_fiche_url,
                    raw_data, last_sync_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (eprel_product_id) DO UPDATE SET
                    product_group_id = EXCLUDED.product_group_id,
                    supplier_id = EXCLUDED.supplier_id,
                    model_identifier = EXCLUDED.model_identifier,
                    brand = EXCLUDED.brand,
                    energy_class = EXCLUDED.energy_class,
                    energy_class_index = EXCLUDED.energy_class_index,
                    status = EXCLUDED.status,
                    on_market_start_date = EXCLUDED.on_market_start_date,
                    on_market_end_date = EXCLUDED.on_market_end_date,
                    registration_date = EXCLUDED.registration_date,
                    energy_label_url = EXCLUDED.energy_label_url,
                    product_fiche_url = EXCLUDED.product_fiche_url,
                    raw_data = EXCLUDED.raw_data,
                    last_sync_at = CURRENT_TIMESTAMP,
                    sync_version = products.sync_version + 1
                RETURNING id
                """,
                (
                    eprel_id,
                    product_group_id,
                    supplier_id,
                    product_data.get('modelIdentifier') or product_data.get('modelName'),
                    product_data.get('brand') or product_data.get('brandName'),
                    product_data.get('energyClass') or product_data.get('energyEfficiencyClass'),
                    product_data.get('energyEfficiencyIndex'),
                    product_data.get('status', 'active'),
                    on_market_start,
                    on_market_end,
                    registration_date,
                    product_data.get('energyLabelUrl'),
                    product_data.get('productFicheUrl'),
                    Json(product_data),
                )
            )
            return cur.fetchone()[0]
    
    def upsert_products_batch(
        self,
        products: List[Dict[str, Any]],
        product_group_code: str,
    ) -> int:
        """
        Batch insert or update products.
        
        Args:
            products: List of product data dictionaries
            product_group_code: Product group code
            
        Returns:
            Number of products processed
        """
        if not products:
            return 0
        
        count = 0
        with self.transaction():
            for product in products:
                try:
                    product_id = self.upsert_product(product, product_group_code)
                    
                    # Insert category-specific data
                    if product_group_code in self.CATEGORY_TABLES:
                        self._upsert_category_data(product_id, product, product_group_code)
                    
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to insert product {product.get('id')}: {e}")
        
        return count
    
    def _upsert_category_data(
        self,
        product_id: int,
        product_data: Dict[str, Any],
        product_group_code: str,
    ):
        """Insert or update category-specific product data."""
        table_name = self.CATEGORY_TABLES.get(product_group_code)
        if not table_name:
            return
        
        # Get field mappings for this category
        fields = self._get_category_fields(product_group_code, product_data)
        if not fields:
            return
        
        columns = ['product_id'] + list(fields.keys())
        values = [product_id] + list(fields.values())
        
        # Build upsert query using psycopg2.sql for safe interpolation
        # Note: table_name and columns are controlled by CATEGORY_TABLES mapping,
        # not user input, but we use sql.Identifier for safety
        table_ident = sql.Identifier(table_name)
        col_idents = sql.SQL(', ').join([sql.Identifier(c) for c in columns])
        placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(values))
        update_set = sql.SQL(', ').join([
            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(col), sql.Identifier(col))
            for col in fields.keys()
        ])
        
        query = sql.SQL("""
            INSERT INTO {} ({})
            VALUES ({})
            ON CONFLICT (product_id) DO UPDATE SET {}
        """).format(table_ident, col_idents, placeholders, update_set)
        
        with self.cursor() as cur:
            cur.execute(query, values)
    
    def _get_category_fields(
        self,
        product_group_code: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract category-specific fields from product data."""
        # Field mappings for each category
        mappings = {
            'dishwashers': {
                'place_settings': 'placeSettings',
                'energy_consumption_kwh_100cycles': 'energyConsumption100Cycles',
                'water_consumption_liters_cycle': 'waterConsumptionCycle',
                'drying_efficiency_class': 'dryingEfficiencyClass',
                'noise_class': 'noiseClass',
                'noise_level_db': 'noiseLevel',
                'eco_program_duration_minutes': 'ecoProgramDuration',
            },
            'washingmachines': {
                'rated_capacity_kg': 'ratedCapacity',
                'energy_consumption_kwh_100cycles': 'energyConsumption100Cycles',
                'water_consumption_liters_cycle': 'waterConsumptionCycle',
                'spin_drying_efficiency_class': 'spinDryingEfficiencyClass',
                'noise_class': 'noiseClass',
                'noise_level_db': 'noiseLevel',
                'max_spin_speed_rpm': 'maxSpinSpeed',
            },
            'refrigeratingappliances': {
                'appliance_type': 'applianceType',
                'total_volume_liters': 'totalVolume',
                'refrigerator_volume_liters': 'refrigeratorVolume',
                'freezer_volume_liters': 'freezerVolume',
                'annual_energy_consumption_kwh': 'annualEnergyConsumption',
                'noise_class': 'noiseClass',
                'noise_level_db': 'noiseLevel',
                'climate_class': 'climateClass',
                'frost_free': 'frostFree',
            },
            'electronicdisplays': {
                'display_type': 'displayType',
                'screen_diagonal_cm': 'screenDiagonalCm',
                'screen_diagonal_inches': 'screenDiagonalInches',
                'resolution_horizontal': 'horizontalResolution',
                'resolution_vertical': 'verticalResolution',
                'panel_technology': 'panelTechnology',
                'on_mode_power_consumption_w': 'onModePowerConsumption',
                'standby_power_consumption_w': 'standbyPowerConsumption',
                'annual_energy_consumption_kwh': 'annualEnergyConsumption',
            },
            'tyres': {
                'tyre_size_designation': 'tyreSizeDesignation',
                'fuel_efficiency_class': 'fuelEfficiencyClass',
                'wet_grip_class': 'wetGripClass',
                'external_rolling_noise_class': 'externalRollingNoiseClass',
                'external_rolling_noise_db': 'externalRollingNoiseLevel',
                'tyre_type': 'tyreType',
                'snow_tyre': 'snowTyre',
                'ice_tyre': 'iceTyre',
            },
        }
        
        mapping = mappings.get(product_group_code, {})
        result = {}
        
        for db_field, api_field in mapping.items():
            value = product_data.get(api_field)
            if value is not None:
                result[db_field] = value
        
        return result
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string from API response."""
        if not date_str:
            return None
        
        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    # ==========================================
    # Sync Job Operations
    # ==========================================
    
    def create_sync_job(
        self,
        job_type: str,
        product_group_id: Optional[int] = None,
    ) -> int:
        """Create a new sync job and return its ID."""
        with self.transaction():
            with self.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sync_jobs (job_type, status, product_group_id, started_at)
                    VALUES (%s, 'running', %s, CURRENT_TIMESTAMP)
                    RETURNING id
                    """,
                    (job_type, product_group_id)
                )
                return cur.fetchone()[0]
    
    def update_sync_job(
        self,
        job_id: int,
        status: Optional[str] = None,
        total_products: Optional[int] = None,
        synced_products: Optional[int] = None,
        failed_products: Optional[int] = None,
        error: Optional[str] = None,
    ):
        """Update sync job status and counts."""
        # Build updates list - these are hardcoded field names, not user input
        update_parts = []
        values = []
        
        if status:
            update_parts.append(sql.SQL("{} = %s").format(sql.Identifier('status')))
            values.append(status)
            if status in ('completed', 'failed'):
                update_parts.append(sql.SQL("{} = CURRENT_TIMESTAMP").format(sql.Identifier('completed_at')))
        
        if total_products is not None:
            update_parts.append(sql.SQL("{} = %s").format(sql.Identifier('total_products')))
            values.append(total_products)
        
        if synced_products is not None:
            update_parts.append(sql.SQL("{} = %s").format(sql.Identifier('synced_products')))
            values.append(synced_products)
        
        if failed_products is not None:
            update_parts.append(sql.SQL("{} = %s").format(sql.Identifier('failed_products')))
            values.append(failed_products)
        
        if error:
            update_parts.append(sql.SQL("{} = %s").format(sql.Identifier('last_error')))
            values.append(error)
        
        if not update_parts:
            return
        
        values.append(job_id)
        
        query = sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
            sql.Identifier('sync_jobs'),
            sql.SQL(', ').join(update_parts),
            sql.Identifier('id')
        )
        
        with self.transaction():
            with self.cursor() as cur:
                cur.execute(query, values)
    
    def get_latest_sync_job(self, product_group_code: Optional[str] = None) -> Optional[Dict]:
        """Get the latest sync job, optionally filtered by product group."""
        with self.cursor(dict_cursor=True) as cur:
            if product_group_code:
                cur.execute(
                    """
                    SELECT sj.* FROM sync_jobs sj
                    JOIN product_groups pg ON sj.product_group_id = pg.id
                    WHERE pg.code = %s
                    ORDER BY sj.created_at DESC
                    LIMIT 1
                    """,
                    (product_group_code,)
                )
            else:
                cur.execute(
                    "SELECT * FROM sync_jobs ORDER BY created_at DESC LIMIT 1"
                )
            return cur.fetchone()
    
    # ==========================================
    # Sync Progress Operations
    # ==========================================
    
    def save_sync_progress(
        self,
        sync_job_id: int,
        product_group_code: str,
        current_page: int,
        total_pages: Optional[int] = None,
        last_processed_id: Optional[str] = None,
        status: str = 'in_progress',
    ):
        """Save sync progress for resumable downloads."""
        with self.transaction():
            with self.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sync_progress 
                        (sync_job_id, product_group_code, current_page, total_pages, last_processed_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sync_job_id, product_group_code) DO UPDATE SET
                        current_page = EXCLUDED.current_page,
                        total_pages = EXCLUDED.total_pages,
                        last_processed_id = EXCLUDED.last_processed_id,
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (sync_job_id, product_group_code, current_page, total_pages, last_processed_id, status)
                )
    
    def get_sync_progress(
        self,
        sync_job_id: int,
        product_group_code: str,
    ) -> Optional[Dict]:
        """Get sync progress for a specific job and product group."""
        with self.cursor(dict_cursor=True) as cur:
            cur.execute(
                """
                SELECT * FROM sync_progress 
                WHERE sync_job_id = %s AND product_group_code = %s
                """,
                (sync_job_id, product_group_code)
            )
            return cur.fetchone()
    
    # ==========================================
    # Statistics
    # ==========================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.cursor(dict_cursor=True) as cur:
            # Total products
            cur.execute("SELECT COUNT(*) as count FROM products")
            total_products = cur.fetchone()['count']
            
            # Products by category
            cur.execute(
                """
                SELECT pg.code, pg.name, COUNT(p.id) as product_count
                FROM product_groups pg
                LEFT JOIN products p ON pg.id = p.product_group_id
                GROUP BY pg.id, pg.code, pg.name
                ORDER BY product_count DESC
                """
            )
            by_category = list(cur.fetchall())
            
            # Total suppliers
            cur.execute("SELECT COUNT(*) as count FROM suppliers")
            total_suppliers = cur.fetchone()['count']
            
            # Latest sync
            cur.execute(
                """
                SELECT * FROM sync_jobs 
                WHERE status = 'completed' 
                ORDER BY completed_at DESC 
                LIMIT 1
                """
            )
            latest_sync = cur.fetchone()
            
            return {
                'total_products': total_products,
                'total_suppliers': total_suppliers,
                'products_by_category': by_category,
                'latest_sync': latest_sync,
            }
