from typing import List

from pydantic import BaseModel

from prismic.structures.document import Document


class Response(BaseModel):
    page: int
    results_per_page: int
    total_pages: int
    total_results_size: int
    results_size: int
    next_page: str = None
    prev_page: str = None
    results: List[Document]
