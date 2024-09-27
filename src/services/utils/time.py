    
import time

class Timer:
    start_times = []

    def start(self):
        Timer.start_times.append(time.time())

    def stop(self, label=""):
        if not Timer.start_times:
            raise Exception("Timer was not started")
        start_time = Timer.start_times.pop()
        elapsed_time = time.time() - start_time
        return elapsed_time 