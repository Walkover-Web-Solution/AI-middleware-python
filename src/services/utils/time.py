    
import time

class Timer:
    def __init__(self):
        """Initialise a stack-based timer helper."""
        self.start_times = []

    def start(self):
        """Push the current time onto the stack."""
        self.start_times.append(time.time())

    def defaultStart(self, timeArray=None):
        """Seed the timer stack with precomputed timestamps."""
        if timeArray is None:
            timeArray = []
        self.start_times.extend(timeArray)
    
    def getTime(self):
        """Return the current list of tracked start times."""
        return self.start_times

    def stop(self, label=""):
        """Pop the most recent start time and return elapsed seconds."""
        if not self.start_times:
            raise Exception("Timer was not started")
        start_time = self.start_times.pop()
        elapsed_time = time.time() - start_time
        return elapsed_time 

timer_obj = Timer()
