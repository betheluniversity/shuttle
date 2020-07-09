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
            if date != all_shuttle_logs[i]['log_date']:
                date = all_shuttle_logs[i]['log_date']
                date_list.append(date)
        date_list.sort(reverse=True)
        for i in range(len(date_list)):
            date_list[i] = date_list[i].strftime('%b-%d-%Y')
        return all_shuttle_logs, date_list

    def grab_selected_logs(self, date, sort):
        if sort:
            all_shuttle_logs = db.get_shuttle_logs_by_username(date)
        else:
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

    def grab_db_schedule(self):
        schedule = db.get_db_schedule()
        location = ''
        schedule_list = []
        location_list = []
        for i in range(len(schedule)):
            if schedule[i]['location'] != location:
                location_list = []
                schedule_list.append(location_list)
                location = schedule[i]['location']
                location_list.append(location)
            if schedule[i]['arrival_time'].strftime('%d-%b-%Y %I:%M %p') == '01-Aug-2000 01:00 PM':
                location_list.append('-')
            else:
                time = schedule[i]['arrival_time'].strftime('%I:%M').lstrip("0").replace(" 0", " ")
                location_list.append(time)
        return schedule_list
