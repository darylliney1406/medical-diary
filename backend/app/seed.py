"""
Startup seed script.
Creates the initial admin user from environment variables if no users exist.
Run after alembic upgrade head, before starting uvicorn.
"""
import asyncio
import logging
from sqlalchemy import select
from .database import AsyncSessionLocal
from .models.user import User, UserRole
from .services.auth import create_user
from .config import get_settings

log = logging.getLogger(__name__)


async def seed() -> None:
    settings = get_settings()

    if not all([settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD, settings.ADMIN_NAME]):
        log.info("Seed: ADMIN_EMAIL/ADMIN_PASSWORD/ADMIN_NAME not set — skipping.")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            log.info("Seed: users already exist — skipping.")
            return

        await create_user(
            session,
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            name=settings.ADMIN_NAME,
            role=UserRole.admin,
        )
        log.info("Seed: admin user created (%s).", settings.ADMIN_EMAIL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
