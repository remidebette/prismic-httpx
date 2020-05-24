from typing import List, Union, Optional

from pydantic import BaseModel

import prismic.structures.fragments
from prismic.structures.fragments import ResultData


class Document(BaseModel):
    id: Optional[str]
    uid: Optional[str]
    type: Optional[str]
    href: Optional[str]
    tags: Optional[List]
    first_publication_date: Optional[str]
    last_publication_date: Optional[str]
    slugs: Optional[List[str]]
    linked_documents: "Optional[List[Document]]"
    lang: Optional[str]
    alternate_languages: Optional[List]
    data: Optional[ResultData]

    def as_html(self, link_resolver):
        if self.data:
            return self.data.as_html(link_resolver)

        return ''

    @property
    def slug(self):
        """
        Return the most recent slug

        :return: str slug
        """
        return self.slugs[0] if self.slugs else "-"


Document.update_forward_refs()
