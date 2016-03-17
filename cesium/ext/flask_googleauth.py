# Ported to Python 3 from original at https://github.com/sashka/flask-googleauth
#
"""
Implementation of OpenID authentication schema.
No discovery is supported in order to keep the code simple.

This is a partial port of tornado.auth to be used with Flask.

Example usage for Google Federated Login:

    from flask import Flask
    from flask_googleauth import GoogleFederated

    # Setup Flask
    app = Flask(__name__)
    app.secret_key = "random secret key"

    # Setup Google Auth
    auth = GoogleFederated("mokote.com", app)

    @app.route("/")
    @auth.required
    def secret():
        return "ssssshhhhh (c) kennethreitz"
"""

import functools
import logging
try:
    from urllib.parse import urljoin, urlencode
except ImportError:
    from urlparse import urljoin
    from urllib import urlencode

import blinker
import requests

from flask import Blueprint, request, session, redirect, url_for, abort, g, current_app


signals = blinker.Namespace()
login = signals.signal("login")
logout = signals.signal("logout")
login_error = signals.signal("login-error")


class ObjectDict(dict):
    """Makes a dictionary behave like an object."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class OpenIdMixin(object):
    """
    Abstract implementation of OpenID and Attribute Exchange.

    The primary methods are authenticate_redirect(), and get_authenticated_user().
    The former should be called to redirect the user to, e.g., the OpenID
    authentication page on the third party service, and the latter should
    be called upon return to get the user data from the data returned by
    the third party service.

    See GoogleAuth below for example implementations.
    """

    def authenticate_redirect(self, callback_uri=None,
                              ask_for=["name", "email", "language", "username"]):
        """
        Performs a redirect to the authentication URL for this service.

        After authentication, the service will redirect back to the given
        callback URI.

        We request the given attributes for the authenticated user by
        default (name, email, language, and username). If you don't need
        all those attributes for your app, you can request fewer with
        the |ask_for| keyword argument.
        """
        callback_uri = callback_uri or request.url
        args = self._openid_args(callback_uri, ax_attrs=ask_for)
        return redirect(self._OPENID_ENDPOINT +
                        ("&" if "?" in self._OPENID_ENDPOINT else "?") +
                        urlencode(args))

    def get_authenticated_user(self, callback):
        """Fetches the authenticated user data upon redirect.

        This method should be called by the handler that receives the
        redirect from the authenticate_redirect() or authorize_redirect()
        methods.
        """
        # Verify the OpenID response via direct request to the OP
        args = dict((k, v) for k, v in list(request.args.items()))
        args["openid.mode"] = "check_authentication"

        r = requests.post(self._OPENID_ENDPOINT, data=args)
        return self._on_authentication_verified(callback, r)

    def _openid_args(self, callback_uri, ax_attrs=[]):
        url = urljoin(request.url, callback_uri)
        args = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.return_to": url,
            "openid.realm": urljoin(url, "/"),
            "openid.mode": "checkid_setup",
        }
        if ax_attrs:
            args.update({
                "openid.ns.ax": "http://openid.net/srv/ax/1.0",
                "openid.ax.mode": "fetch_request",
            })
            ax_attrs = set(ax_attrs)
            required = []
            if "name" in ax_attrs:
                ax_attrs -= set(["name", "firstname", "fullname", "lastname"])
                required += ["firstname", "fullname", "lastname"]
                args.update({
                    "openid.ax.type.firstname": "http://axschema.org/namePerson/first",
                    "openid.ax.type.fullname": "http://axschema.org/namePerson",
                    "openid.ax.type.lastname": "http://axschema.org/namePerson/last",
                })
            known_attrs = {
                "email": "http://axschema.org/contact/email",
                "language": "http://axschema.org/pref/language",
                "username": "http://axschema.org/namePerson/friendly",
            }
            for name in ax_attrs:
                args["openid.ax.type." + name] = known_attrs[name]
                required.append(name)
            args["openid.ax.required"] = ",".join(required)
        return args

    def _on_authentication_verified(self, callback, response):
        ok = response.status_code == requests.codes.ok
        if not ok or "is_valid:true" not in str(response.content):
            logging.warning("Invalid OpenID response: %s", str(response.content))
            return callback(None)

        # Make sure we got back at least an email from attribute exchange
        ax_ns = None
        for name in request.args:
            if (name.startswith("openid.ns.") and
               request.args.get(name) == "http://openid.net/srv/ax/1.0"):
                ax_ns = name[10:]
                break

        def get_ax_arg(uri):
            if not ax_ns:
                return ""
            prefix = "openid.%s.type." % ax_ns
            ax_name = None
            for name in request.args:
                if request.args.get(name) == uri and name.startswith(prefix):
                    part = name[len(prefix):]
                    ax_name = "openid.%s.value.%s" % (ax_ns, part)
                    break
            if not ax_name:
                return ""
            return request.args.get(ax_name, "")

        email = get_ax_arg("http://axschema.org/contact/email")
        name = get_ax_arg("http://axschema.org/namePerson")
        first_name = get_ax_arg("http://axschema.org/namePerson/first")
        last_name = get_ax_arg("http://axschema.org/namePerson/last")
        username = get_ax_arg("http://axschema.org/namePerson/friendly")
        locale = get_ax_arg("http://axschema.org/pref/language").lower()
        identity = request.args.get("openid.claimed_id", "")

        user = ObjectDict()
        name_parts = []
        if first_name:
            user["first_name"] = first_name
            name_parts.append(first_name)
        if last_name:
            user["last_name"] = last_name
            name_parts.append(last_name)
        if name:
            user["name"] = name
        elif name_parts:
            user["name"] = " ".join(name_parts)
        elif email:
            user["name"] = email.split("@")[0]
        if email:
            user["email"] = email
        if locale:
            user["locale"] = locale
        if username:
            user["username"] = username
        if identity:
            user["identity"] = identity
        return callback(user)


class GoogleAuth(OpenIdMixin):
    """
    Google OpenID authentication.

    Sign-in and sign-out links will be registered automatically.

    No application registration is necessary to use Google for authentication
    or to access Google resources on behalf of a user. To authenticate with
    Google, redirect with authenticate_redirect(). On return, parse the
    response with get_authenticated_user(). We send a dict containing the
    values for the user, including 'email', 'name', 'locale', and 'identity'.

    See also: https://developers.google.com/accounts/docs/OpenID
    """

    _OPENID_ENDPOINT = "https://www.google.com/accounts/o8/ud"

    def __init__(self, app=None, url_prefix=None, name="GoogleAuth",
                 force_auth_on_every_request=False):
        self.app = app
        self.url_prefix = url_prefix
        self.name = name
        self.force_auth_on_every_request = force_auth_on_every_request

        if app:
            self.init_app(app, url_prefix, name)

    def init_app(self, app, url_prefix=None, name=None):
        url_prefix = url_prefix or self.url_prefix
        name = name or self.name

        self.blueprint = Blueprint(name, __name__, url_prefix=url_prefix)
        self.blueprint.add_url_rule("/login/",
                                    "login",
                                    self._login,
                                    methods=["GET", "POST"])
        self.blueprint.add_url_rule("/logout/",
                                    "logout",
                                    self._logout,
                                    methods=["GET", "POST"])

        app.register_blueprint(self.blueprint)
        app.before_request(self._add_user_from_session)
        app.before_request(self._force_auth_on_every_request)
        app.extensions['googleauth'] = ObjectDict(blueprint=self.blueprint)

    def _add_user_from_session(self):
        g.user = None
        if "openid" in session:
            g.user = session["openid"]

    def _force_auth_on_every_request(self):
        if self.force_auth_on_every_request:
            # Use the required decorator where the actual work for
            # authentication is performed.
            # The goal here is to avoid code duplication.
            @self.required
            def _should_auth():
                # If no authentication is required, return None so that
                # the request dispatch process continues.
                return None
            # The required decorator will replace the return value with
            # a redirect if authentication is needed, thus stopping the dispatch
            # process.
            return _should_auth()

    def _login(self):
        if request.args.get("openid.mode", None):
            # After OpenID response:
            return self.get_authenticated_user(self._on_auth)
        return self.authenticate_redirect()

    def _on_auth(self, user):
        """
        This is called when login with OpenID succeeded and it's not
        necessary to figure out if this is the users's first login or not.
        """
        app = current_app._get_current_object()
        if not user:
            # Google auth failed.
            login_error.send(app, user=None)
            abort(403)
        session["openid"] = user
        login.send(app, user=user)
        return redirect(request.args.get("next", None) or request.referrer or "/")

    def _logout(self):
        user = session.pop("openid", None)
        app = current_app._get_current_object()
        logout.send(app, user=user)
        return redirect(request.args.get("next", None) or "/")

    def _check_auth(self):
        return "openid" in session

    def required(self, fn):
        """Request decorator. Forces authentication."""
        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            if (not self._check_auth()
               # Don't try to force authentication if the request is part
               # of the authentication process - otherwise we end up in a
               # loop.
               and request.blueprint != self.blueprint.name):
                return redirect(url_for("%s.login" % self.blueprint.name,
                                        next=request.url))
            return fn(*args, **kwargs)
        return decorated


class GoogleFederated(GoogleAuth):
    """
    Super simple Google Federated Auth for a given domain.
    """

    def __init__(self, domain, app=None, url_prefix=None, name='GoogleAuth'):
        self._OPENID_ENDPOINT = "https://www.google.com/a/%s/o8/ud?be=o8" % domain
        super(GoogleFederated, self).__init__(app, url_prefix, name)
