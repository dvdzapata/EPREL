"""
EPREL Data Synchronization Service.

Handles the synchronization of product data from the EPREL API to the local database.
Supports full sync, incremental sync, and category-specific sync with resumable downloads.
"""

import os
import logging
import signal
import sys
from typing import Optional, List
from datetime import datetime

from dotenv import load_dotenv
from tqdm import tqdm

from eprel_client import EPRELClient, EPRELAPIError
from database import Database, DatabaseError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync.log'),
    ]
)
logger = logging.getLogger(__name__)


class SyncService:
    """
    Service for synchronizing EPREL data to the local database.
    
    Features:
    - Full sync of all product groups
    - Category-specific sync
    - Resumable downloads (saves progress)
    - Progress tracking with tqdm
    - Graceful shutdown handling
    """
    
    def __init__(self, db: Database, client: EPRELClient):
        """
        Initialize the sync service.
        
        Args:
            db: Database instance
            client: EPREL API client instance
        """
        self.db = db
        self.client = client
        self._shutdown_requested = False
        self._current_job_id = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.warning("Shutdown requested. Finishing current batch...")
        self._shutdown_requested = True
    
    def sync_all(self, product_groups: Optional[List[str]] = None, resume: bool = True):
        """
        Sync all product groups or specified ones.
        
        Args:
            product_groups: List of product group codes to sync (None for all)
            resume: Whether to resume from last progress
        """
        # Get product groups to sync
        if product_groups:
            groups = product_groups
        else:
            db_groups = self.db.get_all_product_groups()
            groups = [g['code'] for g in db_groups]
        
        logger.info(f"Starting sync for {len(groups)} product groups")
        
        # Create sync job
        self._current_job_id = self.db.create_sync_job('full')
        
        total_synced = 0
        total_failed = 0
        
        for group_code in groups:
            if self._shutdown_requested:
                break
            
            try:
                synced, failed = self.sync_category(group_code, resume=resume)
                total_synced += synced
                total_failed += failed
            except Exception as e:
                logger.error(f"Failed to sync {group_code}: {e}")
                total_failed += 1
        
        # Update job status
        status = 'completed' if not self._shutdown_requested else 'interrupted'
        self.db.update_sync_job(
            self._current_job_id,
            status=status,
            synced_products=total_synced,
            failed_products=total_failed,
        )
        
        logger.info(f"Sync {'completed' if not self._shutdown_requested else 'interrupted'}. "
                   f"Synced: {total_synced}, Failed: {total_failed}")
    
    def sync_category(
        self,
        product_group_code: str,
        resume: bool = True,
        max_products: Optional[int] = None,
    ) -> tuple:
        """
        Sync a specific product category.
        
        Args:
            product_group_code: Product group code to sync
            resume: Whether to resume from last progress
            max_products: Maximum number of products to sync (None for all)
            
        Returns:
            Tuple of (synced_count, failed_count)
        """
        logger.info(f"Starting sync for category: {product_group_code}")
        
        # Get product group ID
        group_id = self.db.get_product_group_id(product_group_code)
        if not group_id:
            logger.error(f"Unknown product group: {product_group_code}")
            return 0, 0
        
        # Create or use existing job
        if not self._current_job_id:
            self._current_job_id = self.db.create_sync_job('category', group_id)
        
        # Check for resume point
        start_page = 1
        if resume and self._current_job_id:
            progress = self.db.get_sync_progress(self._current_job_id, product_group_code)
            if progress and progress['status'] == 'in_progress':
                start_page = progress['current_page'] + 1
                logger.info(f"Resuming from page {start_page}")
        
        # Get total count
        try:
            total_count = self.client.get_product_count(product_group_code)
            total_pages = (total_count + self.client.page_size - 1) // self.client.page_size
            logger.info(f"Total products in {product_group_code}: {total_count} ({total_pages} pages)")
        except EPRELAPIError as e:
            logger.error(f"Failed to get product count: {e}")
            return 0, 0
        
        # Update product group count
        self.db.update_product_group_count(product_group_code, total_count)
        
        synced_count = 0
        failed_count = 0
        current_page = start_page
        
        # Progress bar
        pbar = tqdm(
            total=total_count,
            initial=(start_page - 1) * self.client.page_size,
            desc=f"Syncing {product_group_code}",
            unit="products"
        )
        
        try:
            while not self._shutdown_requested:
                # Fetch page of products
                try:
                    response = self.client.get_products_page(
                        product_group_code,
                        page=current_page,
                    )
                except EPRELAPIError as e:
                    logger.error(f"Failed to fetch page {current_page}: {e}")
                    failed_count += self.client.page_size
                    
                    # Save error in progress
                    self.db.save_sync_progress(
                        self._current_job_id,
                        product_group_code,
                        current_page - 1,
                        total_pages,
                        status='error',
                    )
                    break
                
                if not response.items:
                    break
                
                # Process batch
                batch_synced = self.db.upsert_products_batch(
                    response.items,
                    product_group_code,
                )
                
                synced_count += batch_synced
                failed_count += len(response.items) - batch_synced
                
                # Update progress bar
                pbar.update(len(response.items))
                
                # Save progress
                last_id = response.items[-1].get('productId') or response.items[-1].get('id')
                self.db.save_sync_progress(
                    self._current_job_id,
                    product_group_code,
                    current_page,
                    total_pages,
                    str(last_id) if last_id else None,
                    status='in_progress',
                )
                
                # Check if we've hit max_products
                if max_products and synced_count >= max_products:
                    break
                
                # Check if there are more pages
                if not response.has_more:
                    break
                
                current_page += 1
        
        finally:
            pbar.close()
        
        # Mark progress as completed
        if not self._shutdown_requested:
            self.db.save_sync_progress(
                self._current_job_id,
                product_group_code,
                current_page,
                total_pages,
                status='completed',
            )
        
        logger.info(f"Synced {synced_count} products from {product_group_code} "
                   f"(failed: {failed_count})")
        
        return synced_count, failed_count
    
    def get_statistics(self):
        """Get and display sync statistics."""
        stats = self.db.get_statistics()
        
        print("\n=== EPREL Database Statistics ===\n")
        print(f"Total Products: {stats['total_products']:,}")
        print(f"Total Suppliers: {stats['total_suppliers']:,}")
        
        if stats['latest_sync']:
            print(f"\nLatest Sync: {stats['latest_sync']['completed_at']}")
            print(f"  Status: {stats['latest_sync']['status']}")
            print(f"  Products Synced: {stats['latest_sync']['synced_products']:,}")
        
        print("\n--- Products by Category ---")
        for cat in stats['products_by_category']:
            print(f"  {cat['name']}: {cat['product_count']:,}")
        
        return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='EPREL Data Synchronization')
    parser.add_argument(
        '--sync',
        choices=['all', 'category'],
        help='Sync mode: all categories or specific category'
    )
    parser.add_argument(
        '--category',
        type=str,
        help='Product group code for category sync'
    )
    parser.add_argument(
        '--categories',
        type=str,
        nargs='+',
        help='List of product group codes to sync'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Do not resume from last progress'
    )
    parser.add_argument(
        '--max-products',
        type=int,
        help='Maximum products to sync per category'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    parser.add_argument(
        '--test-api',
        action='store_true',
        help='Test API connectivity'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    db = Database()
    
    try:
        db.connect()
        
        if args.stats:
            # Initialize client for potential API calls
            try:
                client = EPRELClient()
            except Exception:
                client = None
            
            service = SyncService(db, client) if client else None
            if service:
                service.get_statistics()
            else:
                stats = db.get_statistics()
                print(f"Total Products: {stats['total_products']:,}")
            return
        
        # Initialize API client
        client = EPRELClient()
        
        if args.test_api:
            print("Testing API connectivity...")
            if client.health_check():
                print("✓ API connection successful")
            else:
                print("✗ API connection failed")
            return
        
        # Initialize sync service
        service = SyncService(db, client)
        
        if args.sync == 'all':
            service.sync_all(
                product_groups=args.categories,
                resume=not args.no_resume,
            )
        elif args.sync == 'category':
            if not args.category:
                print("Error: --category required for category sync")
                sys.exit(1)
            service.sync_category(
                args.category,
                resume=not args.no_resume,
                max_products=args.max_products,
            )
        else:
            parser.print_help()
    
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except EPRELAPIError as e:
        logger.error(f"API error: {e}")
        sys.exit(1)
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
