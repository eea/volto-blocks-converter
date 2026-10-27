"""Tests for layout-table detection in html2blocks."""

import json

from app.html2blocks import text_to_blocks


def _blocks_by_type(html):
    result = {}
    for _uid, block in text_to_blocks(html):
        if isinstance(block, dict):
            result.setdefault(block.get("@type"), []).append(block)
    return result


def test_single_row_table_with_image_becomes_columns_block():
    html = (
        "<table><tbody><tr>"
        '<td><p>Some text</p></td>'
        '<td><img src="http://x.test/a.jpg/@@images/x.jpeg" alt="A"></td>'
        "</tr></tbody></table>"
    )

    blocks = _blocks_by_type(html)

    assert "columnsBlock" in blocks
    assert "slateTable" not in blocks

    # the image is extracted into the columns
    raw = json.dumps(blocks["columnsBlock"])
    assert '"@type": "image"' in raw


def test_multi_row_table_with_image_stays_slate_table():
    html = (
        "<table><tbody>"
        '<tr><td><p>a</p></td><td><img src="http://x.test/a.jpg"></td></tr>'
        '<tr><td><p>b</p></td><td><img src="http://x.test/b.jpg"></td></tr>'
        "</tbody></table>"
    )

    blocks = _blocks_by_type(html)

    assert "slateTable" in blocks
    assert "columnsBlock" not in blocks


def test_table_with_header_stays_slate_table():
    html = (
        "<table>"
        "<thead><tr><th>H1</th><th>H2</th></tr></thead>"
        '<tbody><tr><td><p>a</p></td><td><img src="http://x.test/a.jpg"></td></tr></tbody>'
        "</table>"
    )

    blocks = _blocks_by_type(html)

    assert "slateTable" in blocks
    assert "columnsBlock" not in blocks


def test_single_row_table_without_image_stays_slate_table():
    html = (
        "<table><tbody><tr>"
        "<td><p>left</p></td>"
        "<td><p>right</p></td>"
        "</tr></tbody></table>"
    )

    blocks = _blocks_by_type(html)

    assert "slateTable" in blocks
    assert "columnsBlock" not in blocks


def test_images_inside_columns_have_no_float():
    html = (
        "<table><tbody><tr>"
        "<td><p>text</p></td>"
        '<td><img src="http://x.test/a.jpg" style="float: right;"></td>'
        "</tr></tbody></table>"
    )

    blocks = _blocks_by_type(html)

    assert "columnsBlock" in blocks
    raw = json.dumps(blocks["columnsBlock"])
    assert '"@type": "image"' in raw
    # the image fills its column, so the float is cleared
    assert '"align": "right"' not in raw
    assert '"align": ""' in raw


def test_multi_row_layout_table_becomes_one_columns_block():
    """A table marked invisible-grid transposes into one columnsBlock.

    Each table column becomes a single columnsBlock column, collecting its
    cells top to bottom (image above, caption below).
    """
    html = (
        '<table class="invisible-grid"><tbody>'
        '<tr><td><img src="http://x.test/a.jpg" alt="A"></td>'
        '<td><img src="http://x.test/b.jpg" alt="B"></td></tr>'
        "<tr><td><h3>About</h3></td><td><h3>Members</h3></td></tr>"
        "</tbody></table>"
    )

    blocks = _blocks_by_type(html)

    assert "slateTable" not in blocks
    assert len(blocks["columnsBlock"]) == 1

    block = blocks["columnsBlock"][0]
    columns = block["data"]["blocks_layout"]["items"]
    assert len(columns) == 2

    for column_uid in columns:
        column = block["data"]["blocks"][column_uid]
        types = [column["blocks"][uid]["@type"] for uid in column["blocks_layout"]["items"]]
        # each column carries its own image and its own caption
        assert "image" in types
        assert "slate" in types


def test_multi_row_layout_table_with_thirds_grid():
    """Three columns map to the oneThird grid class."""
    html = (
        '<table class="invisible-grid"><tbody>'
        '<tr><td><img src="http://x.test/a.jpg"></td>'
        '<td><img src="http://x.test/b.jpg"></td>'
        '<td><img src="http://x.test/c.jpg"></td></tr>'
        "<tr><td><h3>A</h3></td><td><h3>B</h3></td><td><h3>C</h3></td></tr>"
        "</tbody></table>"
    )

    blocks = _blocks_by_type(html)
    block = blocks["columnsBlock"][0]

    assert len(block["data"]["blocks_layout"]["items"]) == 3
    assert block["gridCols"] == ["oneThird", "oneThird", "oneThird"]
