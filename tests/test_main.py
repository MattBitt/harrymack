import pytest
import harrymack
import os


@pytest.fixture
def track_info():
    '''Returns a Track instance with Omegle Bars 1.1 Info'''
    track_info = {
        'WholeName': "NPdKxsSE5JQ",
        'ArtistName': "Harry Mack",
        'AlbumName': "Omegle Bars 1",
        'TrackNumber': "1",
        'Title': "OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons",
        'StartTime': "00:00:55",
        'EndTime': "00:04:32",
        'URL': "https://www.youtube.com/watch?v=NPdKxsSE5JQ",
        'BeatName': "Test Beatname",
        'Producer': "Homage",
        'Words' : "Florescent Adolescence, Rainbow, Wetherspoons"
    }
    return track_info
    
    


def test_import_file_exists():
    tracks = harrymack.import_from_csv("./tests/HarryMackTest.csv")
    assert type(tracks) is list
    assert len(tracks) == 10

def test_import_file_does_not_exist():
    with pytest.raises(FileNotFoundError, match="^File*"):
        harrymack.import_from_csv("./tests/does not exist.csv")

def test_import_file_empty():
    with pytest.raises(harrymack.EmptyListError, match="^File*"):
        harrymack.import_from_csv("./tests/HarryMackTestEmpty.csv")

def test_import_file_malformed():
    with pytest.raises(KeyError, match=".+does not exist.+"):
        harrymack.import_from_csv("./tests/HarryMackTestMalformed.csv")

def test_create_track(track_info):
    track = harrymack.Track(track_info)
    assert track.source_video_name == "NPdKxsSE5JQ"
    assert track.artist == "Harry Mack"
    assert track.album == "Omegle Bars 1"
    assert track.track_number == "1"
    assert track.track_title == "OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons"
    assert track.filename == "1 - OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons.mp3"
    assert track.start_time == "00:00:55"
    assert track.end_time == "00:04:32"
    assert track.url == "https://www.youtube.com/watch?v=NPdKxsSE5JQ"
    assert track.beatname == "Test Beatname"
    assert track.producer == "Homage"

#def test_empty_track():
#    source_info = {}
#    track = harrymack.Track(source_info)
#    assert track.artist == ""


def test_correct_config_file_load():
    assert 1 == 2

def test_config_file_create():
    assert 1 == 2


def test_incorrect_config_file_load():
    assert 1 == 2

def test_env_variable_change():
    #os.environ['ENVIORNMENT'] = "env_dev"
    config = harrymack.load_config('./config.yaml')
    env = config['enviornment']
    assert config[env]['music_root'] == "./media/musicroot/"
    os.environ['ENVIORNMENT'] = "env_prod"
    config = harrymack.load_config('./config.yaml')
    env = config['enviornment']
    assert config[env]['music_root'] == "/music/"
