import httpx
from config import get_config


class SearchResult:
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet

    def to_dict(self) -> dict:
        return {"title": self.title, "url": self.url, "snippet": self.snippet}


async def search(query: str, num_results: int | None = None, language: str = "zh-CN") -> list[dict]:
    """通过 SearXNG 搜索，支持 SOCKS5 代理出站。"""
    cfg = get_config()
    n = num_results or cfg.num_results

    proxy = cfg.socks5_proxy if cfg.socks5_proxy else None
    transport = None
    try:
        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
    except Exception:
        pass

    params = {
        "q": query,
        "format": "json",
        "language": language,
        "pageno": 1,
    }

    async with httpx.AsyncClient(transport=transport, timeout=30) as client:
        resp = await client.get(f"{cfg.searxng_url.rstrip('/')}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    raw = data.get("results", [])[:n]
    return [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("content", ""),
        ).to_dict()
        for r in raw
    ]


async def fetch_page(url: str) -> str:
    """通过代理抓取网页文本内容。"""
    cfg = get_config()
    proxy = cfg.socks5_proxy if cfg.socks5_proxy else None
    transport = None
    try:
        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
    except Exception:
        pass

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(transport=transport, timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text[:50000]  # 限制返回长度


async def test_proxy() -> dict:
    """测试代理连通性，返回出口 IP 信息。"""
    cfg = get_config()
    proxy = cfg.socks5_proxy if cfg.socks5_proxy else None

    try:
        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
        async with httpx.AsyncClient(transport=transport, timeout=15) as client:
            resp = await client.get("https://httpbin.org/ip")
            resp.raise_for_status()
            ip_info = resp.json()
            return {"ok": True, "ip": ip_info.get("origin", "unknown"), "proxy": cfg.socks5_proxy or "direct"}
    except Exception as e:
        return {"ok": False, "error": str(e), "proxy": cfg.socks5_proxy or "direct"}
