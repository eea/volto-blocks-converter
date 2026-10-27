import json
from copy import deepcopy

import pytest
from bs4 import BeautifulSoup

from app.blocks2html import (
    convert_blocks_to_html,
    serialize_teaser,
    serialize_teaserGrid,
)
from app.html2blocks import text_to_blocks
from app.html2content import deserialize_teaserGrid
from app.main import Blocks
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


# A teaser that was added but never given a card is left by Volto with a partial
# itemModel - no "@type". serialize_itemModel used to do item_model.pop("@type")
# and raise KeyError, which made the whole /blocks2html request return 500. Plone's
# get_blocks_as_html then raised a bare ValueError and queue_translate swallowed
# it, so the object was silently never translated. Observed on 36 published
# Climate-ADAPT pages.
PARTIAL_ITEM_MODEL = {"hasDate": False, "styles": {"align": "left"}}


def test_partial_item_model_does_not_raise():
    block = {
        "@type": "teaser",
        "title": "How to use Climate-ADAPT",
        "itemModel": dict(PARTIAL_ITEM_MODEL),
    }
    text = elements_to_text(serialize_teaser(block))

    assert 'data-block-type="teaser"' in text
    # no model div is emitted for a model we cannot type
    assert "data-model-type" not in text


def test_partial_item_model_round_trips_verbatim():
    grid = {
        "@type": "gridBlock",
        "blocks": {
            "t1": {
                "@type": "teaser",
                "title": "How to use Climate-ADAPT",
                "itemModel": dict(PARTIAL_ITEM_MODEL),
            }
        },
        "blocks_layout": {"items": ["t1"]},
    }
    data = Blocks(blocks={"g1": grid}, blocks_layout={"items": ["g1"]})

    html = convert_blocks_to_html(data)
    assert 'data-block-type="teaser"' in html

    blocks = text_to_blocks(html)
    (_, grid_block) = blocks[0]

    # block uids are regenerated on the way back, so match by content
    teasers = [b for b in grid_block["blocks"].values() if b.get("@type") == "teaser"]
    assert len(teasers) == 1
    teaser = teasers[0]

    # preserved exactly - no invented @type, no dropped keys
    assert teaser["itemModel"] == PARTIAL_ITEM_MODEL
    assert teaser["title"] == "How to use Climate-ADAPT"


def test_configured_item_model_still_gets_a_model_div():
    block = {
        "@type": "teaser",
        "title": "Newsletter",
        "itemModel": {"@type": "card", "hasDate": False},
    }
    text = elements_to_text(serialize_teaser(block))

    assert 'data-model-type="card"' in text
