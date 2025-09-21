#!/usr/bin/env python3
import json
import os
from datetime import datetime
from tinydb import TinyDB, Query

def store_trade_data():
    # Read the JSON trade data
    json_file_path = './data/trade_data_FAB_26933659_20240915_104500.json'
    
    try:
        with open(json_file_path, 'r') as f:
            trade_data = json.load(f)
        
        # Extract Trade_ID from trade_identification.trade_reference
        trade_id = trade_data.get('trade_identification', {}).get('trade_reference', '')
        
        if not trade_id:
            print("Error: Trade_ID not found in data")
            return
        
        # Determine data source - this is bank trade data from FAB
        # Based on source_file "FAB_26933659.pdf" and party_a being the bank
        db_path = './storage/bank_trade_data.db'
        
        # Ensure storage directory exists
        os.makedirs('./storage', exist_ok=True)
        
        # Initialize TinyDB
        db = TinyDB(db_path)
        
        # Add Trade_ID as primary key to the data
        trade_data['Trade_ID'] = trade_id
        
        # Check if record exists
        Trade = Query()
        existing_record = db.search(Trade.Trade_ID == trade_id)
        
        # Log timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing_record:
            # Update existing record
            db.update(trade_data, Trade.Trade_ID == trade_id)
            action = 'updated'
            print(f"[{timestamp}] Updated trade {trade_id} in bank_trade_data.db")
        else:
            # Insert new record
            db.insert(trade_data)
            action = 'inserted'
            print(f"[{timestamp}] Inserted trade {trade_id} in bank_trade_data.db")
        
        # Get total record count
        record_count = len(db.all())
        
        # Print confirmation message in required format
        print(f"Stored trade {trade_id} in bank_trade_data.db")
        print(f"Action: {action}")
        print(f"Database record count: {record_count}")
        
        db.close()
        
    except Exception as e:
        print(f"Error processing trade data: {str(e)}")
        return

if __name__ == '__main__':
    store_trade_data()
