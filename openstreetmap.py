import asyncio
from collections.abc import Iterable
from typing import Any

import stamina
import xmltodict
from httpx import HTTPError

from config import (
    CHANGESET_ID_PLACEHOLDER,
    CREATED_BY,
    DEFAULT_CHANGESET_TAGS,
    OSM_TOKEN,
)
from db import DbItem, OsmId
from utils import HTTP


@stamina.retry(on=HTTPError)
async def osm_authorized_user() -> dict | None:
    r = await HTTP.get(
        'https://api.openstreetmap.org/api/0.6/user/details.json',
        headers={'Authorization': f'Bearer {OSM_TOKEN}'},
    )
    r.raise_for_status()
    return r.json()['user']


@stamina.retry(on=HTTPError)
async def _osm_element(osm_id: OsmId) -> dict:
    type, id = osm_id.split('/', 1)
    r = await HTTP.get(
        f'https://api.openstreetmap.org/api/0.6/{type}/{id}',
        headers={'Authorization': f'Bearer {OSM_TOKEN}'},
    )
    r.raise_for_status()
    return xmltodict.parse(r.text, force_list=('tag', 'nd', 'member'))['osm'][type]


async def upload_osmchange(items: Iterable[DbItem]) -> None:
    print('Preparing OSM Change...')
    osmchange = await _build_osmchange(items)
    changeset = xmltodict.unparse(
        {
            'osm': {
                'changeset': {
                    'tag': [
                        {'@k': k, '@v': v} for k, v in DEFAULT_CHANGESET_TAGS.items()
                    ]
                }
            }
        }
    )

    print('Uploading OSM Change...')
    r = await HTTP.put(
        'https://api.openstreetmap.org/api/0.6/changeset/create',
        content=changeset,
        headers={
            'Authorization': f'Bearer {OSM_TOKEN}',
            'Content-Type': 'text/xml; charset=utf-8',
        },
        follow_redirects=False,
    )
    r.raise_for_status()

    changeset_id = r.text
    osmchange = osmchange.replace(CHANGESET_ID_PLACEHOLDER, changeset_id)
    print(f'🌐 Changeset: https://www.openstreetmap.org/changeset/{changeset_id}')

    upload_resp = await HTTP.post(
        f'https://api.openstreetmap.org/api/0.6/changeset/{changeset_id}/upload',
        content=osmchange,
        headers={
            'Authorization': f'Bearer {OSM_TOKEN}',
            'Content-Type': 'text/xml; charset=utf-8',
        },
        timeout=180,
    )

    r = await HTTP.put(
        f'https://api.openstreetmap.org/api/0.6/changeset/{changeset_id}/close',
        headers={'Authorization': f'Bearer {OSM_TOKEN}'},
    )
    r.raise_for_status()

    if not upload_resp.is_success:
        raise Exception(
            f'Upload failed ({upload_resp.status_code}): {upload_resp.text}'
        )


async def _build_osmchange(items: Iterable[DbItem]) -> str:
    result = {
        'osmChange': {
            '@version': 0.6,
            '@generator': CREATED_BY,
            'modify': {'node': [], 'way': [], 'relation': []},
        }
    }
    modify: dict[str, list[dict[str, Any]]] = result['osmChange']['modify']

    async def task(item: DbItem) -> None:
        element = await _osm_element(item.id)
        if any(k['@k'] == 'website' for k in element['tag']):
            return
        element['@changeset'] = CHANGESET_ID_PLACEHOLDER
        element['tag'].append({'@k': 'website', '@v': item.link})
        modify[item.id.split('/', 1)[0]].append(element)

    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(task(item))

    return xmltodict.unparse(result)
