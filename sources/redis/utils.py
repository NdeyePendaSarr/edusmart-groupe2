import csv
import json

def getcsv(path, sep, columns):
    with open(path) as file:
        reader = csv.DictReader(file, delimiter = sep)

        return [
            {col:row[col] for col in columns}
            for row in reader
        ]
    
def getjson(path):
    with open(path) as file:
        return json.load(file)
