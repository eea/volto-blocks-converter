""" Convert Volto blocks to a special HTML structure that's suitable for eTranslation.
The main goal is to provide all block translatable text as "tag text" so that it can be processed by eTranslation.
It should also be possible to convert this HTML back to Volto blocks, using the html2content.py module
"""

from copy import deepcopy
import json
from lxml.html import builder as E
from .slate2html import elements_to_text, slate_to_elements


TABLE_CELLS = {"header": E.TH, "data": E.TD}


def serialize_slate(block_data):
    if "value" in block_data:
        return slate_to_elements(block_data["value"])
    else:
        return E.P()


def serialize_slate_table(block_data):
    _type = block_data.pop("@type")
    data = block_data.pop("table")
    rows = data.pop("rows")
    attributes = {
        "data-block-type": _type,
        "data-volto-block": json.dumps(data),
    }
    children = []
    for row in rows:
        ecells = []
        for cell in row["cells"]:
            el = TABLE_CELLS[cell["type"]](*slate_to_elements(cell["value"]))
            ecells.append(el)

        erow = E.TR(*ecells)
        children.append(erow)

    etable = E.TABLE(*children)
    ediv = E.DIV(etable, **attributes)
    return [ediv]


def iterate_blocks(data):
    uids = data["blocks_layout"]["items"]
    blocks = data["blocks"]

    for uid in uids:
        yield (uid, blocks[uid])


def get_blockscontainer_data(data):
    data = deepcopy(data)
    if "blocks" in data:
        del data["blocks"]
    if "blocks_layout" in data:
        del data["blocks_layout"]

    return data


def serialize_layout_block(block_data):
    """Serializes a block that contains other blocks, such as column or tabs"""

    _type = block_data.pop("@type")
    data = {
        "blocks": block_data["data"].pop("blocks"),
        "blocks_layout": block_data["data"].pop("blocks_layout"),
    }
    attributes = {
        "data-block-type": _type,
        "data-volto-block": json.dumps(block_data),
    }

    children = []
    for _, coldata in iterate_blocks(data):
        # if "settings" in coldata:
        #     __import__("pdb").set_trace()
        colelements = []
        for _, block in iterate_blocks(coldata):
            colelements.extend(convert_block_to_elements(block))
        colsettings = get_blockscontainer_data(coldata)
        colattributes = {"data-volto-column-data": json.dumps(colsettings)}
        column = E.DIV(*colelements, **colattributes)
        children.append(column)

    div = E.DIV(*children, **attributes)

    return [div]


def serialize_layout_block_with_titles(block_data):
    """Serializes a block that contains other blocks, such as column or tabs"""

    _type = block_data.pop("@type")
    data = {
        "blocks": block_data["data"].pop("blocks"),
        "blocks_layout": block_data["data"].pop("blocks_layout"),
    }
    attributes = {
        "data-block-type": _type,
        "data-volto-block": json.dumps(block_data),
    }

    children = []
    for _, coldata in iterate_blocks(data):
        colelements = []
        colblocksdata = {
            "blocks": coldata.pop("blocks"),
            "blocks_layout": coldata.pop("blocks_layout"),
        }
        translate_fields = ["title"]
        metatags = [
            E.DIV(coldata.pop(name, ""), **{"data-fieldname": name})
            for name in translate_fields
        ]
        metacol = E.DIV(
            *metatags, **{"data-volto-column": json.dumps(coldata)})

        for _, block in iterate_blocks(colblocksdata):
            colelements.extend(convert_block_to_elements(block))
        column = E.DIV(metacol, *colelements)
        children.append(column)

    div = E.DIV(*children, **attributes)

    return [div]


def generic_block_converter(translate_fields):
    def converter(block_data):
        _type = block_data.pop("@type")

        fv = {}
        for name in translate_fields:
            value = block_data.pop(name, None)
            if value is not None:
                fv[name] = value

        attributes = {
            "data-block-type": _type,
            "data-volto-block": json.dumps(block_data),
        }

        children = [
            E.DIV(fv.get(name, ""), **{"data-fieldname": name})
            for name in translate_fields
        ]
        div = E.DIV(*children, **attributes)
        return [div]

    return converter


def serialize_quote(block_data):
    value = block_data.pop("value")
    _type = block_data.pop("@type")
    attributes = {
        "data-block-type": _type,
        "data-volto-block": json.dumps(block_data),
    }
    children = slate_to_elements(value)
    div = E.DIV(*children, **attributes)
    return [div]


def generic_slate_block(fieldname):
    def convertor(block_data):
        value = block_data.pop(fieldname)
        _type = block_data.pop("@type")
        attributes = {
            "data-block-type": _type,
            "data-volto-block": json.dumps(block_data),
        }
        children = slate_to_elements(value)
        div = E.DIV(*children, **attributes)
        return [div]

    return convertor


def serialize_image(block_data):
    # print("img", block_data)
    attributes = {
        "src": block_data["url"],
        "data-volto-block": json.dumps(block_data),
    }
    return [E.IMG(**attributes)]


def serialize_group_block(block_data):
    _type = block_data.pop("@type")
    data = block_data.pop("data")
    attributes = {
        "data-block-type": _type,
        "data-volto-block": json.dumps(block_data),
    }

    children = []
    for _, block in iterate_blocks(data):
        children.extend(convert_block_to_elements(block))

    div = E.DIV(*children, **attributes)
    return [div]


def serialize_teaserGrid(block_data):
    # __import__("pdb").set_trace()
    _type = block_data.pop("@type")
    columns = block_data.pop("columns")
    attributes = {
        "data-block-type": _type,
        "data-volto-block": json.dumps(block_data),
    }
    children = []
    for teaser in columns:
        elements = convert_block_to_elements(teaser)
        children.append(E.DIV(*elements))
    div = E.DIV(*children, **attributes)
    return [div]


TEASER_FIELDS = ["title", "head_title", "description"]


def serialize_teaser(block_data):
    serialized = generic_block_converter(TEASER_FIELDS)(block_data)

    # item_model = block_data.pop('itemModel', None)
    # if item_model:
    #     serialized_model = generic_block_converter()
    # TODO: handle the itemModel
    # __import__("pdb").set_trace()
    return serialized


def serialize_title_block(block_data):
    _type = block_data.pop("@type")
    translate_fields = ["subtitle"]

    fv = {}
    for name in translate_fields:
        value = block_data.pop(name, None)
        if value is not None:
            fv[name] = value

    info = block_data.pop("info", [])
    infoel = E.DIV(
        *[E.DIV(bit.get("description", ""), id=bit["@id"]) for bit in info],
        **{"data-fieldname": "info"},
    )

    attributes = {
        "data-block-type": _type,
        "data-volto-block": json.dumps(block_data),
    }

    children = [infoel] + [
        E.DIV(fv.get(name, ""), **{"data-fieldname": name}) for name in translate_fields
    ]
    div = E.DIV(*children, **attributes)
    return [div]


converters = {
    "slate": serialize_slate,
    "slateTable": serialize_slate_table,
    # TODO: implement specific fields for the title block
    "title": serialize_title_block,
    "image": serialize_image,
    "columnsBlock": serialize_layout_block,
    "tabs_block": serialize_layout_block_with_titles,
    "group": serialize_group_block,
    "teaserGrid": serialize_teaserGrid,
    # "quote": serialize_quote,
    "quote": generic_slate_block("value"),
    "item": generic_slate_block("description"),
    # generics
    "nextCloudVideo": generic_block_converter(["title"]),
    "layoutSettings": generic_block_converter([]),
    "callToActionBlock": generic_block_converter(["text"]),
    "searchlib": generic_block_converter(["searchInputPlaceholder"]),
    "teaser": serialize_teaser,
    # TODO: need to handle call to actions for teasers
    # teaserGrid
}


def convert_block_to_elements(block_data):
    _type = block_data.get("@type", None)

    if _type is None:
        raise ValueError

    if _type not in converters:
        print(f"Block serializer needed: {_type}. Using default")
        return generic_block_converter([])(block_data)

    return converters[_type](block_data)


def convert_blocks_to_html(data):
    order = data.blocks_layout["items"]
    blocks = data.blocks
    fragments = []

    for uid in order:
        block = blocks[uid]
        elements = convert_block_to_elements(block)
        if elements:
            html = elements_to_text(elements)
            fragments.append(html)

    return "\n".join(fragments)
