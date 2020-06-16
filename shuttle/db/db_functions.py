import datetime

from flask import abort
from flask import session as flask_session
from shuttle.db.db_connection import engine
from shuttle import app, sentry_sdk


def send_sentry_message(username, error):
    sentry_sdk.capture_exception()
    app.logger.error("%s -- %s" % (username, str(error)))


def get_results(result, label=""):
    ret = {}
    for i, row in enumerate(result):
        row_dict = {}
        for item in row:
            if isinstance(item, str):
                item = item.split(":", 1)
            else:
                # blob
                item = item.read()
            if len(item) > 1:
                row_dict[item[0]] = item[1]
            else:
                # if the result set doesn't have key / value pairs
                # use a custom label
                row_dict[label] = item[0]

        ret[int(i)] = row_dict

    return ret


# This method takes in a query and runs it. "query_type" will be either "read" or "write."
# "write" will not call "get_formated_results" and just return a string.
# "read" will return formatted results of the query.
def query(sql, query_type):
    conn = engine.connect()
    transaction = conn.begin()
    results = conn.execute(sql)  # This autocommits in most cases, but for our "merge" statements we need to commit
    transaction.commit()
    if query_type == 'read':
        results = get_formatted_results(results)
    conn.close()
    return results


def get_formatted_results(query_results):
    columns = query_results.keys()  # This gets the column names of the results
    results = {}
    for i, row in enumerate(query_results):
        row_dict = {}
        j = 0
        for column in columns:
            row_dict[column] = row[j]
            j += 1
        results[int(i)] = row_dict
    return results


def get_user_by_username(username):
    ret = []
    sql = "SELECT * FROM SHUTTLE_USERS WHERE USERNAME = '{0}'".format(username)
    results = query(sql, 'read')
    for key, columns in results.items():
        ret.append(columns['role'])
    return ret


def get_table_columns(table):
    ret = []
    # 'table' needs to be uppercase to run correctly
    sql = "SELECT column_name FROM USER_TAB_COLUMNS WHERE table_name = '{0}'".format(table.upper())
    results = query(sql, 'read')
    for key, columns in results.items():
        ret.append(columns['column_name'].lower())
    return ret


def check_if_table_exists(table):
    # 'table' needs to be uppercase to run correctly
    sql = "SELECT table_name FROM user_tables where table_name = '{0}'".format(table.upper())
    results = query(sql, 'read')
    if results:
        return True
    return False


def username_search(username):
    conn = None
    try:
        conn = engine.raw_connection()
        call_cursor = conn.cursor()
        result_cursor = conn.cursor()
        call_cursor.callproc('bth_websrv_api.username_search', (username, result_cursor,))
        r = result_cursor.fetchall()
        conn.close()
        return get_results(r)
    except Exception as error:
        send_sentry_message(username, error)
        if conn:
            conn.close()
        # if mybethel can't get the data, then prevent anything from loading
        return abort(503)


def commit_schedule(table, all_locations):
    try:
        sql = "DELETE FROM SHUTTLE_SCHEDULE"
        query(sql, 'write')
        all_locations = [i.upper() for i in all_locations]
        for i in range(len(table)):
            location = ""
            for j in range(len(table[i])):
                arrival_time = 0
                if table[i][j].upper() in all_locations:
                    location = table[i][j].upper()
                elif table[i][j] == '-' or table[i][j] == 'DROP':
                    continue
                elif ':' in table[i][j]:
                    split_time = table[i][j].split(':')
                    if int(split_time[0]) == 12 or 1 <= int(split_time[0]) < 6:
                        joined_time = '.'.join(split_time)
                        arrival_time = '01-SEP-00 ' + joined_time + '.00.000000000 PM'
                    else:
                        joined_time = '.'.join(split_time)
                        arrival_time = '01-SEP-00 ' + joined_time + '.00.000000000 AM'
                else:
                    return "no match"
                if j is not 0:
                    sql = "INSERT INTO SHUTTLE_SCHEDULE (LOCATION,ARRIVAL_TIME) VALUES (" + "\'" + location + \
                          "\',\'" + arrival_time + "\')"
                    query(sql, 'write')
        return "success"
    except:
        return "failure"


def commit_shuttle_request(location):
    try:
        if location != "":
            now = datetime.datetime.now()
            date = now.strftime('%d-%b-%Y %I:%M %p')
            username = flask_session['USERNAME']
            single_quote = "\'"
            sql = "INSERT INTO SHUTTLE_REQUEST_LOGS(LOG_DATE,USERNAME,LOCATION) VALUES (TO_DATE(" + \
                single_quote + date + single_quote + ", \'dd-mon-yyyy hh:mi PM\')," + single_quote + username + \
                single_quote + "," + single_quote + location + single_quote + ")"
            query(sql, 'write')
            return "success"
        return "bad location"
    except:
        return "failure"

def number_active_requests():
    try:
        sql = "SELECT COUNT(*) FROM SHUTTLE_REQUEST_LOGS WHERE ACTIVE = 'Y'"
        results = query(sql, 'read')
        return str(results[0]['COUNT(*)'])
    except:
        return "Error"
