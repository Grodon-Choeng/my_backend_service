import asyncio
import logging

# Configure logging to see output from the context manager
logging.basicConfig(level=logging.INFO)


async def start_shell():
    """Starts an interactive IPython shell with the application context loaded."""
    try:
        from IPython import start_ipython
    except ImportError:
        print("IPython is not installed. Please run 'uv pip install ipython'")
        return

    from src.config import settings
    from src.core import model
    from src.core.context import application_context

    # Use the exact same context manager as the FastAPI app
    async with application_context() as ctx:
        banner = (
            "=================================================================\n"
            " Welcome to the interactive shell!\n"
            " Application context is loaded and available as `ctx`.\n"
            " Available variables: `ctx`, `settings`, `model`\n"
            " Example: `await ctx.redis.ping()`\n"
            "=================================================================\n"
        )

        # Add variables to the shell's namespace for direct access
        user_ns = {
            "ctx": ctx,
            "settings": settings,
            "model": model,
            "asyncio": asyncio,  # Useful for running other async tasks
        }

        # Start IPython
        start_ipython(argv=[], user_ns=user_ns, banner1=banner)


if __name__ == "__main__":
    asyncio.run(start_shell())
