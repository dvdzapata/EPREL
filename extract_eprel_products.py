#!/usr/bin/env python3
"""
Script para extraer 1 producto por categoría de la API EPREL.
Respeta el límite de 5 peticiones por segundo.
"""

import json
import time
import urllib.request
import urllib.error

# Lista de categorías según el issue
CATEGORIES = [
    {
        "code": "AIR_CONDITIONER",
        "url_code": "airconditioners",
        "name": "Air conditioners",
        "regulation": "Regulation (EU) 626/2011"
    },
    {
        "code": "DOMESTIC_OVEN",
        "url_code": "ovens",
        "name": "Domestic Ovens",
        "regulation": "Regulation (EU) 65/2014"
    },
    {
        "code": "RANGE_HOOD",
        "url_code": "rangehoods",
        "name": "Range hoods",
        "regulation": "Regulation (EU) 65/2014"
    },
    {
        "code": "HOUSEHOLD_COMBINED_WASHER_DRIER",
        "url_code": "washerdriers",
        "name": "Household combined washer-driers",
        "regulation": "Regulation 96/60/EC"
    },
    {
        "code": "HOUSEHOLD_DISHWASHER",
        "url_code": "dishwashers",
        "name": "Household dishwashers",
        "regulation": "Regulation (EU) 1059/2010"
    },
    {
        "code": "HOUSEHOLD_REFRIGERATING_APPLIANCE",
        "url_code": "refrigeratingappliances",
        "name": "Household refrigerating appliances",
        "regulation": "Regulation (EU) 1060/2010"
    },
    {
        "code": "HOUSEHOLD_TUMBLE_DRIER",
        "url_code": "tumbledriers",
        "name": "Household tumble driers",
        "regulation": "Regulation (EU) 392/2012"
    },
    {
        "code": "HOUSEHOLD_WASHING_MACHINE",
        "url_code": "washingmachines",
        "name": "Household washing machines",
        "regulation": "Regulation (EU) 1061/2010"
    },
    {
        "code": "LOCAL_SPACE_HEATER",
        "url_code": "localspaceheaters",
        "name": "Local space heaters",
        "regulation": "Regulation (EU) 2015/1186"
    },
    {
        "code": "RESIDENTIAL_VENTILATION_UNIT",
        "url_code": "residentialventilationunits",
        "name": "Residential Ventilation Units",
        "regulation": "Regulation (EU) 1254/2014"
    },
    {
        "code": "TELEVISION",
        "url_code": "televisions",
        "name": "Televisions",
        "regulation": "Regulation (EU) 1062/2010"
    },
    {
        "code": "SPACE_HEATER",
        "url_code": "spaceheaters",
        "name": "Space heaters/Combination heaters",
        "regulation": "Regulation (EU) 811/2013"
    },
    {
        "code": "SPACE_HEATER_TEMPERATURE_CONTROL",
        "url_code": "spaceheatertemperaturecontrol",
        "name": "Temperature controls for space heaters",
        "regulation": "Regulation (EU) 811/2013"
    },
    {
        "code": "WATER_HEATERS",
        "url_code": "waterheaters",
        "name": "Water heaters",
        "regulation": "Regulation (EU) 812/2013"
    },
    {
        "code": "HOT_WATER_STORAGE_TANK",
        "url_code": "hotwaterstoragetanks",
        "name": "Hot water storage tanks for water heaters",
        "regulation": "Regulation (EU) 812/2013"
    },
    {
        "code": "ELECTRONIC_DISPLAY",
        "url_code": "electronicdisplays",
        "name": "Electronic displays",
        "regulation": "Regulation (EU) 2019/2013"
    },
    {
        "code": "HOUSEHOLD_WASHER_DRYER_2019",
        "url_code": "washerdriers2019",
        "name": "Household washer-dryers",
        "regulation": "Regulation (EU) 2019/2014"
    },
    {
        "code": "HOUSEHOLD_WASHING_MACHINE_2019",
        "url_code": "washingmachines2019",
        "name": "Household washing machines",
        "regulation": "Regulation (EU) 2019/2014"
    },
    {
        "code": "HOUSEHOLD_REFRIGERATING_APPLIANCE_2019",
        "url_code": "refrigeratingappliances2019",
        "name": "Refrigerating appliances",
        "regulation": "Regulation (EU) 2019/2016"
    },
    {
        "code": "HOUSEHOLD_DISHWASHER_2019",
        "url_code": "dishwashers2019",
        "name": "Household dishwashers",
        "regulation": "Regulation (EU) 2019/2017"
    },
    {
        "code": "HOUSEHOLD_TUMBLE_DRYER_2023_2534",
        "url_code": "tumbledryers20232534",
        "name": "Household tumble dryers",
        "regulation": "Regulation (EU) 2023/2534"
    },
    {
        "code": "SMARTPHONE_TABLET_2023_1669",
        "url_code": "smartphonestablets20231669",
        "name": "Smartphones and slate tablets",
        "regulation": "Regulation (EU) 2023/1669"
    }
]

# Base URL de la API EPREL
BASE_URL = "https://eprel.ec.europa.eu/api/products"

# Archivo de salida
OUTPUT_FILE = "eprel_products.json"

# Rate limiting: máximo 5 peticiones por segundo -> 0.2 segundos entre peticiones
REQUEST_DELAY = 0.2


def fetch_product_list(url_code):
    """
    Obtiene la lista de productos de una categoría.
    Retorna el primer producto ID de la lista.
    """
    url = f"{BASE_URL}/{url_code}"
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "EPREL-Extractor/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"  URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None


def fetch_product_details(url_code, product_id):
    """
    Obtiene los detalles completos de un producto específico.
    """
    url = f"{BASE_URL}/{url_code}/{product_id}"
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "EPREL-Extractor/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"  URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None


def main():
    """
    Función principal que extrae un producto de cada categoría.
    """
    print("=" * 60)
    print("Extracción de productos EPREL")
    print("=" * 60)
    print(f"Total de categorías: {len(CATEGORIES)}")
    print(f"Archivo de salida: {OUTPUT_FILE}")
    print(f"Delay entre peticiones: {REQUEST_DELAY}s (máx 5 req/s)")
    print("=" * 60)

    results = []

    for i, category in enumerate(CATEGORIES, 1):
        print(f"\n[{i}/{len(CATEGORIES)}] Procesando: {category['name']} ({category['code']})")

        # Obtener lista de productos de la categoría
        print(f"  Obteniendo lista de productos...")
        product_list = fetch_product_list(category["url_code"])
        time.sleep(REQUEST_DELAY)

        if product_list is None:
            print(f"  ❌ No se pudo obtener la lista de productos")
            results.append({
                "category": category,
                "product_list": None,
                "product_details": None,
                "error": "No se pudo obtener la lista de productos"
            })
            continue

        # Verificar si hay productos en la lista
        if not isinstance(product_list, dict):
            print(f"  ⚠️ Respuesta inesperada de la API")
            results.append({
                "category": category,
                "product_list": product_list,
                "product_details": None,
                "error": "Respuesta inesperada de la API"
            })
            continue

        products = product_list.get("hits", [])
        if not products or not isinstance(products, list):
            print(f"  ⚠️ No hay productos en esta categoría")
            results.append({
                "category": category,
                "product_list": product_list,
                "product_details": None,
                "error": "No hay productos disponibles"
            })
            continue

        # Obtener el primer producto
        first_product_id = products[0]
        print(f"  Primer producto ID: {first_product_id}")
        print(f"  Obteniendo detalles del producto...")

        product_details = fetch_product_details(category["url_code"], first_product_id)
        time.sleep(REQUEST_DELAY)

        if product_details is None:
            print(f"  ❌ No se pudo obtener los detalles del producto")
            results.append({
                "category": category,
                "product_list": product_list,
                "product_details": None,
                "error": "No se pudo obtener los detalles del producto"
            })
            continue

        print(f"  ✅ Producto obtenido correctamente")
        results.append({
            "category": category,
            "product_list": product_list,
            "product_details": product_details,
            "error": None
        })

    # Guardar resultados en archivo JSON
    print("\n" + "=" * 60)
    print("Guardando resultados...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Resultados guardados en: {OUTPUT_FILE}")

    # Resumen
    success_count = sum(1 for r in results if r["error"] is None)
    error_count = len(results) - success_count

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total de categorías procesadas: {len(results)}")
    print(f"Exitosas: {success_count}")
    print(f"Con errores: {error_count}")

    if error_count > 0:
        print("\nCategorías con errores:")
        for r in results:
            if r["error"]:
                print(f"  - {r['category']['name']}: {r['error']}")

    print("\n" + "=" * 60)
    print("Extracción completada")
    print("=" * 60)


if __name__ == "__main__":
    main()
