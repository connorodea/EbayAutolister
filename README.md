# eBay Autolister

🚀 **Advanced eBay Inventory Management & Listing Automation**

Automate your eBay selling process with bulk inventory creation, listing management, and seamless integration with eBay's Inventory API.

## ✨ Features

- **Bulk Inventory Management**: Create up to 25 inventory items per API call
- **CSV Processing**: Import products from CSV files with validation
- **OAuth Authentication**: Secure eBay API integration
- **Rate Limiting**: Built-in API rate limiting to prevent throttling  
- **Error Handling**: Comprehensive error tracking and retry logic
- **CLI Interface**: User-friendly command-line interface
- **Sandbox Support**: Test in eBay's sandbox environment
- **Listing Automation**: Create offers and publish listings automatically

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/connorodea/EbayAutolister.git
   cd EbayAutolister
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup configuration**:
   ```bash
   python cli.py setup
   ```

4. **Configure your eBay API credentials** in `.env`:
   ```bash
   EBAY_CLIENT_ID=your_client_id_here
   EBAY_CLIENT_SECRET=your_client_secret_here
   EBAY_SANDBOX=true
   ```

## 🔑 eBay API Setup

1. **Get eBay Developer Account**:
   - Visit [eBay Developers](https://developer.ebay.com)
   - Create an account and application
   - Get your Client ID and Client Secret

2. **Required API Scopes**:
   - `https://api.ebay.com/oauth/api_scope/sell.inventory`

3. **Business Policies**:
   - Configure payment, fulfillment, and return policies in your eBay seller account
   - Update policy IDs in `.env` file

## 🚀 Quick Start

### 1. Test API Connection
```bash
python cli.py test-connection
```

### 2. Create Sample CSV
```bash
python cli.py create-sample sample_products.csv
```

### 3. Process Inventory (Dry Run)
```bash
python cli.py process sample_products.csv --dry-run
```

### 4. Create Inventory Items
```bash
python cli.py process sample_products.csv
```

### 5. Create Inventory + Listings
```bash
python cli.py process sample_products.csv --create-listings
```

## 📄 CSV Format

Required columns for your CSV file:

| Column | Required | Description |
|--------|----------|-------------|
| `sku` | ✅ | Unique product identifier |
| `title` | ✅ | Product title |
| `description` | ✅ | Product description |
| `category_id` | ✅ | eBay category ID |
| `price` | ✅ | Product price |
| `condition` | ✅ | NEW, USED_EXCELLENT, etc. |
| `quantity` | ❌ | Available quantity (default: 1) |
| `brand` | ❌ | Brand name |
| `mpn` | ❌ | Manufacturer part number |
| `weight` | ❌ | Weight in pounds (default: 1.0) |
| `dimensions` | ❌ | LxWxH in inches (e.g., "6x4x2") |
| `images` | ❌ | Comma-separated image URLs |

### Example CSV:
```csv
sku,title,description,condition,category_id,price,quantity,brand,weight,dimensions,images
TEST-001,Sample Product,Product description,NEW,58058,29.99,5,Generic,1.0,6x4x2,https://example.com/image1.jpg
```

## 🛠️ CLI Commands

### Setup
```bash
python cli.py setup                    # Initialize configuration
python cli.py config-info              # Show current configuration
```

### Processing
```bash
python cli.py process FILE.csv         # Create inventory items only
python cli.py process FILE.csv --create-listings  # Create inventory + listings
python cli.py process FILE.csv --dry-run          # Preview without API calls
```

### Management
```bash
python cli.py check SKU-123           # Check inventory item status
python cli.py test-connection         # Test API connectivity
python cli.py create-sample FILE.csv  # Create sample CSV
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# eBay API
EBAY_CLIENT_ID=your_client_id
EBAY_CLIENT_SECRET=your_client_secret
EBAY_SANDBOX=true

# API Settings
RATE_LIMIT_INTERVAL=0.1
BATCH_SIZE=25
MAX_RETRIES=3

# Business Policies
DEFAULT_FULFILLMENT_POLICY=your_policy_id
DEFAULT_PAYMENT_POLICY=your_policy_id
DEFAULT_RETURN_POLICY=your_policy_id

# Logging
LOG_LEVEL=INFO
LOG_FILE=ebay_autolister.log
```

### Common eBay Category IDs

| Category | ID |
|----------|----| 
| Electronics | 58058 |
| Clothing | 11450 |
| Home & Garden | 11700 |
| Automotive | 6000 |
| Collectibles | 1 |
| Books | 267 |
| Toys | 220 |

## 🐍 Python Usage

```python
from ebay_autolister import EbayAutolister

# Initialize
autolister = EbayAutolister(
    client_id="your_client_id",
    client_secret="your_client_secret",
    sandbox=True
)

# Process CSV file
results = autolister.process_csv_file(
    "products.csv", 
    create_listings=True
)

print(f"Created {results['inventory_created']} inventory items")
print(f"Created {results['listings_created']} listings")
```

## 📊 Monitoring & Logging

- **Log File**: `ebay_autolister.log`
- **Verbose Mode**: Use `-v` flag for detailed logging
- **Progress Tracking**: Built-in progress bars for bulk operations
- **Error Reporting**: Detailed error messages and failed item tracking

## 🔒 Security

- ✅ OAuth 2.0 authentication
- ✅ Environment variable configuration
- ✅ No hardcoded credentials
- ✅ Rate limiting protection
- ✅ Token refresh handling

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your Client ID and Client Secret
   - Ensure proper API scopes are configured
   - Verify sandbox/production environment setting

2. **Category ID Invalid**
   - Use eBay's [Category API](https://developer.ebay.com/api-docs/commerce/taxonomy/) to find valid IDs
   - Check category hierarchy requirements

3. **Business Policy Errors**
   - Configure payment, fulfillment, and return policies in eBay seller account
   - Update policy IDs in configuration

4. **Rate Limiting**
   - Increase `RATE_LIMIT_INTERVAL` in `.env`
   - Check eBay API usage limits

## 🔄 API Workflow

1. **Authenticate** → Get OAuth token
2. **Create Inventory** → Bulk create inventory items
3. **Create Offers** → Generate offers for inventory items
4. **Publish Listings** → Make offers live on eBay

## 📈 Performance

- **Bulk Processing**: Up to 25 items per API call
- **Rate Limiting**: Configurable delays between requests
- **Retry Logic**: Automatic retry on transient failures
- **Progress Tracking**: Real-time progress updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- 📧 Issues: [GitHub Issues](https://github.com/connorodea/EbayAutolister/issues)
- 📚 eBay API Docs: [developer.ebay.com](https://developer.ebay.com)
- 🔧 eBay Developer Support: [developer.ebay.com/support](https://developer.ebay.com/support)

---

**Made with ❤️ for eBay sellers who want to automate their listing process**