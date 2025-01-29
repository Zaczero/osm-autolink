import asyncio
from datetime import UTC, datetime
from itertools import batched

from ai import find_link
from config import OPENAI_RPM
from db import DbItem, OsmId, db_filter, db_insert, db_mark_added, db_ready_to_upload
from openstreetmap import osm_authorized_user, upload_osmchange
from overpass import overpass_query


async def main():
    print('Querying Overpass API')
    elements = await overpass_query()

    print(f'Filtering processed POIs ({len(elements)=})')
    ids = set(elements.keys())
    db_filter(ids)
    elements = {k: v for k, v in elements.items() if k in ids}
    print(f'New POIs: {len(elements)=}')

    async def task(id: OsmId, query: str) -> DbItem:
        print(f'[{id}] Searching for a link: {query}')
        link = await find_link(query)
        if link:
            print(f'[{id}] Found a matching link: {link} for: {query}')
        return DbItem(
            id=id,
            date=datetime.now(UTC),
            query=query,
            link=link,
            added=False,
        )

    for batch in batched(elements.items(), OPENAI_RPM - 5):
        print(f'Processing a batch of {len(batch)} elements')
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(task(id, query)) for id, query in batch]

        print('Saving batch results to the database')
        items = [task.result() for task in tasks]
        db_insert(items)

        print('Sleeping for 1 minute...')
        await asyncio.sleep(60)

    display_name = (await osm_authorized_user())['display_name']  # pyright: ignore [reportOptionalSubscript]
    print(f'👤 Welcome, {display_name}!')

    while True:
        items = db_ready_to_upload()
        if not items:
            print('Nothing more to upload, bye!')
            break

        for i, item in enumerate(items):
            type, id = item.id.split('/', 1)
            print(f'🔗 [{i}] https://www.openstreetmap.org/{type}/{id} → {item.link}')

        response = input('Proceed with uploading? (y/n/<ignore-number>) ')
        if response.isdigit():
            id = items[int(response)].id
            print(f'Ignoring item [{response}] {id}')
            db_mark_added([id])
        elif response.lower() == 'n':
            print('Aborting...')
            return
        elif response.lower() == 'y':
            await upload_osmchange(items)
            db_mark_added([item.id for item in items])
            print('Done! Done! Done!')
            break


if __name__ == '__main__':
    asyncio.run(main())
