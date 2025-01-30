import os
import secrets
from pathlib import Path

from openai import AsyncOpenAI

OPENAI = AsyncOpenAI(
    api_key=os.environ['OPENAI_API_KEY'],
    base_url='https://api.perplexity.ai',
    max_retries=int(os.getenv('OPENAI_MAX_RETRIES', 10)),
)
OSM_TOKEN = os.environ['OSM_TOKEN']
DRY_RUN = os.getenv('DRY_RUN', None) == '1'
print('🦺 TEST MODE 🦺' if DRY_RUN else '🔴 PRODUCTION MODE 🔴')

CREATED_BY = 'osm-autolink'
WEBSITE = 'https://github.com/Zaczero/osm-autolink'
USER_AGENT = f'{CREATED_BY} (+{WEBSITE})'

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

OVERPASS_API_INTERPRETER = os.getenv(
    'OVERPASS_API_INTERPRETER', 'https://overpass-api.de/api/interpreter'
)

NOMINATIM_URL = os.getenv('NOMINATIM_URL', 'https://nominatim.openstreetmap.org')

# https://docs.perplexity.ai/guides/usage-tiers#rate-limits-and-usage-tiers
OPENAI_RPM = int(os.getenv('OPENAI_RPM', 50))

DEFAULT_CHANGESET_TAGS = {
    'comment': 'Dodanie brakujących linków stron internetowych',
    'created_by': CREATED_BY,
    'website': WEBSITE,
}

CHANGESET_ID_PLACEHOLDER = f'__CHANGESET_ID_PLACEHOLDER__{secrets.token_urlsafe(8)}__'
