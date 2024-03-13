from .utils import nanoid
from copy import deepcopy
from lxml.html import document_fromstring
from .slate2html import slate_to_html
import json
import logging
from collections import deque
from uuid import uuid4

from bs4 import BeautifulSoup

from .html2slate import text_to_slate

logger = logging.getLogger()


def make_uid():
    return str(uuid4())


def make_tab_block(tabs):
    block_ids = [make_uid() for _ in tabs]
    blocks = {}

    for i, tab in enumerate(tabs):
        blocks[block_ids[i]] = {
            "@type": "tab",
            "title": tab["title"],
            "blocks": dict(tab["content"]),
            "blocks_layout": {"items": [b[0] for b in tab["content"]]},
        }

    data = {
        "@type": "tabs_block",
        "data": {"blocks": blocks, "blocks_layout": {"items": block_ids}},
    }
    return data


def make_accordion_block(panels):
    block_ids = [make_uid() for _ in panels]

    blocks = {}

    for i, panel in enumerate(panels):
        blocks[block_ids[i]] = {
            "@type": "accordionPanel",
            "title": panel["title"],
            "blocks": dict(panel["content"]),
            "blocks_layout": {"items": [b[0] for b in panel["content"]]},
        }

    data = {
        "@type": "accordion",
        "collapsed": "true",
        "non_exclusive": "true",
        "right_arrows": "true",
        "styles": {},
        "data": {"blocks": blocks, "blocks_layout": {"items": block_ids}},
    }
    return data


def block_tag(data, soup_or_tag):
    if soup_or_tag.parent:
        soup = list(soup_or_tag.parents)[-1]
    else:
        soup = soup_or_tag

    element = soup.new_tag("voltoblock")
    element["data-voltoblock"] = json.dumps(data)

    return element


def convert_tabs(soup):
    nav_tabs = soup.find_all("ul", attrs={"class": "nav nav-tabs"})

    if not nav_tabs:
        return

    for ul in nav_tabs:
        div_content = ul.find_next_sibling("div", class_="tab-content")
        tab_structure = []
        tabs = ul.find_all("li")

        for li in tabs:
            if li.a is None:
                # broken html generated
                continue

            tab_id = li.a.attrs["href"].replace("#", "")
            title = li.a.text

            tab_blocks = text_to_blocks(
                div_content.find_all("div", {"id": tab_id}, limit=1)[0]
            )

            tab_structure.append(
                {"id": tab_id, "title": title, "content": tab_blocks})

        data = make_tab_block(tab_structure)
        ul.replace_with(block_tag(data, soup))  # no need to decompose
        div_content.decompose()


def convert_iframe(soup):
    # TODO: also apply the height
    iframes = soup.find_all("iframe")

    for tag in iframes:
        data = {"@type": "maps", "url": tag.attrs["src"]}
        tag.replace_with(block_tag(data, soup))


def convert_button(soup):
    buttons = soup.find_all("a", attrs={"class": "bluebutton"})

    for button in buttons:
        target = button.attrs["target"] if button.has_attr(
            "target") else "_self"

        data = {
            "@type": "callToActionBlock",
            "text": button.text,
            "href": button.attrs["href"],
            "target": target,
            "styles": {"icon": "ri-share-line", "theme": "primary", "align": "left"},
        }

        parent = button.find_parent("p")
        if parent:
            parent.replace_with(block_tag(data, soup))
        else:
            button.replace_with(block_tag(data, soup))


def convert_read_more(soup):
    links = soup.find_all("a", attrs={"class": "accordion-toggle"})

    new_data = {
        "@type": "readMoreBlock",
        "height": "50vh",
        "label_closed": "Read more",
        "label_opened": "Read less",
        "label_position": "right",
    }

    for tag in links:
        if tag.text == "Read more":
            tag.replace_with(block_tag(new_data, soup))


def convert_accordion(soup):
    accordions = soup.find_all("div", attrs={"class": "panel-group"})

    # accordion_titles = soup.find_all("div", attrs={"class": "panel-heading"})
    # if accordion_titles and not accordions:
    #     for node in accordion_titles:
    #         node.decompose()
    #     return

    if not accordions:
        # handle single accordion, aka "Read more", which we remove
        return

    for div in accordions:
        panels = div.find_all("div", attrs={"class": "panel"})

        panels_structure = []
        for panel in panels:
            panel_id = (
                panel.find_all("div", attrs={"class": "panel-heading"})[0]
                .attrs["id"]
                .split("-heading")[0]
            )
            panel_title = panel.find_all(
                "h4", attrs={"class": "panel-title"})[0].text

            _panel_bodies = panel.find_all(
                "div", attrs={"class": "panel-body"})

            if panel_title == "Read more":
                return

            blocks = []
            for panel_body in _panel_bodies:
                blocks.extend(text_to_blocks(panel_body))

            panels_structure.append(
                {"id": panel_id, "title": panel_title, "content": blocks}
            )

        data = make_accordion_block(panels_structure)
        div.replace_with(block_tag(data, soup))


preprocessors = [
    convert_tabs,
    convert_iframe,
    convert_accordion,
    convert_read_more,
    convert_button,
]


def text_to_blocks(text_or_element):
    if text_or_element and not isinstance(text_or_element, str):
        soup = text_or_element
    else:
        soup = BeautifulSoup(str(text_or_element), "html.parser")

    for proc in preprocessors:
        proc(soup)

    new_text = str(soup)

    slate = text_to_slate(new_text)

    blocks = convert_slate_to_blocks(slate)
    return blocks


def convert_slate_to_blocks(slate):
    blocks = []
    for paragraph in slate:
        maybe_block = convert_block(paragraph, parent=None)

        if not isinstance(maybe_block, list):
            blocks.append([make_uid(), maybe_block])
        else:
            blocks.extend(maybe_block)

    return blocks


def iterate_children(value, front=False):
    """iterate_children.

    :param value:
    """
    queue = deque([(child, None) for child in value])

    while queue:
        if not front:
            (child, parent) = queue.pop()
        else:
            (child, parent) = queue.popleft()

        yield (child, parent)

        if isinstance(child, dict) and child.get("children"):
            queue.extend([(ch, child) for ch in (child["children"])])


def has_volto_blocks(children):
    for child, _ in iterate_children(children):
        if isinstance(child, dict) and child.get("type") == "voltoblock":
            return True


def table_to_columns_block(node):
    blocks = []

    def row_to_columns_block(row):
        children = row["children"]
        columns_storage = {
            "blocks": {},  # these are the columns
            "blocks_layout": {"items": []},
        }
        nr = int(12 / len(children))

        blockdata = {
            "@type": "columnsBlock",
            "data": columns_storage,  # stores columns as "blocks"
            "gridSize": 12,
            "gridCols": [COL_MAPPING[nr] for _ in children],
        }

        for cell in children:
            colblocks = {}
            colblocks_layout = []

            for uid, block in convert_slate_to_blocks(cell["children"]):
                colblocks[uid] = block
                colblocks_layout.append(uid)

            uid = make_uid()
            columns_storage["blocks"][uid] = {
                "blocks": colblocks,
                "blocks_layout": {"items": colblocks_layout},
            }
            columns_storage["blocks_layout"]["items"].append(uid)

        blocks.append([make_uid(), blockdata])

    def body_to_columns(body):
        for child in body["children"]:
            row_to_columns_block(child)

    for child in node["children"]:
        if child.get("type") == "tbody":
            body_to_columns(child)
            continue

        if child.get("type") == "tr":
            row_to_columns_block(child)
            continue

    return blocks


COL_MAPPING = {
    2: "oneThird",
    3: "oneThird",
    4: "oneThird",
    5: "oneThird",
    6: "halfWidth",
    7: "twoThirds",
    8: "twoThirds",
    9: "twoThirds",
    10: "twoThirds",
    12: "full",
}


def table_to_table_block(node, plaintext):
    block = {"@type": "slateTable",
             "table": {"rows": []}, "plaintext": plaintext}
    islisting = "listing" in node.get("class", [])
    if islisting:
        block["table"]["striped"] = True
    tbody = None
    thead = None

    for child in node["children"]:
        if child["type"] == "tbody":
            tbody = child
        elif child["type"] == "thead":
            thead = child

    for theadrow in (thead or {}).get("children", []):
        row = {"cells": [], "key": nanoid()}
        block["table"]["rows"].append(row)

        for child in theadrow.get("children", []):
            cell = {"key": nanoid()}
            cell["value"] = child["children"]
            cell["type"] = "header"
            row["cells"].append(cell)

    for tbodyrow in (tbody or {}).get("children", []):
        row = {"cells": [], "key": nanoid()}
        block["table"]["rows"].append(row)

        for child in tbodyrow.get("children", []):
            cell = {"key": nanoid()}
            cell["value"] = child["children"]
            cell["type"] = "data"
            row["cells"].append(cell)

    return block


def convert_volto_block(block, node, plaintext, parent=None):
    # if there's any image in the paragraph, it will be replaced only by the
    # image block. This needs to be treated carefully, if we have inline aligned
    # images

    node_type = node.get("type")

    if node_type == "voltoblock":
        return node["data"]

    elif node_type == "table":  # don't extract anything from tables (yet)
        if has_volto_blocks(node["children"]):
            return table_to_columns_block(node)

        return table_to_table_block(node, plaintext)

    elif node_type == "img":
        if (
            block is node or plaintext == ""
        ):  # convert to a volto block only on top level element or if the block has no text
            res = {
                "@type": "image",
                "url": node.get("url", "").split("/@@images", 1)[0],
                "align": node.get("align", ""),
                "title": node.get("title", ""),
                "alt": node.get("alt", ""),
            }

            if isinstance(parent, list):
                __import__("pdb").set_trace()
            if parent and parent.get("type") == "link":
                href = parent.get("data", {}).get("url", "")
                if href.startswith("resolveuid"):
                    href = f"../{href}"
                if "resolveuid" in href:
                    href = [
                        {
                            "@id": href,
                        }
                    ]
                res["href"] = href

            return res

    elif node_type == "video":
        return {
            "@type": "nextCloudVideo",
            "url": node.get("src", ""),
            "title": node.get("data-matomo-title", ""),
            "alt": node.get("alt", ""),
        }


def extract_text(slate_node):
    html = slate_to_html([slate_node])
    if not (html and html.strip()):
        return ""
    try:
        # throws error on VOLTOBLOCKS
        e = document_fromstring(html)
        text = e.text_content()
        return text
    except AttributeError:
        return ""


def convert_block(slate_node, parent=None):
    # TODO: do the plaintext

    plaintext = extract_text(deepcopy(slate_node))
    volto_block = convert_volto_block(
        slate_node, slate_node, plaintext, parent=parent)
    if volto_block:
        return volto_block

    if slate_node.get("children"):
        children = iterate_children(slate_node["children"])
        for child, parent in children:
            # print('child', child)

            volto_block = convert_volto_block(
                slate_node, child, plaintext, parent=parent
            )

            if volto_block:
                return volto_block

    return {"@type": "slate", "value": [slate_node], "plaintext": plaintext}
