from httpx import AsyncClient

from config import USER_AGENT

HTTP = AsyncClient(
    headers={'User-Agent': USER_AGENT},
    timeout=60,
    follow_redirects=True,
)
