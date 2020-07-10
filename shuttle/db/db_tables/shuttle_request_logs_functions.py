import datetime

from flask import session as flask_session

from shuttle.db.db_functions import query, username_search


# Commits a user's shuttle request to the database
def commit_shuttle_request(pick_up_location, drop_off_location):
    try:
        if pick_up_location == '' or drop_off_location == '':
            return 'no location'
        if pick_up_location == drop_off_location:
            return 'same location'
        username = flask_session['USERNAME']
        now = datetime.datetime.now()
        date = now.strftime('%d-%b-%Y %I:%M %p')
        sql = "INSERT INTO SHUTTLE_REQUEST_LOGS(LOG_DATE, USERNAME, PICK_UP_LOCATION, DROP_OFF_LOCATION) " \
              "VALUES (TO_DATE('{0}', 'dd-mon-yyyy hh:mi PM'), '{1}', '{2}', '{3}')".\
               format(date, username, pick_up_location, drop_off_location)
        query(sql, 'write')
        return 'success'
    except:
        return 'Error'


# This method returns the number of active requests as well as what
# location is currently being requested by the user (if any)
def number_active_requests():
    try:
        sql = "SELECT * FROM SHUTTLE_REQUEST_LOGS WHERE ACTIVE = 'Y'"
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


# Returns the user's position in the waitlist
def get_position_in_waitlist():
    try:
        username = flask_session['USERNAME']
        sql = "WITH NumberedRows AS(SELECT USERNAME, ROW_NUMBER() OVER (ORDER BY LOG_DATE) AS RowNumber from " \
              "SHUTTLE_REQUEST_LOGS WHERE ACTIVE = 'Y') SELECT RowNumber FROM NumberedRows " \
              "WHERE USERNAME = '{0}'".format(username)
        results = query(sql, 'read')
        return results
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


# Grabs every currently active request
# Adds in real name (rather than username) of each user and makes time more readable
def get_requests():
    try:
        sql = "SELECT * FROM SHUTTLE_REQUEST_LOGS WHERE ACTIVE = 'Y' ORDER BY LOG_DATE"
        results = query(sql, 'read')
        for result in results:
            real_name = username_search(results[result]['username'])
            results[result]['name'] = real_name[0]['firstName'] + ' ' + real_name[0]['lastName']
            results[result]['log_date'] = results[result]['log_date'].strftime('%I:%M %p %b-%d-%Y')\
                .lstrip("0").replace(" 0", " ")
        return results
    except:
        return 'Error'


# Completes a specific user's request that a driver marked as completed
def complete_shuttle_request(username):
    try:
        sql = "UPDATE SHUTTLE_REQUEST_LOGS SET ACTIVE = 'N' WHERE USERNAME = '{0}'".format(username)
        query(sql, 'write')
        return 'success'
    except:
        return 'Error'
