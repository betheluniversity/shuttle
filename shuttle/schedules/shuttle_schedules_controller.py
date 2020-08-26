# Local
from shuttle.db import db_functions as db


class ScheduleController(object):
    def __init__(self):
        pass

    def grab_db_schedule(self):
        try:
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
                    row.append(schedule[i]['departure_time'].strftime('%-I:%M %p'))
                if iterator == row_length:
                    schedule_list.append(row)
                    iterator = 0
                    row = []
            return schedule_list
        except:
            return ''
