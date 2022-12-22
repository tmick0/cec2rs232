
driver_registry = {}

def driver(name):
    def decorate(cls):
        driver_registry[name] = cls
        return cls
    return decorate

