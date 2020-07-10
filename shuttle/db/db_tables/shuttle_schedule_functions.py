import re

from shuttle.db.db_functions import query


# Commits schedule from google sheets to the database Assumes schedule in sheets has locations in the first column
# and times are in the format (00:00 / 0:00) or (-) if the location has no time in a column.
def commit_schedule(table, all_locations):
    try:
        all_locations = [i.upper() for i in all_locations]
        queries = []
        for i in range(len(table)):
            location = ''
            for j in range(len(table[i])):
                arrival_time = 0
                if table[i][j].upper() in all_locations:
                    location = table[i][j]
                elif table[i][j] == '-' or table[i][j] == 'DROP':
                    arrival_time = '01-AUG-00 01.00.00.000000000PM'
                elif re.search("^[\d]:[\d][\d]$", table[i][j]) or re.search("^[\d][\d]:[\d][\d]$", table[i][j]):
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
                    queries.append(sql)
        # Don't commit until finished in case it fails (memory inefficient but needed)
        sql = "DELETE FROM SHUTTLE_SCHEDULE"
        query(sql, 'write')
        for sql in queries:
            query(sql, 'write')
        return 'success'
    except:
        return 'Error'


# Returns a dictionary of the entire schedule sorted by the order each item was added
# (so top left to bottom right in sheets)
def get_db_schedule():
    sql = "SELECT LOCATION, ARRIVAL_TIME FROM SHUTTLE_SCHEDULE ORDER BY ID"
    results = query(sql, 'read')
    return results


# Returns every location found in the schedule
def get_db_locations():
    sql = "Select DISTINCT LOCATION from SHUTTLE_SCHEDULE"
    results = query(sql, 'read')
    return results
