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
    def title(self):
        return 'Profile'

    def url(self):
        return ''
    def process_view(self, request, view_func, view_args, view_kwargs):
        logging.debug("processing view")
        if request.has_key('prof'):
            logging.debug("have key")
            self.profiler = profile.Profile()
            #args = (request,) + view_args
            return self.profiler.runcall(view_func, request, *view_args, **view_kwargs)
    def content(self):
        #self.profiler.create_stats()
        out = StringIO()
        old_stdout, sys.stdout = sys.stdout, out
        
        self.tmpfile = tempfile.mktemp()
        self.profiler.dump_stats(self.tmpfile)
        stats = pstats.Stats(self.tmpfile)
        
        stats.sort_stats('time')
        stats.print_stats(.1)
        
        sys.stdout = old_stdout
        content = '<pre>%s</pre>' % out.getvalue()
        return render_to_string('debug_toolbar/panels/profile.html', {'content':content})
        
        
    
        