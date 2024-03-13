""" Convert HTML to slate, slate to HTML

A port of volto-slate' deserialize.js module
"""

import json
import re
from collections import deque

import lxml.html
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from .config import ACCEPTED_TAGS, DEFAULT_BLOCK_TYPE, INLINE_ELEMENTS

SLATE_INLINE_ELEMENTS = [e.lower() for e in INLINE_ELEMENTS] + [
    "link"  # Volto's <a> link
]

SPACE_BEFORE_ENDLINE = re.compile(r"\s+\n", re.M)
SPACE_AFTER_DEADLINE = re.compile(r"\n\s+", re.M)
TAB = re.compile(r"\t", re.M)
LINEBREAK = re.compile(r"\n", re.M)
MULTIPLE_SPACE = re.compile(r" ( +)", re.M)
FIRST_SPACE = re.compile("^ ", re.M)
FIRST_ANY_SPACE = re.compile(r"^\s", re.M)
FIRST_ALL_SPACE = re.compile(r"^\s+", re.M)
ANY_SPACE_AT_END = re.compile(r"\s$", re.M)
ANY_WHITESPACE = re.compile(r"\s|\t|\n", re.M)


def is_inline_slate(el):
    """Returns true if the element is a text node

    Some richtext editors provide support for "inline elements", which is to say they
    mark some portions of text and add flags for that, like "bold:true,italic:true", etc.

    From experience, this is a bad way to go when the output is intended to be HTML. In
    HTML DOM there is only markup and that markup is semantic. So keeping it purely
    markup greately simplifies the number of cases that need to be covered.
    """

    if isinstance(el, dict) and "text" in el:
        return True

    return False


def merge_adjacent_text_nodes(children):
    "Given a list of Slate elements, it combines adjacent texts nodes"

    ranges = []
    for i, v in enumerate(children):
        if "text" in v:
            if ranges and ranges[-1][1] == i - 1:
                ranges[-1][1] = i
            else:
                ranges.append([i, i])
    text_positions = []
    range_dict = {}
    for start, end in ranges:
        text_positions.extend(list(range(start, end + 1)))
        range_dict[start] = end

    result = []
    for i, v in enumerate(children):
        if i not in text_positions:
            result.append(v)
        if i in range_dict:
            d = range_dict[i] + 1
            slice = children[i:d]
            node = {}
            if slice:
                node = slice[0]
            node["text"] = "".join([c["text"] for c in slice])
            result.append(node)

    return result


def remove_space_before_after_endline(text):
    text = SPACE_BEFORE_ENDLINE.sub("\n", text)
    text = SPACE_AFTER_DEADLINE.sub("\n", text)
    return text


def convert_tabs_to_spaces(text):
    return TAB.sub(" ", text)


def convert_linebreaks_to_spaces(text):
    return LINEBREAK.sub(" ", text)


def remove_space_follow_space(text, node):
    """Any space immediately following another space (even across two separate inline
    elements) is ignored (rule 4)
    """

    text = MULTIPLE_SPACE.sub(" ", text)

    if not text.startswith(" "):
        return text

    previous = node.previousSibling
    if previous:
        if is_textnode(previous):
            if previous.text.endswith(" "):
                return FIRST_SPACE.sub("", text)
        elif is_inline(previous):
            prev_text = collapse_inline_space(previous)
            if prev_text.endswith(" "):
                return FIRST_SPACE.sub("", text)
    else:
        parent = node.parent
        if parent.previousSibling:
            prev_text = collapse_inline_space(parent.previousSibling)
            if prev_text and prev_text.endswith(" "):
                return FIRST_SPACE.sub("", text)
        else:
            # TODO: temporary, to be tested
            if parent.parent and is_inline(parent.parent):
                return collapse_inline_space(parent.parent)
            return FIRST_SPACE.sub("", text)

    return text


def is_inline(node):
    assert node is not None

    if isinstance(node, str) or is_textnode(node):
        return True

    if node.name.upper() in INLINE_ELEMENTS:
        return True

    return False


def get_inline_ancestor_sibling(node):
    """Find a "visual sibling" by moving up in DOM hierarchy and finding a sibling"""

    next_ = node.nextSibling

    while next_ is None:
        node = node.parent
        if node is None or not is_inline(node):
            break
        next_ = node.nextSibling

    if (next_ is not None) and (not is_inline(next_)):
        return None

    return next_


def remove_element_edges(text, node):
    """Sequences of spaces at the beginning and end of an element are removed"""

    previous = node.previousSibling
    next_ = node.nextSibling
    parent = node.parent

    if (not is_inline(parent)) and (previous is None) and FIRST_ANY_SPACE.search(text):
        text = FIRST_ALL_SPACE.sub("", text)

    if ANY_SPACE_AT_END.search(text):
        has_inline_ancestor_sibling = get_inline_ancestor_sibling(
            node) is not None
        if not has_inline_ancestor_sibling or (next_ and next_.name == "br"):
            text = ANY_SPACE_AT_END.sub("", text)

    return text


def clean_padding_text(text, node):
    """Cleans head/tail whitespaces of a single html text with multiple toplevel tags"""

    if is_whitespace(text):
        has_prev = (
            node.previousSibling
            and is_element(node.previousSibling)
            and not is_inline(node.previousSibling)
        )
        has_next = (
            node.nextSibling
            and is_element(node.nextSibling)
            and not is_inline(node.nextSibling)
        )

        if has_prev and has_next:
            return ""

        if node.previousSibling and not node.nextSibling:
            return ""

        if node.nextSibling and not node.previousSibling:
            return ""

    return text


def collapse_inline_space(node):
    """Process inline text according to whitespace rules

    See

    https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Whitespace
    """
    text = node.text or ""

    # 0 (Volto). Return None if is text between block nodes
    text = clean_padding_text(text, node)

    # 1. all spaces and tabs immediately before and after a line break are ignored
    text = remove_space_before_after_endline(text)

    # 2. Next, all tab characters are handled as space characters
    text = convert_tabs_to_spaces(text)

    # 3. Convert all line breaks to spaces
    text = convert_linebreaks_to_spaces(text)

    # 4. Any space immediately following another space
    # (even across two separate inline elements) is ignored
    text = remove_space_follow_space(text, node)

    # 5. Sequences of spaces at the beginning and end of an element are removed
    text = remove_element_edges(text, node)

    return text


def fragments_fromstring(text):
    tree = BeautifulSoup(text, "html.parser")
    return list(tree)


def is_textnode(node):
    return isinstance(node, NavigableString)


def is_element(node):
    return isinstance(node, Tag)


def style_to_object(text):
    out = {}

    for pair in [x.strip() for x in text.split(";") if x.strip()]:
        k, v = pair.split(":", 1)
        out[k.strip()] = v.strip()

    return out


def fix_node_attributes(key):
    restricted = ["type", "value", "children"]
    if key in restricted:
        key = "_" + key

    return key


def fix_img_url(url):
    # if 'resolveuid' in url:
    #     # TODO: fix this
    #     return ''
    # ../../../../
    bits = url.split("/@@images", 1)
    url = bits[0]
    scale = None
    if len(bits) > 1:
        scale = list(reversed(bits[1].rsplit("/")))[0]
    if "resolveuid" in url and not url.startswith("/"):
        bits = url.split("resolveuid", 1)
        url = "../resolveuid%s" % bits[1]
    if scale == "large":
        scale = "huge"
    return (url, scale)


class HTML2Slate(object):
    """A parser for HTML to slate conversion

    If you need to handle some custom slate markup, inherit and extend

    See https://github.com/plone/volto/blob/5f9066a70b9f3b60d462fc96a1aa7027ff9bbac0/packages/volto-slate/src/editor/deserialize.js
    """

    def from_elements(self, elements):
        nodes = []
        for f in elements:
            slate_nodes = self.deserialize(f)
            if slate_nodes:
                nodes += slate_nodes

        return self.normalize(nodes)

    def to_slate(self, text):
        "Convert text to a slate value. A slate value is a list of elements"

        fragments = fragments_fromstring(text)
        return self.from_elements(fragments)

    def deserialize(self, node):
        """Deserialize a node into a list Slate Nodes"""

        if node is None:
            return []

        if is_textnode(node):
            text = collapse_inline_space(node)
            return [{"text": text}] if text else None
        elif not is_element(node):
            return None

        tagname = node.name
        handler = None

        if "data-slate-data" in node.attrs:
            handler = self.handle_slate_data_element
        else:
            handler = getattr(self, "handle_tag_{}".format(tagname), None)
            if not handler and tagname in ACCEPTED_TAGS:
                handler = self.handle_block

        if handler:
            slate_node = handler(node)
            if not isinstance(slate_node, list):
                slate_node = [slate_node]
            return slate_node

        # fallback, "skips" the node
        return self.handle_fallback(node)

    def deserialize_children(self, node):
        res = []

        for child in node.children:
            b = self.deserialize(child)
            if isinstance(b, list):
                res += b
            elif b:
                res.append(b)

        return res

    def handle_tag_a(self, node):
        link = node["href"] if "href" in node.attrs else None

        element = {
            "type": "link",
            "children": self.deserialize_children(node),
        }
        if link is not None:
            element["data"] = {"url": link}

        return element

    def handle_tag_ol(self, node):
        return self.handle_tag_ul(node, node_type="ol")

    def handle_tag_span(self, node):
        rawdata = node.attrs.get("data-slate-node", None)
        data = {}
        if rawdata:
            data = json.loads(rawdata)
        data["text"] = node.text
        return data

    def handle_tag_ul(self, node, node_type="ul"):
        children = self.deserialize_children(node)

        if not children:
            # avoid crash in volto-slate when dealing with empty lists
            return {"type": "p", "children": [{"text": ""}]}

        return {"type": node_type, "children": children}

    def handle_tag_img(self, node):
        url = node.attrs.get("src", "")

        str_node = repr(node)

        align = ""
        if "float: left" in str_node:
            align = "left"
        elif "float: right" in str_node:
            align = "right"

        # TODO: just for testing, I'm missing the blobs
        # url = "/fallback.png/@@images/image/preview"
        # resolveuid/88a6567afaa148aabed5c5055e12c509/@@images/image/preview
        # <img alt="" class="image-left" data-linktype="image"
        # data-scale="preview" data-val="88a6567afaa148aabed5c5055e12c509"
        # src="resolveuid/88a6567afaa148aabed5c5055e12c509/@@images/image/preview"
        # title="rawpixel on Unsplash"/>

        # print("fix image url", url)
        url, scale = fix_img_url(url)
        result = {
            "type": "img",
            "align": align,
            "url": url,
            "title": node.attrs.get("title", ""),
            "alt": node.attrs.get("alt", ""),
            "children": [{"text": ""}],
            "scale": scale,
        }
        # print("result", result)
        return result

    def handle_tag_voltoblock(self, node):
        element = {
            "type": "voltoblock",
            "data": json.loads(node.attrs["data-voltoblock"]),
        }
        return element

    def handle_tag_br(self, node):
        return {"text": "\n"}

    def handle_tag_b(self, node):
        # TO DO: implement <b> special cases
        return self.handle_block(node)

    def handle_tag_div(self, node):
        if getattr(node, "name", "") == "[document]":
            # treat divs directly in the input as paragraph nodes. Fixes
            # en/observatory/policy-context/european-policy-framework/who/
            return self.handle_tag_p(node)
        elif node.attrs.get("data-slate-node"):
            rawdata = node.attrs["data-slate-node"]
            slate_node = json.loads(rawdata)
            slate_node["children"] = self.deserialize_children(node)
            return slate_node
        else:
            return self.handle_fallback(node)

    def handle_tag_p(self, node):
        # TO DO: implement <b> special cases
        style = node.get("style", "")
        styles = style_to_object(style)
        if styles.get("text-align") == "center":
            return {
                "type": "p",
                "children": self.deserialize_children(node),
                "styleName": "text-center",
            }
        return self.handle_block(node)

    def handle_block(self, node):
        value = {"type": node.name,
                 "children": self.deserialize_children(node)}
        for k, v in node.attrs.items():
            k = fix_node_attributes(k)
            value[k] = v
        return value

    def handle_slate_data_element(self, node):
        data = node["data-slate-data"]
        element = json.loads(data)
        element["children"] = self.deserialize_children(node)
        return element

    def handle_fallback(self, node):
        """Unknown tags (for example span) are handled as pipe-through"""
        return self.deserialize_children(node)

    def normalize(self, value):
        """Normalize value to match Slate constraints"""

        assert isinstance(value, list)
        value = [v for v in value if v is not None]

        # all top-level elements in the value need to be block tags
        if value and [x for x in value if is_inline_slate(value[0])]:
            value = [{"type": DEFAULT_BLOCK_TYPE, "children": value}]

        stack = deque(value)

        while stack:
            child = stack.pop()
            children = child.get("children", None)
            if children is not None:
                children = [c for c in children if c]
                # merge adjacent text nodes
                child["children"] = merge_adjacent_text_nodes(children)
                stack.extend(child["children"])

                if len(child["children"]) == 0:
                    child["children"].append({"text": ""})

        return value


def tostr(s):
    if isinstance(s, str):
        return s
    else:
        return s.decode("utf-8")


def text_to_slate(text: str):
    # first we cleanup the broken html
    e = lxml.html.document_fromstring(text)
    children = e.find("body").getchildren()
    text = "".join(tostr(lxml.html.tostring(child)) for child in children)
    return HTML2Slate().to_slate(text)


def is_whitespace(text):
    """Returns true if the text is only whitespace characters"""

    if not isinstance(text, str):
        return False

    return len(ANY_WHITESPACE.sub("", text)) == 0
