from cloud_storages.backends.dropbox import *
from django.test import *
from django.core.files.base import ContentFile

class DropBoxStorageTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # print("setUpTestData: Run once to set up non-modified data for all class methods.")
        pass
    
    def setUp(self, *args):
        # print("setUp: Run once for every test method to setup clean data.")
        self.storage = DropBoxStorage()
        self.file_name = "/tests/My-Bucket/test_file.txt"

    def tearDown(self, *args):
        # Clean up run after every test method.
        pass

    def test_open(self, *args):
        self.storage.open(name=self.file_name)

    # def test_save(self, *args):
    #     test_content = ContentFile(content="Test File")
    #     self.storage.save(name=self.file_name, content=test_content)
    
    def test_delete(self, *args):
        self.storage.delete(name=self.file_name)