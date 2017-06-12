"""
Some common framework things.
"""
import logging

def logged(class_):
    """Class-level decorator to insert logging.
    
    This assures that a class has a ``.log`` member.
    
    ::
    
        @logged
        class Something:
            def __init__(self, args):
                self.log(f"init with {args}")
    """
    class_.log= logging.getLogger(class_.__qualname__)
    return class_

class Logging:
    """Logging context manager.
    
    ::
    
        with Logging(stream=sys.stderr, level=logging.INFO):
            do the work.
            
    This guarantees that ``logging.shutdown()`` is run on exit.
    
    """
    def __init__(self, **kw):
        self.kw= kw
    def __enter__(self):
        logging.basicConfig(**self.kw)
        return logging.getLogger()
    def __exit__(self, *exc):
        logging.shutdown()
