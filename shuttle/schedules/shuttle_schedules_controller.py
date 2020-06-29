from shuttle.db import db_functions as db


class ScheduleController(object):
    def __init__(self):
        pass

    def grab_logs(self):
        all_shuttle_logs = db.get_shuttle_logs()
        date = 0
        date_list = []
        # finds every different date and changes that date to be more readable
        for i in range(len(all_shuttle_logs)):
            all_shuttle_logs[i]['log_date'] = all_shuttle_logs[i]['log_date'].strftime('%b-%d-%Y')
            if date != all_shuttle_logs[i]['log_date']:
                date = all_shuttle_logs[i]['log_date']
                date_list.append(date)
        return all_shuttle_logs, date_list

    def grab_selected_logs(self, date):
        all_shuttle_logs = db.get_shuttle_logs_by_date(date)
        shuttle_logs = {}
        break_logs = {}
        shuttle_iter = 0
        break_iter = 0
        # Adds in the user's real name to the logs, changes times/dates to be more readable,
        # and seperates logs into shuttle logs and break logs
        for i in range(len(all_shuttle_logs)):
            real_name = db.username_search(all_shuttle_logs[i]['username'])
            all_shuttle_logs[i]['name'] = real_name[0]['firstName'] + ' ' + real_name[0]['lastName']
            all_shuttle_logs[i]['log_date'] = all_shuttle_logs[i]['log_date'].strftime('%b-%d-%Y')
            if all_shuttle_logs[i]['arrival_time']:
                all_shuttle_logs[i]['arrival_time'] = all_shuttle_logs[i]['arrival_time'].strftime('%I:%M %p %b-%d-%Y')
            elif all_shuttle_logs[i]['departure_time']:
                all_shuttle_logs[i]['departure_time'] = all_shuttle_logs[i]['departure_time'].strftime('%I:%M %p %b-%d-%Y')
            if all_shuttle_logs[i]['location']:
                shuttle_logs[shuttle_iter] = all_shuttle_logs[i]
                shuttle_iter += 1
            else:
                break_logs[break_iter] = all_shuttle_logs[i]
                break_iter += 1
        return shuttle_logs, break_logs
