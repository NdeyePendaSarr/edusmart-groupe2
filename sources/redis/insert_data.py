import redis

from config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB
)


class RedisInserter:

    def __init__(self):

        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

    def login(self, event):

        self.redis.hset(
            f"session:{event['session_id']}",
            mapping={
                "student_code": event["student_code"],
                "login_time": event["login_time"],
                "last_activity": event["last_activity"],
                "device": event["device"],
                "ip": event["ip"]
            }
        )

        self.redis.expire(
            f"session:{event['session_id']}",
            1800
        )

        self.redis.incr("online_users")

        self.increment_stats("total_connections")

    def logout(self, event):

        self.redis.delete(
            f"session:{event['session_id']}"
        )

        self.redis.decr("online_users")

    def course_open(self, event):

        self.redis.set(
            f"last_course:{event['student_code']}",
            event["course"]
        )

        self.increment_stats("total_opened_courses")

    def progress(self, event):

        self.redis.hset(
            f"progress:{event['student_code']}",
            mapping={
                "module": event["module"],
                "course": event["course"],
                "progress": event["progress"],
                "last_update": event["time"]
            }
        )

    def quiz(self, event):

        self.redis.zadd(
            f"leaderboard:{event['quiz']}",
            {
                event["student_code"]:
                event["score"]
            }
        )

        self.increment_stats("total_completed_quizzes")


    def notification(self, event):

        self.redis.lpush(
            f"notifications:{event['student_code']}",
            event["message"]
        )

    def expired_session(self, event):

        self.redis.hset(
            f"session:{event['session_id']}",
            mapping={
                "student_code": event["student_code"],
                "status": "ONLINE",
                "login_time": event["login_time"],
                "last_activity": event["last_activity"],
                "device": event["device"],
                "ip": event["ip"]
            }
        )

        self.redis.incr("online_users")

    def init_daily_stats(self):
        if self.redis.exists("statistics:today"):
            return

        self.redis.hset(
            "statistics:today",
            mapping={
                "total_connections": 0,
                "total_opened_courses": 0,
                "total_completed_quizzes": 0,
            },
        )
        self.redis.expire("statistics:today", 24 * 60 * 60)

    def increment_stats(self, field):
        self.init_daily_stats()
        self.redis.hincrby("statistics:today", field, 1)



    def insert(self, event):


        if event is None:
            return

        handlers = {
            "LOGIN": self.login,
            "UNKNOWN_STUDENT": self.login,
            "EXPIRED_SESSION": self.expired_session,
            "NOTIFICATION": self.notification,
            "PROGRESS_UPDATE": self.progress,
            "INVALID_PROGRESS": self.progress,
            "QUIZ_COMPLETED": self.quiz,
            "COURSE_OPEN": self.course_open,
            "LOGOUT": self.logout
        }

        event_type = event["type"]

        if event_type == "DUPLICATE NOTIFICATION":
            self.notification(event)
            self.notification(event)
        else:
            handlers[event["type"]](event)