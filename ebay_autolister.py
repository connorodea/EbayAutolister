#!/usr/bin/env python3
"""
eBay Autolister - Advanced Inventory Management & Listing Automation
Integrates with eBay Inventory API for bulk listing creation and management
"""

import json
import csv
import requests
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import pandas as pd

@dataclass
class InventoryItem:
    sku: str
    title: str
    description: str
    condition: str
    category_id: str
    price: float
    quantity: int
    brand: str = ""
    mpn: str = ""
    weight: float = 1.0
    dimensions: Dict[str, float] = None
    images: List[str] = None
    
    def __post_init__(self):
        if self.dimensions is None:
            self.dimensions = {"length": 10.0, "width": 10.0, "height": 10.0}
        if self.images is None:
            self.images = []

class EbayAPI:
    """eBay API client with OAuth authentication and rate limiting"""
    
    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        self.access_token = None
        self.token_expires = 0
        
        # API endpoints
        base_url = "https://api.sandbox.ebay.com" if sandbox else "https://api.ebay.com"
        self.inventory_url = f"{base_url}/sell/inventory/v1"
        self.oauth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" if sandbox else "https://api.ebay.com/identity/v1/oauth2/token"
        
        # Rate limiting
        self.last_request = 0
        self.min_interval = 0.1  # 100ms between requests
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def authenticate(self) -> bool:
        """Get OAuth access token for API requests"""
        if self.access_token and time.time() < self.token_expires:
            return True
            
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {self._get_auth_header()}'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope/sell.inventory'
            }
            
            response = requests.post(self.oauth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires = time.time() + token_data['expires_in'] - 300  # 5min buffer
            
            self.logger.info("Successfully authenticated with eBay API")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def _get_auth_header(self) -> str:
        """Generate base64 encoded auth header"""
        import base64
        auth_string = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(auth_string.encode()).decode()
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated API request with rate limiting"""
        if not self.authenticate():
            raise Exception("Failed to authenticate")
        
        self._rate_limit()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        url = f"{self.inventory_url}/{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        try:
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"API request failed: {e}")
            self.logger.error(f"Response: {response.text}")
            raise

class InventoryManager:
    """Manages eBay inventory items and bulk operations"""
    
    def __init__(self, api: EbayAPI):
        self.api = api
        self.logger = logging.getLogger(__name__)
    
    def create_inventory_item(self, item: InventoryItem) -> bool:
        """Create a single inventory item"""
        try:
            inventory_data = {
                "availability": {
                    "shipToLocationAvailability": {
                        "quantity": item.quantity
                    }
                },
                "condition": item.condition,
                "product": {
                    "title": item.title,
                    "description": item.description,
                    "aspects": {},
                    "brand": item.brand,
                    "mpn": item.mpn if item.mpn else item.sku,
                    "imageUrls": item.images[:12]  # Max 12 images
                },
                "packageWeightAndSize": {
                    "dimensions": {
                        "height": item.dimensions["height"],
                        "length": item.dimensions["length"],
                        "width": item.dimensions["width"],
                        "unit": "INCH"
                    },
                    "weight": {
                        "value": item.weight,
                        "unit": "POUND"
                    }
                }
            }
            
            # Add brand to aspects if provided
            if item.brand:
                inventory_data["product"]["aspects"]["Brand"] = [item.brand]
            
            response = self.api._make_request('PUT', f"inventory_item/{item.sku}", inventory_data)
            self.logger.info(f"Created inventory item: {item.sku}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create inventory item {item.sku}: {e}")
            return False
    
    def bulk_create_inventory_items(self, items: List[InventoryItem], batch_size: int = 25) -> Dict:
        """Create multiple inventory items in batches"""
        results = {"successful": [], "failed": []}
        
        # Process in batches of 25 (API limit)
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_data = {"requests": []}
            
            for item in batch:
                inventory_data = {
                    "sku": item.sku,
                    "product": {
                        "title": item.title,
                        "description": item.description,
                        "brand": item.brand,
                        "mpn": item.mpn if item.mpn else item.sku,
                        "imageUrls": item.images[:12]
                    },
                    "condition": item.condition,
                    "availability": {
                        "shipToLocationAvailability": {
                            "quantity": item.quantity
                        }
                    },
                    "packageWeightAndSize": {
                        "dimensions": {
                            "height": item.dimensions["height"],
                            "length": item.dimensions["length"],
                            "width": item.dimensions["width"],
                            "unit": "INCH"
                        },
                        "weight": {
                            "value": item.weight,
                            "unit": "POUND"
                        }
                    }
                }
                
                if item.brand:
                    inventory_data["product"]["aspects"] = {"Brand": [item.brand]}
                
                batch_data["requests"].append(inventory_data)
            
            try:
                response = self.api._make_request('POST', 'bulk_create_or_replace_inventory_item', batch_data)
                
                # Process response
                for idx, resp in enumerate(response.get('responses', [])):
                    item_sku = batch[idx].sku
                    if resp.get('statusCode') == 200:
                        results["successful"].append(item_sku)
                    else:
                        results["failed"].append({
                            "sku": item_sku,
                            "error": resp.get('errors', ['Unknown error'])
                        })
                
                self.logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} items")
                
            except Exception as e:
                self.logger.error(f"Batch creation failed: {e}")
                for item in batch:
                    results["failed"].append({"sku": item.sku, "error": str(e)})
        
        return results
    
    def get_inventory_item(self, sku: str) -> Dict:
        """Retrieve inventory item by SKU"""
        try:
            return self.api._make_request('GET', f'inventory_item/{sku}')
        except Exception as e:
            self.logger.error(f"Failed to retrieve inventory item {sku}: {e}")
            return {}

class ListingManager:
    """Manages eBay listing offers and publication"""
    
    def __init__(self, api: EbayAPI):
        self.api = api
        self.logger = logging.getLogger(__name__)
    
    def create_offer(self, sku: str, category_id: str, price: float, 
                    marketplace_id: str = "EBAY_US") -> str:
        """Create an offer for an inventory item"""
        try:
            offer_data = {
                "sku": sku,
                "marketplaceId": marketplace_id,
                "format": "FIXED_PRICE",
                "availableQuantity": 1,  # Will be pulled from inventory
                "categoryId": category_id,
                "pricingSummary": {
                    "price": {
                        "value": str(price),
                        "currency": "USD"
                    }
                },
                "listingPolicies": {
                    "fulfillmentPolicyId": "DEFAULT",  # Replace with actual policy
                    "paymentPolicyId": "DEFAULT",      # Replace with actual policy
                    "returnPolicyId": "DEFAULT"        # Replace with actual policy
                }
            }
            
            response = self.api._make_request('POST', 'offer', offer_data)
            offer_id = response.get('offerId')
            self.logger.info(f"Created offer {offer_id} for SKU {sku}")
            return offer_id
            
        except Exception as e:
            self.logger.error(f"Failed to create offer for {sku}: {e}")
            return None
    
    def publish_offer(self, offer_id: str) -> bool:
        """Publish an offer to create active listing"""
        try:
            self.api._make_request('POST', f'offer/{offer_id}/publish')
            self.logger.info(f"Published offer {offer_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish offer {offer_id}: {e}")
            return False

class CSVProcessor:
    """Processes CSV files for bulk inventory management"""
    
    @staticmethod
    def load_items_from_csv(file_path: str) -> List[InventoryItem]:
        """Load inventory items from CSV file"""
        items = []
        
        try:
            df = pd.read_csv(file_path)
            
            for _, row in df.iterrows():
                # Parse dimensions if provided
                dimensions = {"length": 10.0, "width": 10.0, "height": 10.0}
                if 'dimensions' in row and pd.notna(row['dimensions']):
                    dim_parts = str(row['dimensions']).split('x')
                    if len(dim_parts) == 3:
                        dimensions = {
                            "length": float(dim_parts[0]),
                            "width": float(dim_parts[1]),
                            "height": float(dim_parts[2])
                        }
                
                # Parse image URLs
                images = []
                if 'images' in row and pd.notna(row['images']):
                    images = [url.strip() for url in str(row['images']).split(',')]
                
                item = InventoryItem(
                    sku=str(row['sku']),
                    title=str(row['title']),
                    description=str(row['description']),
                    condition=str(row.get('condition', 'NEW')),
                    category_id=str(row['category_id']),
                    price=float(row['price']),
                    quantity=int(row.get('quantity', 1)),
                    brand=str(row.get('brand', '')),
                    mpn=str(row.get('mpn', '')),
                    weight=float(row.get('weight', 1.0)),
                    dimensions=dimensions,
                    images=images
                )
                items.append(item)
                
        except Exception as e:
            logging.error(f"Error loading CSV file {file_path}: {e}")
            
        return items

class EbayAutolister:
    """Main application class for eBay automated listing"""
    
    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        self.api = EbayAPI(client_id, client_secret, sandbox)
        self.inventory = InventoryManager(self.api)
        self.listings = ListingManager(self.api)
        self.logger = logging.getLogger(__name__)
        
    def process_csv_file(self, csv_path: str, create_listings: bool = False) -> Dict:
        """Process CSV file and create inventory items and optionally listings"""
        items = CSVProcessor.load_items_from_csv(csv_path)
        
        if not items:
            self.logger.error("No items found in CSV file")
            return {"success": False, "message": "No items found"}
        
        # Create inventory items
        self.logger.info(f"Creating {len(items)} inventory items...")
        inventory_results = self.inventory.bulk_create_inventory_items(items)
        
        results = {
            "inventory_created": len(inventory_results["successful"]),
            "inventory_failed": len(inventory_results["failed"]),
            "failed_items": inventory_results["failed"]
        }
        
        if create_listings:
            # Create and publish listings for successful inventory items
            listings_created = 0
            listings_failed = 0
            
            for item in items:
                if item.sku in inventory_results["successful"]:
                    offer_id = self.listings.create_offer(
                        item.sku, item.category_id, item.price
                    )
                    
                    if offer_id:
                        if self.listings.publish_offer(offer_id):
                            listings_created += 1
                        else:
                            listings_failed += 1
                    else:
                        listings_failed += 1
            
            results.update({
                "listings_created": listings_created,
                "listings_failed": listings_failed
            })
        
        return results
    
    def create_sample_csv(self, file_path: str = "sample_products.csv"):
        """Create a sample CSV file for testing"""
        sample_data = [
            {
                "sku": "TEST-001",
                "title": "Sample Product - Test Listing",
                "description": "This is a test product for eBay API integration",
                "condition": "NEW",
                "category_id": "58058",  # Cell Phones & Accessories
                "price": 29.99,
                "quantity": 5,
                "brand": "Generic",
                "mpn": "TEST-001",
                "weight": 1.0,
                "dimensions": "6x4x2",
                "images": "https://example.com/image1.jpg,https://example.com/image2.jpg"
            },
            {
                "sku": "TEST-002",
                "title": "Another Test Product",
                "description": "Second test product for bulk operations",
                "condition": "NEW",
                "category_id": "58058",
                "price": 49.99,
                "quantity": 10,
                "brand": "TestBrand",
                "mpn": "TB-002",
                "weight": 2.0,
                "dimensions": "8x6x3",
                "images": "https://example.com/image3.jpg"
            }
        ]
        
        df = pd.DataFrame(sample_data)
        df.to_csv(file_path, index=False)
        self.logger.info(f"Sample CSV created: {file_path}")

def main():
    """Example usage"""
    # Initialize with your eBay API credentials
    client_id = os.getenv('EBAY_CLIENT_ID')
    client_secret = os.getenv('EBAY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Please set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET environment variables")
        return
    
    # Create autolister instance
    autolister = EbayAutolister(client_id, client_secret, sandbox=True)
    
    # Create sample CSV for testing
    autolister.create_sample_csv()
    
    # Process CSV file (inventory only, no listings)
    results = autolister.process_csv_file("sample_products.csv", create_listings=False)
    
    print("Processing Results:")
    print(f"Inventory items created: {results['inventory_created']}")
    print(f"Inventory items failed: {results['inventory_failed']}")
    
    if results['failed_items']:
        print("Failed items:")
        for failed in results['failed_items']:
            print(f"  SKU: {failed['sku']}, Error: {failed['error']}")

if __name__ == "__main__":
    main()