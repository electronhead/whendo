from pydantic import BaseModel
from whendo.sdk.client import Client
    
class Workbench(BaseModel):
    clients:dict={}
    def add_client(self, name:str, client:Client):
        self.clients[name] = client
    def get_client(self, name:str):
        return self.clients.get(name, None)
    def get_clients(self):
        return list(self.clients.values())
    def count(self):
        return len(self.clients)