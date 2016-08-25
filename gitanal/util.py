from datetime import datetime
import itertools
import os
import SimpleHTTPServer
import socket
import SocketServer

from dateutil.parser import parse as parse_date
from datemath import parse as parse_datemath



COMMIT_PREFIX = 'commit: '


def groupby(lst, key):
    return itertools.groupby(
        sorted(lst, key=key),
        key=key)


def parse_date_string(s):
    try:
        return parse_date(s)
    except ValueError:
        try:
            return parse_datemath(s).datetime
        except ValueError:
            raise ValueError('Cannot parse datestring %s' % s)


def parse_list_string(s):
    if not s.startswith('^'):
        return s.split(',')
    else:
        cmd = s[1:]
        if cmd == 'ALL':
            return None
        return cmd


def parse_user_arg(s):
    return parse_list_string(s)


def get_commit_date(c):
    return datetime.utcfromtimestamp(c.authored_date)


def get_entry_diff(repo, c):
    if not c.parents:
        return None
    oldhexsha = c.parents[0].hexsha
    return repo.git.diff(oldhexsha, c.hexsha)


def commit_filter(cfg, c, users=None, dt_since=None):
    is_ok = True

    if users == 'CURRENT':
        current_user = cfg.get_value('user', 'name')
        is_ok = is_ok and c.author.name == current_user
    elif isinstance(users, list):
        is_ok = is_ok and c.author.name in users
    elif users is None:
        pass
    else:
        raise ValueError('Invalid users filter: %s' % users)

    if dt_since is not None:
        is_ok = is_ok and get_commit_date(c) >= dt_since

    return is_ok


def format_commit(c):
    msg = c.message
    return '(%s) %s >> %s' % (get_commit_date(c), c.author.email, msg.strip())


class MyTCPServer(SocketServer.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


def serve_directory(d, port):
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = MyTCPServer(("", port), Handler)
    os.chdir(d)
    print "serving at http://0.0.0.0:%d/" % port
    httpd.serve_forever()


def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]
