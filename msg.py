import json

from test.test_script import TestScript
from dynamic_host import DynamicHost
from host import Host

class Msg(list):
    def __init__(self, msg_type):
        super(Msg, self).__init__()
        
        self.append(msg_type)

class MsgACK(Msg):
    def __init__(self, identity):
        super(MsgACK, self).__init__('MSG_ACK')

        self.set_data(identity)

class MsgHeartbeat(Msg):
    def __init__(self, msg_data={}):
        super(MsgHeartbeat, self).__init__('3')

        self.append(msg_data)

class MsgHostCapabilities(Msg):
    def __init__(self, msg_data):
        assert type(msg_data) is Host

        super(MsgHostCapabilities, self).__init__('4')
        
        msg_data = msg_data.to_json()
        self.append(json.dumps(msg_data))

class MsgGetHostList(Msg):
    def __init__(self):
        super(MsgGetHostList, self).__init__('5')

class MsgHostList(Msg):
    def __init__(self, data):
        super(MsgHostList, self).__init__('6')

        if not type(data) is json:
            data = json.dumps(data)

        self.append(data)

class MsgGetState(Msg):
    def __init__(self):
        super(MsgGetState, self).__init__('7')

class MsgGetStateReturn(Msg):
    def __init__(self, state):
        super(MsgGetStateReturn, self).__init__('8')

        self.append(state.name)

class MsgSetState(Msg):
    def __init__(self, state):
        super(MsgSetState, self).__init__('9')

        self.append(state.name)

class MsgClaimHost(Msg):
    def __init__(self, host_id, claim_id):
        assert type(host_id) is int
        assert type(claim_id) is str

        super(MsgClaimHost, self).__init__('10')

        self.append(str(host_id))
        self.append(claim_id)

class MsgReclaimHost(Msg):
    def __init__(self, host_id, claim_id):
        assert type(host_id) is int
        assert type(claim_id) is str

        super(MsgReclaimHost, self).__init__('11')

        self.append(str(host_id))
        self.append(claim_id)

class MsgScheduleTest(Msg):
    def __init__(self, host_id, claim_id, script):
        assert type(host_id) is int
        assert type(claim_id) is str
        assert type(script) is TestScript

        super(MsgScheduleTest, self).__init__('12')

        self.append(str(host_id))
        self.append(claim_id)
        self.append(script.to_json())

class MsgExecuteTest(Msg):
    def __init__(self, script):
        assert type(script) is str

        super(MsgExecuteTest, self).__init__('13')

        self.append(script)
    
