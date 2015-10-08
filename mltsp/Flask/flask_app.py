#!/usr/bin/python

# Machine Learning Timeseries Platform flask application
from __future__ import print_function
import sys
import os

# list of (Google) admin accounts to have access to all projects
sys_admin_emails = ['a.crellinquick@gmail.com']

from .. import cfg
from ..cfg import config

import shutil
import time
import psutil
import smtplib
from email.mime.text import MIMEText
import logging
import simplejson
from flask import (
    Flask, request, abort, render_template,
    session, Response, jsonify, g)
from werkzeug import secure_filename
import uuid
import ntpath

import yaml
if os.getenv("MLTSP_DEBUG_LOGIN") == "1" or '--disable-auth' in sys.argv:
    from ..ext import stormpath_mock as stormpath
else:
    from flask.ext import stormpath

import tarfile
import multiprocessing
import rethinkdb as rdb
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

from .. import custom_feature_tools as cft
from .. import custom_exceptions
from .. import featurize
from .. import predict_class as predict
from .. import build_model
from ..version import version

all_available_features_list = cfg.features_list_obs + cfg.features_list_science

# Flask initialization
app = Flask(__name__, static_folder=None)
app.static_folder = 'static'
app.add_url_rule(
    '/static/<path:filename>', endpoint='static',
    view_func=app.send_static_file)

app.config['SECRET_KEY'] = config['flask']['secret-key']
app.config['STORMPATH_API_KEY_ID'] = \
    config['authentication']['stormpath_api_key_id']
app.config['STORMPATH_API_KEY_SECRET'] = \
    config['authentication']['stormpath_api_key_secret']
app.config['STORMPATH_APPLICATION'] = \
    config['authentication']['stormpath_application']
try:
    config['authentication']['google_client_id']
except KeyError:
    config['authentication']['google_client_id'] = None
if config['authentication']['google_client_id'] is not None:
    app.config['STORMPATH_ENABLE_GOOGLE'] = True
    app.config['STORMPATH_SOCIAL'] = {
        'GOOGLE': {
            'client_id': config['authentication']['google_client_id'],
            'client_secret': config['authentication']['google_client_secret'],
        }
    }
else:
    print('(!) No Google authentication token in configuration file.')
    print('(!) Disabling Google logins.')


# Authentication is done using Stormpath
# http://flask-stormpath.readthedocs.org/
stormpath_manager = stormpath.StormpathManager()
stormpath_manager.init_app(app)


app.config['UPLOAD_FOLDER'] = cfg.UPLOAD_FOLDER

logging.basicConfig(filename=cfg.ERR_LOG_PATH, level=logging.WARNING)

# RethinkDB config:
RDB_HOST = os.environ.get('RDB_HOST') or 'localhost'
RDB_PORT = os.environ.get('RDB_PORT') or 28015
if os.getenv("MLTSP_TEST_DB") == "1":
    MLTSP_DB = "mltsp_testing"
else:
    MLTSP_DB = "mltsp_app"

if not ('--help' in sys.argv or '--install' in sys.argv):

    try:
        rdb_conn = rdb.connect(host=RDB_HOST, port=RDB_PORT, db=MLTSP_DB)
    except rdb.errors.RqlDriverError as e:
        print(e)
        print('Unable to connect to RethinkDB.  Please ensure that it is running.')
        sys.exit(-1)

ALLOWED_EXTENSIONS = set([
    'txt', 'dat', 'csv', 'fits', 'jpeg', 'gif', 'bmp', 'doc', 'odt', 'xml',
    'json', 'TXT', 'DAT', 'CSV', 'FITS', 'JPEG', 'GIF', 'BMP', 'DOC', 'ODT',
    'XML', 'JSON'])


@app.before_request
def before_request():
    """Establish connection to RethinkDB DB before each request."""
    try:
        g.rdb_conn = rdb.connect(host=RDB_HOST, port=RDB_PORT, db=MLTSP_DB)
    except RqlDriverError:
        print("No database connection could be established.")
        abort(503, "No database connection could be established.")


@app.teardown_request
def teardown_request(exception):
    """Close connection to RethinkDB DB after each request is completed."""
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass


def establish_rdb_connection():
    """Return RDB connection to MLTSP database.
    """
    connection = rdb.connect(host=RDB_HOST, port=RDB_PORT, db=MLTSP_DB)
    return connection


# sys.excepthook = excepthook_replacement
def excepthook_replacement(exctype, value, tb):
    print("\n\nError occurred in flask_app.py")
    print("Type:", exctype)
    print("Value:", value)
    print("Traceback:", tb, "\n\n")
    logging.exception("Error occurred in flask_app.py")


def num_lines(filename):
    """Return number of non-comment and non-whitespace lines in a file.

    Comment lines are those that start with '#'.

    Parameters
    ----------
    fname : str
        Path to file.

    Returns
    -------
    int
        Number of non-whitespace and non-comment lines in file.

    """
    linecount = 0
    with open(filename) as f:
        for line in f:
            if (len(line) > 0 and line[0] not in ["#", "\n"]
                    and not line.isspace()):
                linecount += 1
    return linecount


@app.route('/check_job_status/', methods=['POST', 'GET'])
@stormpath.login_required
def check_job_status(PID=False):
    """Check status of a process, return string summary.

    Checks the status of a process with given PID (passed as URL
    parameter) and returns a message (str) indicating whether the
    process is running (and when it was started if so), or whether it
    has completed (and when it was started if so), in which case it has
    'zombie' status and is killed.

    Parameters
    ----------
    PID : int or str
        Process ID of process to be checked.

    Returns
    -------
    str
        Message indicating process status.

    """
    if PID:
        PID = str(PID).strip()
    else:
        PID = str(request.args.get('PID', ''))
    if PID == "undefined":
        PID = str(session['PID'])
    start_time = is_running(PID)
    if start_time != "False":
        if psutil.Process(int(PID)).status() != "zombie":
            msg_str = (
                "This process is currently running and was started at "
                "%s (last checked at %s).") % (
                    str(start_time), str(time.strftime("%Y-%m-%d %H:%M:%S",
                                                       time.localtime())))
        else:
            psutil.Process(int(PID)).kill()
            msg_str = ("This process was started at %s and has now finished "
                       "(checked at %s).") % (
                           str(start_time),
                           str(time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime())))
    else:
        msg_str = ("This process has finished (checked at %s)." %
                   str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    return msg_str


def is_running(PID):
    """Check if process with given PID is running.

    Returns a string indicating the time process with given PID was
    started if it is running, otherwise returns False (bool).

    Parameters
    ----------
    PID : int or str
        PID of process to check on.

    Returns
    -------
    str
        Human readable string indicating the time process with
        given PID was started if it is running, otherwise "False".

    """
    if psutil.pid_exists(int(PID)):
        p = psutil.Process(int(PID))
        return time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(p.create_time()))
    else:
        return "False"


def db_init(force=False):
    """Initialize RethinkDB tables.

    Create a RethinkDB database whose name is the value of the global
    `MLTSP_DB` defined above, and creates tables within the new DB
    with the names 'projects', 'users', 'features', 'models',
    'userauth' and 'predictions', respectively.

    Parameters
    ----------
    force : boolean, optional
        If True, any pre-existing database associated with this app and
        all its tables will be deleted and replaced by empty tables.
        Defaults to False.

    """
    try:
        connection = rdb.connect(host=RDB_HOST, port=RDB_PORT)
    except RqlDriverError as e:
        print('db_init:', e.message)
        if 'not connect' in e.message:
            print('Launch the database by executing `rethinkdb`.')
        return
    if force:
        try:
            rdb.db_drop(MLTSP_DB).run(connection)
        except:
            pass
    try:
        rdb.db_create(MLTSP_DB).run(connection)
    except RqlRuntimeError as e:
        print('db_init:', e.message)
        print('The table may already exist.  Specify the --force flag '
              'to clear existing data.')
        return
    table_names = ['projects', 'users', 'features',
                   'models', 'userauth', 'predictions']

    db = rdb.db(MLTSP_DB)

    for table_name in table_names:
        print('Creating table', table_name)
        db.table_create(table_name).run(connection)
    connection.close()

    print('Database setup completed.')


@app.route('/add_user', methods=['POST'])
@stormpath.login_required
def add_user():
    """Add current user to the RethnkDB 'users' table.

    Adds the currently logged-in user to the database's 'users' table.
    Current user accessed via the flask.g application global (user info
    is added to flask.g upon authentication).

    """
    return rdb.table('users').insert({
        "name": stormpath.user.full_name,
        "email": stormpath.user.email,
        "id": stormpath.user.email,
        "created": str(rdb.now().in_timezone("-08:00").run(g.rdb_conn))
    }).run(g.rdb_conn)


# @app.before_first_request
@app.route('/check_user_table', methods=['POST'])
def check_user_table():
    """Add current user to RethinkDB 'users' table if not present."""
    if rdb.table("users").filter({'email': stormpath.user.email})\
                       .count().run(g.rdb_conn) == 0:

        add_user()
    return jsonify({})


def update_model_entry_with_pid(new_model_key, pid):
    """Update RethinkDB model entry with process ID.

    Add process ID to model entry with key `new_model_key` in
    'models' table after subprocess with given PID has been started.

    Parameters
    ----------
    new_model_key : str
        Key of RethinkDB 'models' table entry to be updated.
    pid : str or int
        ID of model building process.

    Returns:
    str
        `new_model_key`, as provided in args.

    """
    (rdb.table('models').get(str(new_model_key).strip())
        .update({"pid": str(pid)}).run(g.rdb_conn))
    return new_model_key


def update_featset_entry_with_pid(featset_key, pid):
    """Update RethinkDB feature set entry with process ID.

    Add process ID to feature set entry with key `featset_key` in
    'features' table after subprocess with given pid has been started.

    Parameters
    ----------
    featset_key : str
        Key of RethinkDB 'features' table entry to be updated.
    pid : str or int
        ID of feature generation process.

    Returns
    -------
    str
        `featset_key`, as provided in function call.

    """
    (rdb.table('features').get(featset_key)
        .update({"pid": str(pid)}).run(g.rdb_conn))
    return featset_key


def update_prediction_entry_with_pid(prediction_key, pid):
    """Update RethinkDB prediction entry with process ID.

    Add process ID to prediction entry with key `prediction_key` in
    'predictions' table after subprocess with given pid has been
    started.

    Parameters
    ----------
    prediction_key : str
        Key of RethinkDB 'predictions' table entry to be updated.
    pid : str or int
        ID of prediction process.

    Returns
    -------
    str
        `prediction_key`, as provided in function call.

    """
    (rdb.table('predictions').get(prediction_key)
        .update({"pid": str(pid)}).run(g.rdb_conn))
    return prediction_key


def update_prediction_entry_with_results(prediction_entry_key, html_str,
                                         features_dict, ts_data_dict,
                                         pred_results_list_dict, err=None):
    """Update RethinkDB prediction entry with results data.

    Add features generated, prediction results and ts data to entry in
    'predictions' table for entry with key `prediction_entry_key`.

    Parameters
    ----------
    prediction_entry_key : str
        Key of RethinkDB 'predictions' table entry to be updated.
    html_str : str
        String containing HTML table of results.
    features_dict : dict
        Dictionary containing generated features.
    ts_data_dict : dict
        Dictionary containing time-series data, with their original
        file names as keys, and list of respective (t,m,e) values as
        each dict value.
    pred_results_list_dict : dict
        Dictionary with original time-series data file name as keys,
        list of respective classifier prediction results as values.
    err : str, optional
        Error message associated with prediction process. Defaults to
        None.

    Returns
    -------
    boolean
        True.

    """
    info_dict = {"results_str_html": html_str,
                 "features_dict": features_dict,
                 "ts_data_dict": ts_data_dict,
                 "pred_results_list_dict": pred_results_list_dict}
    if err is not None:
        info_dict["err_msg"] = err
    rdb.table("predictions").get(prediction_entry_key)\
                          .update(info_dict).run(g.rdb_conn)
    return True


def update_model_entry_with_results_msg(model_key, model_built_msg, err=None):
    """Update RethinkDB model entry with results message.

    Add success/error message to model entry with key `model_key`
    in 'models' table.

    Parameters
    ----------
    model_key : str
        Key of RethinkDB 'models' table entry to be updated.
    model_built_msg : str
        Message provided by model build function.
    err : str, optional
        Error message associated with model build process. Defaults to
        None.

    Returns
    -------
    str
        `model_key`, as provided in function call parameters.

    """
    info_dict = {"results_msg": model_built_msg}
    if err is not None:
        info_dict["err_msg"] = err
    rdb.table('models').get(model_key).update(info_dict).run(g.rdb_conn)
    return model_key


def update_featset_entry_with_results_msg(featureset_key, results_str,
                                          err=None):
    """Update RethinkDB feature set entry with results message.

    Add success/error message to feature set entry with key
    `featureset_key` in 'features' table.

    Parameters
    ----------
    featureset_key : str
        Key of RethinkDB 'features' table entry to be updated.
    results_str : str
        Human readable message provided by featurization function.
    err : str, optional
        Human readable error message associated with featurization
        process. Defaults to None.

    Returns
    -------
    str
        `featureset_key`, as provided in function call parameters.

    """
    info_dict = {"results_msg": results_str}
    if err is not None:
        info_dict["err_msg"] = err
    rdb.table('features').get(featureset_key).update(info_dict).run(g.rdb_conn)
    return featureset_key


def get_current_userkey():
    """Return RethinkDB key/ID associated with current user.

    Returns the key/ID of the 'users' table entry corresponding to
    current user's email (accessed through `stormpath.user` thread-local).

    Returns
    -------
    str
        User key/ID.

    """
    cursor = rdb.table("users").filter({"email": stormpath.user.email})\
                             .run(g.rdb_conn)
    n_entries = 0
    entries = []
    for entry in cursor:
        n_entries += 1
        entries.append(entry)
    if len(entries) == 0:
        print(("ERROR!!! get_current_userkey() - no matching entries in users "
               "table with email"), stormpath.user.email)
        raise Exception(("dbError - No matching entries in users table for "
                         "email address %s.") % str(stormpath.user.email))
    elif len(entries) > 1:
        print(("WARNING!! get_current_userkey() - more than one entry in "
               "users table with email"), stormpath.user.email)
    else:
        return entries[0]['id']


def get_all_projkeys():
    """Return all project keys.

    Returns
    -------
    list of str
        A list of project keys (strings).

    """
    cursor = rdb.table("projects").run(g.rdb_conn)
    proj_keys = []
    for entry in cursor:
        proj_keys.append(entry["id"])
    return proj_keys


def get_authed_projkeys(this_userkey=None):
    """Return all project keys that current user is authenticated for.

    Returns
    -------
    list of str
        A list of project keys (strings).

    """
    if this_userkey is None:
        this_userkey = get_current_userkey()
    cursor = rdb.table('userauth').filter({
        "userkey": this_userkey,
        "active": "y"
    }).map(lambda entry: entry['projkey']).run(g.rdb_conn)
    proj_keys = []
    for entry in cursor:
        proj_keys.append(entry)
    return proj_keys


def list_featsets_cursor_to_html_table(cursor):
    """
    """
    authed_featuresets = (
        "<table id='features_table' style='display:none;'>" +
        "   <tr class='features_row'>" +
        "       <th>Feature set name</th>" +
        "       <th>Date created</th>" +
        "       <th>Features used</th>" +
        "       <th>Remove from database</th>" +
        "   </tr>")
    count = 0
    for entry in cursor:
        authed_featuresets += (
            "<tr class='features_row'><td align='left'>" +
            entry['name'] + "</td><td align='left'>" +
            entry['created'][:-13] +
            (
                " PST</td><td align='center'>" +
                "<a href='#' onclick=\"$('#feats_used_div_%d')" +
                ".dialog('open');\">Show</a><div " +
                "id='feats_used_div_%d' style='display:none;' " +
                "class='feats_used_div' title='%s: Features used'>")
            % (
                count, count, (
                    entry['name'] +
                    ', '.join(entry['featlist']))) +
            ("</div></td><td align='center'><input "
             "type='checkbox' name='delete_features_key' "
             "value='%s'></td></tr>") % entry['id'])
        count += 1
    authed_featuresets += "</table>"
    return authed_featuresets


def list_featuresets(
        auth_only=True, by_project=False, name_only=False,
        as_html_table_string=False):
    """Return list of strings describing entries in 'features' table.

    Parameters
    ----------
    auth_only : bool, optional
        If True, returns only those entries whose parent projects
        current user is authenticated to access. Defaults to True.
    by_project : str, optional
        Project name. Filters by project if not False. Defaults to
        False.
    name_only : bool, optional
        If True, does not include date/time created. Defaults to False.
    as_html_table_string : bool, optional
        If True, returns the results as a single string of HTML markup
        containing a table. Defaults to False.

    Returns
    -------
    list of str
        List of strings describing entries in 'features' table.

    """
    authed_proj_keys = (
        get_authed_projkeys() if auth_only else get_all_projkeys())
    if by_project:
        this_projkey = project_name_to_key(by_project)
        cursor = rdb.table("features").filter({"projkey": this_projkey})\
                                    .pluck("name", "created", "id", "featlist")\
                                    .run(g.rdb_conn)
        if as_html_table_string:
            authed_featuresets = list_featsets_cursor_to_html_table(cursor)
        else:
            authed_featuresets = []
            for entry in cursor:
                authed_featuresets.append(
                    entry['name'] + \
                    (" (created %s PST)" % str(entry['created'])[:-13]
                     if not name_only else ""))
        return authed_featuresets
    else:
        if len(authed_proj_keys) == 0:
            return []
        authed_featuresets = []
        for this_projkey in authed_proj_keys:
            cursor = (
                rdb.table("features").filter({"projkey": this_projkey})
                .pluck("name", "created").run(g.rdb_conn))
            for entry in cursor:
                authed_featuresets.append(
                    entry['name'] +
                    (" (created %s PST)" % str(entry['created'])[:-13]
                        if not name_only else ""))

        return authed_featuresets


def list_models_cursor_to_html_table(cursor):
    """
    """
    authed_models = (
        "<table id='models_table' style='display:none;'>"
        "<tr class='model_row'><th>Model name</th>"
        "<th>Model type</th><th>Date created</th>"
        "<th>Remove from database</th></tr>")
    for entry in cursor:
        authed_models += "<tr class='model_row'><td align='left'"
        authed_models += (
            " class='%s'" '&'.join(entry['meta_feats'])
            if 'meta_feats' in entry and entry['meta_feats']
            not in [False, [], "False", None, "None"] and
            isinstance(entry['meta_feats'], list) else "")
        authed_models += (
            ">" + entry['name']
            + "</td><td align='left'>" + entry['type']
            + "</td><td align='left'>" + entry['created'][:-13]
            + (
                " PST</td><td align='center'><input type='checkbox' "
                "name='delete_model_key' value='%s'></td></tr>")
            % entry['id'])
    authed_models += "</table>"
    return authed_models


def list_models(
        auth_only=True, by_project=False, name_only=False, with_type=True,
        as_html_table_string=False):
    """Return list of strings describing entries in 'models' table.

    Parameters
    ----------
    auth_only : bool, optional
        If True, returns only those entries whose parent projects
        current user is authenticated to access. Defaults to True.
    by_project : str, optional
        Must be project name or False. Filters by project. Defaults
        to False.
    name_only : bool, optional
        If True, does not include date/time created. Defaults to False.
    with_type : bool, optional
        If True, includes model type (e.g. 'RF') in model description.
        Defaults to True.
    as_html_table_string : bool, optional
        If True, returns the results as a single string of HTML markup
        containing a table. Defaults to False.

    Returns
    -------
    list of str
        List of strings describing entries in 'models' table.

    """
    authed_proj_keys = (
        get_authed_projkeys() if auth_only else get_all_projkeys())

    if by_project:
        this_projkey = project_name_to_key(by_project)

        cursor = rdb.table("models").filter({"projkey": this_projkey})\
                                  .pluck("name", "created", "type", "id",
                                         "meta_feats")\
                                  .run(g.rdb_conn)

        if as_html_table_string:
            authed_models = list_models_cursor_to_html_table(cursor)
        else:
            authed_models = []
            for entry in cursor:
                authed_models.append(
                    entry['name']
                    + (" - %s" % str(entry['type']) if with_type else "")
                    + (" (created %s PST)" % str(entry['created'])[:-13]
                       if not name_only else "")
                    + (" meta_feats=%s" % ",".join(entry['meta_feats'])
                       if 'meta_feats' in entry and entry['meta_feats']
                       not in [False, [], "False", None, "None"] and
                       isinstance(entry['meta_feats'], list) else ""))
        return authed_models
    else:
        if len(authed_proj_keys) == 0:
            return []
        authed_models = []
        for this_projkey in authed_proj_keys:
            cursor = (
                rdb.table("models").filter({"projkey": this_projkey})
                .pluck("name", "created", "type", "meta_feats").run(g.rdb_conn))
            for entry in cursor:
                authed_models.append(
                    entry['name']
                    + (" - %s" % str(entry['type']) if with_type else "")
                    + (
                        " (created %s PST)" % str(entry['created'])[:-13]
                        if not name_only else "")
                    + (
                        " meta_feats=%s" % ",".join(entry['meta_feats'])
                        if 'meta_feats' in entry and entry['meta_feats']
                        not in [False, [], "False", None, "None"]
                        and isinstance(entry['meta_feats'], list) else ""))
        return authed_models


def list_predictions_cursor_to_html_table(cursor):
    """
    """
    predictions = (
        "<table id='predictions_table' style='display:none;'>"
        "<tr class='prediction_row'><th>Model/feature set name</th>"
        "<th>Model type</th><th>Time-series filename</th>"
        "<th>Date run</th><th>Results</th>"
        "<th>Remove from database</th></tr>")
    count = 0
    for entry in cursor:
        predictions += (
            "<tr class='prediction_row'><td align='left'>"
            + entry['model_name'] + "</td><td align='left'>"
            + entry['model_type'] + "</td><td align='left'>"
            + entry['filename'] + "</td><td align='left'>"
            + entry['created'][:-13]
            + (
                " PST</td><td align='center'><a href='#' "
                "onclick=\"$('#prediction_results_div_%d')"
                ".dialog('open');\">Show</a>"
                "<div id='prediction_results_div_%d' "
                "style='display:none;' class='pred_results_dialog_div'"
                " title='Prediction Results'>")
            % (count, count))
        try:
            predictions += entry['results_str_html']
        except KeyError:
            predictions += (
                "No prediction results saved for this entry.")
        predictions += ((
            "</div></td><td align='center'><input type='checkbox' "
            "name='delete_prediction_key' value='%s'></td></tr>")
            % entry['id'])
        count += 1
    predictions += "</table>"
    return predictions


def list_predictions(
        auth_only=False, by_project=False, detailed=True,
        as_html_table_string=False):
    """Return list of strings describing entries in 'predictions' table.

    Parameters
    ----------
    auth_only : bool, optional
        If True, returns only those entries whose parent projects
        current user is authenticated to access. Defaults to False.
    by_project : str, optional
        Name of project to restrict results to. Defaults to False.
    detailed : bool, optional
        If True, includes more details such date/time. Defaults to True.
    as_html_table_string : bool, optional
        If True, returns the results as a single string of HTML markup
        containing a table. Defaults to False.

    Returns
    -------
    list of str
        List of strings describing entries in 'models' table.

    """
    if by_project:
        this_projkey = project_name_to_key(by_project)
        cursor = (
            rdb.table("predictions").filter({"projkey": this_projkey})
            .pluck(
                "model_name", "model_type", "filename",
                "created", "id", "results_str_html")
            .run(g.rdb_conn))
        if as_html_table_string:
            predictions = list_predictions_cursor_to_html_table(cursor)
        else:
            predictions = []
            for entry in cursor:
                predictions.append(
                    entry['model_name']
                    + (" - %s" % str(entry['model_type']) if detailed else "")
                    + (
                        " (created %s PST)" % str(entry['created'])[:-13]
                        if detailed else ""))
        return predictions
    else:
        authed_proj_keys = (
            get_authed_projkeys() if auth_only else get_all_projkeys())
        if len(authed_proj_keys) == 0:
            return []
        predictions = []
        for this_projkey in authed_proj_keys:
            cursor = (
                rdb.table("predictions").filter({"projkey": this_projkey})
                .pluck("model_name", "model_type", "filename", "created")
                .run(g.rdb_conn))
            for entry in cursor:
                predictions.append(
                    entry['model_name']
                    + (" - %s" % str(entry['model_type']) if detailed else "")
                    + (
                        " (created %s PST)" % str(entry['created'])[:-13]
                        if detailed else ""))
        return predictions


@app.route('/get_list_of_projects', methods=['POST', 'GET'])
@stormpath.login_required
def get_list_of_projects():
    """Return list of project names current user can access.

    Called from browser to populate select options.

    Returns
    -------
    flask.Response() object
        Creates flask.Response() object with JSONified dict
        (``{'list':list_of_projects}``).

    """
    if request.method == 'GET':
        list_of_projs = list_projects(name_only=True)
        return jsonify({'list': list_of_projs})


def list_projects(auth_only=True, name_only=False):
    """Return list of strings describing entries in 'projects' table.

    Parameters
    ----------
    auth_only : bool, optional
        If True, returns only those projects that the current user is
        authenticated to access, else all projects in table are
        returned. Defaults to True.
    name_only : bool, optional
        If True, includes date & time created, omits if False.
        Defaults to False.

    Returns
    -------
    list of str
        List of strings describing project entries.

    """
    proj_keys = (get_authed_projkeys() if auth_only else get_all_projkeys())
    if len(proj_keys) == 0:
        return []
    proj_names = []
    for entry in (
            rdb.table('projects').get_all(*proj_keys).run(g.rdb_conn)):
        if 'name' in entry:
            if 'created' not in entry:
                name_only = True
            proj_names.append(
                entry['name'] + (
                    " (created %s PST)" % str(entry['created'])[:-13]
                    if not name_only else ""))
    return proj_names


def add_project(name, desc="", addl_authed_users=[], user_email="auto"):
    """Add a new entry to the rethinkDB 'projects' table.

    Parameters
    ----------
    name : str
        New project name.
    desc : str, optional
        Project description. Defaults to an empty strings.
    addl_authed_users : list of str, optional
        List of email addresses (str format) of additional users
        authorized to access this new project. Defaults to empty list.
    user_email : str, optional
        Email of user creating new project. If "auto", user email
        determined by `stormpath.user` thread-local. Defauls to "auto".

    Returns
    -------
    str
        RethinkDB key/ID of newly created project entry.

    """
    if user_email in ["auto", None, "None", "none", "Auto"]:
        user_email = get_current_userkey()
    if isinstance(addl_authed_users, str):
        if addl_authed_users.strip() in [",", ""]:
            addl_authed_users = []
    new_projkey = rdb.table("projects").insert({
        "name": name,
        "description": desc,
        "created": str(rdb.now().in_timezone('-08:00').run(g.rdb_conn))
    }).run(g.rdb_conn)['generated_keys'][0]
    new_entries = []
    for authed_user in [user_email] + addl_authed_users:
        new_entries.append({
            "userkey": authed_user,
            "projkey": new_projkey,
            "active": "y"})
    rdb.table("userauth").insert(new_entries).run(g.rdb_conn)
    print("Project", name, "created and added to db; users",
          [user_email] + addl_authed_users,
          "added to userauth db for this project.")
    return new_projkey


def add_featureset(
        name, projkey, pid, featlist, custom_features_script=None,
        meta_feats=[], headerfile_path=None, zipfile_path=None):
    """Add a new entry to the rethinkDB 'features' table.

    Parameters
    ----------
    name : str
        New feature set name.
    projkey : str
        RethinkDB key/ID of parent project.
    pid : str
        PID of process associated with creation of new feature set.
    featlist : list
        List of names of features (strings) in new feature set.
    custom_features_script : str, optional
        Path to custom features script associated with new feature set.
        Defaults to None.
    meta_feats : list of str, optional
        List of any associated meta features. Defaults to empty list.
    headerfile_path : str, optional
        Path to header file associated with new feature set. Defaults
        to None.
    zipfile_path : str, optional
        Path to tarball file containing time-series data associated
        with new feature set. Defaults to None.

    Returns
    -------
    str
        RethinkDB key/ID of newly created featureset entry.

    """
    new_featset_key = rdb.table("features").insert({
        "projkey": projkey,
        "name": name,
        "featlist": featlist,
        "created": str(rdb.now().in_timezone('-08:00').run(g.rdb_conn)),
        "pid": pid,
        "custom_features_script": custom_features_script,
        "meta_feats": meta_feats,
        "headerfile_path": headerfile_path,
        "zipfile_path": zipfile_path
    }).run(g.rdb_conn)['generated_keys'][0]
    print("Feature set %s entry added to mltsp_app db." % name)
    return new_featset_key


def add_model(
        featureset_name, featureset_key, model_type, projkey, pid,
        meta_feats=False):
    """Add a new entry to the rethinkDB 'models' table.

    Parameters
    ----------
    name : str
        New feature set name.
    featureset_key : str
        RethinkDB key/ID of associated feature set.
    model_type : str
        Abbreviation of model/classifier type (e.g. "RF").
    projkey : str
        RethinkDB key/ID of parent project.
    pid : str
        PID of process associated with creation of new feature set.
    meta_feats : list of str, optional
        List of names of any associated meta features. Defaults to
        False.

    Returns
    -------
    str
        RethinkDB key/ID of newly created model entry.

    """
    entry = rdb.table("features").get(featureset_key).run(g.rdb_conn)
    if entry is not None and 'meta_feats' in entry:
        meta_feats = entry['meta_feats']
    new_model_key = rdb.table("models").insert({
        "name": featureset_name,
        "featset_key": featureset_key,
        "type": model_type,
        "projkey": projkey,
        "created": str(rdb.now().in_timezone('-08:00').run(g.rdb_conn)),
        "pid": pid,
        "meta_feats": meta_feats
    }).run(g.rdb_conn)['generated_keys'][0]
    print("New model entry %s added to mltsp_app db." % featureset_name)
    return new_model_key


def add_prediction(
        project_name, model_name, model_type, pred_filename,
        pid="None", metadata_file="None"):
    """Add a new entry to the rethinkDB 'predictions' table.

    Parameters
    ----------
    project_name : str
        Name of parent project.
    model_name : str
        Name of associated model.
    model_type : str
        Abbreviation of associated model/classifier type (e.g. "RF").
    pred_filename : str
        Name of time-series data file used in prediction.
    pid : str, optional
        PID of process associated with creation of new feature set.
        Defaults to "None".
    metadata_file : str, optional
        Path to associated metadata file. Defaults to "None".

    Returns
    -------
    str
        RethinkDB key/ID of newly created prediction entry.

    """
    project_key = project_name_to_key(project_name)
    new_prediction_key = rdb.table("predictions").insert({
        "project_name": project_name,
        "filename": pred_filename,
        "projkey": project_key,
        "model_name": model_name,
        "model_type": model_type,
        "created": str(rdb.now().in_timezone('-08:00').run(g.rdb_conn)),
        "pid": pid,
        "metadata_file": metadata_file
    }).run(g.rdb_conn)['generated_keys'][0]
    print("New prediction entry added to mltsp_app db.")
    return new_prediction_key


def project_associated_files(proj_key):
    """Return list of saved files associated with specified project.

    Parameters
    ----------
    proj_key : str
        RethinkDB entry ID of project.

    Returns
    -------
    list of str
        List of paths to files associated with said project.

    """
    fpaths = []

    prediction_keys = []
    features_keys = []
    model_keys = []
    try:
        cursor = rdb.table("predictions").filter({"projkey": proj_key})\
                                       .pluck("id").run(g.rdb_conn)
        for entry in cursor:
            prediction_keys.append(entry["id"])
    except:
        pass
    try:
        cursor = rdb.table("features").filter({"projkey": proj_key})\
                                    .pluck("id").run(g.rdb_conn)
        for entry in cursor:
            features_keys.append(entry["id"])
    except:
        pass
    try:
        cursor = rdb.table("models").filter({"projkey": proj_key})\
                                  .pluck("id").run(g.rdb_conn)
        for entry in cursor:
            model_keys.append(entry["id"])
    except:
        pass

    for featset_key in features_keys:
        fpaths += featset_associated_files(featset_key)
    for model_key in model_keys:
        for newpath in model_associated_files(model_key):
            if newpath not in fpaths:
                fpaths.append(newpath)
    for pred_key in prediction_keys:
        for newpath in prediction_associated_files(pred_key):
            if newpath not in fpaths:
                fpaths.append(newpath)
    return fpaths


def model_associated_files(model_key):
    """Return list of saved files associated with specified model.

    Parameters
    ----------
    model_key : str
        RethinkDB entry ID of model.

    Returns
    -------
    list of str
        List of paths to files associated with said model.

    """
    try:
        entry_dict = rdb.table("models").get(model_key).run(g.rdb_conn)
        featset_key = entry_dict["featset_key"]
        model_type = entry_dict["type"]
        fpaths = [os.path.join(cfg.MODELS_FOLDER,
                               "%s_%s.pkl" % (featset_key, model_type))]
        fpaths += featset_associated_files(featset_key)
    except:
        try:
            fpaths
        except:
            fpaths = []
    return fpaths


def featset_associated_files(featset_key):
    """Return list of saved files associated with specified feature set.

    Parameters
    ----------
    featset_key : str
        RethinkDB entry ID of feature set.

    Returns
    -------
    list of str
        List of paths to files associated with said feature set.

    """
    fpaths = []
    for fpath in [
            os.path.join(cfg.FEATURES_FOLDER, "%s_features.csv" % featset_key),
            os.path.join(cfg.FEATURES_FOLDER, "%s_classes.npy" % featset_key),
            os.path.join(os.path.join(os.path.join(
                os.path.dirname(__file__), "static"),
                "data"),
                "%s_features_with_classes.csv" % featset_key)]:
        if os.path.exists(fpath):
            fpaths.append(fpath)
    entry_dict = rdb.table("features").get(featset_key).run(g.rdb_conn)
    for key in ("headerfile_path", "zipfile_path", "custom_features_script"):
        if entry_dict and key in entry_dict:
            if entry_dict[key]:
                fpaths.append(entry_dict[key])
    return fpaths


def prediction_associated_files(pred_key):
    """Return list of saved files associated with specified prediction entry.

    Parameters
    ----------
    pred_key : str
        RethinkDB ID of prediction entry.

    Returns
    -------
    list of str
        List of paths to files associated with said prediction entry.

    """
    return []


def delete_associated_project_data(table_name, proj_key):
    """Delete DB entries and associated files, filtered by project.

    Parameters
    ----------
    table_name : str
        Name of RethinkDB table ("features", "models", or "predictions")
        whose relevant entries and files are to be deleted.

    Returns
    -------
    int
        The number of RethinkDB entries deleted.

    """
    get_files_func_dict = {"features": featset_associated_files,
                           "models": model_associated_files,
                           "predictions": prediction_associated_files}
    delete_keys = []
    cursor = rdb.table(table_name).filter({"projkey": proj_key})\
                                .pluck("id").run(g.rdb_conn)
    for entry in cursor:
        delete_keys.append(entry["id"])
    for feat_key in delete_keys:
        fpaths = get_files_func_dict[table_name](feat_key)
        for fpath in fpaths:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                    print("Deleted", fpath)
                except Exception as e:
                    print(e)
    if len(delete_keys) > 0:
        n_deleted = rdb.table(table_name).get_all(*delete_keys)\
                                       .delete().run(g.rdb_conn)["deleted"]
    else:
        n_deleted = 0
    return n_deleted


def delete_project(project_name):
    """Delete project entry and associated data.

    Deletes RethinkDB project entry whose 'name' attribute is
    `project_name`. Also deletes all entries in 'predictions',
    'features', 'models' and 'userauth' tables that are solely
    associated with this project, and removes all project data
    (features, models, etc) from the disk.

    Parameters
    ----------
    project_name : str
        Name of project to be deleted.

    Returns
    -------
    int
        The number of projects successfully deleted.

    """
    proj_keys = []
    cursor = rdb.table("projects").filter({"name": project_name})\
                                .pluck("id").run(g.rdb_conn)
    for entry in cursor:
        proj_keys.append(entry["id"])

    if len(proj_keys) > 1:
        print((
            "#######  WARNING: DELETING MORE THAN ONE PROJECT WITH NAME %s. "
            "DELETING PROJECTS WITH KEYS %s  ########") % (
            project_name, ", ".join(proj_keys)))
    elif len(proj_keys) == 0:
        print((
            "####### WARNING: flask_app.delete_project() - NO PROJECT "
            "WITH NAME %s.") % project_name)
        return 0
    for proj_key in proj_keys:
        # Delete associated data (features, models, predictions)
        for table_name in ("features", "models", "predictions"):
            n_deleted = delete_associated_project_data(table_name, proj_key)
            print("Deleted", n_deleted, table_name,
                  "entries and associated data.")
        # Delete relevant 'userauth' table entries
        rdb.table("userauth").filter({"projkey": proj_key})\
                           .delete().run(g.rdb_conn)
    # Delete project entries
    msg = rdb.table("projects").get_all(*proj_keys).delete().run(g.rdb_conn)
    print("Deleted", msg['deleted'], "projects.")
    return msg['deleted']


def get_project_details(project_name):
    """Return dict containing project details.

    Parameters
    ----------
    project_name : str
        Name of project.

    Returns
    -------
    dict
        Dictionary with the following key-value pairs:
        "authed_users": a list of emails of authenticated users
        "featuresets": a string of HTML markup of a table describing
            all associated featuresets
        "models": a string of HTML markup of a table describing all
            associated models
        "predictions": a string of HTML markup of a table describing
            all associated predictions
        "created": date/time created
        "description": project description

    """
    # TODO: add following info: associated featuresets, models
    entries = []
    cursor = rdb.table("projects").filter({"name": project_name}).run(g.rdb_conn)
    for entry in cursor:
        entries.append(entry)
    if len(entries) == 1:
        proj_info = entries[0]
        cursor = (
            rdb.table("userauth")
            .filter({"projkey": proj_info["id"], "active": "y"})
            .pluck("userkey").run(g.rdb_conn))
        authed_users = []
        for entry in cursor:
            authed_users.append(entry["userkey"])
        proj_info["authed_users"] = authed_users
        proj_info["featuresets"] = list_featuresets(
            by_project=project_name, as_html_table_string=True)
        proj_info["models"] = list_models(
            by_project=project_name, as_html_table_string=True)
        proj_info["predictions"] = list_predictions(
            by_project=project_name, as_html_table_string=True)
        return proj_info
    elif len(entries) > 1:
        print(("###### get_project_details() - ERROR: MORE THAN ONE PROJECT "
               "WITH NAME %s. ######") % project_name)
        return False
    elif len(entries) == 0:
        print(("###### get_project_details() - ERROR: NO PROJECTS WITH "
               "NAME %s. ######") % project_name)
        return False


@app.route('/get_project_details/<project_name>', methods=["POST", "GET"])
@stormpath.login_required
def get_project_details_json(project_name=None):
    """Return Response object containing project details.

    Returns flask.Response() object with JSONified output of
    `get_project_details`.

    Parameters
    ----------
    project_name : str
        Name of project.

    Returns
    -------
    flask.Response object
        Response object contains project details in JSON form.

    """
    if project_name is None:
        try:
            project_name = str(request.args.get("project_name")).strip()
        except:
            print("project_name parameter not present in call to "
                  "get_project_details")
            return jsonify({
                "Server response": "URL parameter must be 'project_name'"})
    project_details = get_project_details(project_name)
    return jsonify(project_details)


def get_authed_users(project_key):
    """Return list of users authenticated for the specified project.

    Parameters
    ----------
    project_key : str
        RethinkDB entry key/ID of project.

    Returns
    -------
    list of str
        List of authed user emails.

    """
    authed_users = []
    cursor = (rdb.table("userauth").filter({"projkey": project_key})
              .pluck("userkey").run(g.rdb_conn))
    for entry in cursor:
        authed_users.append(entry["userkey"])
    return authed_users + sys_admin_emails


def project_name_to_key(projname):
    """Return RethinkDB entry key associated with project name
    `projname`.

    Parameters
    ----------
    projname : str
        Project name.

    Returns
    -------
    str
        RethinkDB ID associated with project name.

    """
    projname = projname.strip().split(" (created")[0]
    cursor = rdb.table("projects").filter({"name": projname})\
                                .run(g.rdb_conn)
    projkeys = []
    for entry in cursor:
        projkeys.append(entry['id'])
    if len(projkeys) >= 1:
        return projkeys[-1]
    else:
        raise Exception(
            "No matching project name! - projname=" + str(projname))
        return False


def featureset_name_to_key(
        featureset_name, project_name=None, project_id=None):
    """Return RethinkDB key associated with given feature set details.

    Parameters
    ----------
    featureset_name : str
        Name of the feature set.
    project_name : str, optional
        Name of project to which feature set in question belongs.
        Defaults to None. If None, `project_id` (see below) must be
        provided.
    project_id : str, optional
        ID of project to wuich feature set in question belongs.
        Defaults to None. If None, `project_name` (see above) must be
        provided.

    Returns
    -------
    str
        RethinkDB ID/key of specified feature set.

    """
    if project_name is None and project_id is None:
        print ("featureset_name_to_key() - Neither project name nor id "
               "provided - returning false.")
        return False
    else:
        if project_id is None:
            project_id = project_name_to_key(project_name)

        featureset_key = []
        cursor = (
            rdb.table("features")
            .filter({"projkey": project_id, "name": featureset_name})
            .pluck("id").run(g.rdb_conn))
        for entry in cursor:
            featureset_key.append(entry["id"])
        try:
            featureset_key = featureset_key[0]
        except Exception as theError:
            print(theError)
            return False
        return featureset_key


def update_project_info(
        orig_name, new_name, new_desc, new_addl_authed_users,
        delete_features_keys=[], delete_model_keys=[], delete_prediction_keys=[]):
    # TODO - Refactor; delete custom feat scripts
    """Modify/update project entry with new information.

    If `delete_feature_keys`, `delete_model_keys` or
    `delete_prediction_keys` are provided, their RethinkDB entries will
    be deleted along with all associated data and files.

    Parameters
    ----------
    orig_name : str
        Name of project to be modified.
    new_name : str
        New project name. If unchanged, must be the same as `orig_name`.
    new_desc : str
        New project description (if unchanged, must be the same as
        original).
    new_addl_authed_users : list of str
        New list of authorized users (email addresses).
    delete_feature_keys : list of str, optional
        List of feature set IDs/keys to delete from this project.
    delete_model_keys : list, optional
        List of model IDs/keys to delete from this project.
    delete_prediction_keys : list of str, optional
        List of prediction IDs/keys to delete from this project.

    Returns
    -------
    dict
        Dictionary containing new project details.

    """
    userkey = get_current_userkey()
    projkey = project_name_to_key(orig_name)
    (rdb.table("projects").get(projkey)
        .update({
            "name": new_name,
            "description": new_desc})
        .run(g.rdb_conn))
    already_authed_users = get_authed_users(projkey)
    delete_fpaths = []
    for prev_auth in already_authed_users:
        if prev_auth not in new_addl_authed_users + [userkey]:
            (rdb.table("userauth")
                .filter({"userkey": prev_auth, "projkey": projkey})
                .delete().run(g.rdb_conn))
    for new_auth in new_addl_authed_users + [userkey]:
        if new_auth not in already_authed_users + [""]:
            (rdb.table("userauth")
                .insert({"userkey": new_auth, "projkey": projkey,
                         "active": "y"})
                .run(g.rdb_conn))
    if len(delete_prediction_keys) > 0:
        for pred_key in delete_prediction_keys:
            delete_fpaths.extend(prediction_associated_files(pred_key))
        rdb.table("predictions").get_all(*delete_prediction_keys)\
                              .delete().run(g.rdb_conn)
    if len(delete_features_keys) > 0:
        for features_key in delete_features_keys:
            delete_fpaths.extend(featset_associated_files(features_key))
        rdb.table("features").get_all(*delete_features_keys)\
                           .delete().run(g.rdb_conn)
    if len(delete_model_keys) > 0:
        for model_key in delete_model_keys:
            delete_fpaths.extend(model_associated_files(model_key))
        rdb.table("models").get_all(*delete_model_keys).delete().run(g.rdb_conn)
    for fpath in delete_fpaths:
        try:
            os.remove(fpath)
        except Exception as e:
            pass
    new_proj_details = get_project_details(new_name)
    return new_proj_details


def get_all_info_dict(auth_only=True):
    """Return dictionary containing application-wide information.

    For populating browser fields.

    Parameters
    ----------
    auth_only : bool, optional
        Return only data associated with projects current user is
        authenticated to access. Defaults to True.

    Returns
    -------
    dict
        Dictionary with the following keys (whose associated
        values are self-explanatory):
            'list_of_current_projects'
            'list_of_current_feature_sets'
            'list_of_current_models'
            'list_of_available_features'

    """
    info_dict = {}
    info_dict['list_of_current_projects'] = list_projects(auth_only=auth_only)
    info_dict['list_of_current_projects_json'] = simplejson.dumps(
        list_projects(auth_only=auth_only, name_only=True))
    info_dict['list_of_current_featuresets'] = list_featuresets(
        auth_only=auth_only)
    info_dict['list_of_current_featuresets_json'] = simplejson.dumps(
        list_featuresets(auth_only=auth_only, name_only=True))
    info_dict['list_of_current_models'] = list_models(auth_only=auth_only)
    info_dict['list_of_current_models_json'] = simplejson.dumps(
        list_models(auth_only=auth_only, name_only=True))
    info_dict['PROJECT_NAME'] = (
        session['PROJECT_NAME'] if "PROJECT_NAME" in session else "")
    info_dict['features_available_set1'] = get_list_of_available_features()
    info_dict['features_available_set2'] = \
        get_list_of_available_features_set2()
    return info_dict


def get_list_of_available_features():
    """Return list of built-in time-series features available."""
    return sorted([feat for feat in cfg.features_list_science if feat not in
                   cfg.ignore_feats_list_science])


def get_list_of_available_features_set2():
    """Return list of additional built-in time-series features."""
    return sorted([feat for feat in cfg.features_list_obs if feat not in
                   cfg.ignore_feats_list_science])


def allowed_file(filename):
    """Return bool indicating whether `filename` has allowed extension."""
    return ('.' in filename and
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS)


def list_filename_variants(file_name):
    """Return list of possible matching file name variants.
    """
    return [file_name, ntpath.basename(file_name),
            os.path.splitext(file_name)[0],
            os.path.splitext(ntpath.basename(file_name))[0]]


def check_headerfile_and_tsdata_format(headerfile_path, zipfile_path):
    """Ensure uploaded files are correctly formatted.

    Ensures that headerfile_path and zipfile_path conform
    to expected format - returns False if so, raises Exception if not.

    Parameters
    ----------
    headerfile_path : str
        Path to header file to inspect.
    zipfile_path : str
        Path to tarball to inspect.

    Returns
    -------
    bool
        Returns False if files are correctly formatted, otherwise
        raises an exception (see below).

    Raises
    ------
    custom_exceptions.TimeSeriesFileNameError
        If any provided time-series data files' names are absent in
        provided header file.
    custom_exceptions.DataFormatError
        If provided time-series data files or header file are
        improperly formatted.

    """
    with open(headerfile_path) as f:
        all_header_fnames = []
        column_header_line = str(f.readline())
        for line in f:
            line = str(line)
            if line.strip() != '':
                if len(line.strip().split(",")) < 2:
                    raise custom_exceptions.DataFormatError((
                        "Header file improperly formatted. At least two "
                        "comma-separated columns (file_name,class_name) are "
                        "required."))
                else:
                    all_header_fnames.append(line.strip().split(",")[0])
    the_zipfile = tarfile.open(zipfile_path)
    file_list = list(the_zipfile.getnames())
    all_fname_variants = []
    for file_name in file_list:
        this_file = the_zipfile.getmember(file_name)
        if this_file.isfile():
            file_name_variants = list_filename_variants(file_name)
            all_fname_variants.extend(file_name_variants)
            if (len(list(set(file_name_variants) &
                         set(all_header_fnames))) == 0):
                raise custom_exceptions.TimeSeriesFileNameError((
                    "Time series data file %s provided in tarball/zip file "
                    "has no corresponding entry in header file.")
                    % str(file_name))
            f = the_zipfile.extractfile(this_file)
            all_lines = [
                line.strip() for line in f.readlines() if line.strip() != '']
            line_no = 1
            for line in all_lines:
                line = str(line)
                if line_no == 1:
                    num_labels = len(line.split(','))
                    if num_labels < 2:
                        raise custom_exceptions.DataFormatError((
                            "Time series data file improperly formatted; at "
                            "least two comma-separated columns "
                            "(time,measurement) are required. Error occurred "
                            "on file %s") % str(file_name))
                else:
                    if len(line.split(',')) != num_labels:
                        raise custom_exceptions.DataFormatError((
                            "Time series data file improperly formatted; in "
                            "file %s line number %s has %s columns while the "
                            "first line has %s columns.") %
                            (
                                file_name, str(line_no),
                                str(len(line.split(","))), str(num_labels)))
                line_no += 1
    for header_fname in all_header_fnames:
        if header_fname not in all_fname_variants:
            raise custom_exceptions.TimeSeriesFileNameError((
                "Header file entry with file_name=%s has no corresponding "
                "file in provided tarball/zip file.") % header_fname)
    return False


def check_prediction_tsdata_format(newpred_file_path, metadata_file_path=None):
    """Ensure uploaded files are correctly formatted.

    Ensures that time-series data file(s) and metadata file (if any)
    conform to expected format - returns False if so, raises Exception
    if not.

    Parameters
    ----------
    newpred_file_path : str
        Path to time-series data file or tarball of files.
    metadata_file_path : str
        Path to metadata file or "None".

    Returns
    -------
    bool
        False if files are correctly formatted, otherwise raises an
        exception (see below).

    Raises
    ------
    custom_exceptions.TimeSeriesFileNameError
        If any provided time-series data files' names are absent in
        provided metadata file (only if `metadata_file_path` is not
        "None" or None).
    custom_exceptions.DataFormatError
        If provided time-series data files or metadata file are
        improperly formatted.

    """
    all_fname_variants = []
    all_fname_variants_list_of_lists = []
    if tarfile.is_tarfile(newpred_file_path):
        the_zipfile = tarfile.open(newpred_file_path)
        file_list = list(the_zipfile.getnames())

        for file_name in file_list:
            this_file = the_zipfile.getmember(file_name)
            if this_file.isfile():

                file_name_variants = list_filename_variants(file_name)
                all_fname_variants.extend(file_name_variants)
                all_fname_variants_list_of_lists.append(file_name_variants)

                f = the_zipfile.extractfile(this_file)
                all_lines = [
                    line.strip() for line in
                    f.readlines() if line.strip() != '']
                line_no = 1
                for line in all_lines:
                    line = str(line)
                    if line_no == 1:
                        num_labels = len(line.split(','))
                        if num_labels < 2:
                            raise custom_exceptions.DataFormatError((
                                "Error occurred processing file %s. Time "
                                "series data file improperly formatted; at "
                                "least two comma-separated columns "
                                "(time,measurement) are required. ")
                                % str(file_name))
                    else:
                        if len(line.split(',')) != num_labels:
                            raise custom_exceptions.DataFormatError((
                                "Time series data file improperly formatted; "
                                "in file %s line number %s has %s columns "
                                "while the first line has %s columns.")
                                % (
                                    file_name, str(line_no),
                                    str(len(line.split(","))), str(num_labels)))
                    line_no += 1
    else:
        with open(newpred_file_path) as f:
            all_lines = [str(line).strip() for line in
                         f.readlines() if str(line).strip() != '']
        file_name_variants = [
            f.name, ntpath.basename(f.name),
            os.path.splitext(f.name)[0],
            os.path.splitext(ntpath.basename(f.name))[0]]
        all_fname_variants.extend(file_name_variants)
        all_fname_variants_list_of_lists.append(file_name_variants)

        line_no = 1
        for line in all_lines:
            if line_no == 1:
                num_labels = len(line.split(','))
                if num_labels < 2:
                    raise custom_exceptions.DataFormatError(((
                        "Error occurred processing file %s. Time series data "
                        "file improperly formatted; at least two "
                        "comma-separated columns (time,measurement) are "
                        "required. Error occurred processing file %s.") %
                        ntpath.basename(newpred_file_path)))
            else:
                if len(line.split(',')) != num_labels:
                    raise custom_exceptions.DataFormatError(((
                        "Time series data file improperly formatted; in file "
                        "%s line number %s has %s columns while the first "
                        "line has %s columns.") %
                        (
                            ntpath.basename(newpred_file_path),
                            str(line_no), str(len(line.split(","))),
                            str(num_labels))))
            line_no += 1
    # Inspect metadata file, if exists
    if metadata_file_path not in ["None", None, "False", False, 0, ""]:
        all_metafile_fnames = []
        with open(metadata_file_path) as f:
            line_count = 0
            for line in f:
                line = str(line)
                if line.strip() != '':
                    if len(line.strip().split(",")) < 2:
                        raise custom_exceptions.DataFormatError((
                            "Meta data file improperly formatted. At least "
                            "two comma-separated columns "
                            "(file_name,meta_feature) are required."))
                    if line_count > 0:
                        this_fname = line.strip().split(",")[0]
                        if this_fname in all_fname_variants:
                            all_metafile_fnames.append(this_fname)
                        else:
                            raise custom_exceptions.TimeSeriesFileNameError((
                                "Metadata file entry with file_name=%s has no"
                                " corresponding file in provided time series "
                                "data files.") % this_fname)
                line_count += 1
        for file_name_vars in all_fname_variants_list_of_lists:
            if (len(set(file_name_vars) & set(all_metafile_fnames)) == 0 and
                    len(file_name_vars) > 1):
                raise custom_exceptions.TimeSeriesFileNameError(
                    ("Provided time series data file %s has no corresponding "
                     "entry in provided metadata file.") % file_name_vars[1])
    return False


def featurize_proc(
        headerfile_path, zipfile_path, features_to_use, featureset_key,
        is_test, email_user, already_featurized, custom_script_path):
    """Generate features and update feature set entry with results.

    To be executed in a subprocess using the multiprocessing module's
    Process routine.

    Parameters
    ----------
    headerfile_path : str
        Path to TS data header file.
    zipfile_path : str
        Path TS data tarball.
    features_to_use : list
        List of features to generate.
    featureset_key : str
        RethinkDB ID of new feature set.
    is_test : bool
        Boolean indicating whether to run as test.
    email_user : str or False
        If not False, email address of user to be notified upon
        completion.
    already_featurized : bool
        Boolean indicating whether files contain already generated
        features as opposed to TS data to be used for feature
        generation.
    custom_script_path : str
        Path to custom features definition script, or "None".

    """
    # needed to establish database connection because we're now in a
    # subprocess that is separate from main app:
    before_request()
    try:
        results_str = featurize.featurize(
            headerfile_path, zipfile_path, features_to_use=features_to_use,
            featureset_id=featureset_key, is_test=is_test,
            already_featurized=already_featurized,
            custom_script_path=custom_script_path)
    except Exception as theErr:
        results_str = ("An error occurred while processing your request. "
                       "Please ensure that the header file and tarball of time series "
                       "data files conform to the formatting requirements.")
        print(("   #########      Error:    flask_app.featurize_proc: %s" %
               str(theErr)))
        import traceback
        print(traceback.format_exc())
        logging.exception(("Error occurred during featurize.featurize() "
                           "call."))
        try:
            if custom_script_path not in ("None", None, False, "False"):
                os.remove(custom_script_path)
        except Exception as err:
            print ("An error occurred while attempting to remove files "
                   "associated with failed featurization attempt.")
            print(err)
            logging.exception("An error occurred while attempting to remove "
                              "files associated with failed featurization "
                              "attempt.")
    finally:
        for fpath in (headerfile_path, zipfile_path):
            try:
                os.remove(fpath)
            except Exception as e:
                print(e)
    update_featset_entry_with_results_msg(featureset_key, results_str)


def build_model_proc(featureset_name, featureset_key, model_type, model_key):
    """Build a model based on given features.

    Begins the model building process by calling
    build_model.build_model with provided parameters. To be executed
    as a separate process using the multiprocessing module's Process
    routine.

    Parameters
    ----------
    featureset_name : str
        Name of the feature set associated with the model to be created.
    model_type : str
        Abbreviation of the model type to be created (e.g. "RF").
    featureset_key : str
        RethinkDB ID of the associated feature set.

    Returns
    -------
    bool
        Returns True.
    """
    # needed to establish database connect because we're now in a subprocess
    # that is separate from main app:
    before_request()
    print("Building model...")
    try:
        model_built_msg = build_model.build_model(
            featureset_name=featureset_name, featureset_key=featureset_key,
            model_type=model_type)
        print("Done!")
    except Exception as theErr:
        print("  #########   Error: flask_app.build_model_proc() -", theErr)
        model_built_msg = (
            "An error occurred while processing your request. "
            "Please try again at a later time. If the problem persists, please"
            " <a href='mailto:MLTimeseriesPlatform+Support@gmail.com' "
            "target='_blank'>contact the support team</a>.")
        logging.exception(
            "Error occurred during build_model.build_model() call.")
    update_model_entry_with_results_msg(model_key, model_built_msg)
    return True


def prediction_proc(
        newpred_file_path, project_name, model_name, model_type,
        prediction_entry_key, sep=",", metadata_file=None,
        path_to_tmp_dir=None):
    """Generate features for new TS data and perform model prediction.

    Begins the featurization and prediction process. To be executed
    as a subprocess using the multiprocessing module's Process
    routine.

    Parameters
    ----------
    newpred_file_path : str
        Path to file containing time series data for featurization and
        prediction.
    project_name : str
        Name of the project associated with the model to be used.
    model_name : str
        Name of the model to be used.
    model_type : str
        Abbreviation of the model type (e.g. "RF").
    prediction_entry_key : str
        Prediction entry RethinkDB key.
    sep : str, optional
        Delimiting character in time series data files. Defaults to
        comma ",".
    metadata_file : str, optional
        Path to associated metadata file, if any. Defaults to None.

    """
    # sys.stdout = open("/tmp/proc_" + str(os.getpid()) + ".out", "w")
    # Needed to establish database connect because we're now in a subprocess
    # that is separate from main app:
    before_request()
    featset_key = featureset_name_to_key(
        featureset_name=model_name, project_name=project_name)
    is_tarfile = tarfile.is_tarfile(newpred_file_path)
    custom_features_script = None
    entry = rdb.table("features").get(featset_key).run(g.rdb_conn)
    features_to_use = list(entry['featlist'])
    if "custom_features_script" in entry:
        custom_features_script = entry['custom_features_script']
    n_cols_html_table = 5
    results_str = (
        "<table id='pred_results_table' class='tablesorter'>"
        "    <thead>"
        "        <tr class='pred_results'>"
        "            <th class='pred_results'>File</th>")
    for i in range(n_cols_html_table):
        results_str += (
            "            <th class='pred_results'>Class%d</th>"
            "            <th class='pred_results'>Class%d_Prob</th>") % (i + 1,
                                                                         i + 1)
    results_str += (
        "        </tr>"
        "    </thead>"
        "    <tbody>")
    try:
        results_dict = predict.predict(
            newpred_file_path=newpred_file_path, model_name=model_name,
            model_type=model_type, featset_key=featset_key, sepr=sep,
            n_cols_html_table=n_cols_html_table,
            custom_features_script=custom_features_script,
            metadata_file_path=metadata_file)
        try:
            os.remove(newpred_file_path)
            if metadata_file:
                os.remove(metadata_file)
        except Exception as err:
            print (
                "An error occurred while attempting to remove the uploaded "
                "timeseries data file (and possibly associated "
                "metadata file).")
            logging.exception((
                "An error occurred while attempting to remove "
                "the uploaded timeseries data file (and possibly associated "
                "metadata file)."))
    except Exception as theErr:
        msg = (
            "<font color='red'>An error occurred while processing your "
            "request. Please ensure the formatting of the provided time series"
            " data file(s) conforms to the specified requirements.</font>")
        update_prediction_entry_with_results(
            prediction_entry_key, html_str=msg, features_dict={},
            ts_data_dict={}, pred_results_list_dict=[], err=str(theErr))
        print("   #########      Error:   flask_app.prediction_proc:", theErr)
        logging.exception(
            "Error occurred during predict_class.predict() call.")
    else:
        if isinstance(results_dict, dict):
            big_features_dict = {}
            ts_data_dict = {}
            pred_results_list_dict = {}
            for fname, data_dict in results_dict.items():
                pred_results = data_dict['results_str']
                ts_data = data_dict['ts_data']
                features_dict = data_dict['features_dict']
                pred_results_list = data_dict['pred_results_list']

                results_str += pred_results
                big_features_dict[fname] = features_dict
                ts_data_dict[fname] = ts_data
                pred_results_list_dict[fname] = pred_results_list
            results_str += (
                "   </tbody>"
                "</table>")
            update_prediction_entry_with_results(
                prediction_entry_key, html_str=results_str,
                features_dict=big_features_dict, ts_data_dict=ts_data_dict,
                pred_results_list_dict=pred_results_list_dict)
        elif isinstance(results_dict, str):
            update_prediction_entry_with_results(
                prediction_entry_key, html_str=results_dict,
                features_dict={}, ts_data_dict={},
                pred_results_list_dict={})
        else:
            raise ValueError("predict_class.predict() returned object of "
                             "invalid type - {}.".format(type(results_dict)))
        return True
    finally:
        if path_to_tmp_dir is not None:
            try:
                shutil.rmtree(path_to_tmp_dir, ignore_errors=True)
            except:
                logging.exception(("Error occurred while attempting to remove "
                                   "uploaded files and tmp directory."))


@app.route('/')
@stormpath.login_required
def index():
    """Render default page."""
    check_user_table()
    ACTION = "None"
    info_dict = get_all_info_dict()
    return render_template(
        'index.html',
        ACTION=ACTION,
        RESULTS=False,
        FEATURES_AVAILABLE=[info_dict['features_available_set1'],
                            info_dict['features_available_set2']],
        CURRENT_PROJECTS=info_dict['list_of_current_projects'],
        CURRENT_PROJECTS_JSON=info_dict['list_of_current_projects_json'],
        CURRENT_FEATURESETS=info_dict['list_of_current_featuresets'],
        CURRENT_FEATURESETS_JSON=info_dict['list_of_current_featuresets_json'],
        CURRENT_MODELS=info_dict['list_of_current_models'],
        CURRENT_MODELS_JSON=info_dict['list_of_current_models_json'],
        PROJECT_NAME=info_dict['PROJECT_NAME'])


@app.route('/verifyNewScript', methods=['POST', 'GET'])
@stormpath.login_required
def verifyNewScript():
    """Test POSTed custom features script file.

    Handles POSTing of form that uploads a .py script. Script is
    saved and tested inside a docker container. If successful, an HTML
    string containing checkboxes, one for each of the successfully
    tested features in the script, is returned for rendering in the
    browser.

    Returns
    -------
    str
        String of HTML markup for checked checkboxes for each of the
        custom feature names.

    """
    if request.method == "POST":
        if 'custom_feat_script_file' not in request.files:
            return "No custom features script uploaded. Please try again."
        scriptfile = request.files['custom_feat_script_file']
        scriptfile_name = secure_filename(scriptfile.filename)
        scriptfile_path = os.path.join(
            os.path.join(
                cfg.UPLOAD_FOLDER, "custom_feature_scripts"),
            str(uuid.uuid4())[:10] + "_" + str(scriptfile_name))
        scriptfile.save(scriptfile_path)
        try:
            test_results = cft.verify_new_script(script_fpath=scriptfile_path)
            ks = []
#            for thisone in test_results:
            for k, v in test_results.items():
                if k not in ks:
                    ks.append(k)
            res_str = ""
            for k in ks:
                res_str += (("<input type='checkbox' value='%s' "
                             "name='custom_feature_checkbox' "
                             "id='custom_feature_checkbox' checked>%s<br>")
                            % (str(k), str(k)))
        except Exception as theErr:
            print(theErr)
            logging.exception("verifyNewScript error.")
            return str(theErr)
        finally:
            if os.path.exists(scriptfile_path):
                os.remove(scriptfile_path)
        return str(
            "The following features have successfully been tested: <br>"
            + res_str)


@app.route('/editProjectForm', methods=['POST', 'GET'])
@stormpath.login_required
def editProjectForm():
    """Handles project editing form submission."""
    if request.method == 'POST':
        orig_proj_name = str(request.form["project_name_orig"]).strip()
        new_proj_name = str(request.form["project_name_edit"]).strip()
        new_proj_description = str(request.form["project_description_edit"])
        new_addl_users = str(request.form["addl_authed_users_edit"]).split(',')
        try:
            delete_prediction_keys = list(
                request.form.getlist("delete_prediction_key"))
        except:
            delete_prediction_keys = []
        try:
            delete_model_keys = list(
                request.form.getlist("delete_model_key"))
        except:
            delete_model_keys = []
        try:
            delete_features_keys = list(
                request.form.getlist("delete_features_key"))
        except:
            delete_features_keys = []
        if new_addl_users == ['']:
            new_addl_users = []
        result = update_project_info(
            orig_proj_name, new_proj_name, new_proj_description,
            new_addl_users, delete_prediction_keys=delete_prediction_keys,
            delete_features_keys=delete_features_keys,
            delete_model_keys=delete_model_keys)
        return jsonify({"result": result})


@app.route(
    '/newProject/<proj_name>/<proj_description>/<addl_users>/<user_email>')
@app.route('/newProject', methods=['POST', 'GET'])
@stormpath.login_required
def newProject(
        proj_name=None, proj_description=None, addl_users=None, user_email=None):
    """Handle new project form and creates new RethinkDB entry.

    Parameters
    ----------
    proj_name : str
        Project name.
    proj_description : str
        Project description.
    addl_users : str
        String containing comma-separated list of any additional
        authorized users (their email handles).
    user_email : str
        Email of user creating new project.

    Returns
    -------
    flask.Response() object
        flask.Response() object containing JSONified dict with "result"
        as key and the result description as the corresponding value.

    """
    if proj_name is not None:
        try:
            proj_name = str(proj_name).strip()
            proj_description = str(proj_description).strip()
            addl_users = str(addl_users).strip()
            user_email = str(user_email).strip()
            if user_email == "":
                return jsonify({
                    "result": ("Required parameter 'user_email' must be a "
                               "valid email address.")})
        except:
            return jsonify({"result": "Invalid project title."})
        if proj_name == "":
            return jsonify({
                "result": ("Project title must contain non-whitespace "
                           "characters. Please try another name.")})
        addl_users = str(addl_users).split(',')
        if addl_users == [''] or addl_users == [' '] or addl_users == ["None"]:
            addl_users = []
        new_projkey = add_project(
            proj_name, desc=proj_description, addl_authed_users=addl_users,
            user_email=user_email)
        print(("New project %s with key %s successfully created."
               % (str(proj_name), str(new_projkey))))
        return jsonify({
            "result": ("New project %s with key %s successfully created."
                       % (str(proj_name), str(new_projkey)))})
    if request.method == 'POST':
        proj_name = str(request.form["new_project_name"]).strip()
        if proj_name == "":
            return jsonify({
                "result": ("Project title must contain at least one "
                           "non-whitespace character. Please try another name.")
            })
        proj_description = str(request.form["project_description"]).strip()
        addl_users = str(request.form["addl_authed_users"]).strip().split(',')
        if addl_users in [[''], ["None"]]:
            addl_users = []
        if "user_email" in request.form:
            user_email = str(request.form["user_email"]).strip()
        else:
            user_email = "auto"  # will be determined through Flask

        addl_users = [addl_user.strip() for addl_user in addl_users]
        if user_email == "":
            return jsonify({
                "result": ("Required parameter 'user_email' must be a valid "
                           "email address.")})

        new_projkey = add_project(
            proj_name, desc=proj_description, addl_authed_users=addl_users,
            user_email=user_email)
        print("added new proj")
        return jsonify({"result": "New project successfully created."})


@app.route('/editOrDeleteProject', methods=['POST'])
@stormpath.login_required
def editOrDeleteProject():
    """Handle 'editOrDeleteProjectForm' form submission.

    Returns
    -------
    JSON response object
        JSONified dict containing result message.

    """
    if request.method == 'POST':
        proj_name = (str(request.form["PROJECT_NAME_TO_EDIT"])
                     .split(" (created ")[0].strip())
        action = str(request.form["action"])

        if action == "Edit":
            proj_info = get_project_details(proj_name)
            if proj_info != False:
                return jsonify(proj_info)
        elif action == "Delete":
            result = delete_project(proj_name)
            print(result)
            return jsonify({"result": "Deleted %s project(s)." % result})
            # return Response(status=str(result))
        else:
            print ("###### ERROR - editOrDeleteProject() - 'action' not "
                   "in ['Edit', 'Delete'] ########")
            return jsonify({"error": "Invalid request action."})


@app.route(
    ("/get_featureset_id_by_projname_and_featsetname/<project_name>/"
     "<featureset_name>"),
    methods=["POST", "GET"])
@stormpath.login_required
def get_featureset_id_by_projname_and_featsetname(
        project_name=None, featureset_name=None):
    """Return flask.Response() object containing feature set ID.

    Parameters
    ----------
    project_name :str
        Project name.
    featureset_name : str
        Feature set name.

    Returns
    -------
    flask.Response() object
        flask.Response() object containing JSONified dict with
        "featureset_id" as a key.

    """
    project_name = project_name.split(" (created")[0].strip()
    featureset_name = featureset_name.split(" (created")[0].strip()

    projkey = project_name_to_key(project_name)
    cursor = (
        rdb.table("features")
        .filter({"name": featureset_name, "projkey": projkey})
        .pluck("id").run(g.rdb_conn))
    featureset_id = []
    for entry in cursor:
        print(entry)
        featureset_id.append(entry["id"])
    featureset_id = featureset_id[0]
    return jsonify({"featureset_id": featureset_id})


@app.route('/get_list_of_featuresets_by_project', methods=['POST', 'GET'])
@app.route(
    '/get_list_of_featuresets_by_project/<project_name>',
    methods=['POST', 'GET'])
@stormpath.login_required
def get_list_of_featuresets_by_project(project_name=None):
    """Return (in JSON form) list of project's feature sets.

    Parameters
    ----------
    project_name : str
        Name of project to inspect.

    Returns
    -------
    flask.Response() object
        flask.Response() object containing JSONified dict with
        "featset_list" as a key, whose value is a list of strings
        describing the feature sets.

    """
    if request.method == 'GET':
        if project_name is None:
            try:
                project_name = str(request.form["project_name"]).strip()
            except:
                return jsonify({"featset_list": []})
        project_name = project_name.split(" (created")[0]
        if project_name not in ["", "None", "null", None]:
            featset_list = list_featuresets(
                auth_only=False, by_project=project_name, name_only=True)
        else:
            return jsonify({"featset_list": []})
        return jsonify({"featset_list": featset_list})


@app.route('/get_list_of_models_by_project', methods=['POST', 'GET'])
@app.route(
    '/get_list_of_models_by_project/<project_name>', methods=['POST', 'GET'])
@stormpath.login_required
def get_list_of_models_by_project(project_name=None):
    """Return list of models in specified project.

    Parameters
    ----------
    project_name : str
        Name of project whose models to list.

    Returns
    -------
    flask.Response() object
        Response object containing JSONified dict with "model_list" as
        a key, whose corresponding value is a list of strings
        describing the models in specified project.

    """
    if request.method == 'GET':
        if project_name is None:
            try:
                project_name = str(request.form["project_name"]).strip()
            except:
                return jsonify({"model_list": []})

        project_name = project_name.split(" (created")[0]
        if project_name not in ["", "None", "null"]:
            model_list = list_models(
                auth_only=False, by_project=project_name,
                name_only=False, with_type=True)
        else:
            return jsonify({"model_list": []})
        return jsonify({"model_list": model_list})


@app.route('/uploadFeaturesForm', methods=['POST', 'GET'])
@stormpath.login_required
def uploadFeaturesForm():
    """Save uploaded features file(s).

    Handles POST form submission.

    Returns
    -------
    Redirects to featurizationPage. See that function for output
    details.

    """
    if request.method == 'POST':
        features_file = request.files["features_file"]
        featureset_name = str(request.form["featuresetname"]).strip()
        project_name = (str(request.form["featureset_projname_select"]).
                        strip().split(" (created")[0])
        features_file_name = (str(uuid.uuid4()) +
                              str(secure_filename(features_file.filename)))
        path = os.path.join(cfg.UPLOAD_FOLDER, features_file_name)
        features_file.save(path)
        print("Saved", path)
        return featurizationPage(
            featureset_name=featureset_name, project_name=project_name,
            headerfile_name=features_file_name, zipfile_name=None, sep=',',
            featlist=[], is_test=False, email_user=False,
            already_featurized=True)


@app.route(('/uploadDataFeaturize/<headerfile>/<zipfile>/<sep>/<project_name>'
            '/<featureset_name>/<features_to_use>/<custom_features_script>/'
            '<user_email>/<email_user>/<is_test>'), methods=['POST'])
@app.route('/uploadDataFeaturize', methods=['POST', 'GET'])
@stormpath.login_required
def uploadDataFeaturize(
        headerfile=None, zipfile=None, sep=None, project_name=None,
        featureset_name=None, features_to_use=None,
        custom_features_script=None, user_email=None, email_user=False,
        is_test=False):
    """Save uploaded time series data files and begin featurization.

    Handles POST form submission.

    Returns
    -------
    Redirects to featurizationPage, see that function for output
    details.

    """
    # TODO: ADD MORE ROBUST EXCEPTION HANDLING (HERE AND ALL OTHER FUNCTIONS)
    if request.method == 'POST':
        post_method = "browser"
        # Parse form fields
        featureset_name = str(request.form["featureset_name"]).strip()
        headerfile = request.files["headerfile"]
        zipfile = request.files["zipfile"]
        if featureset_name == "":
            return jsonify({
                "message": ("Feature Set Title must contain non-whitespace "
                            "characters. Please try a different title."),
                "type": "error"})
        sep = str(request.form["sep"])
        project_name = (str(request.form["featureset_project_name_select"]).
                        strip().split(" (created")[0])
        features_to_use = request.form.getlist("features_selected")
        custom_script_tested = str(request.form["custom_script_tested"])
        if custom_script_tested == "yes":
            custom_script = request.files["custom_feat_script_file"]
            customscript_fname = str(secure_filename(custom_script.filename))
            print(customscript_fname, 'uploaded.')
            customscript_path = os.path.join(
                os.path.join(
                    cfg.UPLOAD_FOLDER, "custom_feature_scripts"),
                str(uuid.uuid4()) + "_" + str(customscript_fname))
            custom_script.save(customscript_path)
            custom_features = request.form.getlist("custom_feature_checkbox")
            features_to_use += custom_features
        else:
            customscript_path = False
        print("Selected features:", features_to_use)
        try:
            email_user = request.form["email_user"]
            if email_user == "True":
                email_user = True
        except:  # unchecked
            email_user = False
        try:
            is_test = request.form["is_test"]
            if is_test == "True":
                is_test = True
        except:  # unchecked
            is_test = False
        # Create unique file names
        headerfile_name = (str(uuid.uuid4()) + "_" +
                           str(secure_filename(headerfile.filename)))
        zipfile_name = (str(uuid.uuid4()) + "_" +
                        str(secure_filename(zipfile.filename)))
        proj_key = project_name_to_key(project_name)
        if not sep or sep == "":
            print(filename, "uploaded but no sep info. Setting sep=,")
            sep = ","
        headerfile_path = os.path.join(
            cfg.UPLOAD_FOLDER, headerfile_name)
        zipfile_path = os.path.join(cfg.UPLOAD_FOLDER, zipfile_name)
        headerfile.save(headerfile_path)
        zipfile.save(zipfile_path)
        print("Saved", headerfile_name, "and", zipfile_name)
        try:
            check_headerfile_and_tsdata_format(headerfile_path, zipfile_path)
        except custom_exceptions.DataFormatError as err:
            os.remove(headerfile_path)
            os.remove(zipfile_path)
            print("Removed", headerfile_name, "and", zipfile_name)
            return jsonify({"message": str(err), "type": "error"})
        except custom_exceptions.TimeSeriesFileNameError as err:
            os.remove(headerfile_path)
            os.remove(zipfile_path)
            print("Removed", headerfile_name, "and", zipfile_name)
            return jsonify({"message": str(err), "type": "error"})
        except:
            raise
        return featurizationPage(
            featureset_name=featureset_name, project_name=project_name,
            headerfile_name=headerfile_name, zipfile_name=zipfile_name,
            sep=sep, featlist=features_to_use, is_test=is_test,
            email_user=email_user, custom_script_path=customscript_path)


@app.route('/featurizing')
@stormpath.login_required
def featurizing():
    """Render template for featurization in process page.

    Browser redirects here after featurization process has commenced.
    Renders template with process ID, which continually checks and
    reports progress.

    Parameters
    ----------
    PID : str
        ID of featurization subprocess.
    featureset_key : str
        RethinkDB key of feature set.
    project_name : str
        Name of parent project.

    Returns
    -------
    Rendered Jinja2 template
        flask.render_template()

    """
    PID = request.args.get("PID")
    featureset_key = request.args.get("featureset_key")
    project_name = request.args.get("project_name")
    featureset_name = request.args.get("featureset_name")
    info_dict = get_all_info_dict()
    return render_template(
        'index.html', ACTION="featurizing", PID=PID, newpred_filename="",
        FEATURES_AVAILABLE=[info_dict['features_available_set1'],
                            info_dict['features_available_set2']],
        CURRENT_PROJECTS=info_dict['list_of_current_projects'],
        CURRENT_PROJECTS_JSON=info_dict['list_of_current_projects_json'],
        CURRENT_FEATURESETS=info_dict['list_of_current_featuresets'],
        CURRENT_FEATURESETS_JSON=info_dict['list_of_current_featuresets_json'],
        CURRENT_MODELS=info_dict['list_of_current_models'],
        CURRENT_MODELS_JSON=info_dict['list_of_current_models_json'],
        PROJECT_NAME=project_name, headerfile_name="", RESULTS=True,
        features_str="", new_featset_key=featureset_key,
        featureset_name=featureset_name)


@app.route('/featurizationPage', methods=['POST', 'GET'])
@app.route(('/featurizationPage/<headerfile_name>/<zipfile_name>/<sep>/'
            '<projkey>/<featlist>/<is_test>/<email_user>'), methods=['POST', 'GET'])
@stormpath.login_required
def featurizationPage(
        featureset_name, project_name, headerfile_name, zipfile_name, sep,
        featlist, is_test, email_user, already_featurized=False,
        custom_script_path=None):
    """Save uploaded TS data files and begin featurization process.

    Handles featurization form submission - saves files and begins
    featurization in a subprocess (by calling featurize_proc), and
    returns flask.Response() object with the following info: new
    process ID, feature set name, project name, header file name,
    zip file name, new feature set key.

    Parameters
    ----------
    featureset_name : str
        Feature set name.
    project_name : str
        Name of parent project.
    headerfile_name : str
        Header file name.
    zipfile_name : str
        Tarball file name.
    sep : str
        Delimiting character in CSV data.
    featlist : list of str
        List of names of features in feature set.
    is_test : bool
        Boolean indicating whether to generate features on all TS data
        files (is_test = False) or a test subset (``is_test = True``).
    email_user : str
        Email address of user to be notified upon completion, or
        "False" for no notification.
    already_featurized : bool, optional
        Boolean indicating whether files contain already generated
        features, as opposed to TS data to be used for feature
        generation. Defaults to False.
    custom_script_path : str, optional
        Path to custom features definition script. Defaults
        to None.

    Returns
    -------
    flask.Response() object
        flask.Response() object containing JSONified dict of process
        details.

    """
    projkey = project_name_to_key(project_name)
    if already_featurized and zipfile_name is None:
        # User is uploading pre-featurized data, without time-series data
        features_filename = headerfile_name
        features_filepath = os.path.join(
            cfg.UPLOAD_FOLDER, features_filename)
        with open(features_filepath) as f:
            featlist = f.readline().strip().split(',')[1:]
        meta_feats = []
        if custom_script_path:
            # get list of features provided by custom script
            custom_features = cft.list_features_provided(custom_script_path)
        else:
            custom_features = []
        for feat in featlist:
            if (feat not in all_available_features_list and
                    feat not in custom_features):
                meta_feats.append(feat)
        if len(meta_feats) > 0:
            pass  # do stuff here !!!!!!!!!!!!!!!!!
        new_featset_key = add_featureset(
            name=featureset_name, projkey=projkey, pid="None",
            featlist=featlist, custom_features_script=custom_script_path,
            meta_feats=meta_feats, headerfile_path=features_filepath)
        multiprocessing.log_to_stderr()
        proc = multiprocessing.Process(target=featurize_proc, args=(
            features_filepath, None, featlist, new_featset_key, is_test,
            email_user, already_featurized, custom_script_path))
        proc.start()
        print("NEW FEATURESET ADDED WITH featset_key =", new_featset_key)
        PID = str(proc.pid)
        print("PROCESS ID IS", PID)
        session["PID"] = PID
        update_featset_entry_with_pid(new_featset_key, PID)
        return jsonify({
            "message": ("New feature set files saved successfully, and "
                        "featurization has begun (with process ID = %s).") % str(PID),
            "PID": PID, "featureset_name": featureset_name,
            "project_name": project_name, "headerfile_name": headerfile_name,
            "zipfile_name": str(zipfile_name),
            "featureset_key": new_featset_key})
    else:  # User is uploading time-series data to be featurized
        headerfile_path = os.path.join(
            cfg.UPLOAD_FOLDER, headerfile_name)
        zipfile_path = os.path.join(cfg.UPLOAD_FOLDER, zipfile_name)
        with open(headerfile_path) as f:
            meta_feats = f.readline().strip().split(',')[2:]
        new_featset_key = add_featureset(
            name=featureset_name, projkey=projkey, pid="None",
            featlist=featlist, custom_features_script=custom_script_path,
            meta_feats=meta_feats, headerfile_path=headerfile_path,
            zipfile_path=zipfile_path)
        print("NEW FEATURESET ADDED WITH featset_key =", new_featset_key)
        multiprocessing.log_to_stderr()
        proc = multiprocessing.Process(
            target=featurize_proc,
            args=(
                headerfile_path, zipfile_path, featlist, new_featset_key,
                is_test, email_user, already_featurized, custom_script_path))
        proc.start()
        PID = str(proc.pid)
        print("PROCESS ID IS", PID)
        session["PID"] = PID
        update_featset_entry_with_pid(new_featset_key, PID)
        return jsonify({
            "message": ("New feature set files saved successfully, and "
                        "featurization has begun (with process ID = %s).") % str(PID),
            "PID": PID, "featureset_name": featureset_name,
            "project_name": project_name, "headerfile_name": headerfile_name,
            "zipfile_name": str(zipfile_name),
            "featureset_key": new_featset_key})


@app.route('/buildModel/<project_name>/<featureset_name>/<model_type>',
           methods=['POST'])
@app.route('/buildModel', methods=['POST', 'GET'])
@stormpath.login_required
def buildModel(project_name=None, featureset_name=None, model_type=None):
    """Build new model for specified feature set.

    Handles 'buildModelForm' submission and starts model creation
    process as a subprocess (by calling prediction_proc with the
    multiprocessing.Process method). Returns JSONified dict with PID
    and other details about the process.

    Parameters
    ----------
    project_name : str
        Name of parent project.
    featureset_name : str
        Name of feature set from which to create new model.
    model_type : str
        Abbreviation of type of model to create (e.g. "RF").

    Returns
    -------
    flask.Response() object
        flask.Response() object with JSONified dict containing model
        building details.

    """
    if project_name is None:  # browser form submission
        post_method = "browser"
        project_name = (str(request.form['buildmodel_project_name_select'])
                        .split(" (created")[0].strip())
        featureset_name = (str(request.form['modelbuild_featset_name_select'])
                           .split(" (created")[0].strip())
        model_type = str(request.form['model_type_select'])
    else:
        post_method = "http_api"
    projkey = project_name_to_key(project_name)
    featureset_key = featureset_name_to_key(
        featureset_name=featureset_name,
        project_id=projkey)
    new_model_key = add_model(
        featureset_name=featureset_name,
        featureset_key=featureset_key,
        model_type=model_type,
        projkey=projkey, pid="None")
    print("new model key =", new_model_key)
    print("New model featureset_key =", featureset_key)
    multiprocessing.log_to_stderr()
    proc = multiprocessing.Process(
        target=build_model_proc,
        args=(featureset_name,
              featureset_key,
              model_type,
              str(new_model_key).strip()))
    proc.start()
    PID = str(proc.pid)
    print("PROCESS ID IS", PID)
    session["PID"] = PID
    update_model_entry_with_pid(new_model_key, PID)
    return jsonify({
        "message": "Model creation has begun (with process ID = %s)." % str(PID),
        "PID": PID,
        "project_name": project_name,
        "new_model_key": new_model_key,
        "model_name": featureset_name})


@app.route('/buildingModel')
@stormpath.login_required
def buildingModel():
    """Render template to check on model creation process in browser.

    Browser redirects here after model creation process has
    commenced. Renders browser template with process ID & other details,
    which continually checks and reports progress.

    Parameters described below are URL parameters.

    Parameters
    ----------
    PID : str
        ID of subprocess in which model is being built.
    new_model_key : str
        RethinkDB 'models' table entry key.
    project_name : str
        Name of parent project.
    model_name : str
        Name of model being created.

    Returns
    -------
    Rendered Jinja2 template
        Returns call to flask.render_template(...).

    """
    PID = request.args.get("PID")
    new_model_key = request.args.get("new_model_key")
    project_name = request.args.get("project_name")
    model_name = request.args.get("model_name")
    info_dict = get_all_info_dict()
    return render_template(
        'index.html',
        ACTION="buildingModel",
        PID=PID,
        newpred_filename="",
        FEATURES_AVAILABLE=[info_dict['features_available_set1'],
                            info_dict['features_available_set2']],
        CURRENT_PROJECTS=info_dict['list_of_current_projects'],
        CURRENT_PROJECTS_JSON=info_dict['list_of_current_projects_json'],
        CURRENT_FEATURESETS=info_dict['list_of_current_featuresets'],
        CURRENT_FEATURESETS_JSON=info_dict['list_of_current_featuresets_json'],
        CURRENT_MODELS=info_dict['list_of_current_models'],
        CURRENT_MODELS_JSON=info_dict['list_of_current_models_json'],
        PROJECT_NAME=project_name,
        headerfile_name="",
        RESULTS=True,
        features_str="",
        new_model_key=new_model_key,
        model_name=model_name)


@app.route('/uploadPredictionData', methods=['POST', 'GET'])
@stormpath.login_required
def uploadPredictionData():
    """Save uploaded files and begin prediction process.

    Handles prediction form  submission. Saves uploaded files and
    redirects to predictionPage, which begins the featurization/
    prediction process.

    Redirects to predictionPage - see that function's docstrings for
    return value details.

    """
    if request.method == 'POST':
        newpred_file = request.files["newpred_file"]
        tmp_folder = "tmp_" + str(uuid.uuid4())
        path_to_tmp_dir = os.path.join(cfg.UPLOAD_FOLDER, tmp_folder)
        os.mkdir(path_to_tmp_dir)
        if "prediction_files_metadata" in request.files:
            prediction_files_metadata = request.files[
                "prediction_files_metadata"]
            if prediction_files_metadata.filename in ["", " "]:
                print("prediction_files_metadata file not provided")
                prediction_files_metadata = None
                metadata_file_path = None
            else:
                metadata_filename = secure_filename(
                    prediction_files_metadata.filename)
                metadata_file_path = os.path.join(
                    path_to_tmp_dir,
                    metadata_filename)
        else:
            prediction_files_metadata = None
            metadata_file_path = None
        sep = str(request.form["newpred_file_sep"])
        project_name = (str(request.form["prediction_project_name"])
                        .split(" (created")[0])
        model_name, model_type_and_time = str(
            request.form["prediction_model_name_and_type"]).split(" - ")
        model_type = model_type_and_time.split(" ")[0]
        print(project_name, model_name, model_type)
        newpred_filename = secure_filename(newpred_file.filename)
        if not sep or sep == "":
            print(filename, "uploaded but no sep info. Setting sep=','")
            sep = ","
        newpred_file_path = os.path.join(path_to_tmp_dir, newpred_filename)
        # Save to disk
        newpred_file.save(newpred_file_path)
        print("Saved", newpred_filename)
        if prediction_files_metadata is not None:
            prediction_files_metadata.save(metadata_file_path)
        try:
            check_prediction_tsdata_format(
                newpred_file_path,
                metadata_file_path)
        except custom_exceptions.DataFormatError as err:
            print("DataFormatError")
            print(err)
            os.remove(newpred_file_path)
            if metadata_file_path is not None:
                os.remove(metadata_file_path)
            print("Removed ", str(newpred_file_path), (
                ("and" + str(metadata_file_path) if metadata_file_path is
                 not None else "")))
            return jsonify({"message": str(err), "type": "error"})
        except Exception as err:
            print("Uploaded Data Files Improperly Formatted.")
            print(err)
            os.remove(newpred_file_path)
            if metadata_file_path is not None:
                os.remove(metadata_file_path)
            print("Removed ", str(newpred_file_path), (
                ("and" + str(metadata_file_path) if metadata_file_path is not
                 None else "")))
            return jsonify({
                "message": (
                    "Uploaded data files improperly "
                    "formatted. Please ensure that your data files meet the "
                    "formatting guidelines and try again."),
                "type": "error"})
        return predictionPage(
            newpred_file_path=newpred_file_path,
            sep=sep,
            project_name=project_name,
            model_name=model_name,
            model_type=model_type,
            metadata_file_path=metadata_file_path,
            path_to_tmp_dir=path_to_tmp_dir)


@app.route('/predicting')
@stormpath.login_required
def predicting():
    """Render template that checks on prediction process status.

    Browser redirects here after featurization & prediction process
    has commenced. Renders template with process ID, which
    continually checks and reports progress.

    Parameters
    ----------
    PID : str
        Process ID.
    prediction_entry_key : str
        RethinkDB 'predictions' table entry key.
    project_name : str
        Name of parent project.
    prediction_model_name : str
        Name of prediction model.

    Returns
    -------
    Rendered Jinja2 template
        Returns flask.render_template(...).

    """
    PID = request.args.get("PID")
    prediction_entry_key = request.args.get("prediction_entry_key")
    project_name = request.args.get("project_name")
    prediction_model_name = request.args.get("prediction_model_name")
    model_type = request.args.get("model_type")
    info_dict = get_all_info_dict()
    return render_template(
        'index.html', ACTION="predicting", PID=PID, newpred_filename="",
        FEATURES_AVAILABLE=[info_dict['features_available_set1'],
                            info_dict['features_available_set2']],
        CURRENT_PROJECTS=info_dict['list_of_current_projects'],
        CURRENT_PROJECTS_JSON=info_dict['list_of_current_projects_json'],
        CURRENT_FEATURESETS=info_dict['list_of_current_featuresets'],
        CURRENT_FEATURESETS_JSON=info_dict['list_of_current_featuresets_json'],
        CURRENT_MODELS=info_dict['list_of_current_models'],
        CURRENT_MODELS_JSON=info_dict['list_of_current_models_json'],
        PROJECT_NAME=project_name, headerfile_name="", RESULTS=True,
        features_str="", prediction_entry_key=prediction_entry_key,
        prediction_model_name=prediction_model_name, model_type=model_type)


def predictionPage(
        newpred_file_path, project_name, model_name, model_type,
        sep=",", metadata_file_path=None, path_to_tmp_dir=None):
    """Start featurization/prediction routine in a subprocess.

    Starts featurization and prediction process as a subprocess
    using the multiprocessing.Process method.
    uploadPredictionData method redirects here after saving uploaded
    files. Returns JSONified dict with PID and other details about the
    process.

    Parameters
    ----------
    newpred_file_path : str
        Path to file containing time series data for featurization and
        prediction.
    project_name : str
        Name of the project associated with the model to be used.
    model_name : str
        Name of the model to be used.
    model_type : str
        Abbreviation of the model type (e.g. "RF").
    sep : str, optional
        Delimiting character in time series data files. Defaults to
        comma ",".
    metadata_file : str, optional
        Path to associated metadata file, if any. Defaults to None.

    Returns
    -------
    flask.Response() object
        flask.Response() object containing JSON dict with model details
        and subprocess ID.

    """
    new_prediction_key = add_prediction(
        project_name=project_name,
        model_name=model_name,
        model_type=model_type,
        pred_filename=ntpath.basename(newpred_file_path),
        pid="None",
        metadata_file=(ntpath.basename(metadata_file_path) if
                       metadata_file_path is not None else None))
    #is_tarfile = tarfile.is_tarfile(newpred_file_path)
    pred_file_name = ntpath.basename(newpred_file_path)
    print("starting prediction_proc...")
    multiprocessing.log_to_stderr()
    proc = multiprocessing.Process(
        target=prediction_proc,
        args=(
            newpred_file_path,
            project_name,
            model_name,
            model_type,
            new_prediction_key,
            sep,
            metadata_file_path,
            path_to_tmp_dir))
    proc.start()
    PID = str(proc.pid)
    print("PROCESS ID IS", PID)
    session["PID"] = PID
    update_prediction_entry_with_pid(new_prediction_key, PID)
    return jsonify({
        "message": ("New prediction files saved successfully, and "
                    "featurization/model prediction has begun (with process ID = %s)."
                    ) % str(PID),
        "PID": PID,
        "project_name": project_name,
        "prediction_entry_key": new_prediction_key,
        "model_name": model_name,
        "model_type": model_type,
        "pred_file_name": pred_file_name})


@app.route(
    '/source_details/<prediction_entry_key>/<source_fname>',
    methods=['GET'])
@stormpath.login_required
def source_details(prediction_entry_key, source_fname):
    """Render Source Details page.

    Parameters
    ----------
    prediction_entry_key : str
        RethinkDB predictions table entry key.
    source_fname : str
        File name of individual TS source being requested.

    Returns
    -------
    Rendered Jinja2 template
        flask.render_template()

    """
    return render_template(
        'source_details.html',
        prediction_entry_key=prediction_entry_key,
        source_fname=source_fname)


@app.route(
    '/load_source_data/<prediction_entry_key>/<source_fname>',
    methods=['GET'])
@stormpath.login_required
def load_source_data(prediction_entry_key, source_fname):
    """Return JSONified dict of source data in flask.Response() object.

    Returns flask.Response object containing JSONified dict with
    extracted features, time series data, file name, and class
    predictions. For use in Source Details page.

    Parameters
    ----------
    prediction_entry_key : str
        RethinkDB predictions table entry key.
    source_fname : str
        File name of source being requested.

    Returns
    -------
    flask.Response() object
        flask.Response() object containing JSONified dict with "fname",
        "pred_results", "features_dict", and "ts_data" as keys.

    """
    entry = rdb.table("predictions").get(prediction_entry_key).run(g.rdb_conn)
    if entry is None:
        return jsonify({
            "ts_data": ("No entry found for prediction_entry_key = %s."
                        % prediction_entry_key),
            "features_dict": ("No entry found for prediction_entry_key = %s."
                              % prediction_entry_key),
            "pred_results": pred_results})
    pred_results = entry['pred_results_list_dict'][source_fname]
    features_dict = entry['features_dict'][source_fname]
    ts_data = entry['ts_data_dict'][source_fname]
    return jsonify({
        "fname": source_fname, "pred_results": pred_results,
        "features_dict": features_dict, "ts_data": ts_data})


@app.route(
    '/load_prediction_results/<prediction_key>', methods=['POST', 'GET'])
@stormpath.login_required
def load_prediction_results(prediction_key):
    """Return JSON dict with file name and class prediction results.

    Parameters
    ----------
    prediction_key : str
        RethinkDB prediction entry key.

    Returns
    -------
    flask.Response() object
        flask.Response() object containing JSONified dict with
        "results_str_html" as key - a string containing a table of
        results in HTML markup.

    """
    results_dict = rdb.table("predictions").get(prediction_key).run(g.rdb_conn)
    if results_dict is not None and "results_str_html" in results_dict:
        if ("An error occurred" in results_dict["results_str_html"] or
                "Error occurred" in results_dict["results_str_html"]):
            rdb.table("predictions").get(prediction_key).delete().run(g.rdb_conn)
            print("Deleted prediction entry with key", prediction_key)

        return jsonify(results_dict)
    else:
        return jsonify({
            "results_str_html": ("<font color='red'>An error occurred while "
                                 "processing your request.</font>")})


@app.route('/load_model_build_results/<model_key>', methods=['POST', 'GET'])
@stormpath.login_required
def load_model_build_results(model_key):
    """Return JSON dict with model build request status message.

    If an error occurred during the model building process, the
    RethinkDB entry is deleted.

    Parameters
    ----------
    model_key : str
        RethinkDB model entry key.

    Returns
    -------
    flask.Response() object
        flask.Response() object with JSONified dict containing model
        details.

    """
    results_dict = rdb.table("models").get(model_key).run(g.rdb_conn)
    if results_dict is not None and "results_msg" in results_dict:
        if ("Error occurred" in results_dict["results_msg"] or
                "An error occurred" in results_dict["results_msg"]):
            rdb.table("models").get(model_key).delete().run(g.rdb_conn)
            print("Deleted model entry with key", model_key)
        return jsonify(results_dict)
    else:
        return jsonify({
            "results_msg": ("No status message could be found for this "
                            "process.")})


@app.route('/load_featurization_results/<new_featset_key>',
           methods=['POST', 'GET'])
@stormpath.login_required
def load_featurization_results(new_featset_key):
    """Returns JSON dict with featurization request status message.

    If an error occurred during featurization, the associated files
    uploaded and/or created are deleted, as is the RethinkDB entry.

    Parameters
    ----------
    new_featset_key : str
        RethinkDB 'features' table entry key.

    Returns
    -------
    flask.Response() object
        flask.Response() object with JSONified dict containing feature
        set status message.

    """
    results_dict = rdb.table("features").get(new_featset_key).run(g.rdb_conn)
    if (results_dict is not None and "results_msg" in results_dict and
            results_dict["results_msg"] is not None):
        if ("Error occurred" in str(results_dict["results_msg"]) or
                "An error occurred" in str(results_dict["results_msg"])):
            if ("headerfile_path" in results_dict and
                    results_dict["headerfile_path"] is not None):
                try:
                    os.remove(results_dict["headerfile_path"])
                    print("Deleted", results_dict["headerfile_path"])
                except Exception as err:
                    print(err)
            else:
                print("headerfile_path not in asdfasdf or is None")
            if ("zipfile_path" in results_dict and
                    results_dict["zipfile_path"] is not None):
                try:
                    os.remove(results_dict["zipfile_path"])
                    print("Deleted", results_dict["zipfile_path"])
                except Exception as err:
                    print(err)
            if ("custom_features_script" in results_dict and
                    results_dict["custom_features_script"]):
                try:
                    (os.remove(str(results_dict["custom_features_script"])
                               .replace(".py", ".pyc")))
                    print(("Deleted",
                           (str(results_dict["custom_features_script"])
                            .replace(".py", ".pyc"))))
                except Exception as err:
                    print(err)
                try:
                    os.remove(results_dict["custom_features_script"])
                    print("Deleted", results_dict["custom_features_script"])
                except Exception as err:
                    print(err)
            rdb.table("features").get(new_featset_key).delete().run(g.rdb_conn)
            print("Deleted feature set entry with key", new_featset_key)

        return jsonify(results_dict)
    else:
        return jsonify({
            "results_msg": "No status message could be found for this process."
        })


@app.route('/emailUser', methods=['POST', 'GET'])
@stormpath.login_required
def emailUser(user_email=None):
    """Send a notification email to specified address.

    Emails specified (or current) user with notification that the
    feature creation process has completed.

    Parameters
    ----------
    user_email : str, optional
        Email address. Defaults to None, in which case the current
        user's email is used.

    Returns
    -------
    str
        Human readable success/failure message.

    """
    print('/emailUser() called.')
    try:
        if user_email is None:
            user_email = str(get_current_userkey())
        msg = MIMEText("Notification: Job Complete")
        msg['Subject'] = 'MLTSP - Job Complete'
        msg_from = 'MLTimeseriesPlatform@gmail.com'
        msg_from_passwd = 'Lotsa*Bits'
        msg_to = user_email
        msg['From'] = msg_from
        msg['To'] = user_email
        #s = smtplib.SMTP('localhost')
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(msg_from, msg_from_passwd)
        s.sendmail(msg_from, [user_email], msg.as_string())
        s.quit()
        return "A notification email has been sent to %s." % user_email
    except Exception as theError:
        return str(theError)


def run_main(args=None):
    if args is None:
        import argparse

        parser = argparse.ArgumentParser(description='MLTSP web server')
        parser.add_argument('--port', type=int, default=5000,
                            help='Port number (default 5000)')
        parser.add_argument('--host', type=str, default='127.0.0.1',
                            help='Address to listen on (default 127.0.0.1)')
        parser.add_argument('--debug', action='store_true',
                            help='Enable debugging (default: False)')
        parser.add_argument('--disable-auth', action='store_true',
                            help='Disable user authentication')
        parser.add_argument('--db-init', action='store_true',
                            help='Initialize the database')
        parser.add_argument('--install', action='store_true',
                            help='Install configuration files')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--version', action='store_true')
        args = parser.parse_args()

    if args.version:
        print(version)
        sys.exit(0)

    elif args.install:
        from .. import install
        install()
        sys.exit(0)

    elif args.db_init:
        db_init(force=args.force)
        sys.exit(0)

    if args.debug:
        app.config['DEBUG'] = True
        app.config['WTF_CSRF_ENABLED'] = False

    print("Launching server on %s:%s" % (args.host, args.port))
    print("Logging to:", cfg.ERR_LOG_PATH)
    app.run(port=args.port, host=args.host, threaded=True)


if __name__ == '__main__':
    run_main()
