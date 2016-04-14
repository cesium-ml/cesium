

def login_required(func):
    return func


class StormpathManager:
    """Dummy object for testing purposes"""
    def __init__(self):
        pass

    def init_app(self, app):
        pass


class User:
    def __init__(self):
        self.email = "testhandle@test.com"
        self.first_name = "First"
        self.last_name = "Last"
        self.full_name = self.first_name + " " + self.last_name


user = User()
