from aiogram import Bot, Dispatcher, types
from handlers import addServer, listServers
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import asyncio
import logging
import json

from utils import db

# Create the bot and dispatcher
with open('config/default.json', 'r') as f:
    data = json.load(f)['bot']

bot = Bot(token=data['token'])
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)


async def set_commands():
    await bot.set_my_commands(commands=[
        types.BotCommand(command='start', description='register user'),
        types.BotCommand(command='help', description='show this message'),
    ])


async def main():
    # Init db
    await db.connect_to_db()
    await db.init_db()

    # Register handlers
    addServer.register_handlers_server(dp)
    listServers.register_list_servers_handlers(dp)

    # Set commands
    await set_commands()

    # Start the Bot
    await dp.start_polling()


async def get_main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Servers list', callback_data='list_servers'))
    keyboard.add(types.InlineKeyboardButton(text='Add server', callback_data='add_server'))
    keyboard.add(types.InlineKeyboardButton(text='Seetings', callback_data='settings'))
    return keyboard


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer('Welcome to the telegram admin panel. If you have any questions, please contact @mootfrost.')
    resp = await db.create_user(message.from_user.id)
    if resp['status'] == 200:
        await message.answer('You have been successfully registered.')
    await message.answer(f'Hi, {message.from_user.first_name}!', reply_markup=await get_main_menu_keyboard())


@dp.message_handler(commands=['dash'])
async def dash(message: types.Message):
    await message.answer('Dashboard')


@dp.message_handler(commands=['help'])
async def get_help(message: types.Message):
    commands = 'Here is a list of commands:\n'
    for el in await bot.get_my_commands():
        commands += f'{el.command} - {el.description}\n'
    await message.answer(commands)


if __name__ == '__main__':
    asyncio.run(main())




