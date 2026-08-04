import random
from datetime import datetime, timedelta


random.seed(42)


class AnomalyGenerator:

    def __init__(self, normal_generator):
        self.normal = normal_generator
    
    
    
    def expired_session(self):
        event = self.normal.login()

        old_time = datetime.now() - timedelta(hours=8)

        event["type"] = "EXPIRED_SESSION"
        event["login_time"] = old_time.isoformat()
        event["last_activity"] = datetime.now().isoformat()

        return event


    def duplicate_notification(self):
        event = self.normal.notification()

        event["type"] = "DUPLICATE NOTIFICATION"

        return event

    def unknown_student(self):
        event = self.normal.login()

        event["type"] = "UNKNOWN_STUDENT"
        event["student_code"] = random.choice([
            f"LMS-{i:06d}"
            for i in range(50001, 50500)
        ])

        return event
    

    def invalid_progress(self):
        event = self.normal.progress_update()

        event["type"] = "INVALID_PROGRESS"
        event["progress"] = random.randint(101, 150)

        return event

    def generate(self):

        anomaly = random.choice(
            [
                self.invalid_progress,
                self.duplicate_notification,
                self.expired_session,
                self.unknown_student
            ]
        )

        return anomaly()




