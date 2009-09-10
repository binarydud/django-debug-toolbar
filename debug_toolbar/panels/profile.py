from django.conf import settings
from debug_toolbar.panels import DebugPanel
from django.template.loader import render_to_string
import sys, tempfile, pstats
from cStringIO import StringIO
import logging
from django.utils.translation import ugettext_lazy as _
try:
    import cProfile as profile
except:
    import profile
    

class ProfileDebugPanel(DebugPanel):
    has_content = True
    name = 'Profile'
    def __init__(self):
        self.profiler = None
    
    def nav_title(self):
        return _('Profile')
    
    def title(self):
        return 'Profile'

    def url(self):
        return ''
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.GET.has_key('prof'):
            if profile:
                self.profiler = profile.Profile()
                ret_call = self.profiler.runcall(view_func, request, *view_args, **view_kwargs)
                return ret_call
    
    def content(self):
        #self.profiler.create_stats()
        content = None
        results = None
        profile = None
        data = None
        string = None
        if self.profiler:
            results = self.profiler.getstats()
            data = buildtree(results)
            profile = [x for x in data.values() if not x.get('callers')]
            nodes = []
            for node in profile:
                if "disable' of '_lsprof.Profiler" in node['function']:
                    continue
                if '<module>' in node['function'] and '<string>:1' in node['function']:
                    node = profile_data[node['calls'][0]['function']]
                nodes.append(node)
            profile = do_work(nodes, data)
        return render_to_string('debug_toolbar/panels/profile.html', {'content':profile})
        
        
        
import random
#from django.template import Library, Node, TemplateSyntaxError


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
def do_work(nodes, data):
    contents = []
    for node in nodes:
        for row in yield_work(node, 0, node['cost'], data):
            contents.append(row)
    return '\r\n'.join(contents)

def yield_work(node, depth, tottime, profile_data=None, parents_parent_id=None):
    parent_id = ''.join([str(random.randrange(0,10)) for x in range(0,9)])
    child_nodes = [x for x in node['calls'] if not x['builtin']]
    has_children = len(child_nodes) > 0
    if int(float(tottime)) == 0:
        proj_width = 1
    else:
        factor = float(400) / float(tottime)
        proj_width = int(float(factor) * float(node['cost']))
    proj_width = proj_width * 100 / 400
    name = node['func_name']
    s = 'row %i, %s:%s' % (depth,name,proj_width)
    ret = {
        'parent_id': parent_id,
        'parents_parent_id':parents_parent_id,
        'node':node,
        'proj_width': '%s%%' % proj_width,
        'has_children': has_children
    }
    s = render_to_string('debug_toolbar/profile/render_node.html', ret)
    yield s
    if hasattr(settings, 'DEBUG_TOOLBAR_CONFIG'):
        depth_limit = settings.DEBUG_TOOLBAR_CONFIG.get('PROFILER_DEPTH', 5)
    else:
        depth_limit = 5
    if has_children:
        depth += 1
        for called_node in node["calls"]:
            called = profile_data[called_node['function']]
            if depth >= depth_limit: continue
            for row in yield_work(called, depth, tottime, profile_data, parents_parent_id=parent_id):
                yield row