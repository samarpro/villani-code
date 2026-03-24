from app.backoff import next_delay

def test_single_429_has_minimum_backoff():
    assert next_delay([429]) == 0.5
