from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import db
from models.server import Server


class AddServer(StatesGroup):
    waiting_for_server_name = State()
    waiting_for_server_ip = State()
    waiting_for_server_port = State()
    waiting_for_server_password = State()


async def add_server(message: types.Message):
    await message.answer('Enter server name:')
    await AddServer.waiting_for_server_name.set()


async def name_chosen(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Enter server ip:')
    await AddServer.next()


async def ip_chosen(message: types.Message, state: FSMContext):
    if message.text.count('.') != 3:  # Check if ip is valid
        await message.answer('IP must be in format x.x.x.x!')
        await AddServer.waiting_for_server_ip.set()
        return

    await state.update_data(ip=message.text)
    await message.answer('Enter server port:')
    await AddServer.next()


async def port_chosen(message: types.Message, state: FSMContext):
    if not message.text.isdigit():  # Check if port is integer
        await message.answer('Port must be a number!')
        await AddServer.waiting_for_server_port.set()
        return

    if 1024 > int(message.text) or int(message.text) > 65535:
        await message.answer('Port must be in range 1024-65535!')
        await AddServer.waiting_for_server_port.set()
        return

    await state.update_data(port=int(message.text))
    await message.answer('Enter server password:')
    await AddServer.next()


async def password_chosen(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    await state.update_data(owner_id=message.from_user.id)
    await db.add_server(Server(**await state.get_data()))
    await message.answer('Server added successfully!')
    await state.finish()


def register_handlers_server(dp: Dispatcher):
    dp.register_message_handler(add_server, commands='addServer')
    dp.register_callback_query_handler(add_server, lambda call: call.data == 'add_server')

    dp.register_message_handler(name_chosen, state=AddServer.waiting_for_server_name)
    dp.register_message_handler(ip_chosen, state=AddServer.waiting_for_server_ip)
    dp.register_message_handler(port_chosen, state=AddServer.waiting_for_server_port)
    dp.register_message_handler(password_chosen, state=AddServer.waiting_for_server_password)
