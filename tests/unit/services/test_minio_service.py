import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from minio import Minio
from src.services.minio_service import MinioService

@pytest.fixture
def mock_minio_client():
    with patch('src.services.minio_service.Minio') as mock_minio:
        # Create a mock client instance
        mock_client = Mock()
        mock_minio.return_value = mock_client
        yield mock_client

@pytest.fixture
def minio_service(mock_minio_client):
    return MinioService()

@pytest.fixture
def sample_objects():
    # Create mock objects that mimic Minio's Object class
    objects = []
    for i in range(5):
        obj = Mock()
        obj.object_name = f"test_file_{i}.txt"
        objects.append(obj)
    return objects

def test_init_creates_client_with_correct_settings(mock_minio_client):
    service = MinioService()
    assert service.client == mock_minio_client

def test_ensure_bucket_exists_creates_bucket_if_not_exists(minio_service):
    minio_service.client.bucket_exists.return_value = False
    minio_service.ensure_bucket_exists()
    minio_service.client.make_bucket.assert_called_once_with(minio_service.bucket_name)

def test_ensure_bucket_exists_skips_if_exists(minio_service):
    minio_service.client.bucket_exists.return_value = True
    minio_service.ensure_bucket_exists()
    minio_service.client.make_bucket.assert_not_called()

def test_count_objects_returns_correct_count(minio_service, sample_objects):
    minio_service.client.list_objects.return_value = sample_objects
    count = minio_service.count_objects()
    assert count == 5

def test_list_objects_returns_object_names(minio_service, sample_objects):
    minio_service.client.list_objects.return_value = sample_objects
    object_names = minio_service.list_objects()
    assert object_names == ["test_file_0.txt", "test_file_1.txt", "test_file_2.txt", 
                          "test_file_3.txt", "test_file_4.txt"]

def test_list_objects_with_prefix(minio_service, sample_objects):
    prefix = "test_"
    minio_service.client.list_objects.return_value = sample_objects
    object_names = minio_service.list_objects(prefix=prefix)
    minio_service.client.list_objects.assert_called_once_with(minio_service.bucket_name, prefix=prefix)

def test_download_sample_creates_output_dir(minio_service, tmp_path):
    minio_service.client.list_objects.return_value = []
    output_dir = tmp_path / "test_output"
    minio_service.download_sample(1, output_dir)
    assert output_dir.exists()

def test_download_sample_downloads_correct_number(minio_service, sample_objects, tmp_path):
    minio_service.client.list_objects.return_value = sample_objects
    output_dir = tmp_path / "test_output"
    
    downloaded_files = minio_service.download_sample(3, output_dir)
    
    # Should have called fget_object 3 times
    assert minio_service.client.fget_object.call_count == 3
    assert len(downloaded_files) == 3

def test_download_sample_handles_empty_bucket(minio_service, tmp_path):
    minio_service.client.list_objects.return_value = []
    output_dir = tmp_path / "test_output"
    
    downloaded_files = minio_service.download_sample(5, output_dir)
    
    assert len(downloaded_files) == 0
    minio_service.client.fget_object.assert_not_called() 