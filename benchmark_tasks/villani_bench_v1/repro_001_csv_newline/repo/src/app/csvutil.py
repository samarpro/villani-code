import csv
from io import StringIO

def parse_row(text: str):
    return next(csv.reader(StringIO(text), escapechar='\\'))
