from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request

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


@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}


@app.get("/ping-redis")
async def ping_redis(ctx: AppContext = Depends(get_context)):
    # 使用依赖注入获取的 redis 客户端
    from src.core.redis import ping

    is_ok = await ping(ctx.redis)
    return {"redis_ok": is_ok}


@app.get("/ping-db")
async def ping_db():
    from src.core.databases import check_db_connection

    db_ok = await check_db_connection()
    return {"db_ok": db_ok}
