import pytest
from app.html2content import convert_html_to_content

# HTML matching the serialization of a hero block with nested blocks
HERO_HTML = """
<html><body>
<div data-field="blocks">
<div data-block-type="hero" data-volto-block="{}">
    <div data-fieldname="buttonLabel">Click me</div>
    <div data-fieldname="copyright">© 2026</div>
    <div data-volto-section="blocks">
        <div data-block-type="slate" data-volto-block="{}"><p>Nested text</p></div>
    </div>
</div>
</div>
</body></html>
"""

def test_hero_html2content():
    # This should crash with KeyError: 'data-fieldname' if not handled
    data = convert_html_to_content(HERO_HTML)
    
    blocks = data['blocks']['blocks']
    # If successful, we expect to find the hero block
    assert len(blocks) == 1
    uid = list(blocks.keys())[0]
    hero = blocks[uid]
    assert hero['@type'] == 'hero'
    assert hero['buttonLabel'] == 'Click me'
    # And nested blocks
    assert 'data' in hero
    assert 'blocks' in hero['data']
    
    # Verify nested block content
    nested_blocks = hero['data']['blocks']
    assert len(nested_blocks) == 1
    nested_uid = list(nested_blocks.keys())[0]
    nested_block = nested_blocks[nested_uid]
    assert nested_block['@type'] == 'slate'
    # Check if value/plaintext is populated (slate deserialization)
    assert 'value' in nested_block or 'plaintext' in nested_block


def test_grid_html2content():
    # HTML matching the serialization of a grid block with nested teaser
    GRID_HTML = """
    <html><body>
    <div data-field="blocks">
    <div data-block-type="gridBlock" data-volto-block="{}">
        <div data-block-type="teaser" data-volto-block="{}">
            <div data-fieldname="title">Teaser Title</div>
        </div>
    </div>
    </div>
    </body></html>
    """
    
    data = convert_html_to_content(GRID_HTML)
    
    blocks = data['blocks']['blocks']
    assert len(blocks) == 1
    uid = list(blocks.keys())[0]
    grid = blocks[uid]
    assert grid['@type'] == 'gridBlock'
    
    assert 'blocks' in grid
    assert len(grid['blocks']) == 1
    teaser_uid = list(grid['blocks'].keys())[0]
    teaser = grid['blocks'][teaser_uid]
    assert teaser['@type'] == 'teaser'
    assert teaser['title'] == 'Teaser Title'
