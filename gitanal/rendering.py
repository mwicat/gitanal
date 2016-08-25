import os

from jinja2 import Environment, FileSystemLoader


PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)


def render_template(template_filename, **context):
    return TEMPLATE_ENVIRONMENT.get_template(template_filename).render(context)


def render_repos_commits(title, repos_commits):
    return render_template(
        'repos_commits.html', title=title, repos_commits=repos_commits)


def render_users(users):
    return render_template(
        'users.html', users=users)
