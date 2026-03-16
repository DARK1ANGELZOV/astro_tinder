# app/database/requests.py

from sqlalchemy import delete, update, select
from app.database.models import async_session
from app.database.models import User


async def add_user(tg_id: int, user_data: dict, recreate=False):
    async with async_session() as session:
        async with session.begin():
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
            if user and recreate:
                await session.execute(delete(User).where(User.tg_id == tg_id))

            new_user = User(
                tg_id=tg_id,
                name=user_data['name'],
                age=user_data['age'],
                description=user_data.get('description'),
                city=user_data['city'],
                photo1=user_data.get('photo1'),
                photo2=user_data.get('photo2'),
                photo3=user_data.get('photo3'),
                video=user_data.get('video'),
                longitude=user_data.get('longitude'),
                latitude=user_data.get('latitude'),
                instagram=user_data.get('instagram'),
                phone=user_data.get('phone'),
                is_search=user_data.get('is_search', True),
                min_age=user_data.get('min_age'),
                max_age=user_data.get('max_age'),
                gender=user_data['gender'],
                seeking_gender=user_data.get('seeking_gender', 'N'),
                is_registered=user_data.get('is_registered', False),
                lang_code=user_data.get('lang_code'),
                index_field=user_data.get('index_field'),
                username=user_data.get('username')
            )
            session.add(new_user)
            # Убираем session.commit() - транзакция коммитится автоматически
            # при выходе из блока session.begin()

        # Refresh нужно делать после коммита, но пока сессия еще открыта
        await session.refresh(new_user)
        return new_user


async def get_user_field(tg_id: int, field: str):
    async with async_session() as session:
        stmt = select(getattr(User, field)).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        return result.scalar()


async def update_user(tg_id: int, update_data: dict):
    async with async_session() as session:
        stmt = (
            update(User)
            .where(User.tg_id == tg_id)
            .values(**update_data)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0


async def set_search_status(tg_id: int, status: bool):
    await update_user(tg_id, {'is_search': status})


async def get_user_by_tg_id(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()


async def update_user_field(tg_id: int, field: str, value):
    """Helper to update a single field for a user.

    Maps common external field names to model attribute names (e.g. 'lang' -> 'lang_code').
    """
    # Map external field names to model column names if needed
    field_map = {
        'lang': 'lang_code',
    }
    real_field = field_map.get(field, field)
    return await update_user(tg_id, {real_field: value})