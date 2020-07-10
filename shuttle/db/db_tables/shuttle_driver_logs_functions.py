import datetime

from flask import session as flask_session

from shuttle.db.db_functions import query


# Commits a driver's check in to a location into the database
def commit_driver_check_in(location, direction):
    try:
        now = datetime.datetime.now()
        date = now.strftime('%d-%b-%Y')
        full_date = now.strftime('%d-%b-%Y %I:%M %p')
        username = flask_session['USERNAME']
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
    except:
        return 'Error'


# Commits a driver's break to the database
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
            sql = "INSERT INTO SHUTTLE_DRIVER_LOGS (LOG_DATE, USERNAME, ARRIVAL_TIME, ON_BREAK) VALUES ('{0}'," \
                  "'{1}', TO_DATE('{2}', 'dd-mon-yyyy hh:mi PM'), 'N')".format(date, username, full_date)
            query(sql, 'write')
            sql = "UPDATE SHUTTLE_DRIVER_LOGS SET ON_BREAK = 'N' WHERE ON_BREAK = 'Y' AND " \
                  "USERNAME = '{0}'".format(username)
            query(sql, 'write')
            return 'off break success'
        elif driver_break == 'request-to-clock-out':
            if status == 'On break':
                return 'error: already on break'
            sql = "INSERT INTO SHUTTLE_DRIVER_LOGS (LOG_DATE, USERNAME, DEPARTURE_TIME, ON_BREAK) VALUES ('{0}', " \
                  "'{1}', TO_DATE('{2}', 'dd-mon-yyyy hh:mi PM'), 'Y')".format(date, username, full_date)
            query(sql, 'write')
            return 'on break success'
        else:
            return 'Error'
    except:
        return 'Error'


# Checks the database and returns whether the current user viewing the page is on break or not
def break_status():
    username = flask_session['USERNAME']
    sql = "SELECT * FROM SHUTTLE_DRIVER_LOGS WHERE ON_BREAK = 'Y' AND USERNAME = '{0}'".format(username)
    results = query(sql, 'read')
    if results:
        return 'On break'
    else:
        return 'Not on break'


# Returns a dictionary of every driver log
def get_shuttle_logs():
    sql = "SELECT * FROM SHUTTLE_DRIVER_LOGS ORDER BY LOG_DATE"
    results = query(sql, 'read')
    return results


# Returns a dictionary of every driver log of a specific date
# Logs here are sorted by username first and then by date
def get_shuttle_logs_by_username(date):
    date = datetime.datetime.strptime(date, '%b-%d-%Y').strftime('%d-%b-%Y')
    sql = "SELECT * FROM SHUTTLE_DRIVER_LOGS WHERE LOG_DATE = '{0}' ORDER BY USERNAME," \
          "CASE WHEN ARRIVAL_TIME < DEPARTURE_TIME THEN ARRIVAL_TIME " \
          "ELSE coalesce(DEPARTURE_TIME, ARRIVAL_TIME) END".format(date)
    results = query(sql, 'read')
    return results


# Returns a dictionary of every driver log of a specific date
# Logs here are sorted by date
def get_shuttle_logs_by_date(date):
    date = datetime.datetime.strptime(date, '%b-%d-%Y').strftime('%d-%b-%Y')
    sql = "SELECT * FROM SHUTTLE_DRIVER_LOGS WHERE LOG_DATE = '{0}' ORDER BY " \
          "CASE WHEN ARRIVAL_TIME < DEPARTURE_TIME THEN ARRIVAL_TIME " \
          "ELSE coalesce(DEPARTURE_TIME, ARRIVAL_TIME) END".format(date)
    results = query(sql, 'read')
    return results


# Method that grabs the last data that was inserted into the database
# This assumes the latest data has the largest id and that there is only one driver submitting records
def get_last_location():
    sql = "SELECT * FROM " \
          "(SELECT * FROM SHUTTLE_DRIVER_LOGS WHERE LOCATION IS NOT NULL ORDER BY ID DESC) Where ROWNUM = 1"
    results = query(sql, 'read')
    if results[0]['arrival_time']:
        time = results[0]['arrival_time'].strftime('%I:%M %p').lstrip("0").replace(" 0", " ")
        recent_data = {"location": results[0]['location'], "time": time}
    elif results[0]['departure_time']:
        time = results[0]['departure_time'].strftime('%I:%M %p').lstrip("0").replace(" 0", " ")
        recent_data = {"location": results[0]['location'], "time": time}
    else:
        return "Error"
    return recent_data
