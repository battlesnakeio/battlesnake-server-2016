from flask import (
    request, g, current_app,
    render_template, redirect, url_for, flash,
)
from pymongo.errors import DuplicateKeyError

from flask.ext.login import (
    LoginManager,
    login_user, logout_user, current_user
)


from lib.log import get_logger
from lib.models.team import Team
from lib.server import app, form_error

import settings.secrets


app.secret_key = settings.secrets.SESSION_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

logger = get_logger(__name__)


@app.before_request
def load_users():
    if not current_user.is_authenticated and not is_public():
        app.logger.info('no auth, redirecting')
        return login_manager.unauthorized()

    if is_admin_only() and not current_user.teamname == 'admin':
        return "You do not have access", 403

    g.team = current_user


def public(func):
    """
    Decorator that marks a route as not needing authentication.
    This needs to wrap the inner function, or it won't take effect, e.g.

    @app.route(...)
    @public
    def route...
    """
    func._public = True
    return func


def is_public():
    """Returns True if the current route is public, False otherwise """

    # static files are always public
    if request.endpoint == 'static':
        return True

    endpoint = current_app.view_functions.get(request.endpoint)
    if not endpoint:
        return True

    return getattr(endpoint, '_public', False)


def admin_only(func):
    """
    Decorator that marks a route as only accessable to admins.
    This needs to wrap the inner function, or it won't take effect, e.g.

    @app.route(...)
    @admin_only
    def route...
    """
    func._admin_only = True
    return func


def is_admin_only():
    """Returns True if the current route is only avail to admins, False otherwise """
    endpoint = current_app.view_functions.get(request.endpoint)
    if not endpoint:
        return False

    return getattr(endpoint, '_admin_only', False)


@login_manager.user_loader
def load_team(id):
    """Given id, return the associated Team object.

    :param id: team to retrieve
    """
    return Team.find_one({'_id': id})


@app.route('/login', methods=['GET', 'POST'])
@public
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')

    data = request.form
    next = request.values.get('next') or 'app'

    try:
        email = data['email']
        password = data['password']
    except KeyError as e:
        return form_error('Missing field: "%s"' % e.message)

    team = Team.find_one({'member_emails': email})

    if team and team.check_password(password):
        login_user(team)
        return redirect(next)
    else:
        return form_error('Bad team name or password')


@app.route("/logout")
def logout():
    flash('You have been logged out')
    logout_user()
    return redirect(url_for('login'))
