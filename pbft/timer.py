import asyncio

class Timer():
    def __init__(self, interval, callback,
                 loop = asyncio.get_event_loop()):
        self.interval = interval
        self.callback = callback
        self.loop = loop
        self.timer = None

    def start(self):
        if self.timer and not self.timer.done():
            return
        
        self.timer = self.loop.create_task(
            asyncio.sleep(self.interval, loop = self.loop))

        self.timer.add_done_callback(self.callback)

    def stop(self):
        if not self.timer:
            if not self.timer.done():
                self.timer.remove_done_callback(self.callback)
                self.timer.cancel()
            self.timer = None

    def restart(self):
        self.stop()
        self.start()
    
