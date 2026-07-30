import os
import json

def load_identity():
    # identity_loader.py is in client/src/utils/
    # We need to go UP TWO LEVELS to reach client/
    client_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    identity_path = os.path.join(client_root, "identity.json")
    with open(identity_path, "r") as file:
        return json.load(file)
