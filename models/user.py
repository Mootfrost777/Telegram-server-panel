from dataclasses import dataclass


@dataclass
class User:
    id: int
    admin: bool
