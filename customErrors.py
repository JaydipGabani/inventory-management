class ProjectNotFound(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return (repr(self.value))


class NorexNotFound(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return (repr(self.value))


class ColorNotFound(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return (repr(self.value))


class InvalidProjectUpdate(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return (repr(self.value))
