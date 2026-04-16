from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from config import get_config, save_config, load_config, AppConfig
import searxng_client

app = FastAPI(title="SearXNG Proxy Search", version="1.0.0")

BASE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")

# 启动时加载配置
load_config()


# --- 鉴权依赖 ---
def verify_api_key(request: Request) -> None:
    cfg = get_config()
    if not cfg.api_key:
        return
    key = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if key != cfg.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# --- Web 面板 ---
@app.get("/", response_class=HTMLResponse)
async def panel(request: Request):
    cfg = get_config()
    return templates.TemplateResponse("index.html", {"request": request, "config": cfg})


# --- 配置 API ---
class ConfigUpdate(BaseModel):
    socks5_proxy: str = ""
    searxng_url: str = "http://127.0.0.1:8888"
    num_results: int = 5
    api_key: str = ""


@app.get("/api/config")
async def get_cfg():
    cfg = get_config()
    return cfg.model_dump()


@app.post("/api/config")
async def update_cfg(body: ConfigUpdate):
    cfg = AppConfig(**body.model_dump())
    save_config(cfg)
    return {"ok": True}


# --- 搜索 API ---
class SearchRequest(BaseModel):
    query: str
    num_results: int | None = None
    language: str = "zh-CN"


@app.post("/api/search")
async def api_search(body: SearchRequest, _: None = Depends(verify_api_key)):
    try:
        results = await searxng_client.search(body.query, body.num_results, body.language)
        cfg = get_config()
        return {
            "results": results,
            "proxy_used": bool(cfg.socks5_proxy),
            "search_engine": "searxng",
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# --- 抓取网页 ---
class FetchRequest(BaseModel):
    url: str


@app.post("/api/fetch")
async def api_fetch(body: FetchRequest, _: None = Depends(verify_api_key)):
    try:
        text = await searxng_client.fetch_page(body.url)
        return {"content": text}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# --- 代理测试 ---
@app.post("/api/test-proxy")
async def api_test_proxy():
    try:
        result = await searxng_client.test_proxy()
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "proxy": "unknown"}


# --- 健康检查 ---
@app.get("/api/health")
async def health():
    return {"status": "ok"}
