from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'oscar_vagrant',
        'USER': 'oscar_user',
        'PASSWORD': 'oscar_password',
        'HOST': 'localhost',
        'PORT': '',
    }
}
