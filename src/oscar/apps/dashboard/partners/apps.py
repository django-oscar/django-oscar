# django 3 automatically discovers app configs in apps.py.
# since the apps.py files are for use with oscar3 and oscar uses config.py,
# we must make sure django 3 can not find a valid app config in apps.py
# we do this by providing base classes that so NOT extend from 
# django.apps.AppConfig
class PartnersDashboardConfig:
    pass
