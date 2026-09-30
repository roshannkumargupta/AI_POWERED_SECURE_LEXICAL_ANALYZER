from handlers import auth_handler, data_handler
HANDLERS = {"auth": auth_handler, "data": data_handler}
def get_handler(name: str):
    return HANDLERS.get(name)
