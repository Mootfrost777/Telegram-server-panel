import io
import urllib.parse
import requests
import json
from utils import db

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

with open('config/default.json', 'r') as f:
    url = json.load(f)['run_command']


class SendCommand(StatesGroup):
    waiting_for_server = State()
    waiting_for_command = State()
    waiting_for_dir = State()


async def get_servers_keyboard(servers):
    keyboard = types.InlineKeyboardMarkup()
    for server in servers:
        keyboard.add(types.InlineKeyboardButton(text=server.name, callback_data=f'send_command_server_{server.id}'))
    keyboard.add(types.InlineKeyboardButton(text='Back', callback_data='back'),
                 types.InlineKeyboardButton(text='Next', callback_data='next'))
    keyboard.add(types.InlineKeyboardButton(text='Cancel', callback_data='cancel'))
    return keyboard


async def send_command_command(message: types.Message, state: FSMContext):
    await state.update_data(command=message.text)
    await message.answer('Checking connections. This may take a while...')
    resp = await db.get_servers(message.from_user.id)
    if resp['status'] == 404:
        await message.answer('You have no servers. Please add one.')
        await state.finish()
    servers = resp['message']
    # servers = [server for server in servers if os.system("ping -c 1 " + f'{server.ip}:{server.port}') == 0]
    await message.answer('Select server:', reply_markup=await get_servers_keyboard(servers))
    await SendCommand.next()


async def send_command_callback(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(command=call.message.text)
    await call.message.answer('Checking connections. This may take a while...')
    resp = await db.get_servers(call.message.from_user.id)
    if resp['status'] == 404:
        await call.message.answer('You have no servers. Please add one.')
        await state.finish()
    servers = resp['message']
    # servers = [server for server in servers if os.system("ping -c 1 " + f'{server.ip}:{server.port}') == 0]
    await call.message.answer('Select server:', reply_markup=await get_servers_keyboard(servers))
    await SendCommand.waiting_for_command.set()


async def server_selected(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(server=call.data.split('_')[-1])
    await call.message.answer('Enter command to execute:')
    await SendCommand.next()


async def command_sent(message: types.Message, state: FSMContext):
    await state.update_data(command=message.text)
    await message.answer('Enter directory, send "_" to leave empty:')
    await SendCommand.next()


async def dir_selected(message: types.Message, state: FSMContext):
    await state.update_data(dir=message.text)
    data = await state.get_data()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Yes', callback_data='yes'),
                 types.InlineKeyboardButton(text='No', callback_data='no'))
    await message.answer(f"Selected server id: {data['server']}\n"
                         f"Directory: {data['dir']}\n"
                         f"Are you sure you want to send command '{data['command']}' to this server?\n"
                         f"This action cannot be undone!\n"
                         f"Press 'Yes' to confirm or 'No' to cancel.",
                         reply_markup=keyboard)
    await SendCommand.next()


async def send_command(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    server = await db.get_server(int(data['server']))
    server = server['message']
    params = {'command': data['command'], 'directory': data['dir']}
    path = url.replace('{ip}', server.ip)\
        .replace('{port}', str(server.port))
    path += urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    try:
        resp = requests.post(path, timeout=20).json()
    except TimeoutError:
        await call.message.answer(f'Command is running too long or server is not responding.\n'
                                  f'Problem may also be caused by e.g. long polling script.\n'
                                  f'In this case command will be executed in background and you can ignore this message.\n'
                                  f'Using long polling script is not recommended because you will not be able to control it!')
        await state.finish()
        return

    if resp['status'] == 200:
        reply = f'Command executed without errors. \n'
    else:
        reply = f'Command executed with errors. \n'

    if resp['message'] == '':
        reply += 'No output.'
        await call.message.answer(reply)
    elif len(resp['message']) < 200:
        reply += f'Output: \n<pre>{resp["message"]}</pre>'
        await call.message.answer(reply, parse_mode=types.ParseMode.HTML)
    else:
        reply += f'Output is too long and pinned as a file for more comfortable reading.'
        file = types.InputFile(io.BytesIO(resp['message'].encode()), filename='output.txt')
        await call.message.answer_document(file, caption=reply)
    await state.finish()


async def exit_send_command(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer('Command sending canceled.')
    await state.finish()


def register_send_command_handlers(dp):
    dp.register_message_handler(send_command_command, commands=['sendCommand'])
    dp.register_callback_query_handler(send_command_callback, lambda call: call.data == 'send_command')

    dp.register_callback_query_handler(server_selected, state=SendCommand.waiting_for_server)
    dp.register_message_handler(command_sent, state=SendCommand.waiting_for_command)
    dp.register_message_handler(dir_selected, state=SendCommand.waiting_for_dir)

    dp.register_callback_query_handler(send_command, lambda call: call.data == 'yes')
    dp.register_callback_query_handler(exit_send_command, lambda call: call.data == 'no')
