#!/usr/bin/env python3
"""
Script to fetch 1 sample product from each EPREL category.

This script connects to the EPREL API and retrieves a single product
from each of the 22 product categories to verify API connectivity
and understand the data structure.

Usage:
    python fetch_samples.py

Requires:
    - EPREL_API_KEY environment variable set with your API key
    - requests library (pip install requests)
"""

import os
import json
import time
import requests
from datetime import datetime

# EPREL API Base URL
BASE_URL = "https://eprel.ec.europa.eu/api/products"

# All 22 product categories from EPREL
PRODUCT_CATEGORIES = [
    {"code": "AIR_CONDITIONER", "url_code": "airconditioners", "name": "Air conditioners"},
    {"code": "DOMESTIC_OVEN", "url_code": "ovens", "name": "Domestic Ovens"},
    {"code": "RANGE_HOOD", "url_code": "rangehoods", "name": "Range hoods"},
    {"code": "HOUSEHOLD_COMBINED_WASHER_DRIER", "url_code": "washerdriers", "name": "Household combined washer-driers"},
    {"code": "HOUSEHOLD_DISHWASHER", "url_code": "dishwashers", "name": "Household dishwashers"},
    {"code": "HOUSEHOLD_REFRIGERATING_APPLIANCE", "url_code": "refrigeratingappliances", "name": "Household refrigerating appliances"},
    {"code": "HOUSEHOLD_TUMBLE_DRIER", "url_code": "tumbledriers", "name": "Household tumble driers"},
    {"code": "HOUSEHOLD_WASHING_MACHINE", "url_code": "washingmachines", "name": "Household washing machines"},
    {"code": "LOCAL_SPACE_HEATER", "url_code": "localspaceheaters", "name": "Local space heaters"},
    {"code": "RESIDENTIAL_VENTILATION_UNIT", "url_code": "residentialventilationunits", "name": "Residential Ventilation Units"},
    {"code": "TELEVISION", "url_code": "televisions", "name": "Televisions"},
    {"code": "SPACE_HEATER", "url_code": "spaceheaters", "name": "Space heaters/Combination heaters"},
    {"code": "SPACE_HEATER_TEMPERATURE_CONTROL", "url_code": "spaceheatertemperaturecontrol", "name": "Temperature controls for space heaters"},
    {"code": "WATER_HEATERS", "url_code": "waterheaters", "name": "Water heaters"},
    {"code": "HOT_WATER_STORAGE_TANK", "url_code": "hotwaterstoragetanks", "name": "Hot water storage tanks for water heaters"},
    {"code": "ELECTRONIC_DISPLAY", "url_code": "electronicdisplays", "name": "Electronic displays"},
    {"code": "HOUSEHOLD_WASHER_DRYER_2019", "url_code": "washerdriers2019", "name": "Household washer-dryers"},
    {"code": "HOUSEHOLD_WASHING_MACHINE_2019", "url_code": "washingmachines2019", "name": "Household washing machines"},
    {"code": "HOUSEHOLD_REFRIGERATING_APPLIANCE_2019", "url_code": "refrigeratingappliances2019", "name": "Refrigerating appliances"},
    {"code": "HOUSEHOLD_DISHWASHER_2019", "url_code": "dishwashers2019", "name": "Household dishwashers"},
    {"code": "HOUSEHOLD_TUMBLE_DRYER_2023_2534", "url_code": "tumbledryers20232534", "name": "Household tumble dryers"},
    {"code": "SMARTPHONE_TABLET_2023_1669", "url_code": "smartphonestablets20231669", "name": "Smartphones and slate tablets"},
]


def get_api_key():
    """Get EPREL API key from environment variable."""
    api_key = os.getenv('EPREL_API_KEY')
    if not api_key:
        raise ValueError(
            "EPREL_API_KEY environment variable not set.\n"
            "Request your API key at: https://eprel.ec.europa.eu/screen/requestpublicapikey"
        )
    return api_key


def fetch_one_product(category_url_code, api_key):
    """
    Fetch 1 product from a specific category.
    
    Args:
        category_url_code: The URL code for the category (e.g., 'dishwashers')
        api_key: EPREL API key
        
    Returns:
        dict: Product data or error information
    """
    url = f"{BASE_URL}/{category_url_code}"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    params = {
        "limit": 1  # Request only 1 product
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # Handle different response formats
            if isinstance(data, list):
                return {"success": True, "data": data[0] if data else None, "total": len(data)}
            elif isinstance(data, dict):
                items = data.get('hits', data.get('data', data.get('products', [])))
                total = data.get('total', len(items))
                return {"success": True, "data": items[0] if items else None, "total": total}
            else:
                return {"success": True, "data": data, "total": 1}
        else:
            return {
                "success": False, 
                "error": f"HTTP {response.status_code}", 
                "message": response.text[:200]
            }
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": "Request failed", "message": str(e)}


def main():
    """Main function to fetch 1 product from each category."""
    print("=" * 60)
    print("EPREL API - Fetching 1 sample product from each category")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Get API key
    try:
        api_key = get_api_key()
        print("✓ API key loaded successfully")
    except ValueError as e:
        print(f"✗ Error: {e}")
        return
    
    print(f"\nFetching from {len(PRODUCT_CATEGORIES)} categories...\n")
    print("-" * 60)
    
    results = {}
    successful = 0
    failed = 0
    
    for i, category in enumerate(PRODUCT_CATEGORIES, 1):
        url_code = category['url_code']
        name = category['name']
        
        print(f"[{i:02d}/{len(PRODUCT_CATEGORIES)}] {name} ({url_code})...")
        
        result = fetch_one_product(url_code, api_key)
        results[url_code] = {
            "category": category,
            "result": result
        }
        
        if result['success']:
            successful += 1
            if result['data']:
                product_id = result['data'].get('productId', result['data'].get('id', 'N/A'))
                print(f"         ✓ Success - Product ID: {product_id}, Total in category: {result['total']}")
            else:
                print(f"         ✓ Success - No products in category (Total: {result['total']})")
        else:
            failed += 1
            print(f"         ✗ Failed - {result['error']}: {result.get('message', '')[:50]}")
        
        # Rate limiting - wait between requests
        time.sleep(0.5)
    
    print("-" * 60)
    print(f"\nSummary:")
    print(f"  Successful: {successful}/{len(PRODUCT_CATEGORIES)}")
    print(f"  Failed: {failed}/{len(PRODUCT_CATEGORIES)}")
    
    # Save results to JSON file
    output_file = "eprel_samples.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Full results saved to: {output_file}")
    
    # Print sample of one successful result
    print("\n" + "=" * 60)
    print("Sample product data (first successful category):")
    print("=" * 60)
    
    for url_code, data in results.items():
        if data['result']['success'] and data['result']['data']:
            print(f"\nCategory: {data['category']['name']}")
            print(json.dumps(data['result']['data'], indent=2, ensure_ascii=False)[:2000])
            if len(json.dumps(data['result']['data'])) > 2000:
                print("... (truncated)")
            break


if __name__ == "__main__":
    main()
