import abc
import datetime
import html
from collections import defaultdict
from enum import unique, Enum
from typing import List, Any, Optional, Union

from pydantic import BaseModel, Field, validator


@unique
class LinkTypes(str, Enum):
    web = "Web"
    document = "Document"
    media = "Media"
    file = "File"


class Link(BaseModel, abc.ABC):
    link_type: LinkTypes
    label: Optional[str]

    @abc.abstractmethod
    def get_url(self, link_resolver=None):
        pass


class WebLink(Link):
    url: Optional[str]

    def as_html(self, link_resolver=None):
        return f"""<a href="{self.url}">{self.url}</a>"""

    def get_url(self, link_resolver=None):
        return self.url


class MediaLink(Link):
    name: Optional[str]
    kind: Optional[str]
    url: Optional[str]
    size: Optional[str]
    height: Optional[str]
    width: Optional[str]

    def as_html(self, link_resolver=None):
        return f"""<a href="{self.url}">{self.name}</a>"""

    def get_url(self, link_resolver=None):
        return self.url


class FileLink(Link):
    url: str
    kind: str
    size: str
    name: str

    def as_html(self, link_resolver=None):
        return f"""<a href="{self.url}">{self.name}</a>"""

    def get_url(self, link_resolver=None):
        return self.url


class DocumentLink(Link):
    id: Optional[str]
    uid: Optional[str]
    type: Optional[str]
    tags: Optional[List]
    slug: Optional[str]
    lang: Optional[str]
    isBroken: Optional[bool]
    data: "Optional[ResultData]"

    def as_html(self, documentlink_resolver, html_serializer=None):
        """Get the DocumentLink as html.

        :param documentlink_resolver: A resolver function will be called with
        :class:`~prismic.fragments.Fragment.DocumentLink` object as argument.
        Resolver function should return a string, the local url to the document.

        """
        return """<a href="%(link)s">%(slug)s</a>""" % {
            "link": self.get_url(documentlink_resolver),
            "slug": self.slug
        }

    def get_url(self, documentlink_resolver=None):
        if not hasattr(documentlink_resolver, '__call__'):
            raise Exception(
                "documentlink_resolver should be a callable object, but it's: %s"
                % type(documentlink_resolver)
            )
        return documentlink_resolver(self)


@unique
class SpanTypes(str, Enum):
    strong = "strong"
    em = "em"
    hyperlink = "hyperlink"


class Span(BaseModel):
    start: int
    end: int
    type: SpanTypes
    data: Optional[Union[WebLink, DocumentLink, MediaLink, FileLink]]

    def length(self):
        return self.end - self.start

    def write_tag(self, content, link_resolver, html_serializer):
        if html_serializer is not None:
            custom_html = html_serializer(self, content)
            if custom_html is not None:
                return custom_html
        if self.type == SpanTypes.em:
            return "<em>" + content + "</em>"
        elif self.type == SpanTypes.strong:
            return "<strong>" + content + "</strong>"
        elif self.type == SpanTypes.hyperlink:
            return """<a href="%s">""" % self.data.get_url(link_resolver) + content + "</a>"
        else:
            cls = ""
            if self.data.label is not None:
                cls = " class=\"%s\"" % self.data.label
            return """<span%s>%s</span>""" % (cls, content)


@unique
class StructuredTextTypes(str, Enum):
    heading1 = "heading1"
    heading2 = "heading2"
    heading3 = "heading3"
    heading4 = "heading4"
    heading5 = "heading5"
    heading6 = "heading6"
    paragraph = "paragraph"
    list_item = "list-item"
    o_list_item = "o-list-item"
    image = "image"
    embed = "embed"
    preformatted = "preformatted"


class StructuredText(BaseModel):
    type: StructuredTextTypes
    text: str
    spans: List[Span]
    label: Optional[str]

    def span_as_html(self, link_resolver, html_serializer):
        if self.type in {"image", "embed"}:
            return ""

        html_list = []
        tags_start = defaultdict(list)
        tags_end = defaultdict(list)
        for span in self.spans:
            tags_start[span.start].append(span)

        for span in reversed(self.spans):
            tags_end[span.end].append(span)

        index = 0
        stack = []
        for index, letter in enumerate(self.text):
            if index in tags_end:
                for end_tag in tags_end.get(index):
                    # Close a tag
                    tag = stack.pop()
                    inner_html = tag["span"].write_tag(tag["content"], link_resolver,
                                                               html_serializer)
                    if len(stack) == 0:
                        # The tag was top-level
                        html_list.append(inner_html)
                    else:
                        # Add the content to the parent tag
                        stack[-1]["content"] += inner_html
            if index in tags_start:

                for span in reversed(sorted(tags_start.get(index), key=lambda s: s.length())):
                    # Open a tag
                    stack.append({
                        "span": span,
                        "content": ""
                    })
            if len(stack) == 0:
                # Top-level text
                html_list.append(html.escape(letter))
            else:
                # Inner text of a span
                stack[-1]["content"] += html.escape(letter)

        # Check for the tags after the end of the string
        while len(stack) > 0:
            # Close a tag
            tag = stack.pop()
            inner_html = tag["span"].write_tag(tag["content"], link_resolver, html_serializer)
            if len(stack) == 0:
                # The tag was top-level
                html_list.append(inner_html)
            else:
                # Add the content to the parent tag
                stack[-1]["content"] += inner_html

        return ''.join(html_list)

    def as_html(self, link_resolver, html_serializer=None):
        content = ""
        if self.type not in {"image", "embed"}:  # only not image and not embed
            content = self.span_as_html(link_resolver, html_serializer)

        if html_serializer is not None:
            custom_html = html_serializer(self, content)
            if custom_html is not None:
                return custom_html
        cls = ""
        if self.type not in {"image", "embed"} and self.label is not None:
            cls = " class=\"%s\"" % self.label
        if self.type.startswith("heading"):
            level = self.type[-1]
            return "<h%(level)s%(cls)s>%(html)s</h%(level)s>" % {
                "level": level,
                "cls": cls,
                "html": content
            }
        elif self.type == "paragraph":
            return "<p%s>%s</p>" % (cls, content)
        elif self.type == "preformatted":
            return "<pre%s>%s</pre>" % (cls, content)
        elif self.type in {"list-item", "o-list-item"}:
            return "<li%s>%s</li>" % (cls, content)
        elif self.type == "image":  # TODO: fix
            all_classes = ["block-img"]
            if self.view.label is not None:
                all_classes.append(self.view.label)
            return "<p class=\"%s\">%s</p>" % (" ".join(all_classes), block.get_view().as_html(link_resolver))
        elif self.type == "embed":
            return self.get_embed().as_html  # TODO: fix


class Slice(BaseModel):
    slice_type: str
    slice_label: Optional[str]
    value: Optional[Union[WebLink, DocumentLink, MediaLink, FileLink]]
    repeat: Optional[Any]
    non_repeat: Optional[Any] = Field(None, alias="non-repeat")

    @validator('value', pre=True)
    def validate_value(cls, value):
        if not value:
            raise TypeError("Value must be defined")
        if not isinstance(value, dict):
            raise ValueError(f'invalid value, not dict')
        return cls.value_gen(value)

    @classmethod
    def value_gen(cls, value):
        if "link_type" not in value:
            raise TypeError('value must contain a link_type')

        link_type = value.get('link_type')
        if link_type == LinkTypes.web:
            return WebLink(**value)
        elif link_type == LinkTypes.document:
            return DocumentLink(**value)
        elif link_type == LinkTypes.media:
            return MediaLink(**value)
        elif link_type == LinkTypes.file:
            return FileLink(**value)
        else:
            raise ValueError(f'invalid value, no support for type {link_type!r}')

    def as_html(self, link_resolver):
        classes = ['slice']
        if self.slice_label is not None:
            classes.append(self.slice_label)
        return '<div data-slicetype="%(slice_type)s" class="%(classes)s">%(body)s</div>' % {
            "slice_type": self.slice_type,
            "classes": ' '.join(classes),
            "body": self.value.as_html(link_resolver)
        }


class ImageDimensions(BaseModel):
    width: int
    height: int


class View(BaseModel):
    url: Optional[str]
    dimensions: Optional[ImageDimensions]
    alt: Optional[str] = None
    copyright: Optional[str] = None
    label: Optional[Any]


class Image(View):
    linkTo: Optional[Union[WebLink, DocumentLink, MediaLink, FileLink]]
    small: Optional[View]

    def as_html(self, link_resolver):
        if not self.url:
            return ""

        img_tag = """<img src="%(url)s" alt="%(alt)s" width="%(width)s" height="%(height)s" />""" % {
            'url': self.url,
            'width': self.dimensions.width,
            'height': self.dimensions.height,
            'alt': self.alt if (self.alt is not None) else ""
        }
        if self.linkTo is None:
            return img_tag
        else:
            url = self.linkTo.get_url(link_resolver)
            return """<a href="%(url)s">%(content)s</a>""" % {
                'url': url,
                'content': img_tag
            }


class GeoPoint(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]

    def as_html(self, link_resolver=None):
        if not self.latitude or not self.longitude:
            return ""

        return (f"""<div class="geopoint"><span class="latitude">"""
                f"""{self.latitude:f}</span><span class="longitude">{self.longitude:f}</span>"""
                """</div>""")


class Embed(BaseModel):
    type: Optional[str]
    title: Optional[str]
    embed_url: Optional[str]
    html: Optional[str]
    author_url: Optional[str]
    author_name: Optional[str]
    width: Optional[int]
    height: Optional[int]
    provider_url: Optional[str]
    provider_name: Optional[str]
    thumbnail_url: Optional[str]
    thumbnail_width: Optional[int]
    thumbnail_height: Optional[int]
    version: Optional[str]

    def as_html(self, link_resolver=None):
        return (f"""<div data-oembed="{self.embed_url}" data-oembed-type="{self.type}" data-oembed-provider="{self.provider_name}">"""
                f"{self.html}"
                "</div>")


class ResultData(BaseModel):
    stext_single: Optional[List[StructuredText]]
    stext: Optional[List[StructuredText]]
    image: Optional[Image]
    link_web: Optional[WebLink]
    link_document: Optional[DocumentLink]
    link_media: Optional[MediaLink]
    text: Optional[str]
    date: Optional[datetime.date]
    timestamp: Optional[datetime.datetime]
    number: Optional[float]
    range: Optional[str]
    select: Optional[str]
    color: Optional[str]
    geopoint: Optional[GeoPoint]
    embed: Optional[Embed]
    source: Optional[DocumentLink]
    group: "Optional[List[ResultData]]"
    slices: Optional[List[Slice]]

    def as_html(self, link_resolver, html_serializer=None):
        html_list = []
        for key, fragment in self:
            if fragment:
                html_list.append("""<section data-field="%s">""" % key)
                html_list.append(self.fragment_to_html(key, fragment, link_resolver, html_serializer))
                html_list.append("""</section>""")

        return ''.join(html_list)

    @staticmethod
    def fragment_to_html(key, fragment, link_resolver, html_serializer=None):
        if not fragment:
            return ""

        if key == "select":
            key = "text"

        if key in {"color", "text", "number", "range"}:
            return f"""<span class="{key}">{fragment}</span>"""

        if key == "date":
            return f"""<time>{fragment}</time>"""

        if key == "timestamp":
            return f"""<time>{fragment.isoformat()}</time>"""

        if key in {"image", "link_web", "link_document", "link_media", "source", "geopoint", "embed"}:
            return fragment.as_html(link_resolver)

        if key == "slices":
            html_list = []
            for slice in fragment:
                html_list.append(slice.as_html(link_resolver))
            return "\n".join(html_list)

        if key == "group":
            html_list = []
            for group in fragment:
                html_list.append(group.as_html(link_resolver))
            return "\n".join(html_list)

        if key in {"stext_single", "stext"}:
            groups = []
            for block in fragment:
                # TODO: implement group logic
                # if len(groups) > 0:
                #     last_one = groups[-1:][0]
                #
                #     if last_one.tag == "ul" and isinstance(block, Block.ListItem) and not block.is_ordered:
                #         last_one.blocks.append(block)
                #     elif last_one.tag == "ol" and isinstance(block, Block.ListItem) and block.is_ordered:
                #         last_one.blocks.append(block)
                #     elif isinstance(block, Block.ListItem) and not block.is_ordered:
                #         groups.append(StructuredText.Group("ul", [block]))
                #     elif isinstance(block, Block.ListItem) and block.is_ordered:
                #         groups.append(StructuredText.Group("ol", [block]))
                #     else:
                #         groups.append(StructuredText.Group(None, [block]))
                # else:
                #     if isinstance(block, Block.ListItem) and not block.is_ordered:
                #         groups.append(StructuredText.Group("ul", [block]))
                #     elif isinstance(block, Block.ListItem) and block.is_ordered:
                #         groups.append(StructuredText.Group("ol", [block]))
                #     else:
                #         groups.append(StructuredText.Group(None, [block]))

                pass

            html_list = []
            # for group in groups:
                # if group.tag is not None:
                #     html_list.append("<%(tag)s>" % group.__dict__)
            for block in fragment:
                html_list.append(block.as_html(link_resolver, html_serializer))
                # if group.tag is not None:
                #     html_list.append("</%(tag)s>" % group.__dict__)

            html_str = ''.join(html_list)
            return html_str

        return ""


DocumentLink.update_forward_refs()
ResultData.update_forward_refs()
