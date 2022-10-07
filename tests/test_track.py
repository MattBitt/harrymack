import harrymack
import track
from pathlib import Path


def test_create_source_object(data_row, config):
    source = track.Source(data_row, config)
    assert isinstance(source, track.Source)


def test_source_exists(source_object):
    assert source_object.exists()


def test_source_path(source_object):
    assert source_object.full_path() == "asdf"


def test_source_full_path(source_object):
    assert source_object.full_path() == "asdf"


def test_source_download_file_overwrite_true(source_object):
    assert source_object.download_file == "asdf"


def test_source_download_file_overwrite_false(source_object):
    assert source_object.download_file == "asdf"


def test_source_path(source_object):
    assert source_object.path() == "asdf"


def test_source_find_all_files_all_exist(
    source_object, download_path, downloaded_audio_file, downloaded_image_file, downloaded_description_file
):
    source_object.download_path = download_path
    source_object.filenames = source_object.find_all_files()
    assert source_object.filenames["audio"] == str(source_object.download_path / "NPdKxsSE5JQ.mp3")
    assert source_object.filenames["image"] == str(source_object.download_path / "NPdKxsSE5JQ.jpg")
    assert source_object.filenames["description"] == str(source_object.download_path / "NPdKxsSE5JQ.description")


def test_source_find_all_files_all_existasdfr(source_object, download_path):
    source_object.download_path = download_path
    source_object.filenames = source_object.find_all_files()
    assert source_object.filenames["audio"] == str(source_object.download_path / "NPdKxsSE5JQ.mp3")
    assert source_object.filenames["image"] == str(source_object.download_path / "NPdKxsSE5JQ.jpg")
    assert source_object.filenames["description"] == str(source_object.download_path / "NPdKxsSE5JQ.description")


def test_create_id3_object(data_row):
    id3 = track.ID3(data_row)
    assert isinstance(id3, track.ID3)


def test_create_track_object(data_row, config, source_object, id3_object):
    t = track.Track(data_row, config, source_object, id3_object)
    assert isinstance(t, track.Track)
