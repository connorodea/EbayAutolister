#!/usr/bin/env python3
"""
Command Line Interface for eBay Autolister
"""

import click
import os
import json
import logging
from typing import Optional
from ebay_autolister import EbayAutolister, ConditionMapper
from config import Config, create_sample_env

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """eBay Autolister - Automated inventory management and listing creation"""
    ctx.ensure_object(dict)
    
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ebay_autolister.log')
        ]
    )
    
    # Load configuration
    config = Config()
    ctx.obj['config'] = config
    
    if not config.validate():
        click.echo("❌ Configuration validation failed. Please check your .env file.")
        ctx.exit(1)

@cli.command()
@click.pass_context
def setup(ctx):
    """Initialize eBay Autolister configuration"""
    click.echo("🚀 Setting up eBay Autolister...")
    
    # Create sample .env file
    create_sample_env()
    
    # Create sample CSV
    config = ctx.obj['config']
    autolister = EbayAutolister(
        config.ebay_client_id,
        config.ebay_client_secret,
        config.ebay_sandbox
    )
    
    autolister.create_sample_csv('sample_products.csv')
    
    click.echo("✅ Setup complete!")
    click.echo("📝 Please update .env file with your eBay API credentials")
    click.echo("📄 Sample CSV created: sample_products.csv")

@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--create-listings', is_flag=True, help='Create listings after inventory items')
@click.option('--dry-run', is_flag=True, help='Preview actions without making API calls')
@click.pass_context
def process(ctx, csv_file, create_listings, dry_run):
    """Process CSV file and create inventory items"""
    config = ctx.obj['config']
    
    if dry_run:
        click.echo(f"🔍 Dry run mode - would process: {csv_file}")
        # Load and validate CSV
        from ebay_autolister import CSVProcessor
        items = CSVProcessor.load_items_from_csv(csv_file)
        
        click.echo(f"📊 Found {len(items)} items to process:")
        for item in items[:5]:  # Show first 5
            click.echo(f"  • {item.sku}: {item.title} - ${item.price}")
        
        if len(items) > 5:
            click.echo(f"  ... and {len(items) - 5} more items")
        
        click.echo(f"🔄 Would create inventory items: {'Yes' if items else 'No'}")
        click.echo(f"📋 Would create listings: {'Yes' if create_listings else 'No'}")
        return
    
    click.echo(f"📂 Processing CSV file: {csv_file}")
    
    # Initialize autolister
    autolister = EbayAutolister(
        config.ebay_client_id,
        config.ebay_client_secret,
        config.ebay_sandbox
    )
    
    # Process the file
    with click.progressbar(length=100, label='Processing') as bar:
        results = autolister.process_csv_file(csv_file, create_listings)
        bar.update(100)
    
    # Display results
    click.echo("\n📈 Processing Results:")
    click.echo(f"✅ Inventory items created: {results.get('inventory_created', 0)}")
    click.echo(f"❌ Inventory items failed: {results.get('inventory_failed', 0)}")
    
    if create_listings:
        click.echo(f"📋 Listings created: {results.get('listings_created', 0)}")
        click.echo(f"❌ Listings failed: {results.get('listings_failed', 0)}")
    
    # Show failed items
    if results.get('failed_items'):
        click.echo("\n❌ Failed Items:")
        for failed in results['failed_items'][:5]:  # Show first 5 failures
            click.echo(f"  • {failed['sku']}: {failed['error']}")

@cli.command()
@click.argument('sku')
@click.pass_context
def check(ctx, sku):
    """Check status of inventory item by SKU"""
    config = ctx.obj['config']
    
    autolister = EbayAutolister(
        config.ebay_client_id,
        config.ebay_client_secret,
        config.ebay_sandbox
    )
    
    click.echo(f"🔍 Checking inventory item: {sku}")
    
    item_data = autolister.inventory.get_inventory_item(sku)
    
    if item_data:
        click.echo("✅ Item found:")
        click.echo(f"  Title: {item_data.get('product', {}).get('title', 'N/A')}")
        click.echo(f"  Condition: {item_data.get('condition', 'N/A')}")
        
        availability = item_data.get('availability', {}).get('shipToLocationAvailability', {})
        click.echo(f"  Quantity: {availability.get('quantity', 'N/A')}")
        
        if item_data.get('product', {}).get('imageUrls'):
            click.echo(f"  Images: {len(item_data['product']['imageUrls'])} attached")
    else:
        click.echo("❌ Item not found")

@cli.command()
@click.pass_context
def config_info(ctx):
    """Display current configuration"""
    config = ctx.obj['config']
    
    click.echo("⚙️  Current Configuration:")
    click.echo(f"  Sandbox Mode: {'Yes' if config.ebay_sandbox else 'No'}")
    click.echo(f"  API Base URL: {config.get_api_base_url()}")
    click.echo(f"  Rate Limit: {config.rate_limit_interval}s between requests")
    click.echo(f"  Batch Size: {config.batch_size} items per batch")
    click.echo(f"  Max Retries: {config.max_retries}")
    click.echo(f"  Default Marketplace: {config.default_marketplace}")
    click.echo(f"  Log Level: {config.log_level}")

@cli.command()
@click.argument('output_file', default='sample_products.csv')
@click.pass_context
def create_sample(ctx, output_file):
    """Create a sample CSV file with example products"""
    config = ctx.obj['config']
    
    autolister = EbayAutolister(
        config.ebay_client_id,
        config.ebay_client_secret,
        config.ebay_sandbox
    )
    
    autolister.create_sample_csv(output_file)
    click.echo(f"📄 Sample CSV created: {output_file}")

@cli.command()
@click.option('--marketplace', default='EBAY_US', help='Marketplace ID')
@click.pass_context
def test_connection(ctx, marketplace):
    """Test connection to eBay API"""
    config = ctx.obj['config']
    
    click.echo("🔗 Testing eBay API connection...")
    
    try:
        autolister = EbayAutolister(
            config.ebay_client_id,
            config.ebay_client_secret,
            config.ebay_sandbox
        )
        
        # Test authentication
        if autolister.api.authenticate():
            click.echo("✅ Authentication successful")
            click.echo(f"🌐 Connected to: {config.get_api_base_url()}")
            click.echo(f"📍 Marketplace: {marketplace}")
        else:
            click.echo("❌ Authentication failed")
            
    except Exception as e:
        click.echo(f"❌ Connection failed: {e}")

@cli.command()
@click.argument('condition')
@click.option('--grade', default='', help='Optional grade (PSA 1-10, A+/A/B/C, etc.)')
def map_condition(condition, grade):
    """Test condition mapping to eBay standards"""
    click.echo(f"🔍 Mapping condition: '{condition}' with grade: '{grade}'")
    
    ebay_condition = ConditionMapper.map_condition(condition, grade)
    description = ConditionMapper.get_condition_description(condition, grade)
    
    click.echo(f"✅ eBay Condition: {ebay_condition}")
    click.echo(f"📝 Description: {description}")
    
    # Show some examples
    click.echo("\n💡 Other condition examples:")
    examples = [
        ("new", ""),
        ("open box", ""),
        ("used excellent", "A"),
        ("graded", "9"),
        ("seller refurbished", "B+"),
        ("for parts", "")
    ]
    
    for cond, gr in examples:
        if cond != condition.lower():
            mapped = ConditionMapper.map_condition(cond, gr)
            grade_text = f" (Grade: {gr})" if gr else ""
            click.echo(f"  • '{cond}'{grade_text} → {mapped}")

if __name__ == '__main__':
    cli()