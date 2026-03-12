# api/lazada.py
"""Lazada OAuth 认证回调 API"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
from crawler.products.lazada_api import LazadaOAuthClient
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/lazada", tags=["lazada"])


@router.get("/auth/url")
async def get_lazada_auth_url(country: str = "th"):
    """
    生成 Lazada 授权 URL

    用户需要在浏览器中打开此 URL 进行授权
    """
    try:
        app_key = settings.LAZADA_APP_KEY
        app_secret = settings.LAZADA_APP_SECRET
        redirect_uri = settings.LAZADA_REDIRECT_URI

        if not all([app_key, app_secret, redirect_uri]):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Lazada API 凭证未配置",
                    "message": "请在环境变量中配置 LAZADA_APP_KEY, LAZADA_APP_SECRET, LAZADA_REDIRECT_URI"
                }
            )

        oauth_client = LazadaOAuthClient(
            app_key=app_key,
            app_secret=app_secret,
            redirect_uri=redirect_uri
        )

        auth_url = oauth_client.get_authorization_url(country=country)
        await oauth_client.close()

        return {
            "auth_url": auth_url,
            "message": "请在浏览器中打开上述 URL 完成授权",
            "country": country
        }

    except Exception as e:
        logger.error(f"生成授权 URL 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def lazada_oauth_callback(code: str = None, error: str = None):
    """
    Lazada OAuth 回调端点

    用户授权后，Lazada 会重定向到这个端点，带上 code 参数
    """
    if error:
        logger.error(f"Lazada OAuth 错误: {error}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "OAuth 授权被拒绝或失败",
                "details": error
            }
        )

    if not code:
        return JSONResponse(
            status_code=400,
            content={"error": "缺少授权码 code 参数"}
        )

    try:
        app_key = settings.LAZADA_APP_KEY
        app_secret = settings.LAZADA_APP_SECRET
        redirect_uri = settings.LAZADA_REDIRECT_URI

        oauth_client = LazadaOAuthClient(
            app_key=app_key,
            app_secret=app_secret,
            redirect_uri=redirect_uri
        )

        # 使用 code 换取 access_token
        token_data = await oauth_client.get_access_token(code)
        await oauth_client.close()

        # 返回获取到的凭证信息
        # 注意: 生产环境中应该将此信息存储到数据库或配置中
        return {
            "success": True,
            "message": "OAuth 授权成功",
            "data": {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in"),
                "country": token_data.get("country"),
                "account": token_data.get("account"),
                "seller_id": token_data.get("seller_id"),
                # 注意: 请将以下凭证保存到环境变量或数据库中
                # LAZADA_ACCESS_TOKEN=...
                # LAZADA_REFRESH_TOKEN=...
            }
        }

    except Exception as e:
        logger.error(f"处理 OAuth 回调失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token/refresh")
async def refresh_lazada_token(refresh_token: str):
    """
    刷新 Lazada Access Token
    """
    try:
        app_key = settings.LAZADA_APP_KEY
        app_secret = settings.LAZADA_APP_SECRET
        redirect_uri = settings.LAZADA_REDIRECT_URI

        if not all([app_key, app_secret]):
            return JSONResponse(
                status_code=400,
                content={"error": "Lazada API 凭证未配置"}
            )

        oauth_client = LazadaOAuthClient(
            app_key=app_key,
            app_secret=app_secret,
            redirect_uri=redirect_uri
        )

        token_data = await oauth_client.refresh_access_token(refresh_token)
        await oauth_client.close()

        return {
            "success": True,
            "data": {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in"),
            }
        }

    except Exception as e:
        logger.error(f"刷新 token 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_lazada_status():
    """
    获取 Lazada API 配置状态
    """
    app_key = settings.LAZADA_APP_KEY
    app_secret = settings.LAZADA_APP_SECRET
    access_token = settings.LAZADA_ACCESS_TOKEN

    configured = {
        "app_key": bool(app_key),
        "app_secret": bool(app_secret),
        "access_token": bool(access_token),
        "fully_configured": all([app_key, app_secret, access_token])
    }

    if configured["fully_configured"]:
        return {
            "status": "ready",
            "message": "Lazada API 已配置完成",
            "country": settings.LAZADA_DEFAULT_COUNTRY
        }
    else:
        return {
            "status": "not_ready",
            "message": "Lazada API 配置不完整",
            "missing": [k for k, v in configured.items() if not v and k != "fully_configured"]
        }
