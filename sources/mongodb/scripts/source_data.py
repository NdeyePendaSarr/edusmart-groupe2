import pymongo

def init_mongodb():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    
    # Création de la base de données
    db = client["edusmart_logs"]
    
    # Suppression de la collection si elle existe pour repartir à zéro
    if "events" in db.list_collection_names():
        db["events"].drop()
        print("Ancienne collection 'events' supprimée.")
        
    # Création de la collection avec schéma flexible
    collection = db["events"]
    
    # Création d'index pour optimiser les futures analyses décisionnelles (ETL)
    collection.create_index([("student_code", pymongo.ASCENDING)])
    collection.create_index([("event_type", pymongo.ASCENDING)])
    collection.create_index([("timestamp", pymongo.DESCENDING)])
    collection.create_index([("session_id", pymongo.ASCENDING)])
    
    print("Base de données 'edusmart_logs' et collection 'events' initialisées avec succès !")
    print("Index créés sur student_code, event_type, timestamp et session_id.")

if __name__ == "__main__":
    init_mongodb()