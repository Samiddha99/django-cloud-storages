Dropbox
=======

`DropBox`_ is a file hosting service. If you want to use Dropbox as a storage backend in the django project
to host media files in Dropbox cloud storage, you can use this package.

**Run this command to install** `Dropbox SDK for Python`_::

   pip install django-cloud-storages[dropbox]

NOTE: If you run ``pip install django-cloud-storages``, it will install all the supported cloud storage backends including Dropbox.
Run this command if you need all the available storage backends in your project.

Settings
--------

1. **To use DropBoxStorage as default storage (for all the models) add the following configuration in** **settings.py**:

.. code-block:: python

    # django < 4.2
    DEFAULT_FILE_STORAGE = "cloud_storages.backends.dropbox.DropBoxStorage"

    # django >= 4.2
    STORAGES = {"default": {"BACKEND": "cloud_storages.backends.dropbox.DropBoxStorage"}}

**Or, you can use DropBoxStorage only for specific model:**

.. code-block:: python

    from cloud_storages.backends.dropbox import DropBoxStorage

    custom_storage = DropBoxStorage()

    class Car(models.Model):
        ...
        photo = models.ImageField(storage=custom_storage)

or, Use DropBoxStorage only for specific model using a **callable**:

.. code-block:: python

    from django.core.files.storage import default_storage
    from cloud_storages.backends.dropbox import DropBoxStorage

    def select_storage():
        return default_storage if settings.DEBUG else DropBoxStorage()

    class Car(models.Model):
        ...
        photo = models.ImageField(storage=select_storage)

NOTE: If you do not specify *storage* parameter in a *model field*,
the *storage backend* defined in *DEFAULT_FILE_STORAGE* will be used for the model fields.

2. **Now, set the following variables in** **settings.py**:

``DROPBOX_OAUTH2_ACCESS_TOKEN``
   Your Dropbox *access token*. You can obtain one by following the instructions in the `tutorial`_.

``DROPBOX_OAUTH2_REFRESH_TOKEN``
   Your Dropbox *refresh token*. You can obtain one by following the instructions in the `tutorial`_.

``DROPBOX_APP_KEY``
   Your Dropbox *App Key*. Sign in to `DropBox Developers`_ and go to **App Console** and create/select an app to obtain your *App Key*.

``DROPBOX_APP_SECRET``
   Your Dropbox *App Secret*. Sign in to `DropBox Developers`_ and go to **App Console** and create/select an app to obtain your *App Secret*.

``DROPBOX_ROOT_PATH`` (optional, default ``"/"``)
   Path which will prefix all uploaded files. Must begin with a ``/``.
   This is the root directory inside that all the uploaded contents will be saved.

``DROPBOX_TIMEOUT`` (optional, default ``100``)
   Timeout in seconds for requests to the API. If ``None``, the client will wait forever.
   Request will wait for that time to get response.

``DROPBOX_WRITE_MODE`` (optional, default ``"add"``)
   Sets the Dropbox WriteMode strategy.
   Read more in the `official docs`_.

``DROPBOX_PERMANENT_LINK`` (optional, default ``False``)
   To get the URL of the file (stored in cloud storage) django call ``url()`` method of the ``Storage`` class.
   In case of *Dropbox storage backend* this method return a temporary link of the stored file, i.e at every request you will get a different url for the file.
   If you want to get a permanent link (will be same in every request), set this setting to ``True``.
   Also in ``url()`` method call, you can pass the parameter ``permanent_link`` (value: ``True`` or ``False``).

``CLOUD_STORAGE_CREATE_NEW_IF_SAME_CONTENT`` (optional, default ``False``)
    If it set to ``False``, then during the new file upload/save if it find that a file is already exists in your storage with the same file name
    and also have same file's content, it will not save the new file in the cloud instead it just return the path of that existing file.
    If set to ``True``, it will save the file anyway.

Get DROPBOX_OAUTH2_ACCESS_TOKEN and DROPBOX_OAUTH2_REFRESH_TOKEN
#################################################################

You can obtain the access token and refresh token manually via ``APP_KEY`` and ``APP_SECRET``.

1. Obtain DROPBOX_OAUTH2_ACCESS_TOKEN
**************************************

I. Go to your *app* from `DropBox Developers`_'s **App Console**, then in your *app* go to **Permissions** tab and enable the permissions.
If you have not sign up in Dropbox with a *work email*, then do not enable the permissions under the **Team Scopes**.

II. Go to this link:

   https://www.dropbox.com/oauth2/authorize?client_id=APP_KEY&token_access_type=offline&response_type=code

Replace the ``APP_KEY`` with your app key. It will display your ``ACCESS_TOKEN``, set the value to the ``DROPBOX_OAUTH2_ACCESS_TOKEN``.

2. Obtain DROPBOX_OAUTH2_REFRESH_TOKEN
***************************************

Using your ``APP_KEY``, ``APP_SECRET`` and ``ACCESS_TOKEN`` obtain the refresh token.

Execute this script in a shell.

.. code-block:: shell

   curl https://api.dropbox.com/oauth2/token \
   -d code=ACCESS_TOKEN \
   -d grant_type=authorization_code \
   -d client_id=APP_KEY \
   -d client_secret=APP_SECRET

The response would be:

.. code-block:: json

   {
      "access_token": "sl.************************",
      "token_type": "bearer",
      "expires_in": 14400,
      "refresh_token": "************************", <-- your REFRESH_TOKEN
      "scope": <SCOPES>,
      "uid": "************************",
      "account_id": "dbid:************************"
   }

.. _`DropBox`: https://www.dropbox.com
.. _`DropBox Developers`: https://www.dropbox.com/developers
.. _`Dropbox SDK for Python`: https://www.dropbox.com/developers/documentation/python#tutorial
.. _`Dropbox tutorial`: https://www.dropbox.com/developers/documentation/python#tutorial
.. _`official docs`: https://dropbox-sdk-python.readthedocs.io/en/latest/api/files.html#dropbox.files.WriteMode
.. _`tutorial`: #get-dropbox-oauth2-access-token-and-dropbox-oauth2-refresh-token