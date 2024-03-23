"""Администрирование телеграмм бота"""
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_app.database.models import User, user
from bot_app.filters.is_admin import IsAdmin
from bot_app.keyboards.reply import ADMIN_KBRD, MAIN_MENU_KBRD

logger.add("error_logs.log", level="ERROR")

ADMIN_ONLY = 'Данные действия доступны только администратору'
DELETE_COMPLITE = 'Пользователь удалён'
NOT_FOUND = 'Пользователь не найден'
ADD_ID = 'Введите id'
ALL_USERS = 'Список всех пользователей'
DELETE_USER = 'Удалить пользователя'
DEACTIVATE_USER = 'Деактивировать пользователя'
DEACTIVATE_COMPLITE = 'Пользователь дективирован'
MAIN_MENU = 'Главное меню'
RETURN_TO_MENU = 'Вы вернулись в главное меню'
ADD_USER_TO_ADMIN = 'Добавить пользователя в админы'
ADD_EMAIL = 'Введите почту пользователя'
SUCCESS = 'Пользователь стал администратором'
ANTI_SUCCESS = 'Пользователь перестал быть администратором'
NON_USER = 'Такого пользователя не существует'
ADMIN_ALREADY = 'Этот пользователь уже администратор'
REMOVE_USER_FROM_ADMIN = 'Удалить пользователя из админов'
NON_USER_ADMIN = 'Этот пользователь не является админом'


admin_router = Router()
admin_router.message.filter(IsAdmin())


class DelUser(StatesGroup):
    tg_id = State()


class DeactiveUser(StatesGroup):
    tg_id = State()


class AddUserToAdmin(StatesGroup):
    email = State()
    rem_email = State()

    texts = {
        'AddUser:mail': 'Введите мэйл заново:',
    }


@admin_router.message(StateFilter(None), Command('admin'))
async def get_admin_commands(message: types.Message, session: AsyncSession):
    """Команда для администрирования пользователей."""
    try:
        await message.answer(ADMIN_ONLY, reply_markup=ADMIN_KBRD)
    except Exception as e:
        logger.error(f"Error in get_admin_commands function: {e}")


@admin_router.message(F.text == ALL_USERS)
async def get_user_list(message: types.Message, session: AsyncSession):
    """Получить список всех пользователей."""
    try:
        user_list_str = '\n'.join(
            repr(user) for user in await user.get_all(session)
        )
        if user_list_str:
            await message.answer(user_list_str)
        else:
            await message.answer(NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in get_user_list function: {e}")


@admin_router.message(StateFilter(None), F.text == DELETE_USER)
async def delete_user(message: types.Message, state: FSMContext):
    """Удалить пользователя. Ожидание id пользователя"""
    try:
        await message.answer(
            ADD_ID,
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(DelUser.tg_id)
    except Exception as e:
        logger.error(f"Error in delete_user function: {e}")


@admin_router.message(DelUser.tg_id, F.text)
async def delete_user_id(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession
):
    """Удаление пользователя по tg_id."""
    try:
        await state.update_data(tg_id=message.text)
        if await user.remove(session, await user.get(session, int(message.text))):
            await message.answer(DELETE_COMPLITE, reply_markup=ADMIN_KBRD)
            await state.clear()
        message.answer(NOT_FOUND, reply_markup=ADMIN_KBRD)
    except Exception as e:
        logger.error(f"Error in delete_user_id function: {e}")


@admin_router.message(
        StateFilter(None),
        F.text == DEACTIVATE_USER
)
async def deactive_user(message: types.Message, state: FSMContext):
    """Деактивировать пользователя. Ожидание id пользователя"""
    try:
        await message.answer(ADD_ID, reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(DeactiveUser.tg_id)
    except Exception as e:
        logger.error(f"Error in deactive_user function: {e}")


@admin_router.message(DeactiveUser.tg_id, F.text)
async def deactivate_user_id(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession
):
    """Деактивация пользователя по id."""
    try:
        await state.update_data(tg_id=message.text)
        deactive = await user.activate_deactivate_user(session, int(message.text))
        if deactive:
            await message.answer(
                DEACTIVATE_COMPLITE,
                reply_markup=ADMIN_KBRD
            )
            await state.clear()
        else:
            await message.answer(NOT_FOUND, reply_markup=ADMIN_KBRD)
            await state.clear()
    except Exception as e:
        logger.error(f"Error in deactivate_user_id function: {e}")


@admin_router.message(F.text == MAIN_MENU)
async def menu(message: types.Message):
    """Вернуться в главное меню."""
    try:
        await message.answer(RETURN_TO_MENU, reply_markup=MAIN_MENU_KBRD)
    except Exception as e:
        logger.error(f"Error in menu function: {e}")


@admin_router.message(F.text == ADD_USER_TO_ADMIN)
async def add_user_to_admin(message: types.Message, state: FSMContext,
    session: AsyncSession):
    """Добавить пользователя в админы."""
    try:
        await state.update_data(email=message.text)
        await message.answer(ADD_EMAIL)
        await state.set_state(AddUserToAdmin.email)
    except Exception as e:
        logger.error(f"Error in add_user_to_admin function: {e}")


@admin_router.message(F.text == REMOVE_USER_FROM_ADMIN)
async def remove_user_from_admin(message: types.Message, state: FSMContext,
    session: AsyncSession):
    """Удалить пользователя из админов."""
    try:
        await state.update_data(email=message.text)
        await message.answer(ADD_EMAIL)
        await state.set_state(AddUserToAdmin.rem_email)
    except Exception as e:
        logger.error(f"Error in remove_user_from_admin function: {e}")


@admin_router.message(AddUserToAdmin.email)
async def add_to_admin(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession
):
    try:
        result = await session.execute(select(User).filter(User.email == message.text))
        user = result.scalars().one_or_none()
        if user:
            if user.is_admin == True:
                await message.answer(ADMIN_ALREADY)
            else:
                user.is_admin = True
                await session.commit()
                await message.answer(SUCCESS)
                await state.clear()
        else:
            await message.answer(NON_USER)
    except Exception as e:
        logger.error(f"Error in add_to_admin function: {e}")


@admin_router.message(AddUserToAdmin.rem_email)
async def remove_from_admin(
    message: types.Message,
    session: AsyncSession
):
    try:
        result = await session.execute(select(User).filter(User.email == message.text))
        user = result.scalars().one_or_none()
        if user:
            if user.is_admin == True:
                user.is_admin = False
                await session.commit()
                await message.answer(ANTI_SUCCESS)
            else:
                await message.answer(NON_USER_ADMIN)
        else:
            await message.answer(NON_USER)
    except Exception as e:
        logger.error(f"Error in remove_from_admin function: {e}")
