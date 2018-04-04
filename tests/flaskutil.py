from flask import Flask
from flask.json import JSONEncoder

from typedpy import Structure, deserialize_structure


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Structure):
            return deserialize_structure(obj)
        return JSONEncoder.default(self, obj)

# app = Flask(__name__)
# app.json_encoder = CustomJSONEncoder
