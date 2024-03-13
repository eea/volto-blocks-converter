import json
from copy import deepcopy

from .config import ACCEPTED_TAGS
from lxml.html import builder as E
from lxml.html import tostring

SLATE_ACCEPTED_TAGS = ACCEPTED_TAGS + ["link"]


def join(element, children):
    """join.

    :param element:
    :param children:
    """
    res = []
    for bit in children:
        res.append(bit)
        res.append(element)
    return res[:-1]  # remove the last break


def inline_text_element(text, slate_node):
    if len(slate_node) > 1:
        el = E.SPAN
        slate_node.pop("text", None)
        return el(text, **{"data-slate-node": json.dumps(slate_node)})
    return text


class Slate2HTML(object):
    """Slate2HTML."""

    def serialize(self, element):
        """serialize.

        :param element:
        """
        if "text" in element:
            if "\n" not in element["text"]:
                return [inline_text_element(element["text"], deepcopy(element))]

            return join(
                E.BR,
                [inline_text_element(t, element)
                 for t in element["text"].split("\n")],
            )

        tagname = element["type"]

        if element.get("data") and element["type"] not in SLATE_ACCEPTED_TAGS:
            handler = self.handle_slate_data_element
        else:
            handler = getattr(self, "handle_tag_{}".format(tagname), None)
            if not handler and tagname in SLATE_ACCEPTED_TAGS:
                handler = self.handle_block

        if handler is None:
            print(element)
            handler = self.generic_type_handler
            # raise ValueError("Unknown handler")

        res = handler(element)
        if isinstance(res, list):
            return res
        return [res]

    def handle_tag_div(self, element):
        # TODO: temporary, we need to see what to do for two-way with eTranslation
        return self.handle_block(element)
        # children = []
        # for child in element["children"]:
        #     children += self.serialize(child)
        #

    def handle_tag_p(self, element):
        attributes = {}
        _type = element["type"].upper()
        style = element.get("styleName")
        if style == "text-center":
            attributes = {"style": "text-align: center;"}

        el = getattr(E, _type)
        children = []
        for child in element["children"]:
            children += self.serialize(child)

        return el(*children, **attributes)

    def handle_tag_link(self, element):
        """handle_tag_link.

        :param element:
        """
        url = element.get("data", {}).get("url")

        attributes = {}
        if url is not None:
            attributes["href"] = url

        el = getattr(E, "A")

        children = []
        for child in element["children"]:
            children += self.serialize(child)

        return el(*children, **attributes)

    def handle_slate_data_element(self, element):
        """handle_slate_data_element.

        :param element:
        """
        el = E.SPAN

        children = []
        for child in element["children"]:
            children += self.serialize(child)

        data = {"type": element["type"], "data": element["data"]}
        attributes = {"data-slate-data": json.dumps(data)}

        return el(*children, **attributes)

    def generic_type_handler(self, element):
        el = E.DIV

        children = []
        for child in element.pop("children"):
            children += self.serialize(child)

        return el(*children, **{"data-slate-node": json.dumps(element)})

    # def handle_tag_callout(self, element):
    #     el = E.P
    #     attributes = {"class": "callout"}
    #
    #     children = []
    #     for child in element["children"]:
    #         children += self.serialize(child)
    #
    #     return el(*children, **attributes)

    def handle_block(self, element):
        """handle_block.

        :param element:
        """
        _type = element["type"].upper()
        if _type == "VOLTOBLOCK":
            return []  # TODO: finish this. Right now it's only used in the plone4>plone6 migration
        el = getattr(E, _type)

        children = []
        for child in element["children"]:
            children += self.serialize(child)

        return el(*children)

    def to_elements(self, value):
        children = []
        for child in value:
            children += self.serialize(child)

        return children

    def to_html(self, value):
        """to_html.

        :param value:
        """
        children = []
        for child in value:
            children += self.serialize(child)

        # TO DO: handle unicode properly
        return elements_to_text(children)


def elements_to_text(children):
    return "".join(tostring(f).decode("utf-8") for f in children)


def slate_to_html(value):
    """slate_to_html.

    :param value:
    """

    convert = Slate2HTML()
    return convert.to_html(value)


def slate_to_elements(value):
    """Convert a slate value to lxml Elements"""

    convert = Slate2HTML()
    return convert.to_elements(value)
