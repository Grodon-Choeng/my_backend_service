from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from src.core.context import AppContext, application_context


# 使用我们的上下文管理器定义 FastAPI 的生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with application_context() as ctx:
        app.state.context = ctx  # 将上下文存储在 app.state 中
        yield


app = FastAPI(lifespan=lifespan)


# 创建一个依赖项，以便在路由中轻松获取上下文
def get_context(request: Request) -> AppContext:
    return request.app.state.context
