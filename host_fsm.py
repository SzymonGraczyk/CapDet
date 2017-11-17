from enum import Enum

from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class FSMEvents(Enum):
    AE_WAKE          = 0x00,
    AE_CLAIM         = 0x01,
    AE_RECLAIM       = 0x02,
    AE_SCHEDULE_TEST = 0x03,
    AE_START_TESTING = 0x04,
    AE_STOP_TESTING  = 0x05,
    AE_DEMISE        = 0xFF

class HostEvent(object):
    _type = None
    _data = None

    def __init__(self, event_type, data=None):
        assert type(event_type) is FSMEvents

        self._type = event_type
        self._data = data

    def type(self):
        return self._type

    def data(self):
        return self._data

class FSMStates(Enum):
    AF_UNKNOWN  = 0x00,
    AF_DOWN     = 0x01,
    AF_IDLE     = 0x02,
    AF_CLAIMED  = 0x03,
    AF_TESTING  = 0x04,

class HostFSM(object):
    _state                        = None
    _claim_id                     = None
    _schedule_test_callback       = None
    _has_scheduled_tests_callback = None
    _execute_test_callback        = None

    def __init__(self):
        super(HostFSM, self).__init__()

        self._state = FSMStates.AF_DOWN

        self._state_process_map = {
            FSMStates.AF_UNKNOWN: self._process_unknown_state,
            FSMStates.AF_DOWN:    self._process_down_state,
            FSMStates.AF_IDLE:    self._process_idle_state,
            FSMStates.AF_CLAIMED: self._process_claimed_state,
            FSMStates.AF_TESTING: self._process_testing_state
        }

    def set_schedule_test_callback(self, callback):
        self._schedule_test_callback = callback

    def set_has_scheduled_tests_callback(self, callback):
        self._has_scheduled_tests_callback = callback

    def set_execute_test_callback(self, callback):
        self._execute_test_callback = callback

    def get_state(self):
        return self._state

    def get_claim_id(self):
        return self._claim_id

    def _schedule_test(self, test_script):
        self._schedule_test_callback(test_script)

    def execute(self, ev):
        assert type(ev) is HostEvent

        event  = ev.type()
        data   = ev.data()

        return self._process_event(event, data)

    def _process_event(self, event, data):
        accept = False

        try:
            return self._state_process_map[self._state](event, data)
        except:
            raise HostFSMError('Invalid state: %s' % self._state.name)

    def _process_unknown_state(self, event, data):
        return False

    def _process_down_state(self, event, data):
        accept = False

        if event == FSMEvents.AE_WAKE:
            log.msg('Host has awaken')
            self._state = FSMStates.AF_IDLE
            accept = True
        elif event == FSMEvents.AE_CLAIM:
            self._state = FSMStates.AF_DOWN
            accept = False
        elif event == FSMEvents.AE_RECLAIM:
            self._state = FSMStates.AF_DOWN
            accept = False
        elif event == FSMEvents.AE_SCHEDULE_TEST:
            self._schedule_test(data)
            accept = True
        elif event == FSMEvents.AE_START_TESTING:
            self._state = FSMStates.AF_DOWN
            accept = False
        elif event == FSMEvents.AE_STOP_TESTING:
            self._state = FSMStates.AF_DOWN
            accept = False
        elif event == FSMEvents.AE_DEMISE:
            self._state = FSMStates.AF_DOWN
            accept = False
        else:
            raise HostFSMError('Invalid event: %s' % event.name)

        return accept

    def _process_idle_state(self, event, data):
        accept = False

        if event == FSMEvents.AE_WAKE:
            self._state = FSMStates.AF_IDLE
            accept = False
        elif event == FSMEvents.AE_CLAIM:
            assert not data is None

            if self._claim_id:
                raise HostFSMError("Claim ID is set in idle state (%s)" % self._claim_id)

            self._claim_id = data
            self._state = FSMStates.AF_CLAIMED
            accept = True
        elif event == FSMEvents.AE_RECLAIM:
            self._state = FSMStates.AF_IDLE
            log.warning('Reclaiming host in idle state')
            accept = False
        elif event == FSMEvents.AE_SCHEDULE_TEST:
            self._state = FSMStates.AF_IDLE
            self._schedule_test(data)
            accept = True
        elif event == FSMEvents.AE_START_TESTING:
            self._state = FSMStates.AF_IDLE
            log.warning('Cannot start testing in idle state')
            accept = False
        elif event == FSMEvents.AE_STOP_TESTING:
            self._state = FSMStates.AF_IDLE
            log.warning('Cannot stop testing in idle state')
            accept = False
        elif event == FSMEvents.AE_DEMISE:
            self._state = FSMStates.AF_DOWN
            accept = True
        else:
            raise HostFSMError('Invalid event: %s' % event.name)

        return accept

    def _process_claimed_state(self, event, data):
        accept = False

        if event == FSMEvents.AE_WAKE:
            self._state = FSMStates.AF_CLAIMED
            accept = False
        elif event == FSMEvents.AE_CLAIM:
            log.warning('Cannot claim host in claimed state')
            self._state = FSMStates.AF_CLAIMED
            accept = False
        elif event == FSMEvents.AE_RECLAIM:
            assert not data is None

            if self._claim_id != data:
                self._state = FSMStates.AF_CLAIMED
                log.msg("Claim id's does not match. Cannot reclaim.")
                accept = False
            else:
                self._claim_id = None
                self._state = FSMStates.AF_IDLE
                accept = True
        elif event == FSMEvents.AE_SCHEDULE_TEST:
            self._schedule_test(data)
            accept = True
        elif event == FSMEvents.AE_START_TESTING:
            assert not data is None

            if self._claim_id != data:
                self._state = FSMStates.AF_CLAIMED
                log.msg("Claim id's does not match. Cannot start testing.")
                accept = False
            else:
                res = self._has_scheduled_tests_callback()
                if not res:
                    self._state = FSMStates.AF_CLAIMED
                    log.msg("No tests to execute")
                    accept = False
                else:
                    self._state = FSMStates.AF_TESTING
                    log.msg("Started testing")
                    self._execute_test_callback()
                    accept = True
        elif event == FSMEvents.AE_STOP_TESTING:
            self._state = FSMStates.AF_CLAIMED
            log.warning('Cannot stop testing in claimed state')
            accept = False
        elif event == FSMEvents.AE_DEMISE:
            self._state = FSMStates.AF_DOWN
            accept = True
        else:
            raise HostFSMError('Invalid event: %s' % event.name)

        return accept

    def _process_testing_state(self, event, data):
        if event == FSMEvents.AE_WAKE:
            self._state = FSMStates.AF_TESTING
            accept = False
        elif event == FSMEvents.AE_CLAIM:
            self._state = FSMStates.AF_TESTING
            accept = False
        elif event == FSMEvents.AE_RECLAIM:
            self._state = FSMStates.AF_TESTING
            accept = False
        elif event == FSMEvents.AE_SCHEDULE_TEST:
            self._schedule_test(data)
            accept = True
        elif event == FSMEvents.AE_START_TESTING:
            self._state = FSMStates.AF_TESTING
            log.warning('Cannot start testing in testing state')
            accept = False
        elif event == FSMEvents.AE_STOP_TESTING:
#            assert not data is None

#            if self._claim_id != data:
#                self._state = FSMStates.AF_TESTING
#                log.msg("Claim id's does not match. Cannot stop testing.")
#                accept = False
#            else:
#                self._state = FSMStates.AF_CLAIMED
#                accept = True

            res = self._has_scheduled_tests_callback()
            if not res:
                self._state = FSMStates.AF_CLAIMED
                log.msg("No tests to execute")
                accept = True
            else:
                self._state = FSMStates.AF_TESTING
                log.msg("Started testing")
                self._execute_test_callback()
                accept = True
        elif event == FSMEvents.AE_DEMISE:
            log.error("Host demised duriung testing state")
            self._state = FSMStates.AF_DOWN
            accept = True
        else:
            raise HostFSMError('Invalid event: %s' % event.name)

        return accept

class HostFSMError(Exception):
    pass
