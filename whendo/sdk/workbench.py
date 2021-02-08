from pydantic import BaseModel
from sdk.mothership_client import MothershipClient
    
class Workbench(BaseModel):
    clients:dict={}
    def add_client(self, name:str, client:MothershipClient):
        self.clients[name] = client
    def get_client(self, name:str):
        return self.clients.get(name, None)
    def get_clients(self):
        return list(self.clients.values())
    def count(self):
        return len(self.clients)