from domain.user.value_objects import UserRole


def admin_user():
    return UserRole.ADMIN

def owner_user():
    return UserRole.OWNER
