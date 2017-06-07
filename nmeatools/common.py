"""
Some common framework things.
"""
import logging

def logged(class_):
    """Class-level decorator to insert logging."""
    class_.log= logging.getLogger(class_.__qualname__)
    return class_

class Logging:
    """Logging context manager."""
    def __init__(self, **kw):
        self.kw= kw
    def __enter__(self):
        logging.basicConfig(**self.kw)
        return logging.getLogger()
    def __exit__(self, *exc):
        logging.shutdown()
