import os
import json

class DirectoryLoader:
    def __init__(self, client_root):
        self.path = os.path.join(client_root, "directory.json")

    def load(self):
        with open(self.path, "r") as file:
            return json.load(file)

    def resolve(self, handle):
        data = self.load()
        if handle not in data:
            raise ValueError(f"Handle '{handle}' not found in directory.")
        return data[handle]
        