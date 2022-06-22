import requests


async def check_server_connection(server):
    try:
        requests.get(f'http://{server.ip}:{server.port}/ping', timeout=0.2)
        return True
    except requests.exceptions.ConnectTimeout:
        return False
