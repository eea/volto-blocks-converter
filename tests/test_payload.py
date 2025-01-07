import json
import logging

import requests

logger = logging.getLogger("")

SLATE_CONVERTER = "http://localhost:8000/html"
BLOCKS_CONVERTER = "http://localhost:8000/blocks2html"
CONTENT_CONVERTER = "http://localhost:8000/html2content"


def get_content_from_html(html, language=None):
    """Given an HTML string, converts it to Plone content data"""

    data = {"html": html, "language": language}
    headers = {"Content-type": "application/json",
               "Accept": "application/json"}

    req = requests.post(CONTENT_CONVERTER,
                        data=json.dumps(data), headers=headers)
    if req.status_code != 200:
        logger.debug(req.text)
        raise ValueError

    data = req.json()["data"]
    logger.info("Data from converter: %s", data)

    # because the blocks deserializer returns {blocks, blocks_layout} and is saved in "blocks", we need to fix it
    if data.get("blocks"):
        blockdata = data["blocks"]
        data["blocks_layout"] = blockdata["blocks_layout"]
        data["blocks"] = blockdata["blocks"]

    logger.info("Data with tiles decrypted %s", data)

    return data


if __name__ == "__main__":
    with open("payload.html") as f:
        payload = f.read()

    data = get_content_from_html(payload, "de")
    print(data)
