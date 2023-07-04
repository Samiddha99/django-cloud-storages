import requests
import secrets
import string
import traceback
import re
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.core.files import File
from django.utils.deconstruct import deconstructible
from django.utils.deconstruct import deconstructible

from appwrite.role import Role
from appwrite.permission import Permission
from appwrite.client import Client
from appwrite.input_file import InputFile
from appwrite.services.storage import Storage as appwrite_storage
from appwrite.exception import AppwriteException

from cloud_storages.utils import *


@deconstructible
class AppWriteStorage(Storage):
    CHUNK_SIZE = 4 * 1024 * 1024
    MAX_FILE_NAME_LENGTH = 30
    def __init__(self):
        self.OVERWRITE_FILE = setting('OVERWRITE_FILE', False)
        self.CLOUD_STORAGE_CREATE_NEW_IF_SAME_CONTENT = setting('CLOUD_STORAGE_CREATE_NEW_IF_SAME_CONTENT', True)
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
        folder, filename = self.extract_folder_and_filename(name)
        try:
            response = self.storage.get_file_view(folder, filename)
            file_content = BytesIO(response)
            response_file = File(file_content, name=name)
            return response_file
        except AppwriteException as e:
            throwAppwriteException(e, folder, filename)
    
    def save(self, name, content, max_length=None):
        """
        Save new content to the file specified by name. The content should be
        a proper File object or any Python file-like object, ready to be read
        from the beginning.
        """
        folder, org_filename = self.extract_folder_and_filename(name)
        content = File(content, org_filename)
        # if not hasattr(content, "chunks"):
        #     content = File(content, org_filename)
        folder = self.create_folder(folder)
        path = self.get_available_name(name=name, content=content, max_length=max_length)
        if path[1] is None:
            self._save(path[0], content)
        return path[0]
    def _save(self, path, content):
        folder, filename = self.extract_folder_and_filename(path)
        content.open()
        the_file = InputFile.from_bytes(bytes=content.read(), filename=content.name)
        result = self.storage.create_file(bucket_id=folder, file_id=filename, file=the_file)
        content.close()
        return path
    
    def _id_validation(self, name):
        name = re.sub(r"^\W+|^_+", "", name) # Remove special characters at beginning
        name = re.sub(r"[^a-zA-Z0-9-._]*", "", name)
        return name

    def extract_folder_and_filename(self, path):
        path = str(path).replace("\\", "/")
        folders = path.split("/")
        if len(folders) == 0:  # file.txt
            last_folder = self.APPWRITE_BUCKET_ID
            file_name = path
        elif len(folders) == 1:  # /file.txt
            last_folder = self.APPWRITE_BUCKET_ID
            file_name = folders[0]
        else: # folder/folder2/file.txt
            file_name = folders.pop()  # eliminate the last item i.e. file name
            last_folder = folders.pop()
        last_folder = last_folder if len(last_folder) <= self.MAX_FILE_NAME_LENGTH else last_folder[0:30]
        last_folder = self._id_validation(last_folder)
        # file_name = self.get_valid_name(file_name)
        return (last_folder, file_name)
    
    def create_folder(self, folder):
        try:
            result = self.storage.get_bucket(folder)
        except AppwriteException as e:
            if str(e) == "Storage bucket with the requested ID could not be found.":
                result = self.storage.create_bucket(bucket_id=folder, name=folder, permissions=[Permission.read(Role.any())], file_security=False, enabled=True, encryption=False, antivirus=False)
            else:
                raise e
        return folder

    def get_available_name(self, name, content, max_length=None):
        """
        Return a filename that's free on the target storage system and
        available for new content to be written to.
        """
        formatted_name = self.get_valid_name(name)
        new_name = formatted_name
        if self.OVERWRITE_FILE:
            try:
                self.delete(new_name)
            except ContentDoesNotExistsError:
                pass
        else:
            index = 0
            while(1):
                index += 1
                if self.exists(new_name): # check file existence with file name
                    if not self.CLOUD_STORAGE_CREATE_NEW_IF_SAME_CONTENT:
                        # check file existence with file's contents
                        remote_file = self.open(new_name)
                        remote_file_data = remote_file.read()
                        content_data = content.read()
                        if remote_file_data == content_data:
                            return (new_name, 'Exists')
                    new_name = self.get_alternative_name(formatted_name, index=index)
                    continue
                break
        return (new_name, None)
    
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
        folder, filename = self.extract_folder_and_filename(name)
        filename = self._id_validation(filename)
        res = filename.rsplit('.', 1)  # Split on last occurrence of delimiter
        if len(res[0])>self.MAX_FILE_NAME_LENGTH:
            err_msg = f"File name's length must be less than or equal to {self.MAX_FILE_NAME_LENGTH}."
            raise FileNameLengthError(max_length=self.MAX_FILE_NAME_LENGTH, message=err_msg)
        elif len(res[0]) < 1:
            err_msg = f"File name's length is too small. Avoid using special characters in file name, and file name should not start with underscore."
            raise FileNameLengthError(message=err_msg)
        return f"{folder}/{filename}"
        # return {'file_id': filename, 'file_name': filename, 'folder_id': folder, 'folder_name': folder}

    def get_alternative_name(self, file_root, file_ext=None, index=0):
        """
        Return an alternative filename if one exists to the filename.
        """
        folder, filename = self.extract_folder_and_filename(file_root)
        res = filename.rsplit('.', 1)  # Split on last occurrence of delimiter
        file_name = f"{res[0]}-{index}"
        file_ext = res[1]
        updated_name =  f"{file_name}.{file_ext}"
        return f"{folder}/{updated_name}"
        # return {'file_id': updated_name, 'file_name': updated_name, 'folder_id': file_root['folder_id'], 'folder_name': file_root['folder_name']}

    def delete(self, name):
        """
        Delete the specified file from the storage system.
        """
        folder, filename = self.extract_folder_and_filename(name)
        try:
            result = self.storage.delete_file(folder, filename)
            return result
        except AppwriteException as e:
            throwAppwriteException(e, folder, filename)

    def exists(self, name):
        """
        Return True if a file referenced by the given name already exists in the
        storage system, or False if the name is available for a new file.
        """
        folder, filename = self.extract_folder_and_filename(name)
        try:
            result = self.storage.get_file(folder, filename)
            return True
        except AppwriteException as e:
            if str(e) == "The requested file could not be found." or str(e) == "Storage bucket with the requested ID could not be found.":
                return False
            else:
                raise e
        
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
        folder, filename = self.extract_folder_and_filename(name)
        try:
            result = self.storage.get_file(folder, filename)
            return result.sizeOriginal
        except AppwriteException as e:
            throwAppwriteException(e, folder, filename)
    
    def url(self, name, permanent_link=None):
        """
        Return an absolute URL where the file's contents can be accessed directly by a web browser.
        """
        folder, filename = self.extract_folder_and_filename(name)
        file_url = f"{self.APPWRITE_API_ENDPOINT}/storage/buckets/{folder}/files/{filename}/view?project={self.APPWRITE_PROJECT_ID}"
        return file_url
    
    def get_accessed_time(self, name):
        """
        Return the last accessed time (as a datetime) of the file specified by name.
        The datetime will be timezone-aware if USE_TZ=True.
        """
        folder, filename = self.extract_folder_and_filename(name)
        try:
            result = self.storage.get_file(folder, filename)
            return result.updatedAt
        except AppwriteException as e:
            throwAppwriteException(e, folder, filename)

    def get_created_time(self, name):
        """
        Return the creation time (as a datetime) of the file specified by name.
        The datetime will be timezone-aware if USE_TZ=True.
        """
        folder, filename = self.extract_folder_and_filename(name)
        try:
            result = self.storage.get_file(folder, filename)
            return result.createdAt
        except AppwriteException as e:
            throwAppwriteException(e, folder, filename)
    
    def get_modified_time(self, name):
        """
        Return the last modified time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        folder, filename = self.extract_folder_and_filename(name)
        try:
            result = self.storage.get_file(folder, filename)
            return result.updatedAt
        except AppwriteException as e:
            throwAppwriteException(e, folder, filename)