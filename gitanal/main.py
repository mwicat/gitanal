#!/usr/bin/env python
"""
Tool to analyze git repositories.
"""

from datetime import datetime, timedelta
import logging
import os
import sys

from argh import ArghParser, arg

from git import Repo
from git.exc import InvalidGitRepositoryError

from .util import (
    parse_date_string,
    parse_user_arg,
    commit_filter,
    format_commit,
)

from . import util

from .rendering import (
    render_repos_commits,
    render_users
)


logging.basicConfig()
logging.captureWarnings(True)
logging.getLogger('py.warnings').setLevel(logging.ERROR)
logger = logging.getLogger(__package__)


def scan_repositories(dir, repo_filter=None, maxdepth=2):
    repos = []
    for path, subdirs, files in util.walklevel(dir, maxdepth):
        basepath = os.path.basename(path)
        if repo_filter is not None and basepath not in repo_filter:
            continue
        fullpath = os.path.join(dir, path)
        print 'Scanning directory %s' % fullpath
        if fullpath.endswith('.git') and os.path.isdir(fullpath):
            try:
                repos.append(Repo(fullpath))
                print 'Found repository at', fullpath
            except InvalidGitRepositoryError:
                pass
    return repos


def filter_commits(repo, pred, branches=None, **filters):
    commits = []
    cfg = repo.config_reader()

    try:
        for branch in repo.branches:
            if branches is not None and branch.name not in branches:
                continue
            for c in repo.iter_commits(branch):
                if pred(cfg, c, **filters):
                    commits.append(c)
    except ValueError as ve:
        print 'Error %s while processing %s' % (ve, repo)

    commits.sort(key=lambda c: c.authored_date, reverse=True)

    return commits


def get_name(repo):
    repo_dir = repo.git_dir
    if os.path.basename(repo_dir) == '.git':
        repo_dir = os.path.dirname(repo_dir)
    return os.path.basename(repo_dir)


@arg('-r', '--root', help='git repositories root', default='.')
@arg('-S', '--since',
     type=parse_date_string,
     help='Since date')
@arg('-F', '--output-format', help='Output format')
@arg('-G', '--groupby')
def me(
        root='.',
        since=timedelta(days=7),
        output_format='plain',
        groupby='repo'):
    return report(
        root=root,
        since=since,
        output_format=output_format,
        groupby=groupby)


@arg('-r', '--root', help='git repositories root', default='.')
@arg('-S', '--since',
     type=parse_date_string,
     help='Since date')
@arg('-U', '--user',
     type=parse_user_arg,
     help='User filter comma-separated.')
@arg('-F', '--output-format', help='Output format')
@arg('-o', '--output-directory', help='Output directory')
@arg('-G', '--groupby')
@arg('-s', '--server')
@arg('-p', '--server-port')
@arg('-R', '--repo', type=lambda x: x.split(','), help='Repository filter')
@arg('-B', '--branch', type=lambda x: x.split(','), help='Branch filter')
def report(
        root='.',
        since=timedelta(days=7),
        user=None,
        output_format='plain',
        output_directory='gitanal_out',
        groupby='user',
        server=False,
        server_port=5555,
        repo=None,
        branch=None):
    repos = scan_repositories(root, repo_filter=repo)

    if isinstance(since, timedelta):
        dt_since = datetime.utcnow() - since
    else:
        dt_since = since

    dt_since = dt_since.replace(tzinfo=None)

    filters = {
        'users': user,
        'dt_since': dt_since
    }

    def write_file(basename, s):
        path = os.path.join(output_directory, basename)
        print 'Writing %s' % path
        return open(path, 'wb').write(s.encode('utf-8'))

    all_commits = []

    for repo in repos:
        print 'Processing', repo
        commits = filter_commits(
            repo, commit_filter, branches=branch, **filters)

        if not commits:
            continue

        all_commits.extend((repo, c) for c in commits)

    def key_user((repo, c)):
        return c.author.email

    def key_repo((repo, c)):
        return repo

    if server:
        print 'Forcing output format to html'
        output_format = 'html'

    if output_format == 'plain':
        if groupby == 'user':
            for user, user_commits in util.groupby(all_commits, key_user):
                print user
                for repo, repo_commits in util.groupby(user_commits, key_repo):
                    print ' %s' % get_name(repo)
                    for repo, c in repo_commits:
                        print '  %s' % format_commit(c)
        elif groupby == 'repo':
            for repo, repo_commits in util.groupby(all_commits, key_repo):
                print '%s' % get_name(repo)
                for c in commits:
                    print ' %s' % format_commit(c)
        else:
            raise ValueError('Invalid parameter groupby: %s' % groupby)
    elif output_format == 'html':
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        if groupby == 'user':
            users = []
            for user, user_commits in util.groupby(all_commits, key_user):
                user_repos_commits = []

                for repo, repo_commits in util.groupby(user_commits, key_repo):
                    commits_data = [
                        {'message': format_commit(c),
                         'sha': c.hexsha,
                         'diff': util.get_entry_diff(repo, c)}
                        for repo, c in repo_commits]
                    user_repos_commits.append(
                        {'name': get_name(repo), 'commits': commits_data})

                user_fn = 'user_%s.html' % user
                users.append(
                    {'username': user, 'url': user_fn})

                user_repos_commits.sort(key=lambda x: x['name'])
                write_file(user_fn, render_repos_commits(user, user_repos_commits))

            users_fn = 'users.html'
            write_file(users_fn, render_users(users))
        else:
            raise ValueError('Invalid parameter groupby: %s' % groupby)
    else:
        raise ValueError('Invalid parameter format: %s' % output_format)

    if server:
        try:
            util.serve_directory(output_directory, server_port)
        except KeyboardInterrupt:
            pass


def main():
    parser = ArghParser(description=__doc__)
    parser.add_commands([
        report,
        me
    ])
    try:
        parser.dispatch()
    except Exception as e:
        raise
        logger.error('Runtime exception: %s' % e)
        sys.exit(1)


if __name__ == "__main__":
    main()
