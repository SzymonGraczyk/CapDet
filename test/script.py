from test_interface import TestInterface

class Script(TestInterface):
    _script = None

    def __init__(self, id, script):
        super(Script, self).__init__(id)

        self._script = script
