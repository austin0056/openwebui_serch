import json
import os
from pathlib import Path
from pydantic import BaseModel, Field

CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/app/data/config.json"))


class AppConfig(BaseModel):
    socks5_proxy: str = Field("", description="SOCKS5 代理地址, 如 socks5://user:pass@host:port")
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
    return _config


def save_config(cfg: AppConfig) -> None:
    global _config
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
    _config = cfg


def get_config() -> AppConfig:
    global _config
    if _config is None:
        return load_config()
    return _config
