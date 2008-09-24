import sys
import inspect
from StringIO import StringIO
from SimpleXMLRPCServer import SimpleXMLRPCServer
try:
    import signal
except ImportError:
    signal = None


class RobotRemoteServer(SimpleXMLRPCServer):
  
    def __init__(self, library, port=8270):
        SimpleXMLRPCServer.__init__(self, ('localhost', int(port)),
                                    logRequests=False)
        self._library = library
        self.register_function(self.get_keyword_names)
        self.register_function(self.run_keyword)
        self.register_function(self.get_keyword_arguments)
        self.register_function(self.get_keyword_documentation)
        self.register_function(self.stop_remote_server)
        if signal:
            callback = lambda signum, frame: self.stop_remote_server()
            signal.signal(signal.SIGHUP, callback)
            signal.signal(signal.SIGINT, callback)
        self.serve_forever()

    def serve_forever(self):
        self._shutdown = False
        while not self._shutdown:
            self.handle_request()

    def stop_remote_server(self):
        self._shutdown = True
        return True

    def get_keyword_names(self):
        names = [ attr for attr in dir(self._library) if attr[0] != '_'
                  and callable(getattr(self._library, attr)) ]
        return names + ['stop_remote_server']

    def run_keyword(self, name, args):
        result = {'status':'PASS', 'return':'', 'message':'',  'output':''}
        self._intercept_stdout()
        try:
            return_value = self._get_keyword(name)(*args)
        except:
            result['status'] = 'FAIL'
            result['message'] = self._get_error_message()
        else:
            result['return'] = self._handle_return_value(return_value)
        result['output'] = self._restore_stdout()
        return result

    def get_keyword_arguments(self, name):
        kw = self._get_keyword(name)
        args, varargs, _, defaults = inspect.getargspec(kw)
        if inspect.ismethod(kw):
            args = args[1:]  # drop 'self'
        if defaults:
            args, names = args[:-len(defaults)], args[-len(defaults):]
            args += [ '%s=%s' % (name, value)
                      for name, value in zip(names, defaults) ]
        if varargs:
            args.append('*%s' % varargs)
        return args

    # TODO: Not tested
    def get_keyword_documentation(self, name):
        return inspect.getdoc(self._get_keyword(name)) or ''

    def _get_keyword(self, name):
        if name == 'stop_remote_server':
            return self.stop_remote_server
        return getattr(self._library, name)

    def _get_error_message(self):
        # TODO: Return details too
        exc_type, exc_value, exc_tp = sys.exc_info()
        name = exc_type.__name__
        message = str(exc_value)
        if not message:
            return name
        if name in ['AssertionError', 'RuntimeError', 'Exception']:
            return message
        return '%s: %s' % (name, message)
  
    def _handle_return_value(self, ret):
        if isinstance(ret, (basestring, int, long, float, bool)):
            return ret
        if isinstance(ret, (tuple, list)):
            return [ self._handle_return_value(item) for item in ret ]
        if isinstance(ret, dict):
            return dict([ (self._str(key), self._handle_return_value(value))
                          for key, value in ret.items() ])
        return self._str(ret)

    def _str(self, item):
        if item is None:
            return ''
        return str(item)

    def _intercept_stdout(self):
        # TODO: What about stderr?
        sys.stdout = StringIO()

    def _restore_stdout(self):
        output = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = sys.__stdout__
        return output
