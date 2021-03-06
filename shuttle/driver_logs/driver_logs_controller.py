# Local
from shuttle.db import db_functions as db


class DriverLogsController:
    def __init__(self):
        pass

    def grab_dates(self):
        off_campus_shuttle_logs = db.get_scheduled_shuttle_logs()
        on_campus_shuttle_logs = db.get_on_call_shuttle_logs()
        break_logs = db.get_break_logs()
        # Changes dates to format that can be compared easily. Then adds it to list if it hasn't already shown up
        date_list_formatted = []
        date_list = []
        for i in range(len(off_campus_shuttle_logs)):
            date = off_campus_shuttle_logs[i]['log_date'].strftime('%d-%b-%Y')
            if date not in date_list_formatted:
                date_list_formatted.append(date)
                date_list.append(off_campus_shuttle_logs[i]['log_date'])
        for i in range(len(on_campus_shuttle_logs)):
            date = on_campus_shuttle_logs[i]['log_date'].strftime('%d-%b-%Y')
            if date not in date_list_formatted:
                date_list_formatted.append(date)
                date_list.append(on_campus_shuttle_logs[i]['log_date'])
        for i in range(len(break_logs)):
            date = break_logs[i]['clock_out'].strftime('%d-%b-%Y')
            if date not in date_list_formatted:
                date_list_formatted.append(date)
                date_list.append(break_logs[i]['clock_out'])
        # Sorts dates and makes them more readable
        date_list.sort(reverse=True)
        for i in range(len(date_list)):
            date_list[i] = date_list[i].strftime('%d-%b-%Y')
        return date_list

    def grab_selected_logs(self, date, name_sort):
        if name_sort == 'Sort By Name':
            scheduled_shuttle_logs = db.get_scheduled_shuttle_logs_by_username(date)
            on_call_shuttle_logs = db.get_on_call_logs_by_username(date)
            driver_break_logs = db.get_break_logs_by_username(date)
        else:
            scheduled_shuttle_logs = db.get_scheduled_shuttle_logs_by_date(date)
            on_call_shuttle_logs = db.get_on_call_shuttle_logs_by_date(date)
            driver_break_logs = db.get_break_logs_by_date(date)

        shuttle_logs = {}
        shuttle_iter = 0
        # Adds in the user's real name to the logs, changes times/dates to be more readable,
        # and separates logs into shuttle logs and break logs
        for i in range(len(scheduled_shuttle_logs)):
            real_name = db.username_search(scheduled_shuttle_logs[i]['username'])
            scheduled_shuttle_logs[i]['name'] = real_name[0]['firstName'] + ' ' + real_name[0]['lastName']
            scheduled_shuttle_logs[i]['log_date'] = scheduled_shuttle_logs[i]['log_date'].strftime('%d-%b-%Y')
            scheduled_shuttle_logs[i]['departure_time'] = scheduled_shuttle_logs[i]['departure_time'].strftime('%-I:%M %p | %-m/%-d/%y').lower()
            shuttle_logs[shuttle_iter] = scheduled_shuttle_logs[i]
            shuttle_iter += 1

        break_logs = {}
        break_iter = 0
        # Changes times to be in correct format
        for i in range(len(driver_break_logs)):
            if driver_break_logs[i]['clock_in']:
                driver_break_logs[i]['clock_in'] = driver_break_logs[i]['clock_in'].strftime('%I:%M %p | %m/%d/%y')
            driver_break_logs[i]['clock_out'] = driver_break_logs[i]['clock_out'].strftime('%I:%M %p | %m/%d/%y')
            break_logs[i] = driver_break_logs[i]
            break_iter += 1

        completed_logs = {}
        deleted_logs = {}
        completed_iter = 0
        deleted_iter = 0
        # Adds in the user's real name to the logs, changes times/dates to be more readable,
        # and separates logs into completed logs and deleted logs
        for i in range(len(on_call_shuttle_logs)):
            user_name = db.username_search(on_call_shuttle_logs[i]['username'])
            on_call_shuttle_logs[i]['user_name'] = user_name[0]['firstName'] + ' ' + user_name[0]['lastName']
            driver_name = db.username_search(on_call_shuttle_logs[i]['completed_by'])
            on_call_shuttle_logs[i]['driver_name'] = driver_name[0]['firstName'] + ' ' + driver_name[0]['lastName']
            on_call_shuttle_logs[i]['log_date'] = on_call_shuttle_logs[i]['log_date'].strftime('%d-%b-%Y')
            completed_time = on_call_shuttle_logs[i]['completed_at']
            on_call_shuttle_logs[i]['completed_at'] = completed_time.strftime('%-I:%M %p | %-m/%-d/%y').lower()
            if on_call_shuttle_logs[i]['deleted'] == 'Y':
                deleted_logs[deleted_iter] = on_call_shuttle_logs[i]
                deleted_iter += 1
            else:
                completed_logs[completed_iter] = on_call_shuttle_logs[i]
                completed_iter += 1

        return shuttle_logs, break_logs, completed_logs, deleted_logs
