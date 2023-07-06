import requests
import os
import traceback
from io import BytesIO
import inspect

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.core.files import File
from django.utils.deconstruct import deconstructible
from django.utils._os import safe_join

import dropbox
from dropbox import sharing as dbx_sharing
from dropbox.exceptions import ApiError
from dropbox.files import *

from cloud_storages.utils import *

_DEFAULT_TIMEOUT = 100
_DEFAULT_MODE = 'add'

@deconstructible
class DropBoxStorage(Storage):
    CHUNK_SIZE = 4 * 1024 * 1024
    DROPBOX_PERMANENT_LINK = False
    def __init__(self):
        self.OVERWRITE_FILE = setting('OVERWRITE_FILE', False)
        self.CLOUD_STORAGE_CREATE_NEW_IF_SAME_CONTENT = setting('CLOUD_STORAGE_CREATE_NEW_IF_SAME_CONTENT', True)
        self.DROPBOX_OAUTH2_ACCESS_TOKEN = setting('DROPBOX_OAUTH2_ACCESS_TOKEN')
        self.DROPBOX_OAUTH2_REFRESH_TOKEN = setting('DROPBOX_OAUTH2_REFRESH_TOKEN')
        self.DROPBOX_APP_KEY = setting('DROPBOX_APP_KEY')
        self.DROPBOX_APP_SECRET = setting('DROPBOX_APP_SECRET')
        self.DROPBOX_PERMANENT_LINK = DROPBOX_PERMANENT_LINK = setting('DROPBOX_PERMANENT_LINK', False)
        self.DROPBOX_ROOT_PATH = setting('DROPBOX_ROOT_PATH')
        self.MEDIA_URL = setting('MEDIA_URL')
        self.timeout = setting('DROPBOX_TIMEOUT', _DEFAULT_TIMEOUT)
        self.write_mode = setting('DROPBOX_WRITE_MODE', _DEFAULT_MODE)
        self.dbx = dropbox.Dropbox(app_key=self.DROPBOX_APP_KEY, app_secret=self.DROPBOX_APP_SECRET, oauth2_refresh_token=self.DROPBOX_OAUTH2_REFRESH_TOKEN)
        self.dbx.users_get_current_account()

    def _full_path(self, name):
        if name == '/':
            name = ''
        if name[0] in ["/", "\\"]:
            name = name[1:]
        joined_path = os.path.join(self.DROPBOX_ROOT_PATH, name).replace("\\", "/")
        return joined_path

    def open(self, name, mode="rb"):
        """Retrieve the specified file from storage."""
        return self._open(name, mode)
    def _open(self, name, mode='rb'):
        full_name = self._full_path(name)
        try:
            file_metadata, response = self.dbx.files_download(full_name)
            file_content = BytesIO(response.content)
            response_file = File(file_content, name=name)
            return response_file
        except ApiError as e:
            throwDropboxException(e)
           
        
    def save(self, name, content, max_length=None):
        """
        Save new content to the file specified by name. The content should be
        a proper File object or any Python file-like object, ready to be read
        from the beginning.
        """
        # Get the proper name for the file, as it will actually be saved.
        if name is None:
            name = content.name
        # if not hasattr(content, "chunks"):
        #     content = File(content, name)
        path = self.get_available_name(name, content, max_length=max_length)
        if path[1] is None:
            self._save(path[0], content)
        return path[0]
    def _save(self, name, content):
        full_name = self._full_path(name)
        content.open()
        if content.size <= self.CHUNK_SIZE:
            self.dbx.files_upload(content.read(), full_name, mode=WriteMode(self.write_mode))
        else:
            self._chunked_upload(content, full_name)
        content.close()
        return name

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
                        remote_file = self.open(name=new_name)
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
        name = str(name).replace("\\", "/")
        # name = self._full_path(name)
        return name
    
    def get_alternative_name(self, file_root, file_ext=None, index=0):
        """
        Return an alternative filename if one exists to the filename.
        """
        res = file_root.rsplit('.', 1)  # Split on last occurrence of delimiter
        file_name = f"{res[0]}({index})"
        file_ext = res[1]
        updated_name =  f"{file_name}.{file_ext}"
        # updated_name = self._full_path(updated_name)
        return updated_name

    def delete(self, name):
        """
        Delete the specified file from the storage system.
        """
        full_name = self._full_path(name)
        try:
            result = self.dbx.files_delete_v2(full_name)
            return result
        except ApiError as e:
            throwDropboxException(e)
                
    def exists(self, name):
        """
        Return True if a file referenced by the given name already exists in the
        storage system, or False if the name is available for a new file.
        """
        full_name = self._full_path(name)
        try:
            self.dbx.files_get_metadata(full_name)
            return True
        except ApiError as e:
            err = e.error
            if err.is_path():
                # lookUpError = err.get_path_lookup()
                # error_msg = dropBoxErrorMsg(lookUpError._tag)
                return False
            else:
                raise e
    
    def listdir(self, path):
        """
        List the contents of the specified path. Return a 2-tuple of lists:
        the first item being directories, the second item being files.
        """
        directories, files = [], []
        metadata = self.dbx.files_list_folder(path)
        for entry in metadata.entries:
            if isinstance(entry, FolderMetadata):
                directories.append(entry.name)
            else:
                files.append(entry.name)
        return directories, files
    
    def size(self, name):
        """
        Return the total size, in bytes, of the file specified by name.
        """
        full_name = self._full_path(name)
        try:
            metadata = self.dbx.files_get_metadata(full_name)
            return metadata.size
        except ApiError as e:
            throwDropboxException(e)

    def url(self, name, permanent_link=DROPBOX_PERMANENT_LINK):
        """
        Return an absolute URL where the file's contents can be accessed directly by a web browser.
        """
        full_name = self._full_path(name)
        try:
            if not permanent_link:
                media = self.dbx.files_get_temporary_link(full_name)
                file_url = media.link
            else:
                dbx_share_settings = dbx_sharing.SharedLinkSettings(allow_download=True)
                media = self.dbx.sharing_create_shared_link_with_settings(full_name, settings=dbx_share_settings)
                file_url = str(media.url)[:-1]+"1"
            return file_url
        except Exception:
            return None

    def get_accessed_time(self, name):
        """
        Return the last accessed time (as a datetime) of the file specified by name.
        The datetime will be timezone-aware if USE_TZ=True.
        """
        full_name = self._full_path(name)
        try:
            last_accessed = self.dbx.files_get_metadata(full_name).client_modified
            return last_accessed
        except ApiError as e:
            throwDropboxException(e)

    def get_created_time(self, name):
        """
        Return the creation time (as a datetime) of the file specified by name.
        The datetime will be timezone-aware if USE_TZ=True.
        """
        full_name = self._full_path(name)
        try:
            created_at = self.dbx.files_get_metadata(full_name).client_modified
            return created_at
        except ApiError as e:
            throwDropboxException(e)

    def get_modified_time(self, name):
        """
        Return the last modified time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        full_name = self._full_path(name)
        try:
            last_modified = self.dbx.files_get_metadata(full_name).server_modified
            return last_modified
        except ApiError as e:
            throwDropboxException(e)
                
    def _chunked_upload(self, content, dest_path):
        upload_session = self.dbx.files_upload_session_start(content.read(self.CHUNK_SIZE))
        cursor = UploadSessionCursor(session_id=upload_session.session_id, offset=content.tell())
        commit = CommitInfo(path=dest_path, mode=WriteMode(self.write_mode))
        while content.tell() < content.size:
            if (content.size - content.tell()) <= self.CHUNK_SIZE:
                self.dbx.files_upload_session_finish(content.read(self.CHUNK_SIZE), cursor, commit)
            else:
                self.dbx.files_upload_session_append_v2(content.read(self.CHUNK_SIZE), cursor)
                cursor.offset = content.tell()