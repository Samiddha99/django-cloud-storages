from pathlib import Path
from decouple import config, Csv
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env_file = BASE_DIR / '.env'
env = environ.Env()

DEBUG = True

APPWRITE_API_KEY = config('APPWRITE_API_KEY')
APPWRITE_PROJECT_ID = config('APPWRITE_PROJECT_ID')
APPWRITE_BUCKET_ID = config('APPWRITE_BUCKET_ID')

CLOUD_STORAGE_CREATE_NEW_IF_SAME_CONTENT = False
DROPBOX_OAUTH2_ACCESS_TOKEN = config('DROPBOX_OAUTH2_ACCESS_TOKEN')
DROPBOX_OAUTH2_REFRESH_TOKEN = config('DROPBOX_OAUTH2_REFRESH_TOKEN')
DROPBOX_APP_KEY = config('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = config('DROPBOX_APP_SECRET')
DROPBOX_ROOT_PATH = "/Apps/my_personal_website_data/media"
DROPBOX_PERMANENT_LINK = True
OVERWRITE_FILE =True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}
SECRET_KEY = 'justfortest'
