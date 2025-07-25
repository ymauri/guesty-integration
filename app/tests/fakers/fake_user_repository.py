class FakeUserRepository:
    def __init__(self, users):
        self.users = users

    def get_by_email(self, email):
        return self.users.get(email)

    def get_by_id(self, user_id):
        return None

    def create_user(self, user):
        self.users[user.email] = user
