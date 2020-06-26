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
            location = ''
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
                    return 'no match'
                if j is not 0:
                    sql = "INSERT INTO SHUTTLE_SCHEDULE (LOCATION, ARRIVAL_TIME) VALUES ('{0}', '{1}')".format\
                        (location, arrival_time)
                    query(sql, 'write')
        return 'success'
    except:
        return 'Error'


def commit_shuttle_request(location):
    try:
        username = flask_session['USERNAME']
        sql = "SELECT * FROM SHUTTLE_REQUEST_LOGS WHERE ACTIVE = 'Y'"
        results = query(sql, 'read')
        for log in results:
            if results[log]['username'] == username:
                return 'user has active request'

        if location != '':
            now = datetime.datetime.now()
            date = now.strftime('%d-%b-%Y %I:%M %p')
            sql = "INSERT INTO SHUTTLE_REQUEST_LOGS(LOG_DATE, USERNAME, LOCATION) VALUES (TO_DATE('{0}', " \
                  "'dd-mon-yyyy hh:mi PM'), '{1}', '{2}')".format(date, username, location)
            query(sql, 'write')
            return 'success'
        return 'bad location'
    except:
        return 'Error'


# This method returns the number of active requests as well as what
# location is currently being requested by the user (if any)
def number_active_requests():
    try:
        sql = "SELECT * FROM SHUTTLE_REQUEST_LOGS WHERE ACTIVE = 'Y'"
        results = query(sql, 'read')
        username = flask_session['USERNAME']
        location = ''
        for log in results:
            if results[log]['username'] == username:
                location = results[log]['location']
        requests = {'waitlist-num': len(results), 'requested-location': location}
        return requests
    except:
        return 'Error'


# This method changes the user's active request to inactive
def delete_current_request():
    try:
        username = flask_session['USERNAME']
        sql = "UPDATE SHUTTLE_REQUEST_LOGS SET ACTIVE = 'N' WHERE USERNAME = '{0}'".format(username)
        query(sql, 'write')
        return 'success'
    except:
        return 'Error'


def commit_driver_check_in(location, direction, driver_break):
    try:
        now = datetime.datetime.now()
        date = now.strftime('%d-%b-%Y')
        full_date = now.strftime('%d-%b-%Y %I:%M %p')
        username = flask_session['USERNAME']
        if location != '':
            if direction == 'departure':
                sql = "INSERT INTO SHUTTLE_DRIVER_LOGS (LOG_DATE, USERNAME, LOCATION, DEPARTURE_TIME) VALUES ('{0}', " \
                      "'{1}', '{2}', TO_DATE('{3}', 'dd-mon-yyyy hh:mi PM'))".format(date, username, location, full_date)
                query(sql, 'write')
                return 'success departure'
            elif direction == 'arrival':
                sql = "INSERT INTO SHUTTLE_DRIVER_LOGS (LOG_DATE, USERNAME, LOCATION, ARRIVAL_TIME) VALUES ('{0}', " \
                      "'{1}', '{2}', TO_DATE('{3}', 'dd-mon-yyyy hh:mi PM'))".format(date, username, location, full_date)
                query(sql, 'write')
                return 'success arrival'
            else:
                return 'Error'
        elif driver_break != '':
            if driver_break == 'N':
                sql = "INSERT INTO SHUTTLE_DRIVER_LOGS (LOG_DATE, USERNAME, ARRIVAL_TIME, ON_BREAK) VALUES ('{0}'," \
                      "'{1}', TO_DATE('{2}', 'dd-mon-yyyy hh:mi PM'), '{3}')".format(date, username, full_date, driver_break)
                query(sql, 'write')
                return 'Not on break'
            elif driver_break == 'Y':
                sql = "INSERT INTO SHUTTLE_DRIVER_LOGS (LOG_DATE, USERNAME, DEPARTURE_TIME, ON_BREAK) VALUES ('{0}', " \
                      "'{1}', TO_DATE('{2}', 'dd-mon-yyyy hh:mi PM'), '{3}')".format(date, username, full_date, driver_break)
                query(sql, 'write')
                return 'On break'
            else:
                return 'Error'
        return 'bad location'
    except:
        return 'Error'


def get_shuttle_logs():
    sql = "SELECT * FROM SHUTTLE_DRIVER_LOGS ORDER BY LOG_DATE"
    results = query(sql, 'read')
    return results


# Method that grabs the last data that was inserted into the database
# This assumes the latest data has the largest id and that there is only one driver submitting records
def get_last_location():
    sql = "SELECT * FROM " \
          "(SELECT * FROM SHUTTLE_DRIVER_LOGS WHERE LOCATION IS NOT NULL ORDER BY ID DESC) Where ROWNUM = 1"
    results = query(sql, 'read')
    if results[0]['arrival_time']:
        time = results[0]['arrival_time'].strftime('%I:%M %p')
        recent_data = {"location": results[0]['location'], "time": time}
    elif results[0]['departure_time']:
        time = results[0]['departure_time'].strftime('%I:%M %p')
        recent_data = {"location": results[0]['location'], "time": time}
    else:
        return "Error"
    return recent_data



