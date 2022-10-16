import pytest
from loguru import logger
from _pytest.logging import LogCaptureFixture
import harrymack
from myclasses import ID3, Source, Track
import os
from pathlib import Path


@pytest.fixture
def data_row():
    """Returns track_info with Omegle Bars 1.1 info to create a Track instance"""
    data_row = {
        "ClipTypes": "OmegleBarsClips",
        "EpisodeNumber": "1",
        "TrackNumber": "1",
        "StartTime": "00:00:55",
        "EndTime": "00:04:32",
        "PrimaryWords": "Florescent Adolescence, Rainbow, Wetherspoons",
        "ArtistName": "Harry Mack",
        "URL": "https://www.youtube.com/watch?v=NPdKxsSE5JQ",
        "AlbumName": "Omegle Bars 1",
        "Title": "OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons",
        "Filename": "1 - OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons",
        "WholeName": "NPdKxsSE5JQ",
        "BeatName": "Test Beatname",
        "Producer": "Homage",
    }
    return data_row


@pytest.fixture
def track_object(data_row, config, source_object, id3_object):
    """Returns a Track instance with Omegle Bars 1.1 Info"""
    return Track(data_row, config, source_object, id3_object)


@pytest.fixture
def source_object(data_row, config):
    return Source(data_row, config)


# * These fixtures create a temporary directory that contains empty audio, image, and description files
@pytest.fixture
def download_path(tmp_path):
    d = tmp_path / "downloads"
    d.mkdir()
    return d


@pytest.fixture
def downloaded_audio_file(source_object, download_path):
    audio_file = download_path / (source_object.id + ".mp3")
    audio_file.touch()
    return audio_file


@pytest.fixture
def downloaded_image_file(source_object, download_path):
    image_file = download_path / (source_object.id + ".jpg")
    image_file.touch()
    return image_file


@pytest.fixture
def downloaded_description_file(source_object, download_path):
    description_file = download_path / (source_object.id + ".mp3.description")
    description_file.touch()
    return description_file


@pytest.fixture
def id3_object(data_row):
    return ID3(data_row)


@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)


@pytest.fixture
def default_config_data():
    return harrymack.default_config()


@pytest.fixture
def config(tmp_path, default_config_data):
    tmp_config_path = Path.joinpath(tmp_path, "test-config.yaml")
    harrymack.create_yaml_from_dict(default_config_data, tmp_config_path)
    return harrymack.load_config(tmp_config_path)


@pytest.fixture
def correct_csv(tmp_path):
    source_csv = "./HarryMackClips.csv"
    target_csv = "HarryMackClipsCorrect.csv"
    n = 10  # * number of records to keep
    if os.path.exists(source_csv):
        correct_csv = Path.joinpath(tmp_path, target_csv)
        harrymack.copy_file(source_csv, correct_csv, overwrite=True)
        correct_csv = harrymack.keep_n_lines_of_file(n, correct_csv)
        return correct_csv
    else:
        # * Have to have CSV available to run this test
        return None


@pytest.fixture
def empty_csv(correct_csv):
    empty_csv = harrymack.keep_n_lines_of_file(0, correct_csv)
    return empty_csv


@pytest.fixture
def malformed_csv(correct_csv, tmp_path):
    malformed_csv = harrymack.remove_random_column_from_csv(correct_csv, tmp_path)
    return malformed_csv
