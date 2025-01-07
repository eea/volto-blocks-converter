import json

import pytest

from app.blocks2html import convert_blocks_to_html
from app.main import Blocks


@pytest.fixture
def json_payload():
    with open("tests/payload-t1.json") as f:
        payload = json.load(f)
    return payload


def test_it(json_payload):
    data = Blocks(**json_payload)
    html = convert_blocks_to_html(data)
    assert """<p data-slate-data='{"styleName": "text-justify"}'""" in html
