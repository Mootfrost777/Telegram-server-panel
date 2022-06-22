import asyncpg  # Странная либа, но работает
import logging
import json

from models.user import User
from models.server import Server

global conn


async def connect_to_db():
    with open('./config/default.json', 'r') as f:
        data = json.load(f)['db']

    global conn
    conn = await asyncpg.connect(
        database=data['name'],
        user=data['user'],
        password=data['password'],
        host=data['host'],
        port=data['port'])
    logging.info("Database connected")


async def init_db():
    await conn.execute("""create table if not exists users (
        id serial primary key,
        admin boolean default false
        )""")

    await conn.execute("""create table if not exists servers (
        id integer primary key,
        owner_id integer not null,
        name varchar(255) not null,
        ip varchar(255) not null,
        port integer not null,
        password varchar(255) not null,
        created_at timestamp default current_timestamp not null default current_timestamp,
        foreign key (owner_id) references users(id)
        )""")
    await conn.execute('''commit''')
    logging.info("Database initialized")


async def get_user(user_id):
    resp = await conn.fetchrow("""select * from users where id = $1""", user_id)
    if resp is None:
        return {
            'status': 404,
            'message': 'User not found'
        }
    user = User(resp['id'], resp['admin'])
    logging.info(f"User {user.id} fetched")
    return {
        'status': 200,
        'message': user
    }


async def create_user(user_id):
    resp = await get_user(user_id)
    if resp['status'] == 200:
        return {
            'status': 409,
            'message': 'User already exists'
        }
    await conn.execute("""insert into users (id, admin) values ($1, $2)""", user_id, False)
    await conn.execute('''commit''')
    return {
        'status': 200,
        'message': 'User created'
    }


async def add_server(server):
    await conn.execute("""insert into servers (owner_id, name, ip, port, password) values ($1, $2, $3, $4, $5)""",
                       server.owner_id,
                       server.name,
                       server.ip,
                       server.port,
                       server.password)
    await conn.execute('''commit''')
    return {
        'status': 200,
        'message': 'Server created'
    }


async def get_server(server_id: int):
    resp = await conn.fetchrow("""select * from servers where id = $1""", server_id)
    if resp is None:
        return {
            'status': 404,
            'message': 'Server not found'
        }
    server = Server(**resp)
    logging.info(f"Server {server.id} fetched")
    return {
        'status': 200,
        'message': server
    }


async def get_servers(user_id):
    resp = await conn.fetch("""select * from servers where owner_id = $1""", user_id)
    if not resp:
        return {
            'status': 404,
            'message': 'Servers not found'
        }
    servers = []
    for row in resp:
        servers.append(Server(**row))

    logging.info(f"Servers for user {user_id} fetched")
    return {
        'status': 200,
        'message': servers
    }
