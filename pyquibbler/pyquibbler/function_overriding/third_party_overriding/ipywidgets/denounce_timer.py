import threading


class DebounceTimer:
    def __init__(self, wait_time, callback):
        """
        Initializes the DebounceTimer.

        :param wait_time: Time in seconds to wait before triggering the callback.
            0 means the callback is called immediately.
            None means the callback is not called. instead, it can be called manually using the call_now method.
        :param callback: The function to call after the wait_time has elapsed without new events.
        """
        self.wait_time = wait_time
        self.callback = callback
        self.timer = None
        self.lock = threading.Lock()
        self.args = None
        self.kwargs = None

    def call(self, *args, **kwargs):
        """
        Resets the timer. If the timer is already running, it cancels it and starts a new one.
        """
        self.args = args
        self.kwargs = kwargs
        with self.lock:
            if self.timer:
                self.timer.cancel()
            if self.wait_time == 0:
                self.call_now()
            elif self.wait_time is None:
                pass
            else:
                self.timer = threading.Timer(self.wait_time, self.call_now)
                self.timer.start()

    def call_now(self):
        """
        Calls the callback that is waiting to be called.
        """
        self.callback(*self.args, **self.kwargs)

    def cancel(self):
        """
        Cancels the timer if it's running.
        """
        with self.lock:
            if self.timer:
                self.timer.cancel()
                self.timer = None
