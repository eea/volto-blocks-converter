""" Convert html produced by blocks2html
"""

import json
from bs4 import BeautifulSoup

from .html2slate import HTML2Slate
from .blocks import text_to_blocks
from .utils import nanoid
from uuid import uuid4

import os

DEBUG = os.environ.get("DEBUG", False) and "TTT----" or ""


def get_elements(node):
    for child in node.children:
        if child.name:
            yield child


def deserialize_layout_block(fragment):
    rawdata = fragment.attrs["data-volto-block"]
    data = json.loads(rawdata)
    data["@type"] = fragment.attrs["data-block-type"]

    colblockdata = {"blocks_layout": {"items": []}, "blocks": {}}

    for column in get_elements(fragment):
        rawcolsettings = column.attrs.get("data-volto-column-data", "{}")
        colsettings = json.loads(rawcolsettings)
        coldata = deserialize_blocks(column)
        coldata.update(colsettings)
        coluid = str(uuid4())
        colblockdata["blocks"][coluid] = coldata
        colblockdata["blocks_layout"]["items"].append(coluid)

    if "data" not in data:
        data["data"] = {}
    data["data"].update(colblockdata)
    uid = str(uuid4())

    return [uid, data]


def deserialize_teaserGrid(fragment):
    rawdata = fragment.attrs["data-volto-block"]
    data = json.loads(rawdata)
    data["@type"] = fragment.attrs["data-block-type"]
    columns = []
    for colel in fragment.children:
        blockel = next(colel.children)
        block = deserialize_block(blockel)[1]
        columns.append(block)

    data["columns"] = columns

    uid = str(uuid4())
    return [uid, data]


def deserialize_title_block(fragment):
    rawdata = fragment.attrs["data-volto-block"]
    data = json.loads(rawdata)
    data["@type"] = fragment.attrs["data-block-type"]

    for ediv in fragment.children:
        name = ediv.attrs["data-fieldname"]
        if name != "info":
            data[name] = f"{DEBUG}{ediv.text}"
        else:
            data["info"] = [
                {"@id": el.attrs["id"], "description": f"{DEBUG}{el.text}"}
                for el in ediv.children
            ]

    uid = str(uuid4())
    return [uid, data]


def deserialize_layout_block_with_titles(fragment):
    rawdata = fragment.attrs["data-volto-block"]
    data = json.loads(rawdata)
    data["@type"] = fragment.attrs["data-block-type"]

    colblockdata = {"blocks_layout": {"items": []}, "blocks": {}}

    for column in get_elements(fragment):
        metaelement = next(column.children)
        metaelement.extract()
        metadata = json.loads(metaelement.attrs["data-volto-column"])
        for ediv in metaelement.children:
            name = ediv.attrs["data-fieldname"]
            metadata[name] = f"{DEBUG}{ediv.text}"

        coldata = deserialize_blocks(column)
        coldata.update(metadata)
        coluid = str(uuid4())
        colblockdata["blocks"][coluid] = coldata
        colblockdata["blocks_layout"]["items"].append(coluid)

    if "data" not in data:
        data["data"] = {}
    data["data"].update(colblockdata)
    uid = str(uuid4())

    return [uid, data]


def deserialize_group_block(fragment):
    rawdata = fragment.attrs["data-volto-block"]
    data = json.loads(rawdata)
    data["@type"] = fragment.attrs["data-block-type"]
    data["data"] = deserialize_blocks(fragment)
    uid = str(uuid4())
    return [uid, data]


def deserialize_slate_table_block(fragment):
    rawdata = fragment.attrs["data-volto-block"]
    data = json.loads(rawdata)

    data["rows"] = []

    for erow in fragment.css.select("table tr"):
        row = {"cells": [], "key": nanoid()}
        data["rows"].append(row)
        for ecell in get_elements(erow):
            cell = {"key": nanoid()}
            cell["value"] = HTML2Slate().from_elements(ecell)

            if ecell.name == "th":
                cell["type"] = "header"
            elif ecell.name == "td":
                cell["type"] = "data"
            else:
                raise ValueError

            row["cells"].append(cell)

    block = {"@type": "slateTable", "table": data}
    return [str(uuid4()), block]


def generic_slateblock_converter(fieldname):
    def converter(fragment):
        rawdata = fragment.attrs["data-volto-block"]
        _type = fragment.attrs["data-block-type"]
        data = json.loads(rawdata)
        data["@type"] = _type

        elements = list(get_elements(fragment))
        slate_value = HTML2Slate().from_elements(elements)

        visit_slate_nodes(slate_value, debug_translation)
        data[fieldname] = slate_value

        uid = str(uuid4())

        return [uid, data]

    return converter


def generic_block_converter(fragment):
    rawdata = fragment.attrs["data-volto-block"]
    data = json.loads(rawdata)
    data["@type"] = fragment.attrs["data-block-type"]

    for ediv in fragment.children:
        name = ediv.attrs["data-fieldname"]
        data[name] = f"{DEBUG}{ediv.text}"

    uid = str(uuid4())
    return [uid, data]


converters = {
    "columnsBlock": deserialize_layout_block,
    "tabs_block": deserialize_layout_block_with_titles,
    # "quote": deserialize_quote_block,
    "quote": generic_slateblock_converter("value"),
    "item": generic_slateblock_converter("description"),
    "slateTable": deserialize_slate_table_block,
    "group": deserialize_group_block,
    "teaserGrid": deserialize_teaserGrid,
    # generics
    "nextCloudVideo": generic_block_converter,
    "title": deserialize_title_block,
    "layoutSettings": generic_block_converter,
    "callToActionBlock": generic_block_converter,
    "searchlib": generic_block_converter,
    "teaser": generic_block_converter,
}


def visit_slate_nodes(slate_value, visitor):
    for node in slate_value:
        visitor(node)
        if isinstance(node, dict) and node.get("children"):
            visit_slate_nodes(node["children"], visitor)


def debug_translation(node):
    # just a debugging helper to understand which fields will be translated
    if isinstance(node, dict) and node.get("text"):
        node["text"] = f"{DEBUG}{node['text']}"


def deserialize_block(fragment):
    """Convert a lxml fragment to a Volto block. This assumes that the HTML
    structure has been previously exported with block2html"""
    _type = fragment.attrs.get("data-block-type")
    if _type:
        if _type not in converters:
            print(f"Block deserializer needed: {_type}. Using default.")
            return generic_block_converter(fragment)
        else:
            deserializer = converters[_type]
            return deserializer(fragment)

    # fallback to slate deserializer
    blocks = text_to_blocks(fragment)
    assert len(blocks) == 1
    [uid, block] = blocks[0]

    if block.get("@type") == "slate":
        slate_value = block["value"]
        visit_slate_nodes(slate_value, debug_translation)

    return [uid, block]


def deserialize_blocks(element):
    """Converts a <div> with serialized (html) blocks inside to Volto blocks"""

    blocks = {}
    items = []

    for f in get_elements(element):
        pair = deserialize_block(f)
        if len(pair) != 2:
            continue  # converter not created yet
        uid, block = pair
        blocks[uid] = block
        items.append(uid)

    return {"blocks": blocks, "blocks_layout": {"items": items}}


def convert_html_to_content(text: str):
    data = {}
    tree = BeautifulSoup(text, "html.parser")

    body = tree.find("body")
    if body is None:
        return data

    fragments = body.find_all("div", recursive=False)

    for f in fragments:
        if not hasattr(f, "attrs"):
            continue
        field = f.attrs.get("data-field")
        if not field:
            continue

        if field == "blocks":
            data[field] = deserialize_blocks(f)
        else:
            data[field] = f.text or ""

    return data
