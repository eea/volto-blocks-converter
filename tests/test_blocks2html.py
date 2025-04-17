import json

import pytest

from app.blocks2html import convert_blocks_to_html
from app.html2content import convert_html_to_content
from app.main import Blocks


@pytest.fixture
def json_payload():
    with open("tests/fixtures/payload-t1.json") as f:
        payload = json.load(f)
    return payload


HTML_TPL = """<html><body>
<div data-field="blocks">
%s
</div>
</body></html>"""


def test_it(json_payload):
    data = Blocks(**json_payload)
    html = convert_blocks_to_html(data)

    # with open('tests/out.html', 'w') as f:
    #     f.write(html)

    assert """<p data-slate-data='{"styleName": "text-justify"}'""" in html

    dump = HTML_TPL % html
    content = convert_html_to_content(dump)

    assert content

    # with open('tests/out.json', 'w') as f:
    #     json.dump(content, f)

    # assert json_payload == content['blocks']
