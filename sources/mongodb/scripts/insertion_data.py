import json
import pymongo
from pymongo.errors import BulkWriteError

def bulk_insert_jsonl():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["edusmart_logs"]
    collection = db["events"]
    
    file_path = "edusmart_mobile_events.jsonl"
    batch_size = 5000
    buffer = []
    total_inserted = 0
    total_duplicates = 0
    
    print(f"Début de l'importation du fichier {file_path} dans MongoDB...")
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                buffer.append(json.loads(line.strip()))
                
            if len(buffer) >= batch_size:
                try:
                    res = collection.insert_many(buffer, ordered=False)
                    total_inserted += len(res.inserted_ids)
                except BulkWriteError as bwe:
                    # On comptabilise ce qui a quand même pu être inséré dans le lot
                    total_inserted += bwe.details['nInserted']
                    total_duplicates += len(bwe.details['writeErrors'])
                
                print(f"-> Environ {total_inserted} documents traités...")
                buffer = []
                
        # Insérer le reste du buffer s'il en reste
        if buffer:
            try:
                res = collection.insert_many(buffer, ordered=False)
                total_inserted += len(res.inserted_ids)
            except BulkWriteError as bwe:
                total_inserted += bwe.details['nInserted']
                total_duplicates += len(bwe.details['writeErrors'])
            
    print(f"\n=== Analyse du chargement ===")
    print(f" Documents insérés en base : {total_inserted}")
    print(f" Doublons bruts ignorés (Anomalie attendue) : {total_duplicates}")

if __name__ == "__main__":
    bulk_insert_jsonl()