from debug_toolbar.panels import DebugPanel
from django.template.loader import render_to_string
import sys, tempfile, pstats
from cStringIO import StringIO
import logging
try:
    import cProfile as profile
except:
    import profile

class ProfileDebugPanel(DebugPanel):
    has_content = True
    name = 'Profile'
    def __init__(self):
        self.profiler = None
        
    
    def title(self):
        return 'Profile'

    def url(self):
        return ''
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        logging.debug("processing view")
        if request.GET.has_key('prof'):
            logging.debug("have key")
            self.profiler = profile.Profile()
            #args = (request,) + view_args
            return self.profiler.runcall(view_func, request, *view_args, **view_kwargs)
    
    def content(self):
        #self.profiler.create_stats()
        content = None
        logging.debug("WTF")
        print 'WTF'
        results = None
        profile = None
        if self.profiler:
            logging.debug("getting stats")
            results = self.profiler.getstats()
            data = buildtree(results)
            print data
        return render_to_string('debug_toolbar/panels/profile.html', {'results':results,'profile':profile})
        
        
def buildtree(data):
    """Takes a pmstats object as returned by cProfile and constructs
    a call tree out of it"""
    functree = {}
    callregistry = {}
    for entry in data:
        node = {}
        code = entry.code
        # If its a builtin
        if isinstance(code, str):
            node['filename'] = '~'
            node['source_position'] = 0
            node['func_name'] = code
        else:
            node['filename'] = code.co_filename
            node['source_position'] = code.co_firstlineno
            node['func_name'] = code.co_name
            node['line_no'] = code.co_firstlineno
        node['cost'] = setup_time(entry.totaltime)
        node['function'] = label(code)

        if entry.calls:
            for subentry in entry.calls:
                subnode = {}
                subnode['builtin'] = isinstance(subentry.code, str)
                subnode['cost'] = setup_time(subentry.totaltime)
                subnode['function'] = label(subentry.code)
                subnode['callcount'] = subentry.callcount
                node.setdefault('calls', []).append(subnode)
                callregistry.setdefault(subnode['function'], []).append(node['function'])
        else:
            node['calls'] = []
        functree[node['function']] = node
    for key in callregistry:
        node = functree[key]
        node['callers'] = callregistry[key]
    return functree
    
def setup_time(t):
    """Takes a time generally assumed to be quite small and blows it
    up into millisecond time.

    For example:
        0.004 seconds     -> 4 ms
        0.00025 seconds   -> 0.25 ms

    The result is returned as a string.

    """
    t = t*1000
    t = '%0.2f' % t
    return t

def label(code):
    """Generate a friendlier version of the code function called"""
    if isinstance(code, str):
        return code
    else:
        return '%s %s:%d' % (code.co_name,
                             code.co_filename,
                             code.co_firstlineno)