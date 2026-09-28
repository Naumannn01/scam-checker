def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_check_creates_entry_and_queues_task(client, mock_task):
    r = client.post("/check", json={"input_value": "http://paytm-refund-verify.tk"})
    assert r.status_code == 200
    data = r.json()
    assert data["input_type"] == "url"
    assert data["verdict"] == "unknown"
    mock_task.delay.assert_called_once_with(data["id"], None)


def test_check_dedups_repeat_input(client, mock_task):
    first = client.post("/check", json={"input_value": "google.com"}).json()
    second = client.post("/check", json={"input_value": "google.com"}).json()
    assert first["id"] == second["id"]
    assert mock_task.delay.call_count == 1


def test_upi_without_message_does_not_queue_task(client, mock_task):
    r = client.post("/check", json={"input_value": "scammer@ybl"})
    assert r.json()["input_type"] == "upi"
    mock_task.delay.assert_not_called()

def test_check_rejects_garbage_input(client, mock_task):
    r = client.post("/check", json={"input_value": "hello world"})
    assert r.status_code == 422
    mock_task.delay.assert_not_called()


def test_check_rejects_blank_input(client):
    assert client.post("/check", json={"input_value": "   "}).status_code == 422


def test_check_strips_whitespace_before_storing(client):
    r = client.post("/check", json={"input_value": "  google.com  "})
    assert r.status_code == 200
    assert r.json()["input_value"] == "google.com"