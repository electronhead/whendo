"""
Instances of this class manage motherships in putative mothership-ready, network-visible hosts.

A host will at least have ip address and port as properties
"""
from pydantic import BaseModel
from typing import List

class Fleet(BaseModel):
    host:FleetHost
    fleet_hosts:List[FleetHost]=[]

    def collect_hosts():
    """
    populate hosts with locatable fleet hosts
    """
        pass

class FleetHost(BaseModel):
    name:str
    description:str
    ip_addr:str
    host_ports:List[HostPort]=[]

class HostPort(BaseModel):
    name:str
    port:int