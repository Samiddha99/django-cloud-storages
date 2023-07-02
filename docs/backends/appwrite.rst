Appwrite
========

`AppWrite`_ is a platform that provides lots of backend services. It also provide cloud storage.
If you want to use `Appwrite storage`_ backend in your django project to host media files in Appwrite cloud storage, you can use this package.

**Run this command to install** `Appwrite Python SDK`_::

   pip install django-cloud-storages[appwrite]

NOTE: If you run ``pip install django-cloud-storages``, it will install all the supported cloud storage backends including Appwrite.
Run this command if you need all the available storage backends in your project.

Settings
--------

1. **To use AppWriteStorage as default storage (for all the models) add the following configuration in** **settings.py**:

.. code-block:: python

    # django < 4.2
    DEFAULT_FILE_STORAGE = "cloud_storages.backends.appwrite.AppWriteStorage"

    # django >= 4.2
    STORAGES = {"default": {"BACKEND": "cloud_storages.backends.appwrite.AppWriteStorage"}}

**Or, you can use AppWriteStorage only for specific model:**

.. code-block:: python

    from cloud_storages.backends.appwrite import AppWriteStorage

    custom_storage = AppWriteStorage()

    class Car(models.Model):
        ...
        photo = models.ImageField(storage=custom_storage)

or, use AppWriteStorage only for specific model using a **callable**:

.. code-block:: python

    from django.core.files.storage import default_storage
    from cloud_storages.backends.appwrite import AppWriteStorage

    def select_storage():
        return default_storage if settings.DEBUG else AppWriteStorage()

    class Car(models.Model):
        ...
        photo = models.ImageField(storage=select_storage)

NOTE: If you do not specify *storage* parameter in a *model field*,
the *storage backend* defined in *DEFAULT_FILE_STORAGE* will be used for the model fields.

2. **Now, set the following variables in** **settings.py**:

Sign In to `AppWrite`_ and create a new *project* and *bucket* in *storage*.

``APPWRITE_API_KEY``
   Your Apprite project's *API Key*. You will find the API Key into the *Settings* of your *Appwrite project*.
   The API key is different for each *Appwrite project*.

``APPWRITE_PROJECT_ID``
   Your Apprite project's *Project ID*. You will find the Project ID into the *Settings* of your *Appwrite project*.
   The Project ID is different for each *Appwrite project*.

``APPWRITE_BUCKET_ID``
   Your storage's *Bucket ID*. In Appwrite bucket is act like a folder. See the `Important Notes`_.

``APPWRITE_API_ENDPOINT`` (optional, default ``"https://cloud.appwrite.io/v1"``)
   Appwrite support custom domain; so if you want to use your domain address for API call and file hosting, you can set the your domain in this setting.
   The domain address must not end with ``/``. For more details check `Appwrite Custom domain`_.

``CLOUD_STORAGE_CREATE_NEW_IF_SAME_CONTENT`` (optional, default ``True``)
    If it set to ``False``, then during the new file upload/save if it find that a file is already exists in your storage with the same file name
    and also have same file's content, it will not save the new file in the cloud instead it just return the path of that existing file.
    If set to ``True``, it will save the file anyway.

``OVERWRITE_FILE`` (optional, default ``False``)
    If it set to ``True``, then during saving a file in cloud if the storage backend find that another file with the same name (but may have different contents)
    exists in the cloud, then it will delete the existing file from the cloud and save the new file.
    When set to ``False``, it will not delete the existing file from the cloud, instead it will save the new by modifying the name of the new file to avoid conflict.

Important Notes
****************

Appwrite does not store file like *general file system*, that is it does not support to create any folder or sub-folder to save a file inside a folder/sub-folder.
Instead appwrite allows to create buckets and save files inside the buckets. But it does not support sub-bucket (a bucket inside a bucket), you can create multiple buckets in your *Appwrite project*.
So, If you have used Appwrite as storage backend, the last directory in your path will be consider.
For example, you are saving a file having path ``assets/statics/media/my_file.txt``, it will ignore the first two directories **assets** and **statics**,
And create bucket (named **media**) in your project (if the bucket with same name is not exits in your project) and save the file **my_file.txt** inside that bucket.

If you saving a file with path ``my_file.txt`` that is when the path does't contain any directory, the storage backend will save the file inside the bucket
whose *bucket_id* you have mentioned in ``APPWRITE_BUCKET_ID`` setting.

.. _`AppWrite`: https://appwrite.io
.. _`Appwrite Python SDK`: https://pypi.org/project/appwrite/
.. _`Appwrite storage`: https://appwrite.io/docs/server/storage?sdk=python-default
.. _`Appwrite Custom domain`: https://appwrite.io/docs/custom-domains
.. _`Important Notes`: #important-notes