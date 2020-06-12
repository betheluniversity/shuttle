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


def mybethel_roles(username):
    conn = None
    try:
        conn = engine.raw_connection()
        call_cursor = conn.cursor()
        result_cursor = conn.cursor()
        call_cursor.callproc("bth_websrv_api.user_to_roles", (username, result_cursor))
        result = result_cursor.fetchall()
        conn.close()

        return get_results(result)
    except Exception as error:
        send_sentry_message(username, error)
        if conn:
            conn.close()
        # if mybethel can't get the data, then prevent anything from loading
        return abort(503)


def portal_common_profile(username):
    conn = None
    try:
        conn = engine.raw_connection()
        call_cursor = conn.cursor()
        result_cursor = conn.cursor()
        call_cursor.callproc('bth_portal_channel_api.bu_profile_name_photo', (username, result_cursor,))
        r = result_cursor.fetchall()
        conn.close()
        return get_results(r)
    except Exception as error:
        send_sentry_message(username, error)
        if conn:
            conn.close()
        # if mybethel can't get the data, then prevent anything from loading
        return abort(503)


def commit_schedule_to_db(table):
    sql = "DELETE FROM SHUTTLE_SCHEDULE"
    query(sql, 'write')

    for i in range(len(table)):
        location = ""
        for j in range(len(table[i])):
            try:
                arrival_time = 0
                if table[i][j].lower() == 'clc' or table[i][j].lower() == 'anderson' or table[i][j].lower() == 'pine tree' \
                        or table[i][j].lower() == 'kresge' or table[i][j].lower() == 'scandia' or table[i][j].lower() == 'north':
                    location = table[i][j].upper()
                elif table[i][j] == '-' or table[i][j] == 'DROP':
                    arrival_time = '01-AUG-00 01.00.00.000000000 AM'
                elif table[i][j].split(':') is not None:
                    split_time = table[i][j].split(':')
                    if int(split_time[0]) == 12 or 1 <= int(split_time[0]) < 6:
                        joined_time = '.'.join(split_time)
                        arrival_time = '01-SEP-00 ' + joined_time + '.00.000000000 PM'
                    else:
                        joined_time = '.'.join(split_time)
                        arrival_time = '01-SEP-00 ' + joined_time + '.00.000000000 AM'
                else:
                    return "data in calendar does not match specified format"
                if j is not 0:
                    sql = "INSERT INTO SHUTTLE_SCHEDULE (LOCATION,ARRIVAL_TIME) VALUES (" + "\'" + location + \
                          "\',\'" + arrival_time + "\')"
                    query(sql, 'write')
            except:
                return "Something went wrong. Please check that the table formatting is correct or call the " \
                       "ITS Help Desk at 651-638-6500"
    return "The Calendar has been submitted"


def commit_shuttle_request_to_db(location):
    if location != "":
        try:
            now = datetime.datetime.now()
            date = now.strftime('%d-%b-%Y %I:%M %p')
            username = flask_session['USERNAME']
            single_quote = "\'"
            sql = "INSERT INTO SHUTTLE_REQUEST_LOGS(LOG_DATE,USERNAME,LOCATION,ACTIVE) VALUES (TO_DATE(" + \
                single_quote + date + "\', \'dd-mon-yyyy hh:mi PM\')," + single_quote + username + single_quote + \
                "," + single_quote + location + single_quote + ",\'y" + single_quote + ")"
            query(sql, 'write')
            return "Your request has been submitted"
        except:
            return "Something went wrong. Please try again or call the ITS Help Desk at 651-638-6500"
    return "Please select a location"


def number_active_in_db():
    try:
        sql = "SELECT ACTIVE FROM SHUTTLE_REQUEST_LOGS"
        results = query(sql, 'read')
        return str(len(results))
    except:
        return "error"
