import harrymack
from myclasses import ID3, Source, Track
from pathlib import Path


def test_create_source_object(data_row, config):
    source = Source(data_row, config)
    assert isinstance(source, Source)


def test_source_exists(source_object):
    assert source_object.exists("audio")


def test_source_path2(source_object):
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
    source_object,
    download_path,
    downloaded_audio_file,
    downloaded_image_file,
    downloaded_description_file,
):
    source_object.root_directory = download_path
    source_object.find_all_files()
    assert source_object.filenames["audio"] == str(downloaded_audio_file)
    assert source_object.filenames["image"] == str(downloaded_image_file)
    assert source_object.filenames["description"] == str(downloaded_description_file)


def test_create_id3_object(data_row):
    id3 = ID3(data_row)
    assert isinstance(id3, ID3)


def test_create_track_object(data_row, config, source_object, id3_object):
    t = Track(data_row, config, source_object, id3_object)
    assert isinstance(t, Track)


def test_track_create_folder(track_object):
    assert 1 == 2


def test_track_load_data(track_object):
    assert 1 == 2


def test_track_exists(track_object):
    assert 1 == 2


def test_track_extract_from_source(track_object):
    assert 1 == 2


def test_track_write_id3_tags(track_object):
    assert 1 == 2


def test_track_add_source(track_object):
    assert 1 == 2
