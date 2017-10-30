from enum import Enum

class HostState(Enum):
    HS_UNKNOWN = 0,
    HS_IDLE    = 1,
    HS_CLAIMED = 2,
    HS_TESTING = 3

class HostAlive(Enum):
    HA_UNKNOWN = 0,
    HA_ALIVE   = 1,
    HA_DOWN    = 2
