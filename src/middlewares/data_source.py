from collections import deque

class DataSource:
    _data_queue = deque()

    def generate_data(self):
        # 1. Run this in a thread
        # 2. Randomly generate data in intervals.
        # 3. Push to the queue.
        pass

    def fetch_data(self):

        data = list(self._data_queue)
        self._data_queue.clear()

        # return data

        # For test purposes.
        return [
            {
                "id": "1234",
                "value": "CPU:89;RAM:37;NET:18"
            }
        ]