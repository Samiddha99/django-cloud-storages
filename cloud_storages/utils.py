from django.conf import settings

def setting(name, default=None):
    """
    Helper function to get a Django setting by name. If setting doesn't exists
    it will return a default.

    :param name: Name of setting
    :type name: str
    :param default: Value if setting is not found
    :returns: Setting's value
    """
    return getattr(settings, name, default)


def dropBoxErrorMsg(err_tag):
    err_dict = {
        "not_found": "not_found: There is nothing at the given path.",
        "not_file": "not_file: We were expecting a file, but the given path refers to something that isn't a file.",
        "not_folder": "not_folder: We were expecting a folder, but the given path refers to something that isn't a folder.",
        "restricted_content": "restricted_content: The file cannot be proceed because the content is restricted."
    }
    return err_dict[err_tag]

class FileNameLengthError(Exception):
    """Exception raised for errors when file name length is too large or too small.
    """
    def __init__(self, message, min_length=None, max_length=None):
        self.min_length = min_length
        self.max_length = max_length
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return self.message

class ContentDoesNotExistsError(Exception):
    """Exception raised for errors when the requested file or folder does not exists.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return self.message

def throwAppwriteException(exception, folder='', filename=''):
    if str(exception.message) == "Storage bucket with the requested ID could not be found.":
        error_msg = f"The folder does not exists on the cloud storage.\nFolder Name: {folder}."
        raise ContentDoesNotExistsError(error_msg)
    elif str(exception.message) == "The requested file could not be found.":
        error_msg = f"The file does not exists on the cloud storage.\nFile Name: {filename}."
        raise ContentDoesNotExistsError(error_msg)
    else:
        raise exception

def throwDropboxException(exception):
    err = exception.error
    if err.is_path_lookup():
        lookUpError = err.get_path_lookup()
        error_msg = dropBoxErrorMsg(lookUpError._tag)
        raise ContentDoesNotExistsError(error_msg)
    raise exception