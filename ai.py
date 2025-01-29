import re

from config import OPENAI

_LINK_RE = re.compile(r'https?://\S+')
_SUFFIX_RE = re.compile(r'(?:\[\d+]|[,.)])+$')


async def find_link(query: str) -> str | None:
    completion = await OPENAI.chat.completions.create(
        model='sonar-reasoning',
        temperature=0.1,
        messages=[
            {
                'role': 'system',
                'content': (
                    'You try to find homepage websites for requested POIs. '
                    'Those links will be added to the POIs on OpenStreetMap. '
                    'You must ignore non-exact matches and false positives! '
                    "If there isn't a high-quality match, say nothing. "
                    'If there is, say just the single best-matching fully qualified URL in plain text.'
                ),
            },
            {
                'role': 'user',
                'content': f'Can you search for a homepage website for this POI? {query}',
            },
        ],
    )

    response = completion.choices[0].message.content.rsplit('</think>', 1)[-1].strip()  # pyright: ignore [reportOptionalMemberAccess]
    match = _LINK_RE.search(response)
    if match is None:
        return None

    return _SUFFIX_RE.sub('', match.group())
