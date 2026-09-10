from ..models.role import Role


def character(role: Role, on_path: bool = False) -> str:
    if on_path and role in (Role.OPEN, Role.PATH):
        return Role.PATH.value
    return role.value
