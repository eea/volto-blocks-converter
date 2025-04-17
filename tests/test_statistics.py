import json
from bs4 import BeautifulSoup
from copy import deepcopy

import pytest

from app.slate2html import elements_to_text
from app.blocks2html import serialize_statistics_block
from app.html2content import deserialize_statistic_block


@pytest.fixture
def json_payload():
    with open("tests/fixtures/statistic_block.json") as f:
        payload = json.load(f)
    return payload


@pytest.fixture
def html_payload():
    with open("tests/fixtures/statistic_block.html") as f:
        payload = f.read()
    return payload


def test_it(json_payload, html_payload):
    payload = deepcopy(json_payload)
    fragments = serialize_statistics_block(payload)
    text = elements_to_text(fragments)
    assert 'data-block-type="statistic_block"' in text

    tree = BeautifulSoup(text, "html.parser")
    ediv = tree.find("div")
    (uid, data) = deserialize_statistic_block(ediv)

    assert data == json_payload

    print(data)
    print(text)
    # assert out == html_payload
