import collections
import hashlib
import uuid
import zmq


class LimitedDict(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        """A dictionary that stores at most `max_len` items.

        If the item threshold is reached, ``max_len / 2`` items are dropped.
        """
        self.max_len = kwargs.pop('max_len', 1000)
        collections.OrderedDict.__init__(self, *args, **kwargs)

    def __setitem__(self, key, value):
        nr_entries = len(self)

        if nr_entries >= self.max_len:

            # Throw away half the entries
            for i, k in zip(range(self.max_len // 2), self.keys()):
                self.pop(k)

        return collections.OrderedDict.__setitem__(self, key, value)


if __name__ == "__main__":
    addr = "ipc:///tmp/authenticator.sock"

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(addr)

    auth_db = LimitedDict(max_len=50000)

    print('[authenticator] Serving on {}'.format(addr))

    while True:
        message = socket.recv()

        # Messages can be in one of the following formats:
        #
        # ! username@foo.bar
        # ? username@foo.bar token
        #
        # The first generates a new token for the specified user.
        # The second validates a given token.

        command, rest = message.decode('utf-8').split(' ', 1)

        if command == '!':
            username = rest
            token = hashlib.sha256(uuid.uuid4().bytes + username.encode()).hexdigest()
            auth_db[token] = username
            socket.send((username + ' ' + token).encode('utf-8'))

        elif command == '?':
            try:
                username, token = rest.split(' ', 1)
            except:
                socket.send(b'INVALID')
            else:
                if auth_db.get(token, None) == username:
                    socket.send(b'OK')
                else:
                    socket.send(b'FAIL')
