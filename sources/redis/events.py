import random
import uuid
from datetime import datetime
from faker import Faker
from utils import getcsv


random.seed(42)

fake = Faker()
Faker.seed(42)

NUMBER = 50000 

class NormalEventGenerator:

    def __init__(self):

        self.STUDENTS = [ f"LMS-{i:06d}"
                    for i in range(1, NUMBER)]

        self.DEVICES = [
            "Android",
            "iPhone",
            "Desktop"
        ]

        self.COURSES = getcsv("./file/cours.csv", ";",  ["id_module", "id_cours"])
        self.QUIZ = getcsv("./file/quiz.csv", ";",  ["id_cours", "id_quiz"])



        self.NOTIFICATIONS = [
            "Quiz disponible",
            "Nouveau cours publié",
            "Paiement validé",
            "Votre certificat est disponible"
            ]
        


        # état interne du simulateur
        # étudiant connecté -> informations session
        self.connected_students = {}




    def login(self):

        # choisir un étudiant non connecté
        available_students = [
            s for s in self.STUDENTS
            if s not in self.connected_students
        ]

        if not available_students:
            return None

        student = random.choice(available_students)

        session_id = str(uuid.uuid4())


        self.connected_students[student] = {
            "session_id": session_id,
            "device": random.choice(self.DEVICES)
        }


        return {
            "type": "LOGIN",
            "session_id": session_id,
            "student_code": student,
            "device": self.connected_students[student]["device"],
            "login_time": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "ip": fake.ipv4()
        }


    def logout(self):

        if not self.connected_students:
            return None


        student = random.choice(
            list(self.connected_students.keys())
        )


        session_id = self.connected_students[student]["session_id"]


        del self.connected_students[student]


        return {
            "type": "LOGOUT",
            "session_id": session_id,
            "student_code": student,
            "time": datetime.now().isoformat()
        }


    def course_open(self):

        if not self.connected_students:
            return None


        student = random.choice(
            list(self.connected_students.keys())
        )

        course = random.choice(self.COURSES)


        return {
            "type": "COURSE_OPEN",
            "student_code": student,
            "course": course["id_cours"],
        }


    def notification(self):

        if not self.connected_students:
            return None

        student = random.choice(
            list(self.connected_students.keys())
        )

        message = random.choice(self.NOTIFICATIONS)

        return {
            "type": "NOTIFICATION",
            "student_code": student,
            "message": message,
            "time": datetime.now().isoformat()
        }

    def progress_update(self):

        if not self.connected_students:
            return None


        student = random.choice(
            list(self.connected_students.keys())
        )

        course = random.choice(self.COURSES)


        return {
            "type": "PROGRESS_UPDATE",
            "student_code": student,
            "module": course["id_module"],
            "course": course["id_cours"],
            "progress": random.randint(0,100),
            "time": datetime.now().isoformat()
        }

    def quiz_completed(self):

        if not self.connected_students:
            return None


        student = random.choice(
            list(self.connected_students.keys())
        )

        course = random.choice(self.QUIZ)



        return {
            "type":"QUIZ_COMPLETED",
            "student_code":student,
            "quiz":course["id_quiz"],
            "score":random.randint(0,100),
            "time":datetime.now().isoformat()
        }

    def generate(self):

        normal = random.choices([self.login, self.logout, self.course_open, self.notification, self.progress_update, self.quiz_completed], [30,10, 25, 5, 15, 15], k=1)[0]

        return normal()

       