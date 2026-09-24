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
