from config import OVERPASS_API_INTERPRETER
from db import OsmId
from utils import HTTP

_REQUIRED_KEYS = {'amenity', 'shop', 'craft', 'office'}


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
    result = {}

    for element in r.json()['elements']:
        tags = element['tags']
        if any(k in tags for k in _REQUIRED_KEYS):
            id = OsmId(f'{element["type"]}/{element["id"]}')
            query = _build_query(tags)
            result[id] = query

    return result


def _build_query(tags: dict[str, str]) -> str:
    names = [
        f'{k}={v!r}'
        for k, v in tags.items()  #
        if k in {'alt_name', 'official_name'}
    ]
    names_query = f' ({", ".join(names)})' if names else ''
    tags.setdefault('addr:city', 'Radom')
    tags.setdefault('addr:province', 'Mazowieckie')
    addr = [
        f'{k}={v!r}'
        for k, v in tags.items()  #
        if k[:5] == 'addr:'
    ]
    addr_query = ', '.join(addr)
    required = [f'{k}={v!r}' for k, v in tags.items() if k in _REQUIRED_KEYS]
    required_query = f'. POI category: {", ".join(required)}' if required else ''
    return f'{tags["name"]!r}{names_query} near {addr_query}{required_query}'
