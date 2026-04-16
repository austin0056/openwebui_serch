import json
import os
import re
import subprocess
from pathlib import Path
from pydantic import BaseModel, Field

CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/data/config.json"))
SEARXNG_SETTINGS = Path(os.getenv("SEARXNG_SETTINGS_PATH", "/etc/searxng/settings.yml"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

_PROXY_RE = re.compile(r'^socks5h?://.+@.+:\d+$')

SEARXNG_TEMPLATE = """use_default_settings: true

server:
  bind_address: "127.0.0.1"
  port: 8888
  secret_key: "searxng-proxy-search-secret-key"

search:
  safe_search: 0
  autocomplete: "google"
  default_lang: "zh-CN"
  formats:
    - html
    - json

engines:
  - name: google
    engine: google
    shortcut: g
    disabled: false
  - name: bing
    engine: bing
    shortcut: b
    disabled: false
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    disabled: false
  - name: wikipedia
    engine: wikipedia
    shortcut: wp
    disabled: false

outgoing:
  request_timeout: 15.0
  useragent_suffix: ""
{proxy_section}"""


class AppConfig(BaseModel):
    socks5_proxy: str = Field("", description="SOCKS5 代理地址")
    searxng_url: str = Field("http://127.0.0.1:8888", description="SearXNG 实例地址")
    num_results: int = Field(5, description="默认搜索结果数量", ge=1, le=20)
    api_key: str = Field("", description="API 访问密钥 (留空则不验证)")


_config: AppConfig | None = None


def load_config() -> AppConfig:
    global _config
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            _config = AppConfig(**data)
        except Exception:
            _config = AppConfig()
    else:
        _config = AppConfig()
    # 自动修复：清除格式错误的代理地址
    if _config.socks5_proxy and not _PROXY_RE.match(_config.socks5_proxy):
        _config.socks5_proxy = ""
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(_config.model_dump_json(indent=2), encoding="utf-8")
        except Exception:
            pass
    # 启动时也同步一次 SearXNG 代理
    _update_searxng_proxy(_config.socks5_proxy)
    return _config


def save_config(cfg: AppConfig) -> None:
    global _config
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
    _config = cfg
    _update_searxng_proxy(cfg.socks5_proxy)


def get_config() -> AppConfig:
    global _config
    if _config is None:
        return load_config()
    return _config


def _update_searxng_proxy(socks5_proxy: str) -> None:
    """重写 SearXNG settings.yml 并重启 SearXNG。"""
    if not SEARXNG_SETTINGS.parent.exists():
        return

    if socks5_proxy:
        proxy_section = f'  proxies:\n    all://:\n      - {socks5_proxy}\n  extra_proxy_timeout: 10.0'
    else:
        proxy_section = ""

    content = SEARXNG_TEMPLATE.format(proxy_section=proxy_section)
    SEARXNG_SETTINGS.write_text(content, encoding="utf-8")

    try:
        subprocess.run(
            ["supervisorctl", "restart", "searxng"],
            timeout=10, capture_output=True
        )
    except Exception:
        pass
