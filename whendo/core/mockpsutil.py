"""
This file contains the psutil functions necessary for the absence of
psutil in a whendo environment.

Not having psutil in the build spec might enable

    >> python -m build

to work. The build failed from the presence of psutil as a required
library.
"""

from socket import AddressFamily
from collections import namedtuple
import logging


logger = logging.getLogger(__name__)


def net_if_addrs():
    named_tuple = namedtuple(
        "snicaddr", ["family", "address", "netmask", "broadcast", "ptp"]
    )
    snicaddr = named_tuple(
        AddressFamily.AF_INET, "0.0.0.0", "255.0.0.0", "127.0.0.1", None
    )
    return {"unknown": [snicaddr]}


def virtual_memory():
    svmem = namedtuple("svmem", ["unknown"])
    return svmem(0.0)


def getloadavg():
    return [0.0, 0.0, 0.0]


def cpu_percent():
    return 0.0
