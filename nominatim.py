from collections.abc import Iterable
from typing import Any

import stamina
from httpx import HTTPError

from config import NOMINATIM_URL
from db import OsmId
from utils import HTTP


@stamina.retry(on=HTTPError)
async def nominatim_address_lookup(ids: Iterable[OsmId]) -> list[dict[str, Any]]:
    r = await HTTP.get(
        f'{NOMINATIM_URL}/lookup',
        params={
            'format': 'jsonv2',
            'osm_ids': (
                ','.join(f'{id[:1].upper()}{id.split("/", 1)[1]}' for id in ids)
            ),
        },
    )
    r.raise_for_status()
    return r.json()
