import datetime
import re
import time

# Packages
from flask import abort
from flask import session as flask_session

# Local
from shuttle.db import engine
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


# Commits schedule to the db. Assumes first row has the locations with its times in the same column
def commit_schedule(table, all_locations):
    try:
        all_locations = [i.upper() for i in all_locations]
        queries = []
        locations = {}
        for i in range(len(table)):
            for j in range(len(table[i])):
                departure_time = ''
                if i == 0:
                    if table[i][j].upper() in all_locations:
                        locations.update({j: table[i][j]})
                        sql = "INSERT INTO SHUTTLE_CAMPUS_LOCATIONS (LOCATION) VALUES ('{0}')" \
                            .format(locations[j])
                        queries.append(sql)
                        continue
                    else:
                        return 'no match'
                elif table[i][j] == '-' or table[i][j] == 'DROP':
                    pass
                elif re.search("^[\d]:[\d][\d]$", table[i][j]) or re.search("^[\d][\d]:[\d][\d]$", table[i][j]):
                    split_time = table[i][j].split(':')
                    if int(split_time[0]) == 12 or 1 <= int(split_time[0]) < 6:
                        joined_time = '.'.join(split_time)
                        departure_time = '01-SEP-00 ' + joined_time + '.00.000000000 PM'
                    else:
                        joined_time = '.'.join(split_time)
                        departure_time = '01-SEP-00 ' + joined_time + '.00.000000000 AM'
                else:
                    return 'no match'
                sql = "INSERT INTO SHUTTLE_SCHEDULE (LOCATION, DEPARTURE_TIME) VALUES ('{0}', '{1}')"\
                    .format(locations[j], departure_time)
                queries.append(sql)
        # Don't until finished in case it fails (memory inefficient but needed)
        sql = "DELETE FROM SHUTTLE_SCHEDULE"
        query(sql, 'write')
        sql = "DELETE FROM SHUTTLE_CAMPUS_LOCATIONS"
        query(sql, "write")
        for sql in queries:
            query(sql, 'write')
        return 'success'
    except:
        return 'Error'


def commit_shuttle_request(pick_up_location, drop_off_location):
    try:
        if pick_up_location == '' or drop_off_location == '':
            return 'no location'
        if pick_up_location == drop_off_location:
            return 'same location'

        now = datetime.datetime.now()
        current_time = now.strftime('%H:%M')
        current_time = time.strptime(current_time, '%H:%M')
        day = now.strftime('%a')
        # If it is the weekend, the hours for an On Call shuttle are only from 12:30am to 9:00pm
        if day == 'Sat' or day == 'Sun':
            if current_time < time.strptime('12:30', '%H:%M') or current_time > time.strptime('21:00', '%H:%M'):
                return 'bad time'
        # If it is a weekday, the hours of operation are specific
        else:
            if current_time < time.strptime('8:00', '%H:%M') \
                    or time.strptime('9:00', '%H:%M') < current_time < time.strptime('9:45', '%H:%M') \
                    or time.strptime('10:45', '%H:%M') < current_time < time.strptime('13:00', '%H:%M') \
                    or time.strptime('13:45', '%H:%M') < current_time < time.strptime('14:30', '%H:%M') \
                    or current_time > time.strptime('21:00', '%H:%M'):
                return 'bad time'

            # The shuttle only does off campus stops from 8:00am to 5:30pm during the week
            db_locations = get_db_locations()
            on_campus_locations = []
            for location in db_locations:
                on_campus_locations.append(db_locations[location]['location'])
            if time.strptime('8:00', '%H:%M') < current_time < time.strptime('17:30', '%H:%M') and \
                    pick_up_location in on_campus_locations and drop_off_location in on_campus_locations:
                return 'bad location'

        username = flask_session['USERNAME']
        date = now.strftime('%d-%b-%Y %I:%M %p')
        sql = "INSERT INTO SHUTTLE_REQUEST_LOGS(LOG_DATE, USERNAME, PICK_UP_LOCATION, DROP_OFF_LOCATION) " \
              "VALUES (TO_DATE('{0}', 'dd-mon-yyyy hh:mi PM'), '{1}', '{2}', '{3}')". \
            format(date, username, pick_up_location, drop_off_location)
        query(sql, 'write')
        return 'success'
    except:
        return 'Error'


# This method returns the number of active requests as well as what
# location is currently being requested by the user (if any)
def number_active_requests():
    try:
        sql = "SELECT * FROM SHUTTLE_REQUEST_LOGS WHERE COMPLETED_AT IS NULL"
        results = query(sql, 'read')
        username = flask_session['USERNAME']
        pick_up_location = ''
        drop_off_location = ''
        for log in results:
            if results[log]['username'] == username:
                pick_up_location = results[log]['pick_up_location']
                drop_off_location = results[log]['drop_off_location']
        requests = {
            'waitlist-num': len(results),
            'requested-pick-up': pick_up_location,
            'requested-drop-off': drop_off_location
        }
        return requests
    except:
        return 'Error'


def get_position_in_waitlist():
    username = flask_session['USERNAME']
    sql = "WITH NumberedRows AS(SELECT USERNAME, ROW_NUMBER() OVER (ORDER BY LOG_DATE) AS RowNumber from " \
          "SHUTTLE_REQUEST_LOGS WHERE COMPLETED_AT IS NULL) SELECT RowNumber FROM NumberedRows " \
          "WHERE USERNAME = '{0}'".format(username)
    results = query(sql, 'read')
    return results


def get_users():
    sql = "SELECT * FROM SHUTTLE_USERS"
    results = query(sql, 'read')
    return results


def delete_user(username):
    try:
        sql = "DELETE FROM SHUTTLE_USERS WHERE USERNAME = '{0}'".format(username)
        query(sql, 'write')
        return 'success'
    except Exception as error:
        return 'error'


def change_user_role(username, role):
    try:
        sql = "UPDATE SHUTTLE_USERS SET ROLE = '{0}' WHERE USERNAME = '{1}'".format(role, username)
        results = query(sql, 'write')
        return 'success'
    except Exception as error:
        return 'error'


# This method deletes the user's active request
def user_deleted_request():
    try:
        username = flask_session['USERNAME']
        sql = "DELETE FROM SHUTTLE_REQUEST_LOGS WHERE COMPLETED_AT IS NULL AND USERNAME = '{0}'".format(username)
        query(sql, 'write')
        return 'success'
    except:
        return 'Error'


def commit_driver_check_in(location):
    try:
        now = datetime.datetime.now()
        date = now.strftime('%d-%b-%Y')
        full_date = now.strftime('%d-%b-%Y %I:%M %p')
        username = flask_session['USERNAME']
        if location != '':
            sql = "INSERT INTO SHUTTLE_DRIVER_LOGS (LOG_DATE, USERNAME, LOCATION, DEPARTURE_TIME) VALUES ('{0}', " \
                  "'{1}', '{2}', TO_DATE('{3}', 'dd-mon-yyyy hh:mi PM'))".format(date, username, location, full_date)
            query(sql, 'write')
            return 'Success'
        return 'bad location'
    except:
        return 'Error'


def commit_break(driver_break):
    try:
        now = datetime.datetime.now()
        date = now.strftime('%d-%b-%Y')
        full_date = now.strftime('%d-%b-%Y %I:%M %p')
        username = flask_session['USERNAME']
        status = break_status()
        if driver_break == 'request-to-clock-in':
            if status == 'Not on break':
                return 'error: not on break'
            sql = "UPDATE SHUTTLE_BREAK_LOGS SET CLOCK_IN = TO_DATE('{0}','dd-mon-yyyy hh:mi PM') " \
                  "WHERE USERNAME = '{1}' AND CLOCK_IN IS NULL".format(full_date, username)
            query(sql, 'write')
            return 'off break success'
        elif driver_break == 'request-to-clock-out':
            if status == 'On break':
                return 'error: already on break'
            sql = "INSERT INTO SHUTTLE_BREAK_LOGS (USERNAME, CLOCK_OUT) " \
                  "VALUES ('{0}', TO_DATE('{1}','dd-mon-yyyy hh:mi PM'))".format(username, full_date)
            query(sql, 'write')
            return 'on break success'
        else:
            return 'Error'
    except:
        return 'Error'


def get_scheduled_shuttle_logs():
    sql = "SELECT DISTINCT LOG_DATE FROM SHUTTLE_DRIVER_LOGS ORDER BY LOG_DATE"
    results = query(sql, 'read')
    return results


def get_on_call_shuttle_logs():
    sql = "SELECT DISTINCT LOG_DATE FROM SHUTTLE_REQUEST_LOGS ORDER BY LOG_DATE"
    results = query(sql, 'read')
    return results


def get_break_logs():
    sql = "SELECT * FROM SHUTTLE_BREAK_LOGS"
    results = query(sql, 'read')
    return results


def get_specific_break_logs(date):
    logs = get_break_logs()
    logs_for_date = {}
    logs_for_date_iter = 0
    # Break logs don't have a log date so we need to split the clock_out time to date
    # Then we sort it in another method
    for i in range(len(logs)):
        date_of_log = logs[i]['clock_out'].strftime('%d-%b-%Y')
        if date_of_log == date:
            logs_for_date[logs_for_date_iter] = logs[i]
            real_name = username_search(logs_for_date[logs_for_date_iter]['username'])
            logs_for_date[logs_for_date_iter]['name'] = real_name[0]['firstName'] + ' ' + real_name[0]['lastName']
            logs_for_date_iter += 1
    return logs_for_date


def get_break_logs_by_username(date):
    logs = get_specific_break_logs(date)
    sort = sorted(logs, key=lambda i: ((logs[i]['name']), logs[i]['clock_out']))
    sorted_logs = {}
    for i in range(len(sort)):
        sorted_logs[i] = logs[sort[i]]
    return sorted_logs


def get_break_logs_by_date(date):
    logs = get_specific_break_logs(date)
    sort = sorted(logs, key=lambda i: (logs[i]['clock_out']))
    sorted_logs = {}
    for i in range(len(sort)):
        sorted_logs[i] = logs[sort[i]]
    return sorted_logs


def get_scheduled_shuttle_logs_by_username(date):
    sql = "SELECT * FROM SHUTTLE_DRIVER_LOGS WHERE LOG_DATE = '{0}' " \
          "ORDER BY USERNAME, DEPARTURE_TIME ASC".format(date)
    results = query(sql, 'read')
    return results


def get_scheduled_shuttle_logs_by_date(date):
    sql = "SELECT * FROM SHUTTLE_DRIVER_LOGS WHERE LOG_DATE = '{0}' " \
          "ORDER BY DEPARTURE_TIME ASC".format(date)
    results = query(sql, 'read')
    return results


def get_on_call_logs_by_username(date):
    sql = "SELECT * FROM SHUTTLE_REQUEST_LOGS WHERE TRUNC(LOG_DATE) = '{0}' " \
          "AND COMPLETED_AT IS NOT NULL ORDER BY COMPLETED_BY, COMPLETED_AT".format(date)
    results = query(sql, 'read')
    return results


def get_on_call_shuttle_logs_by_date(date):
    sql = "SELECT * FROM SHUTTLE_REQUEST_LOGS WHERE TRUNC(LOG_DATE) = '{0}' " \
          "AND COMPLETED_AT IS NOT NULL ORDER BY COMPLETED_AT".format(date)
    results = query(sql, 'read')
    return results


def get_requests():
    sql = "SELECT * FROM SHUTTLE_REQUEST_LOGS WHERE COMPLETED_AT IS NULL ORDER BY LOG_DATE"
    results = query(sql, 'read')
    for result in results:
        real_name = username_search(results[result]['username'])
        results[result]['name'] = real_name[0]['firstName'] + ' ' + real_name[0]['lastName']
        log_time = results[result]['log_date']
        results[result]['log_date'] = log_time.strftime('%-I:%M %p | %-m/%-d/%y').lower()
    return results


def complete_shuttle_request(username):
    try:
        now = datetime.datetime.now()
        full_date = now.strftime('%d-%b-%Y %I:%M %p')
        driver_username = flask_session['USERNAME']
        sql = "UPDATE SHUTTLE_REQUEST_LOGS SET COMPLETED_AT = TO_DATE('{0}','dd-mon-yyyy hh:mi PM'), " \
              "COMPLETED_BY = '{1}' WHERE USERNAME = '{2}'".format(full_date, driver_username, username)
        query(sql, 'write')
        return 'success'
    except:
        return 'Error'


# deletes a user's request but doesn't remove it from logs
def driver_deleted_request(username):
    try:
        now = datetime.datetime.now()
        full_date = now.strftime('%d-%b-%Y %I:%M %p')
        driver_username = flask_session['USERNAME']
        sql = "UPDATE SHUTTLE_REQUEST_LOGS SET DELETED = 'Y', COMPLETED_AT = TO_DATE('{0}','dd-mon-yyyy hh:mi PM'), " \
              "COMPLETED_BY = '{1}' WHERE USERNAME = '{2}' AND COMPLETED_AT IS NULL".format(full_date, driver_username, username)
        query(sql, 'write')
        return 'success'
    except:
        return 'Error'


def break_status():
    username = flask_session['USERNAME']
    sql = "SELECT * FROM SHUTTLE_BREAK_LOGS WHERE CLOCK_IN IS NULL AND USERNAME = '{0}'".format(username)
    results = query(sql, 'read')
    if results:
        return 'On break'
    else:
        return 'Not on break'


# Method that grabs the last data that was inserted into the database
# This assumes the latest data has the largest id and that there is only one driver submitting records
def get_last_location():
    try:
        sql = "SELECT * FROM " \
              "(SELECT * FROM SHUTTLE_DRIVER_LOGS WHERE LOCATION IS NOT NULL ORDER BY ID DESC) Where ROWNUM = 1"
        results = query(sql, 'read')
        if results[0]['departure_time']:
            last_time = results[0]['departure_time'].strftime('%-I:%M %p').lower()
            last_date = results[0]['departure_time'].strftime('%d-%b-%y')
            recent_data = {'location': results[0]['location'], 'time': last_time, 'date': last_date}
        else:
            return {'location': 'Error', 'time': 'Error', 'date': 'Error'}
        return recent_data
    except:
        return {'location': 'Error', 'time': 'Error', 'date': 'Error'}


def get_db_schedule():
    sql = "SELECT LOCATION, DEPARTURE_TIME FROM SHUTTLE_SCHEDULE ORDER BY ID"
    results = query(sql, 'read')
    return results


def get_db_locations():
    sql = "Select DISTINCT LOCATION from SHUTTLE_CAMPUS_LOCATIONS"
    results = query(sql, 'read')
    return results


# Called as a cronjob that clears every active request every night
def clear_waitlist():
    try:
        now = datetime.datetime.now()
        full_date = now.strftime('%d-%b-%Y %I:%M %p')
        sql = "UPDATE SHUTTLE_REQUEST_LOGS SET COMPLETED_AT = TO_DATE('{0}','dd-mon-yyyy hh:mi PM'), " \
              "SET DELETED = 'Y' WHERE COMPLETED_AT IS NULL".format(full_date)
        query(sql, 'write')
        return 'success'
    except:
        return 'Error'


def get_campus_locations():
    sql = "Select LOCATION from SHUTTLE_CAMPUS_LOCATIONS ORDER BY ID"
    results = query(sql, 'read')
    return results
