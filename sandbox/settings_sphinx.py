from settings import *

# Remove debug toolbar
try:
    idx = INSTALLED_APPS.index('debug_toolbar')
except ValueError:
    pass
else:
    del INSTALLED_APPS[idx]
