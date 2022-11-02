# import pytest
# from loguru import logger
# from _pytest.logging import LogCaptureFixture
# import main
# import os
# from pathlib import Path
# from myclasses import ID3, Source, Track

# def test_import_track_data_file_exists(correct_csv):
#     tracks = main.import_from_csv(correct_csv)
#     assert type(tracks) is list
#     assert len(tracks) == 10

# def test_import_track_data_file_does_not_exist(caplog, config):
#     with pytest.raises(FileNotFoundError, match="^File*"):
#         main.load_track_data("./tests/does not exist.csv")
#     assert "No CSV file" in caplog.text

# def test_import_track_data_file_empty(empty_csv, caplog, config):
#     with pytest.raises(main.EmptyListError, match="^File*"):
#         main.load_track_data(empty_csv)
#     assert "No records found in CSV file" in caplog.text

# # ! This test randomly fails.  I belive it depends on what field is removed from the csv.  Do I even need to test this?
# # ! When could this occur and what could i do besides exit anyway?
# # def test_import_track_data_file_malformed(malformed_csv, caplog, config):
# #    with pytest.raises(KeyError, match=".+does not exist.+"):
# #        harrymack.load_track_data(malformed_csv, config)
# #    assert "does not exist" in caplog.text

# # def test_create_tracks(data_row, config, source_object, id3_object):
# #     track = Track(data_row, config, source_object, id3_object)
# #     assert track.source.base_name == "NPdKxsSE5JQ"
# #     assert track.source.get_full_path() == os.path.join(config[config['enviornment']]['download_directory'], track.source.base_name + ' (20200826).mp3')
# #     assert track.artist == "Harry Mack"
# #     assert track.album == "Omegle Bars 1"
# #     assert track.track_number == "1"
# #     assert track.track_title == "OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons"
# #     assert track.filename == "1 - OB 1.1 Florescent Adolescence, Rainbow, Wetherspoons.mp3"
# #     assert track.start_time == "00:00:55"
# #     assert track.end_time == "00:04:32"
# #     assert track.url == "https://www.youtube.com/watch?v=NPdKxsSE5JQ"
# #     assert track.beatname == "Test Beatname"
# #     assert track.producer == "Homage"
# #     assert track.destination_path == os.path.join(config[config['enviornment']]['music_root'], track.album)
# #     assert track.destination_full_path == os.path.join(track.destination_path, track.filename)


# def test_env_dev_variables(config):
#     # * should be running as development profile.
#     env = config['enviornment']
#     assert config[env]['music_root'] == "./media/musicroot/"

# # def test_env_prod_variables(config, caplog):
#     # since the tests are running on the dev server, the prod paths won't be valid
# #   orig_env = os.environ['ENVIORNMENT']
# #    os.environ['ENVIORNMENT'] = "env_prod"
#     # with pytest.raises(KeyError, match=".+directory found.+"):
#     #    harrymack.load_config('./config.yaml')
#     # assert "directory found" in caplog.text
#     # return the enviornment to its original state
# #    os.environ['ENVIORNMENT'] = orig_env


# def test_process_with_ffmpeg_destination_exists_overwrite_false(track_object):
#     process = main.process_with_ffmpeg(track_object, False)
#     assert not process

# def test_process_with_ffmpeg_destination_exists_overwrite_true(track_object):
#     process = main.process_with_ffmpeg(track_object, True)
#     assert process

# # TODO: Need to do a use tmp_path fixture for this
# def test_process_with_ffmpeg_destination_does_not_exist(track_object):
#     # * simulates the situation where the destination file does not exist
#     track_object.destination_full_path = '/nonsense_directory/'
#     process = main.process_with_ffmpeg(track_object)
#     assert process

# # TODO: Need to do a use tmp_path fixture for this
# def test_download_source_source_exists_overwrite_false(track_object):
#     test_mp3 = './media/test/test.mp3'
#     Path(test_mp3).touch()
#     track_object.source.base_name = 'test'
#     track_object.source.path = './media/test/'
#     download = main.download_source_file(track_object, False)
#     assert not download
#     if os.path.exists(test_mp3):
#         os.remove(test_mp3)

# # TODO: Need to do a use tmp_path fixture for this
# def test_download_source_source_exists_overwrite_true(track_object):
#     test_mp3 = './media/test/test.mp3'
#     Path(test_mp3).touch()
#     track_object.source.base_name = 'test'
#     track_object.source.path = './media/test/'
#     download = main.download_source_file(track_object, True)
#     assert download
#     if os.path.exists(test_mp3):
#         os.remove(test_mp3)

# # TODO: Need to do a use tmp_path fixture for this
# def test_download_source_source_does_not_exist(track_object):
#     # * simulates the situation where the destination file does not exist
#     track_object.source.path = '/nonsense_directory/'
#     download = main.download_source_file(track_object)
#     assert download

# # def test_logging(caplog):
#     # assert harrymack.some_func(-1) == 2
#     # assert "Error:" in caplog.text
# # def test_correct_config_file_load():
# #    assert 1 == 2


# def test_create_config_from_dict(tmp_path, default_config_data):
#     tmp_config_path = Path.joinpath(tmp_path, 'config.yaml')
#     main.create_yaml_from_dict(default_config_data, tmp_config_path)
#     with open(tmp_config_path, 'r') as f:
#         lines = f.readlines()
#         assert 'app_name: harrymack' in lines[0]

# # def test_config_file_create():
# #    assert 1 == 2

# # def test_incorrect_config_file_load():
# #    assert 1 == 2

# # def test_empty_track():
# #    source_info = {}
# #    track = harrymack.Track(source_info)
# #    assert track.artist == ""
