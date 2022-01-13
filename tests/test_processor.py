from awsdsc.processor import ResourceTypeProcessor


class MockResourceTypeProcessor(ResourceTypeProcessor):
    def __init__(self):
        pass

    def _init_client(self):
        pass

    def _describe(self, key_values: dict[str, str]):
        return {}

    def _list_candidates(self, typ: str):
        return []

    def _list_types(self):
        return []


processor = MockResourceTypeProcessor()


def test_exec_with_next_token():
    results = processor._exec_with_next_token(
        {},
        _do_with_next_token,
        lambda r: r["Results"],
    )
    assert results == [f"result{n}" for n in range(1, 11)]


def _do_with_next_token(NextToken: str = None):
    new_next_token_num = int(NextToken) + 1 if NextToken else 1
    results: dict = {"Results": [f"result{new_next_token_num}"]}
    if new_next_token_num < 10:
        results["NextToken"] = str(new_next_token_num)
    return results


def test_json_loads_recursively():
    data = {
        "list_key": [
            "%7B%22key%22%3A%22value%22%7D",
        ],
        "dict_key": {
            "key": "%7B%22key%22%3A%22value%22%7D",
        },
    }
    expected = {
        "list_key": [
            {"key": "value"},
        ],
        "dict_key": {
            "key": {"key": "value"},
        },
    }

    result = processor._json_loads_recursively(data)
    assert result == expected


def test_map_nested_dicts():
    data = {
        "list_key": [
            1,
            2,
        ],
        "dict_key": {
            "key": {"key": 3},
        },
    }
    expected = {
        "list_key": [
            2,
            3,
        ],
        "dict_key": {
            "key": {"key": 4},
        },
    }

    result = processor._map_nested_dicts(data, lambda n: n + 1)
    assert result == expected


def test_json_loads():
    data = "%7B%22key%22%3A%22value%22%7D"
    expected = {"key": "value"}
    assert processor._json_loads_without_error(data) == expected
