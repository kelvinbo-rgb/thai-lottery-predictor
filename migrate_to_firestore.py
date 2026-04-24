import csv
import json
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import ast
import os

# --- Configuration ---
DATA_FILE = "historical_data.csv"
COLLECTION_NAME = "lottery_history"

def parse_date_to_iso(date_str):
    """Convert M/D/YYYY to YYYY-MM-DD"""
    try:
        dt = datetime.datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
            dt = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except:
            return None

def safe_parse_list(s):
    """Safely parse string representation of list"""
    try:
        if not s or s == "[]":
            return []
        return ast.literal_eval(s)
    except:
        return []

def migrate():
    # Initialize Firestore (Uses Application Default Credentials)
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    
    db = firestore.client()
    batch = db.batch()
    count = 0
    
    print(f"🚀 Starting migration from {DATA_FILE} to Firestore...")

    with open(DATA_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = parse_date_to_iso(row['date'])
            if not doc_id:
                continue
            
            # Prepare Data
            data = {
                "date": doc_id,
                "prize_1st": row['prize_1st'],
                "prize_pre_3digit": safe_parse_list(row['prize_pre_3digit']),
                "prize_sub_3digits": safe_parse_list(row['prize_sub_3digits']),
                "prize_2digits": row['prize_2digits'],
                "nearby_1st": safe_parse_list(row.get('nearby_1st', '[]')),
                "prize_2nd": safe_parse_list(row.get('prize_2nd', '[]')),
                "prize_3rd": safe_parse_list(row.get('prize_3rd', '[]')),
                "prize_4th": safe_parse_list(row.get('prize_4th', '[]')),
                "prize_5th": safe_parse_list(row.get('prize_5th', '[]')),
                "updated_at": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
            batch.set(doc_ref, data)
            count += 1
            
            # Firestore batch limit is 500
            if count % 400 == 0:
                batch.commit()
                batch = db.batch()
                print(f"📦 Committed {count} records...")

    batch.commit()
    print(f"✅ Migration complete! Total records: {count}")

if __name__ == "__main__":
    migrate()
