"""
title: SearXNG Proxy Web Search
author: openwebui_serch
author_url: https://github.com/openwebui_serch
description: 通过部署在 Zeabur 上的 SearXNG 代理搜索服务搜索互联网内容，支持静态住宅 IP 代理
required_open_webui_version: 0.4.0
requirements: httpx
version: 1.0.0
licence: MIT
"""

import httpx
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any


class Tools:
    class Valves(BaseModel):
        api_base_url: str = Field(
            "https://your-service.zeabur.app",
            description="SearXNG 代理搜索服务的地址 (部署在 Zeabur 上的服务 URL)",
        )
        api_key: str = Field(
            "",
            description="API 访问密钥 (与服务端管理面板中设置的密钥一致)",
        )
        num_results: int = Field(
            5,
            description="默认返回的搜索结果数量",
            ge=1,
            le=20,
        )

    def __init__(self):
        self.valves = self.Valves()

    async def web_search(
        self,
        query: str,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ) -> str:
        """
        搜索互联网内容。通过静态住宅 IP 代理访问 SearXNG 搜索引擎获取最新的网页搜索结果。
        :param query: 搜索关键词
        :return: 格式化的搜索结果文本
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"正在搜索: {query}", "done": False}})

        url = f"{self.valves.api_base_url.rstrip('/')}/api/search"
        headers = {"Content-Type": "application/json"}
        if self.valves.api_key:
            headers["Authorization"] = f"Bearer {self.valves.api_key}"

        payload = {"query": query, "num_results": self.valves.num_results}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": f"搜索失败: {e}", "done": True}})
            return f"搜索出错: {str(e)}"

        results = data.get("results", [])
        if not results:
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": "未找到结果", "done": True}})
            return "未找到相关搜索结果。"

        lines = [f"搜索 \"{query}\" 的结果:\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r['title']}]({r['url']})")
            if r.get("snippet"):
                lines.append(f"   {r['snippet']}")
            lines.append("")

        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"找到 {len(results)} 条结果", "done": True}})

        return "\n".join(lines)

    async def fetch_page(
        self,
        url: str,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ) -> str:
        """
        通过代理抓取指定网页的文本内容。用于获取搜索结果中某个链接的详细内容。
        :param url: 要抓取的网页 URL
        :return: 网页的文本内容
        """
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"正在抓取: {url}", "done": False}})

        api_url = f"{self.valves.api_base_url.rstrip('/')}/api/fetch"
        headers = {"Content-Type": "application/json"}
        if self.valves.api_key:
            headers["Authorization"] = f"Bearer {self.valves.api_key}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(api_url, json={"url": url}, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": f"抓取失败: {e}", "done": True}})
            return f"抓取出错: {str(e)}"

        content = data.get("content", "")
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": "抓取完成", "done": True}})

        return content[:30000] if content else "页面内容为空。"
