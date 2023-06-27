import requests
import secrets
import string
import traceback

from django.core.files.storage import Storage
from django.core.files import File
from django.utils.deconstruct import deconstructible
from django.utils.deconstruct import deconstructible

from appwrite.client import Client
from appwrite.input_file import InputFile
from appwrite.services.storage import Storage as appwrite_storage
from appwrite.exception import AppwriteException

from cloud_storages.utils import *


@deconstructible
class AppWriteStorage(Storage):
    CHUNK_SIZE = 4 * 1024 * 1024
    def __init__(self):
        self.APPWRITE_API_KEY = setting('APPWRITE_API_KEY')
        self.APPWRITE_PROJECT_ID = setting('APPWRITE_PROJECT_ID')
        self.APPWRITE_BUCKET_ID = setting('APPWRITE_BUCKET_ID')
        self.APPWRITE_API_ENDPOINT = setting('APPWRITE_API_ENDPOINT', "https://cloud.appwrite.io/v1")
        self.MEDIA_URL = setting('MEDIA_URL')
        
        self.client = Client()
        (self.client
        .set_endpoint(self.APPWRITE_API_ENDPOINT) # Your API Endpoint
        .set_project(self.APPWRITE_PROJECT_ID) # Your project ID
        .set_key(self.APPWRITE_API_KEY) # Your secret API key
        )
        self.storage = appwrite_storage(self.client)

    def open(self, name, mode="rb"):
        """Retrieve the specified file from storage."""
        return self._open(name, mode)
    def _open(self, name, mode='rb'):
        result = self.url(name)
        response = requests.get(result)
        if (response.status_code == 200):
            data = response.text
            remote_file = File(data)
            return remote_file
    
    def save(self, name, content, max_length=None):
        """
        Save new content to the file specified by name. The content should be
        a proper File object or any Python file-like object, ready to be read
        from the beginning.
        """
        if not hasattr(content, "chunks"):
            content = File(content, name)
        name = self.get_available_name(name, max_length=max_length)
        name = self._save(name, content)
        return name['file_id']
    def _save(self, name, content):
        content.open()
        the_file = InputFile.from_bytes(bytes=content.read(), filename=name['file_name'])
        result = self.storage.create_file(self.APPWRITE_BUCKET_ID, name['file_id'], the_file)
        content.close()
        return name
    
    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's free on the target storage system and
        available for new content to be written to.
        """
        new_name = self.get_valid_name(name)
        while(1):
            if self.exists(new_name['file_id']):
                new_name = self.get_valid_name(name)
                continue
            break
        return new_name
    
    def generate_filename(self, filename):
        """
        Validate the filename by calling get_valid_name() and return a filename
        to be passed to the save() method.
        """
        name = self.get_valid_name(filename)
        return name

    def get_valid_name(self, name):
        """
        Return a filename, based on the provided filename, that's suitable for
        use in the target storage system.
        """
        name = str(name).replace("\\", "/")
        alphaNumeric = string.ascii_uppercase + string.digits
        file_id = ''.join([secrets.choice(alphaNumeric) for i in range(36)])
        return {'file_id': file_id, 'file_name': name}

    def get_alternative_name(self, file_root, file_ext):
        """
        Return an alternative filename if one exists to the filename.
        """
        name = str(name).replace("\\", "/")
        alphaNumeric = string.ascii_uppercase + string.digits
        file_id = ''.join([secrets.choice(alphaNumeric) for i in range(36)])
        return {'file_id': file_id, 'file_name': name}

    def delete(self, name):
        """
        Delete the specified file from the storage system.
        """
        result = self.storage.delete_file(self.APPWRITE_BUCKET_ID, name)

    def exists(self, name):
        """
        Return True if a file referenced by the given name already exists in the
        storage system, or False if the name is available for a new file.
        """
        try:
            result = self.storage.get_file(self.APPWRITE_BUCKET_ID, name)
            return True
        except AppwriteException as e:
            if str(e) == "The requested file could not be found.":
                return False
            else:
                traceback.print_exc()
                raise(e)
        
    def listdir(self, path):
        """
        List the contents of the specified path. Return a 2-tuple of lists:
        the first item being directories, the second item being files.
        """
        pass
    
    def size(self, name):
        """
        Return the total size, in bytes, of the file specified by name.
        """
        result = self.storage.get_file(self.APPWRITE_BUCKET_ID, name)
        return result.sizeOriginal
    
    def url(self, name, permanent_link=False):
        """
        Return an absolute URL where the file's contents can be accessed directly by a web browser.
        """
        try:
            file_url = f"https://cloud.appwrite.io/v1/storage/buckets/{self.APPWRITE_BUCKET_ID}/files/{name}/view?project={self.APPWRITE_PROJECT_ID}"
            return file_url
        except Exception as e:
            print(e)
            return None
    
    def get_accessed_time(self, name):
        """
        Return the last accessed time (as a datetime) of the file specified by name.
        The datetime will be timezone-aware if USE_TZ=True.
        """
        result = self.storage.get_file(self.APPWRITE_BUCKET_ID, name)
        return result.updatedAt

    def get_created_time(self, name):
        """
        Return the creation time (as a datetime) of the file specified by name.
        The datetime will be timezone-aware if USE_TZ=True.
        """
        result = self.storage.get_file(self.APPWRITE_BUCKET_ID, name)
        return result.createdAt
    
    def get_modified_time(self, name):
        """
        Return the last modified time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        result = self.storage.get_file(self.APPWRITE_BUCKET_ID, name)
        return result.updatedAt
    

    
    
    

        

