"""
EPREL API Client for fetching product data from the European Product Registry for Energy Labelling.
"""

import os
import logging
import time
from typing import Optional, Dict, Any, Iterator, List
from dataclasses import dataclass

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


@dataclass
class PaginatedResponse:
    """Represents a paginated API response."""
    items: List[Dict[str, Any]]
    total_count: int
    current_page: int
    page_size: int
    has_more: bool
    

class EPRELAPIError(Exception):
    """Base exception for EPREL API errors."""
    pass


class EPRELRateLimitError(EPRELAPIError):
    """Raised when rate limit is exceeded."""
    pass


class EPRELAuthError(EPRELAPIError):
    """Raised when authentication fails."""
    pass


class EPRELClient:
    """
    Client for the EPREL Public API.
    
    Handles pagination, rate limiting, and retry logic for fetching 
    product data from the European Product Registry for Energy Labelling.
    """
    
    # Known product group endpoints
    PRODUCT_GROUPS = {
        'airconditioners': 'airconditioners',
        'dishwashers': 'dishwashers',
        'washingmachines': 'washingmachines',
        'washerdryers': 'washerdryers',
        'tumbledryers': 'tumbledryers',
        'refrigeratingappliances': 'refrigeratingappliances',
        'electronicdisplays': 'electronicdisplays',
        'lightsources': 'lightsources',
        'ovens': 'ovens',
        'rangehoods': 'rangehoods',
        'tyres': 'tyres',
        'waterheaters': 'waterheaters',
        'spaceheaters': 'spaceheaters',
        'ventilationunits': 'ventilationunits',
        'professionalrefrigeratedstoragecabinets': 'professionalrefrigeratedstoragecabinets',
        'solidfuelboilers': 'solidfuelboilers',
        'localheaterssolid': 'localheaterssolid',
        'localheatersgaseous': 'localheatersgaseous',
    }
    
    DEFAULT_BASE_URL = "https://eprel.ec.europa.eu/api/public"
    MAX_PAGE_SIZE = 100  # Maximum items per request as per API limit
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        page_size: int = 100,
        request_delay: float = 0.5,
        max_retries: int = 3,
    ):
        """
        Initialize the EPREL API client.
        
        Args:
            api_key: EPREL API key (defaults to EPREL_API_KEY env var)
            base_url: Base URL for the API (defaults to EPREL_API_BASE_URL env var)
            page_size: Number of items per page (max 100)
            request_delay: Delay between requests in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.api_key = api_key or os.getenv('EPREL_API_KEY')
        if not self.api_key:
            raise EPRELAuthError("EPREL API key is required. Set EPREL_API_KEY environment variable.")
        
        self.base_url = base_url or os.getenv('EPREL_API_BASE_URL', self.DEFAULT_BASE_URL)
        self.page_size = min(page_size, self.MAX_PAGE_SIZE)
        self.request_delay = request_delay
        self.max_retries = max_retries
        
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self._last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((requests.exceptions.RequestException, EPRELRateLimitError)),
    )
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a rate-limited request to the API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            EPRELAPIError: For API errors
            EPRELRateLimitError: For rate limit errors
            EPRELAuthError: For authentication errors
        """
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 401:
                raise EPRELAuthError("Invalid API key")
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                raise EPRELRateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                raise EPRELAPIError(f"API error {response.status_code}: {response.text}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_product_groups(self) -> List[Dict[str, Any]]:
        """
        Get list of available product groups.
        
        Returns:
            List of product group dictionaries
        """
        try:
            response = self._make_request('product-groups')
            return response if isinstance(response, list) else response.get('data', [])
        except Exception:
            # Return static list if API doesn't support this endpoint
            return [{'code': code, 'name': code} for code in self.PRODUCT_GROUPS.keys()]
    
    def get_products_page(
        self,
        product_group: str,
        page: int = 1,
        page_size: Optional[int] = None,
    ) -> PaginatedResponse:
        """
        Fetch a single page of products for a product group.
        
        Args:
            product_group: Product group code (e.g., 'dishwashers')
            page: Page number (1-indexed)
            page_size: Items per page (defaults to client page_size)
            
        Returns:
            PaginatedResponse with products and pagination info
        """
        page_size = page_size or self.page_size
        
        params = {
            'page': page,
            'limit': page_size,
        }
        
        endpoint = f"products/{product_group}"
        response = self._make_request(endpoint, params)
        
        # Handle different response formats
        if isinstance(response, list):
            items = response
            total_count = len(items)
        else:
            items = response.get('data', response.get('items', response.get('products', [])))
            total_count = response.get('total', response.get('totalCount', response.get('count', len(items))))
        
        has_more = len(items) == page_size and (page * page_size) < total_count
        
        return PaginatedResponse(
            items=items,
            total_count=total_count,
            current_page=page,
            page_size=page_size,
            has_more=has_more,
        )
    
    def get_all_products(
        self,
        product_group: str,
        start_page: int = 1,
        max_products: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Generator that yields all products for a product group.
        
        Handles pagination automatically, fetching pages of products
        until all are retrieved or max_products is reached.
        
        Args:
            product_group: Product group code
            start_page: Starting page number (for resuming)
            max_products: Maximum products to fetch (None for all)
            
        Yields:
            Product dictionaries one at a time
        """
        page = start_page
        products_fetched = 0
        
        while True:
            try:
                response = self.get_products_page(product_group, page)
                
                if not response.items:
                    break
                
                for product in response.items:
                    yield product
                    products_fetched += 1
                    
                    if max_products and products_fetched >= max_products:
                        return
                
                if not response.has_more:
                    break
                    
                page += 1
                
            except EPRELAPIError as e:
                logger.error(f"Error fetching page {page} of {product_group}: {e}")
                raise
    
    def get_product_count(self, product_group: str) -> int:
        """
        Get total count of products in a product group.
        
        Args:
            product_group: Product group code
            
        Returns:
            Total number of products
        """
        # Fetch first page with minimal items to get total count
        response = self.get_products_page(product_group, page=1, page_size=1)
        return response.total_count
    
    def get_product_details(self, product_group: str, product_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific product.
        
        Args:
            product_group: Product group code
            product_id: EPREL product ID
            
        Returns:
            Product details dictionary
        """
        endpoint = f"products/{product_group}/{product_id}"
        return self._make_request(endpoint)
    
    def get_energy_label(self, product_group: str, product_id: str, format: str = 'pdf') -> bytes:
        """
        Download energy label for a product.
        
        Args:
            product_group: Product group code
            product_id: EPREL product ID
            format: Label format ('pdf', 'svg', 'jpg')
            
        Returns:
            Label file content as bytes
        """
        self._rate_limit()
        
        url = f"{self.base_url}/products/{product_group}/{product_id}/labels"
        params = {'format': format}
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response.content
    
    def get_product_fiche(self, product_group: str, product_id: str, format: str = 'pdf') -> bytes:
        """
        Download product information sheet for a product.
        
        Args:
            product_group: Product group code
            product_id: EPREL product ID
            format: Sheet format ('pdf')
            
        Returns:
            Product sheet file content as bytes
        """
        self._rate_limit()
        
        url = f"{self.base_url}/products/{product_group}/{product_id}/fiches"
        params = {'format': format}
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response.content
    
    def health_check(self) -> bool:
        """
        Check if the API is accessible and credentials are valid.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to fetch first page of a common product group
            self.get_products_page('dishwashers', page=1, page_size=1)
            return True
        except EPRELAuthError:
            logger.error("API authentication failed")
            return False
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return False
