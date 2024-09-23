# import time

# class Timer:
#     def __init__(self):
#         self.start_time = None

#     def start(self):
#         self.start_time = time.time()

#     def stop(self, label=""):
#         if self.start_time is None:
#             raise Exception("Timer was not started")
#         elapsed_time = time.time() - self.start_time
#         print(f"{label} took {elapsed_time} seconds to execute")
#         self.start_time = None
#         return elapsed_time

import time

class Timer:
    def __init__(self):
        self.start_times = []

    def start(self):
        self.start_times.append(time.time())

    def stop(self, label=""):
        if not self.start_times:
            raise Exception("Timer was not started")
        start_time = self.start_times.pop()
        elapsed_time = time.time() - start_time
        print(f"{label} took {elapsed_time} seconds to execute")
        return elapsed_time 