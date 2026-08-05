import json
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from bson import ObjectId

fake = Faker(['fr_FR'])
Faker.seed(42)
random.seed(42)

# Configuration du volume (Réglé à 200 000 événements pour le minimum requis)
TOTAL_EVENTS = 200000
OUTPUT_FILE = "edusmart_mobile_events.jsonl"

EVENT_TYPES = [
    "LOGIN", "LOGOUT", "COURSE_OPENED", "COURSE_COMPLETED", 
    "VIDEO_STARTED", "VIDEO_FINISHED", "QUIZ_STARTED", 
    "QUIZ_SUBMITTED", "RESOURCE_DOWNLOADED", "SEARCH", 
    "PROFILE_UPDATED", "PAYMENT_STARTED", "PAYMENT_SUCCESS", "PAYMENT_FAILED"
]

def generate_logs():
    print(f"Début de la génération de {TOTAL_EVENTS} événements...")
    
    # Préparation d'un pool d'étudiants et de modules pour garder une cohérence interne
    student_codes = [f"LMS-{random.randint(100000, 999999)}" for _ in range(500)]
    modules = ["MOD-IA-01", "MOD-DEV-02", "MOD-WEB-03", "MOD-MKT-04"]
    
    # Dictionnaires pour simuler des anomalies spécifiques
    city_variants = ["Dakar", "DAKAR", "dakarr", "Thiès", "THIES", "St-Louis", "Saint-Louis"]
    os_variants = ["Android", "ANDROID", "android", "iOS", "ios", "IOS"]
    version_variants = ["2.4.1", "2.4", "2.4.0", "v2.4", "2.5.1-beta"]
    ip_variants = ["197.210.15.24", "196.201.34.85", "999.999.999.999", "abc.def.ghi.jkl", "10.0.0.1"]
    
    count = 0
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        while count < TOTAL_EVENTS:
            # Règle métier : On regroupe par session de quelques événements successifs
            session_id = str(uuid.uuid4())
            student_code = random.choice(student_codes)
            
            # Anomalie : Événement sans student code (3% de chances)
            if random.random() < 0.03:
                student_code = None
                
            session_start = fake.date_time_between(start_date="-30d", end_date="now")
            num_events_in_session = random.randint(3, 15)
            
            # Environnement technique stable pour la session
            device = random.choice(["Samsung Galaxy A54", "iPhone 14", "Xiaomi Redmi Note 12", "Huawei P30"])
            os_selected = random.choice(os_variants)
            app_ver = random.choice(version_variants)
            ip = random.choice(ip_variants) if random.random() < 0.05 else fake.ipv4()
            city = random.choice(city_variants)
            country = "Sénégal"
            
            for i in range(num_events_in_session):
                if count >= TOTAL_EVENTS:
                    break
                    
                event_type = random.choice(EVENT_TYPES)
                event_time = session_start + timedelta(minutes=i * random.randint(1, 10))
                
                # Création du document de base
                doc = {
                    "_id": str(ObjectId()),
                    "event_id": str(uuid.uuid4()),
                    "timestamp": event_time.isoformat(),
                    "event_type": event_type,
                    "device": device,
                    "operating_system": os_selected,
                    "app_version": app_ver,
                    "ip_address": ip,
                    "city": city,
                    "country": country,
                    "session_id": session_id,
                    "duration_seconds": random.randint(10, 1200),
                    "success": random.choice([True, True, True, False]) 
                }
                
                if student_code:
                    doc["student_code"] = student_code
                    
                if random.random() < 0.02:
                    doc["duration_seconds"] = random.randint(-500, -10)
                    
                if random.random() < 0.05:
                    if random.random() < 0.5:
                        doc["timestamp"] = str(int(event_time.timestamp()))
                    else:
                        doc["timestamp"] = event_time.strftime("%d/%m/%Y %H:%M:%S")

                # Schéma Flexible MongoDB : Champs contextuels selon l'événement
                if event_type in ["COURSE_OPENED", "COURSE_COMPLETED", "VIDEO_STARTED", "VIDEO_FINISHED"]:
                    doc["module_code"] = random.choice(modules)
                    doc["course_code"] = f"COURSE-{random.randint(1, 50)}"
                    
                if event_type in ["QUIZ_STARTED", "QUIZ_SUBMITTED"]:
                    doc["module_code"] = random.choice(modules)
                    doc["quiz_code"] = f"QUIZ-{random.randint(1, 10)}"

#injection metadonnees
                if event_type == "QUIZ_SUBMITTED":
                    doc["metadata"] = {
                        "score": random.randint(0, 20),
                        "attempt": random.randint(1, 3),
                        "network": random.choice(["4G", "5G", "Wi-Fi"])
                    }
                elif event_type == "VIDEO_STARTED":
                    doc["metadata"] = {
                        "video_quality": random.choice(["720p", "1080p", "4K"]),
                        "buffer_time": round(random.uniform(0.2, 5.5), 2)
                    }
                elif event_type == "VIDEO_FINISHED":
                    doc["metadata"] = {
                        "watch_time_seconds": random.randint(300, 3600),
                        "completed_percentage": round(random.uniform(80.0, 100.0), 1)
                    }
                elif event_type == "SEARCH":
                    doc["metadata"] = {
                        "search_query": random.choice(["python pandas", "mongodb indexing", "sql join", "data science"]),
                        "results_count": random.randint(0, 30)
                    }
                elif event_type == "RESOURCE_DOWNLOADED":
                    doc["metadata"] = {
                        "file_name": f"support_cours_{random.randint(100, 999)}.pdf",
                        "file_size_mb": round(random.uniform(0.5, 15.0), 2)
                    }
                elif event_type in ["PAYMENT_STARTED", "PAYMENT_SUCCESS", "PAYMENT_FAILED"]:
                    doc["metadata"] = {
                        "payment_provider": random.choice(["Wave", "Orange Money", "Free Money", "Carte Bancaire"]),
                        "amount_cfa": random.choice([25000, 50000, 150000])
                    }
                    if event_type == "PAYMENT_FAILED":
                        doc["metadata"]["error_code"] = random.choice(["INSUFFICIENT_FUNDS", "TIMEOUT", "CANCELLED"])
                else:
                    # Pour les événements simples (LOGIN, LOGOUT, etc.) : 50% avec métadonnées génériques, 50% sans
                    if random.random() < 0.5:
                        doc["metadata"] = {"network": random.choice(["4G", "3G", "Wi-Fi"])}

                # Anomalies structurelles NoSQL : Suppressions ou nullités (5% de chances)
                #if random.random() < 0.05:
                #    champs_a_retirer = random.choice([["city", "country"], ["device"], ["success"]])
                #    for c in champs_a_retirer:
                #        doc.pop(c, None)
                
                if random.random() < 0.05:
                    doc["app_version"] = None

                # Écriture dans le fichier JSONL
                f.write(json.dumps(doc) + "\n")
                count += 1
                
                # Anomalie : Cloner exactement le log (1% de chances)
                if random.random() < 0.01 and count < TOTAL_EVENTS:
                    f.write(json.dumps(doc) + "\n")
                    count += 1

                if count % 50000 == 0:
                    print(f"✓ {count} événements générés...")

    print(f"Génération terminée ! Fichier disponible : {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_logs()

    