from collections.abc import Collection, Iterable
from datetime import datetime
from typing import NamedTuple, NewType

import polars as pl
from polars._typing import SchemaDict

from config import DATA_DIR

OsmId = NewType('OsmId', str)


class DbItem(NamedTuple):
    id: OsmId
    date: datetime
    query: str
    link: str | None
    added: bool


_PATH = DATA_DIR / 'db.parquet'
_SCHEMA: SchemaDict = {
    'id': pl.Utf8,
    'date': pl.Datetime,
    'query': pl.Utf8,
    'link': pl.Utf8,
    'added': pl.Boolean,
}


def db_filter(ids: set[OsmId]) -> None:
    if _PATH.is_file():
        ids.difference_update(
            pl.read_parquet(_PATH, columns=['id'], schema=_SCHEMA)
            .get_column('id')
            .to_list()
        )


def db_insert(items: Iterable[DbItem]) -> None:
    rows = [item._asdict() for item in items]
    (
        (
            pl.read_parquet(_PATH, schema=_SCHEMA)
            if _PATH.is_file()
            else pl.DataFrame(None, _SCHEMA)
        )
        .vstack(pl.DataFrame(rows, _SCHEMA))
        .write_parquet(
            _PATH,
            compression='uncompressed',  # using disk compression
        )
    )


def db_ready_to_upload() -> list[DbItem]:
    return [
        DbItem(**d)
        for d in (
            pl.scan_parquet(_PATH, schema=_SCHEMA)
            .filter(
                pl.col('link').is_not_null(),
                pl.col('added') == False,  # noqa: E712
            )
            .collect()
            .to_dicts()
        )
    ]


def db_mark_added(ids: Collection[OsmId]) -> None:
    (
        pl.scan_parquet(_PATH, schema=_SCHEMA)
        .with_columns(
            added=pl.when(pl.col('id').is_in(ids))
            .then(True)
            .otherwise(pl.col('added')),
        )
        .collect()
        .write_parquet(
            _PATH,
            compression='uncompressed',  # using disk compression
        )
    )
