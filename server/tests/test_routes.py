"""
This module contains unit tests for the routes in the Toniebox Audio Match application.
The tests cover various endpoints such as /ping, /audiobooks, /songs, /creativetonies, etc.
Each test case verifies the expected behavior of the corresponding route by sending HTTP requests
and asserting the response status code, response body, and other relevant attributes.

The module also includes mock functions and fixtures to simulate network calls and other side effects
that are not desired during testing. These mock functions are used to replace the actual functions
in the application code, ensuring that the tests are isolated and predictable.

Note: The tests are written using the pytest framework.
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from app import Upload
from app import app as application
from dotenv import load_dotenv

load_dotenv("/home/laudanum/projects/toniebox-audio-match/.env")

# Mock the `get_item_from_request` and `g.tonie_api_client.get_tonie_content` functions
# if they involve network calls or other side-effects you don't want in tests.

mock_tonie1 = Mock(id="tonie_1")
mock_tonie2 = Mock(id="tonie_2")

def mock_get_item_from_request(request_data, key, default):
    """
    Mock function to retrieve an item from the request data based on the given key.

    Args:
        request_data (dict): The request data.
        key (str): The key to retrieve the item.
        default: The default value to return if the item is not found.

    Returns:
        The item corresponding to the key in the request data, or the default value if not found.
    """
    if key == "tonie_id":
        if request_data["tonie_id"] == ["invalid_tonie"]:
            return None
        elif request_data["tonie_id"] == ["tonie_1"]:
            return [mock_tonie1]
        elif request_data["tonie_id"] == ["tonie_2"]:
            return [mock_tonie2]
        elif request_data["tonie_id"] == ["tonie_1", "tonie_2"]:
            return [mock_tonie1, mock_tonie2]
    if key == "track_id":
        return request_data["track_id"]
    
@pytest.fixture
def client():
    """
    Fixture that sets up a test client for the application.
    This client can be used to send HTTP requests and test the routes.
    """
    application.config['TESTING'] = True
    with application.test_client() as client:
        yield client

def mock_get_tonie_content(*args, **kwargs):
    """
    Mock function to simulate the response of getting Tonie content.
    
    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    
    Returns:
        dict: A dictionary representing the response with chapters.
            Each chapter is represented by a dictionary with an 'id' key.
    """
    return {"chapters": [{"id": "track_1"}, {"id": "track_2"}]}

def mock_update_tonie_content(*args, **kwargs):
    return None

def test_ping_route(client):
    """
    Test the /ping route.

    This function sends a GET request to the /ping route and asserts that the response
    status code is 200 and the response body is "pong!".

    Args:
        client: The test client for making HTTP requests.

    Returns:
        None
    """
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json == "pong!"

def test_all_audiobooks(client):
    """
    Test case for retrieving all audiobooks.

    Args:
        client: The test client for making HTTP requests.

    Returns:
        None
    """
    response = client.get("/audiobooks")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert "audiobooks" in response.json

def test_all_songs(client):
    """
    Test case for retrieving all songs.

    Args:
        client: The test client for making HTTP requests.

    Returns:
        None
    """
    response = client.get("/songs")
    assert response.status_code == 200
    assert "songs" in response.json

def test_all_creativetonies(client):
    """
    Test case for the '/creativetonies' endpoint.
    """
    response = client.get("/creativetonies")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert "creativetonies" in response.json



def test_tonie_overview_invalid_tonie(client):
    """
    Test case for the '/tonie_overview' route when an invalid tonie ID is provided.
    """
    payload = json.dumps({"tonie_id": ["invalid_tonie"]})
    rv = client.post("/tonie_overview", data=payload, content_type="application/json")
    assert rv.status_code == 400
    assert rv.json["status"] == "failure"
    assert rv.json["message"] == "No matching tonie found"

def test_tonie_overview_valid_tonie(client):
    """
    Test case for validating the tonie overview with a valid tonie ID.

    Args:
        client: The test client for making HTTP requests.

    Returns:
        None
    """
    payload = json.dumps({"tonie_id": ["tonie_1"]})    
    with application.app_context(): 
        with patch('app.get_item_from_request', side_effect=mock_get_item_from_request):
            with patch('toniecloud.client.TonieCloud.get_tonie_content', Mock(return_value="test")):
                rv = client.post("/tonie_overview", data=payload, content_type="application/json")
                assert rv.status_code == 200
                assert rv.json["status"] == "success"
                assert "tracks" in rv.json

def test_delete_track_invalid_tonie(client):
    """
    Test case to verify the behavior of deleting a track from an invalid tonie.

    Args:
        client: The test client for making HTTP requests.

    Returns:
        None

    Raises:
        AssertionError: If the response status code, status, or message do not match the expected values.
    """
    payload = json.dumps({"tonie_id": "invalid_tonie", "track_id": "track_1"})
    rv = client.post("/delete_track", data=payload, content_type="application/json")
    assert rv.status_code == 400
    assert rv.json["status"] == "failure"
    assert rv.json["message"] == "No matching tonie found"

def test_delete_track_multiple_tonies(client):
    """
    Test case for deleting a track from multiple tonies.

    Args:
        client: The test client for making HTTP requests.

    Returns:
        None
    """
    payload = json.dumps({"tonie_id": ["tonie_1", "tonie_2"], "track_id": "track_1"})
    with patch('app.get_item_from_request', side_effect=mock_get_item_from_request):
        rv = client.post("/delete_track", data=payload, content_type="application/json")
        assert rv.status_code == 400
        assert rv.json["status"] == "failure"
        assert rv.json["message"] == "Multiple tonies provided, can only handle one"

def test_delete_track_valid_tonie(client):
    """
    Test case for deleting a track from a valid Tonie.

    Args:
        client: The test client for making HTTP requests.

    Returns:
        None
    """
    payload = json.dumps({"tonie_id": ["tonie_1"], "track_id": [{"id": "track_1"}]})
    with application.app_context(): 
        with patch('app.get_item_from_request', side_effect=mock_get_item_from_request):
            with patch('toniecloud.client.TonieCloud.get_tonie_content', side_effect=mock_get_tonie_content):
                with patch('toniecloud.client.TonieCloud.update_tonie_content', side_effect=mock_update_tonie_content):
                    rv = client.post("/delete_track", data=payload, content_type="application/json")
                    assert rv.status_code == 200
                    assert rv.json["status"] == "success"
                    assert rv.json["tonie_id"] == 'tonie_1'
                    assert rv.json["track_id"] == ["track_1"]

def test_delete_local_track(client):
    """
    Test case for deleting a local track.

    Args:
        client (TestClient): The test client for making requests.

    Returns:
        None
    """
    # Mock os.remove to avoid actually deleting files during the test
    with patch('app.songs_update', return_value=[{"file": "path/to/existing_track.mp3", "file_original": "path/to/existing_track.mp3"}]):
        with patch("os.remove", return_value=None) as mock_remove:
            payload = json.dumps({"file": "path/to/existing_track.mp3"})
            response = client.post("/delete_local_track", data=payload, content_type="application/json")
            assert response.status_code == 200
            assert response.json["status"] == "success"
            mock_remove.assert_called_once()

@patch("yt_dlp.YoutubeDL.download")
def test_download_youtube(mock_download, client):
    """
    Test case for the download_youtube route.

    This test verifies that the route '/download_youtube' can successfully handle a POST request
    with a valid YouTube URL. It checks that the response status code is 200 and the response
    JSON contains a 'status' key with the value 'success'. Additionally, it ensures that the
    'download' method of the 'YoutubeDL' class is called once.

    Parameters:
    - mock_download: A MagicMock object representing the patched 'download' method of 'YoutubeDL'.
    - client: A test client object for making HTTP requests.

    Returns:
    None
    """
    payload = json.dumps({"youtube_url": "https://youtube.com/watch?v=example"})
    response = client.post("/download_youtube", data=payload, content_type="application/json")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    mock_download.assert_called_once()

def test_upload_album_to_tonie_success(client):
    mock_upload = MagicMock(spec=Upload)
    mock_upload.audiobook = "mock_audiobook"
    mock_upload.tonie = "mock_tonie"
    mock_upload.track = None

    mock_api_client = MagicMock()
    mock_api_client.put_album_on_tonie.return_value = True
    with patch('app.get_item_from_request', side_effect=lambda x, y, z: z[0] if y == "tonie_id" else z[1]):
        with patch('app.get_creative_tonies', return_value=["tonie_id_sample", "audiobook_id_sample"]):
            with patch('app.Upload.from_ids', return_value=mock_upload):
                with client.application.app_context():
                    client.application.config['TEST_TONIE_API_CLIENT'] = mock_api_client

                    with patch('app.get_tonie_api', return_value=mock_api_client):
                        
                        payload = json.dumps({"tonie_id": "tonie_id_sample", "audiobook_id": "audiobook_id_sample"})
                        response = client.post("/upload", data=payload, content_type="application/json")
                    
                        assert response.status_code == 201
                        assert response.json["status"] == "success"

def test_upload_album_to_tonie_failure(client):
    payload = json.dumps({"tonie_id": "invalid", "audiobook_id": "invalid"})
    # Mocking the behavior when tonie or audiobook id is not found or invalid
    with patch('app.Upload.from_ids', side_effect=ValueError("Invalid IDs")):
        response = client.post("/upload", data=payload, content_type="application/json")
        assert response.status_code == 400  # Assuming you add a handler for ValueError to respond with 400
