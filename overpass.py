from itertools import batched

import stamina
from httpx import HTTPError

from config import OVERPASS_API_INTERPRETER
from db import OsmId
from nominatim import nominatim_address_lookup
from utils import HTTP

_REQUIRED_KEYS = {'amenity', 'shop', 'craft', 'office'}


@stamina.retry(on=HTTPError)
async def overpass_query() -> dict[OsmId, str]:
    timeout = 180
    query = (
        f'[out:json][timeout:{timeout}];'
        'relation(id:1668045);'  # https://www.openstreetmap.org/relation/1668045
        'map_to_area;'
        'nwr[name][!highway][!place][!brand][!wikidata][!website][!url](area);'
        'out tags qt;'
    )

    r = await HTTP.post(
        OVERPASS_API_INTERPRETER,
        data={'data': query},
        timeout=timeout * 2,
    )
    r.raise_for_status()

    id_tags: dict[OsmId, dict[str, str]] = {
        OsmId(f'{element["type"]}/{element["id"]}'): element['tags']
        for element in r.json()['elements']
        if any(k in element['tags'] for k in _REQUIRED_KEYS)
    }

    print('Looking up addresses in Nominatim')
    id_address: dict[OsmId, dict[str, str]] = {
        OsmId(f'{data["osm_type"]}/{data["osm_id"]}'): data['address']
        for ids in batched(id_tags.keys(), 50)
        for data in await nominatim_address_lookup(ids)
    }

    return {
        id: _build_query(tags, id_address.get(id) or {})  #
        for id, tags in id_tags.items()
    }


def _build_query(tags: dict[str, str], address: dict[str, str]) -> str:
    names = [
        f'{k}={v!r}'
        for k, v in tags.items()  #
        if k in {'alt_name', 'official_name'}
    ]
    names_query = f' ({", ".join(names)})' if names else ''
    addr = [
        f'{k}={v!r}'
        for k in ('road', 'house_number', 'postcode', 'village', 'town', 'city')
        if (v := address.get(k)) is not None
    ]
    addr_query = ', '.join(addr)
    required = [f'{k}={v!r}' for k, v in tags.items() if k in _REQUIRED_KEYS]
    required_query = f'. Mapped as {", ".join(required)}.' if required else ''
    return f'{tags["name"]!r}{names_query} near {addr_query}{required_query}'
