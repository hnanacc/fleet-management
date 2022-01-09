import sys
import random

class FaultStrategies:

    def __init__(self):
        self._options = [fn for fn in self.__dir__() if fn.startswith('_fail')]
        print(self._options)

    def execute_random_fault(self):
        choice = random.choice(self._options)
        getattr(self, choice)()

    def _fail_stop(self):
        print('Executed fail stop!')

    def _fail_crash(self):
        print('Executed fail_crash!')

    def _fail_byzantine(self):
        # Randomly corrupt some data.
        print('Executed byzantine!')