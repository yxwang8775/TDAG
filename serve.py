import os

from fastapi import FastAPI
import config
from utils.config_manager import ConfigManager

app = FastAPI()

# Import your services
from api.python.interpreter import router as python_router
from api.arxiv.arxiv import router as arxiv_router
from api.bing.bing_service import router as bing_router
from api.calculator.calculator import router as calculator_router
from api.chemical.chemical import router as chemical_router
from api.ppt.ppt import router as ppt_router
from api.shell.shell import router as shell_router
from api.database.database import router as db_router
from api.wolfram_alpha.wolfram_alpha import router as wa_router
from api.weather.weather import router as weather_router  # 新增这一行
from api.google_calendar.calendar_service import router as calendar_router
from api.gmail.gmail import router as gmail_router  # 新增这一行

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Incoming request: {request.method} {request.url}")
        try:
            response = await call_next(request)
        except Exception as e:
            print(f"Request error: {str(e)}")
            raise e from None
        else:
            print(f"Outgoing response: {response.status_code}")
        return response


app.add_middleware(LoggingMiddleware)

# Create a dictionary that maps service names to their routers
services = {
    "python_executor": python_router,
    "calculator": calculator_router,
    "arxiv": arxiv_router,
    "bing": bing_router,
    "chemical": chemical_router,
    "ppt": ppt_router,
    "shell": shell_router,
    "database": db_router,
    "wolframalpha": wa_router,
    "weather": weather_router,
    "calendar": calendar_router,
    "gmail": gmail_router

}

# Include only the routers for the services listed in server_list
for service in config.server_list:
    if service in services:
        app.include_router(services[service])

proxy_manager = ConfigManager()
proxy_manager.apply_proxies()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8079)
