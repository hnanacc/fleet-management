from collections import deque
import random

class DataSource:
    _data_queue = deque()
    data_id = 0

    def generate_data(self):
        # 1. Run this in a thread
        # 2. Randomly generate data in intervals.
        # 3. Push to the queue.
        pass

    def fetch_data(self):
        # Supposed to get the data from data_queue.
        self.data_id += 1
        return { 'id': self.data_id, 'sensor': random.randint(100, 1000) }