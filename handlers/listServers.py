import os
import json

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from utils import db, checkServerConnection

with open('config/default.json', 'r') as f:
    config = json.load(f)['page']


class ListServers(StatesGroup):
    waiting_for_action = State()
    waiting_for_list_server = State()
    show_only_online = State()
    show_only_offline = State()
    show_all = State()


async def get_servers_page(message: types.Message, page: int, state: FSMContext):
    resp = await db.get_servers(message.chat.id)  # Тут почему-то данные пользователя в ключе chat

    if not resp['status'] != 404:
        await message.answer('You have no servers!')
        return

    servers = resp['message']
    data = await state.get_data()

    if data['sort'] == 'online':
        await message.answer('It may take a while to check connections...')
        servers = [server for server in servers if await checkServerConnection.check_server_connection(server)]
        if not servers:
            await message.answer('No servers are online!')
            return
    elif data['sort'] == 'offline':
        await message.answer('It may take a while to check connections...')
        servers = [server for server in servers if not await checkServerConnection.check_server_connection(server)]
        if not servers:
            await message.answer('All servers are online!')
            return

    result = f'You have {len(servers)} server'
    if len(servers) != 1:
        result += 's'
    result += ':\n'

    for server in servers[(page - 1) * config['per_page']: page * config['per_page']]:
        result += f'{server.id} - {server.name}\n'

    total = len(servers) // config['per_page']
    if total == 0:
        total = 1
    await message.answer(result, reply_markup=await get_page_markup(page, total))


async def process_page_callback(call: types.CallbackQuery, state: FSMContext):
    await get_servers_page(call.message, int(call.data.split('_')[1]), state)


async def get_page_markup(page: int, total: int):
    print(f'{page}-{total}')
    markup = types.InlineKeyboardMarkup()
    if page == 0 and page != total:
        markup.add(types.InlineKeyboardButton('Next', callback_data=f'page_{page+1}'))
    elif page == total and page != 1:
        markup.add(types.InlineKeyboardButton('Previous', callback_data=f'page_{page-1}'))
    elif page == total and page == 1:
        return
    else:
        markup.add(types.InlineKeyboardButton('Previous', callback_data=f'page_{page-1}'))
        markup.add(types.InlineKeyboardButton('Next', callback_data=f'page_{page+1}'))
    return markup


async def get_actions_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Show only online', callback_data='show_only_online'))
    markup.add(types.InlineKeyboardButton('Show only offline', callback_data='show_only_offline'))
    markup.add(types.InlineKeyboardButton('Show all', callback_data='show_all'))
    return markup


async def list_servers_command(message: types.Message, state: FSMContext):
    await state.reset_data()
    await message.answer('Choose action:', reply_markup=await get_actions_markup())


async def list_servers_callback(call: types.CallbackQuery, state: FSMContext):
    await state.reset_data()
    await call.message.answer('Choose action:', reply_markup=await get_actions_markup())


async def show_online(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(sort='online')
    await get_servers_page(call.message, 1, state)


async def show_offline(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(sort='offline')
    await get_servers_page(call.message, 1, state)


async def show_all(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(sort='all')
    await get_servers_page(call.message, 1, state)


def register_list_servers_handlers(dp):
    # Handlers for commands
    dp.register_message_handler(list_servers_command, commands='listservers')
    dp.register_callback_query_handler(list_servers_callback, lambda call: call.data == 'list_servers')

    # Handlers for sort options
    dp.register_callback_query_handler(show_online, lambda call: call.data == 'show_only_online')
    dp.register_callback_query_handler(show_offline, lambda call: call.data == 'show_only_offline')
    dp.register_callback_query_handler(show_all, lambda call: call.data == 'show_all')

    # Handlers for pages
    dp.register_callback_query_handler(process_page_callback, lambda call: call.data.startswith('page'))


