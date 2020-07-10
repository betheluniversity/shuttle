from shuttle.db.db_tables import shuttle_schedule_functions as schedule_db


class ScheduleController(object):
    def __init__(self):
        pass

    def grab_db_schedule(self):
        schedule = schedule_db.get_db_schedule()
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
