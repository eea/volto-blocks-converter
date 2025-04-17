import json
from copy import deepcopy

import pytest
from bs4 import BeautifulSoup

from app.blocks2html import serialize_teaserGrid
from app.html2content import deserialize_teaserGrid
from app.slate2html import elements_to_text


@pytest.fixture
def json_payload():
    with open("tests/fixtures/teaser.json") as f:
        payload = json.load(f)
    return payload


@pytest.fixture
def html_payload():
    with open("tests/fixtures/teaser.html") as f:
        payload = f.read()
    return payload


def test_it(json_payload, html_payload):
    payload = deepcopy(json_payload)
    fragments = serialize_teaserGrid(payload)
    text = elements_to_text(fragments)
    assert 'data-block-type="teaserGrid"' in text

    tree = BeautifulSoup(text, "html.parser")
    ediv = tree.find("div")
    (uid, data) = deserialize_teaserGrid(ediv)

    assert data == json_payload

    print(data)
    print(text)
    # assert out == html_payload
