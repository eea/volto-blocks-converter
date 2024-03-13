# import json
import logging
from dataclasses import dataclass
from typing import Any, Dict

from litestar import Litestar, get, post  # Request,
from litestar.status_codes import HTTP_200_OK

from .blocks import text_to_blocks
from .blocks2html import convert_blocks_to_html
from .html2content import convert_html_to_content
from .html2slate import text_to_slate
from .tests import run

logger = logging.getLogger()


@dataclass
class HtmlData:
    html: str


@dataclass
class Blocks:
    blocks: Any
    blocks_layout: Any


@dataclass
class Response:
    data: Any


@get(path="/healthcheck")
async def health_check() -> str:
    return "healthy"


@get(path="/test")
async def run_tests() -> str:
    run()
    return "healthy"


@post(path="/html")
async def html(data: HtmlData) -> Dict:
    html = data.html
    return {"data": text_to_slate(html)}


@post(path="/toblocks", status_code=HTTP_200_OK)
async def toblocks(data: HtmlData) -> Dict:
    html: str = data.html
    data = text_to_blocks(html)

    # logger.info("Blocks: \n%s", json.dumps(data, indent=2))
    return {"data": data}


@post(path="/blocks2html", status_code=HTTP_200_OK)
async def handle_block2html(data: Blocks) -> Dict:
    html = convert_blocks_to_html(data)

    # logger.info("HTML: \n%s", html)
    return {"html": html}


@post(path="/html2content", status_code=HTTP_200_OK)
async def handle_html2content(data: HtmlData) -> Dict:
    html = data.html
    data = convert_html_to_content(html)

    # logger.info("Data: \n%s", json.dumps(data, indent=2))
    return {"data": data}


app = Litestar(
    route_handlers=[
        health_check,
        html,
        toblocks,
        handle_block2html,
        handle_html2content,
    ],
    debug=True,
)
