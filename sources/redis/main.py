# import time
# from generate_data import EduSmartSimulator
# import json

from insert_data import RedisInserter

from utils import getjson

def main():

    # simulator = EduSmartSimulator()
    # inserter = RedisInserter()


    # print("Simulation EduSmart démarrée... (Ctrl+C pour arrêter)")
    # data = []

    # try:
    #     while True:

    #         event = simulator.generate()

    #         if event:
    #             inserter.insert(event)
    #             data.append(event)
    #             print(event)
    #         # print(event)

    #         time.sleep(0.005)

    # except KeyboardInterrupt:
    #     with open("data.json", "w", encoding="utf-8") as f:
    #         json.dump(data, f, indent=4, ensure_ascii=False)
    #     print("\nSimulation arrêtée.")


    inserter = RedisInserter()

    events = getjson('data.json')

    for event in events:
        inserter.insert(event)


if __name__ == "__main__":
    main()