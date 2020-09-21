class GLObject:
    def __init__(self):
        self._needs_setup = True
        self._needs_update = True

    def setup(self):
        self._needs_setup = False

    def update(self):
        self._needs_update = False

    def draw(self):
        if self._needs_setup:
            self.setup()

    def destroy(self):
        pass