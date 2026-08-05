from datetime import datetime
from faker import Faker
import pandas as pd
import random
import secrets

fake = Faker(locale='fr_FR')
data = pd.read_csv('enseignants.csv', sep=';')
enseignants = data['teacher_code'].tolist()
justification = ['Oui', 'Non', 'OUI', 'NON', 'YES', 'No', '0', '1']


def generer_fake_absences():
    teacher_code = random.choice(enseignants)
    teacher_row = data[data['teacher_code'] == teacher_code]

    if teacher_row.empty:
        return []

    annee_min = pd.to_datetime(teacher_row['date_embauche'].iloc[0], format='%Y-%m-%d').year
    annee_max = 2026

    nb_annees = random.randint(1, min(5, annee_max - annee_min + 1))
    annees = random.sample(range(annee_min, annee_max + 1), nb_annees)

    absences = []
    for annee in annees:
        nb_absences = random.randint(1, 5)
        for _ in range(nb_absences):
            date_absence = fake.date_between(
                start_date=datetime(annee, 1, 1),
                end_date=datetime(annee, 12, 31)
            )
            absences.append({
                'id_absence': secrets.randbelow(90000) + 100000,
                'teacher_code': teacher_code,
                'annee': date_absence.strftime('%d-%m-%Y'),
                'motif': fake.sentence(nb_words=6),
                'justifiee': random.choice(justification),
                'duree_heures': random.randint(1, 8),
                'remplace': random.choice(justification)
            })
    return absences


abse = []
for _ in range(3000):
    abse.extend(generer_fake_absences())

absences_df = pd.DataFrame(abse)
absences_df.to_csv('absences.csv', sep=':', encoding='UTF-8', index=False)
print(f"{len(absences_df)} absences générées")
