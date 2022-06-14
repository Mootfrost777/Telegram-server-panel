from dataclasses import dataclass


@dataclass
class Server:
    name: str
    ip: str
    port: int
    password: str
    owner_id: int
    created_at: str = None
    id: int = None
