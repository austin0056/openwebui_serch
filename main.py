import os
import secrets
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from config import get_config, save_config, load_config, AppConfig, ADMIN_PASSWORD, normalize_proxy, _PROXY_RE
import searxng_client

app = FastAPI(title="SearXNG Proxy Search", version="1.0.0")

BASE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")

load_config()

# 简单 token 会话管理
_valid_tokens: set[str] = set()


def check_admin(request: Request) -> None:
    """检查管理面板登录状态"""
    token = request.cookies.get("admin_token", "")
    if token not in _valid_tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")


# --- API 鉴权 ---
def verify_api_key(request: Request) -> None:
    cfg = get_config()
    if not cfg.api_key:
        return
    key = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if key != cfg.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# --- 登录页 ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})


@app.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        token = secrets.token_hex(32)
        _valid_tokens.add(token)
        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie("admin_token", token, httponly=True, max_age=86400)
        return resp
    return templates.TemplateResponse("login.html", {"request": request, "error": "密码错误"})


@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("admin_token", "")
    _valid_tokens.discard(token)
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("admin_token")
    return resp


# --- Web 面板 (需登录) ---
@app.get("/", response_class=HTMLResponse)
async def panel(request: Request):
    token = request.cookies.get("admin_token", "")
    if token not in _valid_tokens:
        return RedirectResponse(url="/login", status_code=303)
    cfg = get_config()
    return templates.TemplateResponse("index.html", {"request": request, "config": cfg})


# --- 配置 API (需登录) ---
class ConfigUpdate(BaseModel):
    socks5_proxy: str = ""
    searxng_url: str = "http://127.0.0.1:8888"
    num_results: int = 5
    api_key: str = ""


@app.get("/api/config")
async def get_cfg(request: Request, _: None = Depends(check_admin)):
    cfg = get_config()
    return cfg.model_dump()


@app.post("/api/config")
async def update_cfg(request: Request, body: ConfigUpdate):
    token = request.cookies.get("admin_token", "")
    if token not in _valid_tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # 自动转换代理格式
    proxy = normalize_proxy(body.socks5_proxy)
    if proxy and not _PROXY_RE.match(proxy):
        return {
            "ok": False,
            "error": "代理格式错误! 支持的格式:\n"
                     "① socks5://用户名:密码@IP:端口\n"
                     "② socks5://IP:端口:用户名:密码\n"
                     "③ IP:端口:用户名:密码"
        }
    body.socks5_proxy = proxy
    cfg = AppConfig(**body.model_dump())
    save_config(cfg)
    return {"ok": True, "normalized_proxy": proxy}


# --- 搜索 API (API Key 鉴权) ---
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


# --- 代理测试 (需登录) ---
@app.post("/api/test-proxy")
async def api_test_proxy(request: Request):
    token = request.cookies.get("admin_token", "")
    if token not in _valid_tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        result = await searxng_client.test_proxy()
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "proxy": "unknown"}


# --- 健康检查 ---
@app.get("/api/health")
async def health():
    return {"status": "ok"}
