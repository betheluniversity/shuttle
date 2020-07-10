from shuttle.db.db_functions import query


# Return the role of a passed in user
def get_roles_by_username(username):
    ret = []
    sql = "SELECT * FROM SHUTTLE_USERS WHERE USERNAME = '{0}'".format(username)
    results = query(sql, 'read')
    for key, columns in results.items():
        ret.append(columns['role'])
    return ret


# Returns every user in SHUTTLE_USERS
def get_users():
    sql = "SELECT * FROM SHUTTLE_USERS"
    results = query(sql, 'read')
    return results


# Deletes passed in user from SHUTTLE_USERS
def delete_user(username):
    try:
        sql = "DELETE FROM SHUTTLE_USERS WHERE USERNAME = '{0}'".format(username)
        results = query(sql, 'write')
        return 'success'
    except Exception as error:
        return 'error'


# Changes passed in user to passed in role in the database
def change_user_role(username, role):
    try:
        sql = "UPDATE SHUTTLE_USERS SET ROLE = '{0}' WHERE USERNAME = '{1}'".format(role, username)
        results = query(sql, 'write')
        return 'success'
    except Exception as error:
        return 'error'
