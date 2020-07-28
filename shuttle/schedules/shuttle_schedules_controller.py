# Local
from shuttle.db import db_functions as db


class ScheduleController(object):
    def __init__(self):
        pass

    def grab_dates(self, log_type):
        date_list = []
        if log_type == 'Scheduled Shuttle Logs':
            # Grabs every date for scheduled logs
            shuttle_logs = db.get_scheduled_shuttle_logs()
        else:
            # Grabs every date for on call logs
            shuttle_logs = db.get_on_call_shuttle_logs()
        for i in range(len(shuttle_logs)):
            if shuttle_logs[i]['log_date'] not in date_list:
                date_list.append(shuttle_logs[i]['log_date'])
        # Sorts dates and makes them more readable
        date_list.sort(reverse=True)
        for i in range(len(date_list)):
            date_list[i] = date_list[i].strftime('%b-%d-%Y')
        return date_list

    def grab_selected_logs(self, date, name_sort):
        if name_sort == 'Sort By Name':
            all_shuttle_logs = db.get_scheduled_shuttle_logs_by_username(date)
        else:
            all_shuttle_logs = db.get_scheduled_shuttle_logs_by_date(date)
        shuttle_logs = {}
        break_logs = {}
        shuttle_iter = 0
        break_iter = 0
        # Adds in the user's real name to the logs, changes times/dates to be more readable,
        # and separates logs into shuttle logs and break logs
        for i in range(len(all_shuttle_logs)):
            real_name = db.username_search(all_shuttle_logs[i]['username'])
            all_shuttle_logs[i]['name'] = real_name[0]['firstName'] + ' ' + real_name[0]['lastName']
            all_shuttle_logs[i]['log_date'] = all_shuttle_logs[i]['log_date'].strftime('%b-%d-%Y')
            if all_shuttle_logs[i]['arrival_time']:
                all_shuttle_logs[i]['arrival_time'] = all_shuttle_logs[i]['arrival_time'].strftime('%I:%M %p %b-%d-%Y')\
                    .lstrip("0").replace(" 0", " ")
            elif all_shuttle_logs[i]['departure_time']:
                all_shuttle_logs[i]['departure_time'] = all_shuttle_logs[i]['departure_time'].strftime('%I:%M %p %b-%d-%Y')\
                    .lstrip("0").replace(" 0", " ")
            if all_shuttle_logs[i]['location']:
                shuttle_logs[shuttle_iter] = all_shuttle_logs[i]
                shuttle_iter += 1
            else:
                break_logs[break_iter] = all_shuttle_logs[i]
                break_iter += 1
        return shuttle_logs, break_logs

    def grab_selected_on_call_logs(self, date, name_sort):
        if name_sort == 'Sort By Name':
            all_shuttle_logs = db.get_on_call_logs_by_username(date)
        else:
            all_shuttle_logs = db.get_on_call_shuttle_logs_by_date(date)
        completed_logs = {}
        deleted_logs = {}
        completed_iter = 0
        deleted_iter = 0
        # Adds in the user's real name to the logs, changes times/dates to be more readable,
        # and separates logs into completed logs and deleted logs
        for i in range(len(all_shuttle_logs)):
            user_name = db.username_search(all_shuttle_logs[i]['username'])
            all_shuttle_logs[i]['user_name'] = user_name[0]['firstName'] + ' ' + user_name[0]['lastName']
            driver_name = db.username_search(all_shuttle_logs[i]['completed_by'])
            all_shuttle_logs[i]['driver_name'] = driver_name[0]['firstName'] + ' ' + driver_name[0]['lastName']
            all_shuttle_logs[i]['log_date'] = all_shuttle_logs[i]['log_date'].strftime('%b-%d-%Y')
            all_shuttle_logs[i]['completed_at'] = all_shuttle_logs[i]['completed_at'].\
                strftime('%I:%M %p %b-%d-%Y').lstrip("0").replace(" 0", " ")
            if all_shuttle_logs[i]['deleted'] == 'Y':
                deleted_logs[deleted_iter] = all_shuttle_logs[i]
                deleted_iter += 1
            else:
                completed_logs[completed_iter] = all_shuttle_logs[i]
                completed_iter += 1
        return completed_logs, deleted_logs

    def grab_db_schedule(self):
        schedule = db.get_db_schedule()
        locations = db.get_campus_locations()
        schedule_list = []
        row = []
        iterator = 0
        for location in locations:
            row.append(locations[location]['location'])
        schedule_list.append(row)
        row_length = len(row)
        row = []
        for i in range(len(schedule)):
            iterator += 1
            if schedule[i]['departure_time'] is None:
                row.append('-')
            else:
                row.append(schedule[i]['departure_time'].strftime('%I:%M').lstrip("0").replace(" 0", " "))
            if iterator == row_length:
                schedule_list.append(row)
                iterator = 0
                row = []
        return schedule_list
