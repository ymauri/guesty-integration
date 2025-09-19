#!/usr/bin/env python3
"""
Simple production migration script that creates listing to price list mappings.
This script works without the full application dependencies and can be run in production.
"""
import sqlite3
import os
import sys

def run_simple_migration():
    """
    Run a simple migration to create the listing_price_list_mapping table and populate it.
    """
    print("🔄 Starting simple database migration...")
    
    # Database path - use environment variable or default
    db_path = os.getenv("SQLITE_DB_PATH", "/data/database.db")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the listing_price_list_mapping table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS listing_price_list_mapping (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          guesty_listing_id TEXT NOT NULL UNIQUE,
          booking_experts_price_list_id TEXT NOT NULL,
          is_active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
        
        cursor.execute(create_table_sql)
        print("✅ Created listing_price_list_mapping table")
        
        # Create indexes
        index_sqls = [
            "CREATE INDEX IF NOT EXISTS idx_lplm_listing ON listing_price_list_mapping(guesty_listing_id);",
            "CREATE INDEX IF NOT EXISTS idx_lplm_active ON listing_price_list_mapping(is_active);"
        ]
        
        for index_sql in index_sqls:
            cursor.execute(index_sql)
        
        print("✅ Created indexes")
        
        # Get the default price list ID from environment
        default_price_list_id = os.getenv("DEFAULT_PRICE_LIST_ID", "22671")
        print(f"📋 Using default price list ID: {default_price_list_id}")
        
        # Get existing listings from the data file
        existing_listings = [
            "6687e17c9d796c00126e6dda",
            "668ba438f3d3dc0017059185",
            "668bb2df8e4411005a83f526",
            "668bb65bf3d3dc00170601f2",
            "668bb786e75f650011473a9d",
            "668bb883d64f540013b2fbac"
        ]
        
        print(f"📋 Found {len(existing_listings)} existing listings")
        
        # Check if mappings already exist
        cursor.execute("SELECT COUNT(*) FROM listing_price_list_mapping WHERE is_active = 1")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"✅ Found {existing_count} existing mappings - migration already completed")
            conn.close()
            return True
        
        # Create mappings for all existing listings
        insert_sql = """
        INSERT OR REPLACE INTO listing_price_list_mapping 
        (guesty_listing_id, booking_experts_price_list_id, is_active)
        VALUES (?, ?, 1)
        """
        
        for listing_id in existing_listings:
            cursor.execute(insert_sql, [listing_id, default_price_list_id])
        
        # Commit changes
        conn.commit()
        print(f"✅ Created {len(existing_listings)} listing to price list mappings")
        
        # Verify mappings
        cursor.execute("SELECT * FROM listing_price_list_mapping WHERE is_active = 1")
        all_mappings = cursor.fetchall()
        print(f"📊 Total active mappings: {len(all_mappings)}")
        
        print("\n📋 Created mappings:")
        for mapping in all_mappings:
            print(f"   - {mapping[1]} -> {mapping[2]}")
        
        conn.close()
        print("\n🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_simple_migration()
    sys.exit(0 if success else 1)
