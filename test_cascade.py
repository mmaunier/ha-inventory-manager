#!/usr/bin/env python3
"""Script de test pour vérifier la cascade de recherche de codes-barres."""

import asyncio
import aiohttp
import logging
import sys

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_LOGGER = logging.getLogger(__name__)

# URLs des APIs
OPENFOODFACTS_API_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
UPCITEMDB_API_URL = "https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
OPENGTINDB_API_URL = "https://opengtindb.org/?ean={barcode}&cmd=query&queryid=400000000"


async def fetch_from_openfoodfacts(barcode: str) -> dict | None:
    """Fetch product information from Open Food Facts (food products)."""
    url = OPENFOODFACTS_API_URL.format(barcode=barcode)
    
    try:
        _LOGGER.info("Trying Open Food Facts API: %s", url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                _LOGGER.debug("Open Food Facts response status: %s", response.status)
                if response.status != 200:
                    return None

                data = await response.json()
                
                if data.get("status") != 1:
                    _LOGGER.debug("Open Food Facts: Product not found (status=%s)", data.get("status"))
                    return None

                product = data.get("product", {})
                
                result = {
                    "barcode": barcode,
                    "name": product.get("product_name", product.get("product_name_fr", "")),
                    "brand": product.get("brands", ""),
                    "categories": product.get("categories", ""),
                    "categories_tags": product.get("categories_tags", []),
                    "image_url": product.get("image_url", ""),
                    "quantity_info": product.get("quantity", ""),
                    "nutriscore": product.get("nutriscore_grade", ""),
                }
                _LOGGER.info("✓ Found in Open Food Facts: %s", result["name"])
                return result

    except asyncio.TimeoutError:
        _LOGGER.warning("Open Food Facts: Request timeout (>15s)")
        return None
    except Exception as err:
        _LOGGER.debug("Open Food Facts: Error - %s", err)
        return None


async def fetch_from_upcitemdb(barcode: str) -> dict | None:
    """Fetch product information from UPCitemdb (general products)."""
    url = UPCITEMDB_API_URL.format(barcode=barcode)
    
    try:
        _LOGGER.info("Trying UPCitemdb API: %s", url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                _LOGGER.debug("UPCitemdb response status: %s", response.status)
                if response.status != 200:
                    return None

                data = await response.json()
                
                # Check if product found
                if not data.get("items") or len(data["items"]) == 0:
                    _LOGGER.debug("UPCitemdb: Product not found (items empty)")
                    return None
                
                product = data["items"][0]
                
                # Extract name and brand
                title = product.get("title", "")
                brand = product.get("brand", "")
                category_raw = product.get("category", "")
                
                result = {
                    "barcode": barcode,
                    "name": title,
                    "brand": brand,
                    "categories": category_raw,
                    "categories_tags": [category_raw.lower()] if category_raw else [],
                    "image_url": product.get("images", [""])[0] if product.get("images") else "",
                    "quantity_info": "",
                    "nutriscore": "",
                }
                _LOGGER.info("✓ Found in UPCitemdb: %s", result["name"])
                return result

    except asyncio.TimeoutError:
        _LOGGER.warning("UPCitemdb: Request timeout (>15s)")
        return None
    except Exception as err:
        _LOGGER.debug("UPCitemdb: Error - %s", err)
        return None


async def fetch_from_opengtindb(barcode: str) -> dict | None:
    """Fetch product information from OpenGTINDB (free, no registration required)."""
    url = OPENGTINDB_API_URL.format(barcode=barcode)
    
    try:
        _LOGGER.info("Trying OpenGTINDB API: %s", url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                _LOGGER.debug("OpenGTINDB response status: %s", response.status)
                if response.status != 200:
                    return None

                text = await response.text()
                
                # Parse the simple key=value format
                lines = text.strip().split('\n')
                data = {}
                for line in lines:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        data[key] = value
                
                # Check if error=0 (found) or error=1 (not found)
                if data.get("error") != "0":
                    _LOGGER.debug("OpenGTINDB: Product not found (error=%s)", data.get("error"))
                    return None
                
                # Extract product name (prioritize detailname over name)
                product_name = data.get("detailname", "").strip() or data.get("name", "").strip()
                if not product_name:
                    _LOGGER.debug("OpenGTINDB: Product found but no name available")
                    return None
                
                vendor = data.get("vendor", "").strip()
                maincat = data.get("maincat", "").strip()
                subcat = data.get("subcat", "").strip()
                
                # Combine categories for mapping
                categories_list = []
                if maincat:
                    categories_list.append(maincat.lower())
                if subcat:
                    categories_list.append(subcat.lower())
                
                result = {
                    "barcode": barcode,
                    "name": product_name,
                    "brand": vendor,
                    "categories": f"{maincat}/{subcat}" if maincat and subcat else maincat or subcat,
                    "categories_tags": categories_list,
                    "image_url": "",
                    "quantity_info": data.get("contents", ""),
                    "nutriscore": "",
                }
                _LOGGER.info("✓ Found in OpenGTINDB: %s", result["name"])
                return result

    except asyncio.TimeoutError:
        _LOGGER.warning("OpenGTINDB: Request timeout (>15s)")
        return None
    except Exception as err:
        _LOGGER.debug("OpenGTINDB: Error - %s", err)
        return None


async def cascade_search(barcode: str):
    """Perform cascade search across all APIs."""
    _LOGGER.info("=" * 80)
    _LOGGER.info("[CASCADE SEARCH] Starting search for barcode: %s", barcode)
    _LOGGER.info("=" * 80)
    
    # Try Open Food Facts first
    result = await fetch_from_openfoodfacts(barcode)
    if result:
        result["source"] = "Open Food Facts"
        print(f"\n✓ SUCCESS: Product found in Open Food Facts")
        print(f"  Name: {result.get('name')}")
        print(f"  Brand: {result.get('brand')}")
        print(f"  Categories: {result.get('categories')}")
        return result
    _LOGGER.debug("✗ Not found in Open Food Facts, trying next API...")
    
    # Try UPCitemdb
    result = await fetch_from_upcitemdb(barcode)
    if result:
        result["source"] = "UPCitemdb"
        print(f"\n✓ SUCCESS: Product found in UPCitemdb")
        print(f"  Name: {result.get('name')}")
        print(f"  Brand: {result.get('brand')}")
        print(f"  Categories: {result.get('categories')}")
        return result
    _LOGGER.debug("✗ Not found in UPCitemdb, trying next API...")
    
    # Try OpenGTINDB
    result = await fetch_from_opengtindb(barcode)
    if result:
        result["source"] = "OpenGTINDB"
        print(f"\n✓ SUCCESS: Product found in OpenGTINDB")
        print(f"  Name: {result.get('name')}")
        print(f"  Brand: {result.get('brand')}")
        print(f"  Categories: {result.get('categories')}")
        return result
    _LOGGER.debug("✗ Not found in OpenGTINDB")
    
    _LOGGER.warning("[CASCADE SEARCH] ✗ Product not found in any of the 3 databases")
    print(f"\n✗ FAILURE: Product not found in any database")
    return None


async def main():
    """Test cascade search with multiple barcodes."""
    test_barcodes = [
        ("3017620422003", "Nutella (known product)"),
        ("3770022548008", "User test 1"),
        ("3411112161959", "User test 2"),
    ]
    
    if len(sys.argv) > 1:
        # Use command line argument
        test_barcodes = [(sys.argv[1], "Command line barcode")]
    
    for barcode, description in test_barcodes:
        print(f"\n{'=' * 80}")
        print(f"Testing: {description} - Barcode: {barcode}")
        print(f"{'=' * 80}")
        await cascade_search(barcode)
        await asyncio.sleep(1)  # Small delay between tests


if __name__ == "__main__":
    asyncio.run(main())
