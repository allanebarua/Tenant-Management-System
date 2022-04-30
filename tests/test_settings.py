"""Settings file for tests."""
from keja.config.settings import *  # noqa

# Use SQLite database for tests.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / '../tests/db.sqlite3',  # noqa
    }
}
