import json
import pytest
from app.blocks2html import convert_blocks_to_html
from app.html2blocks import text_to_blocks
from app.main import Blocks

@pytest.fixture
def json_payload():
    with open("tests/fixtures/grid_block.json") as f:
        payload = json.load(f)
    return payload

def test_grid_roundtrip(json_payload):
    # Wrap in Blocks structure
    data = Blocks(
        blocks={"uid1": json_payload},
        blocks_layout={"items": ["uid1"]}
    )
    
    # Serialize
    html = convert_blocks_to_html(data)
    
    # Check fields
    assert 'data-block-type="gridBlock"' in html
    
    # Check nested blocks (teasers)
    assert 'data-block-type="teaser"' in html
    assert 'Heat' in html
    assert 'Infectious diseases' in html
    
    # Deserialize
    blocks = text_to_blocks(html)
    
    # Check structure
    assert len(blocks) == 1
    uid, block = blocks[0]
    
    assert block['@type'] == 'gridBlock'
    
    # Check nested blocks reconstruction
    assert 'blocks' in block
    assert len(block['blocks']) == 4
    
    # Verify content of a nested block
    nested_keys = list(block['blocks'].keys())
    first_teaser = block['blocks'][nested_keys[0]]
    assert first_teaser['@type'] == 'teaser'
    # assert first_teaser['title'] == 'Heat' # Order might vary, check if any matches
    
    found_title = False
    for key, val in block['blocks'].items():
        if val.get('title') == 'Heat':
            found_title = True
            # Verify itemModel and callToAction
            assert 'itemModel' in val
            item_model = val['itemModel']
            assert item_model.get('@type') == 'card'
            assert 'callToAction' in item_model
            assert item_model['callToAction'].get('label') == 'Read more'
            break
    assert found_title
