import re

from google.genai.types import GenerateContentConfig, GoogleSearch, Tool
from stamina import retry

from config import GEMINI

_LINK_RE = re.compile(r'https?://[^\s[\](),]+')

_GENERATION_CONFIG = GenerateContentConfig(
    system_instruction=(
        'You try to find homepage websites for requested POIs. '
        'Those links will be added to the POIs on OpenStreetMap. '
        'Avoid non-exact and false positive matches! '
        "If there isn't a high-quality match, output <EOF>. "
        'If there is: output the single best-matching fully-qualified URL in plain-text (starting with "https://" or "http://").'
    ),
    temperature=0,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type='text/plain',
    tools=[Tool(google_search=GoogleSearch())],
)


@retry(on=Exception)
async def find_link(query: str) -> str | None:
    response = await GEMINI.aio.models.generate_content(
        model='gemini-2.0-flash',
        config=_GENERATION_CONFIG,
        contents=f'Can you search for a homepage website for this POI? {query}',
    )
    assert response.text is not None
    match = _LINK_RE.search(response.text)
    return match.group() if match is not None else None
