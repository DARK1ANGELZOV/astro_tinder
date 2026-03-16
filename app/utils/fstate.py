from aiogram.fsm.context import FSMContext

async def update_nested(state: FSMContext, key: str, subkey: str, value: any):
    data = await state.get_data()
    container = data.get(key, {})
    container[subkey] = value
    await state.update_data({key: container})
