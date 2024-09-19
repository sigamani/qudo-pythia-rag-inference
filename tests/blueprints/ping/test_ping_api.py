
def test_ping(client):
    response = client.get('/v1/ping/')
    assert response.status_code == 200
