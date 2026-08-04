import random
from events import NormalEventGenerator
from anomalies import AnomalyGenerator

random.seed(42)

class EduSmartSimulator:

    def __init__(self):
        self.normal = NormalEventGenerator()
        self.anomaly = AnomalyGenerator(self.normal)

    def generate(self):

        if random.random() < 0.05:
            return self.anomaly.generate()

        return self.normal.generate()