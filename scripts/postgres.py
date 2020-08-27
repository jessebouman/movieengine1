# -*- coding: utf-8 -*-
"""
Script with wrappers around PostgreSQL CRUD queries
"""
import psycopg2 as psy
import os

def INSERT(table, vals, conn=None):
    """
    Parameters
    ----------
    table : str
        The table to insert into
    vals : str, list
        The values to insert
    conn : psycopg2 Connection object
        The database connection
    """

    supplied_conn = True
    # CONNECT TO DATABASE
    if conn == None:
        supplied_conn = False
        conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()

    # ADD TO DATABASE
    if type(vals) == list:
        # If vals is a list, insert multiple rows (not a copy command, so beware of performance)
        for v in vals:
            sql = f'''INSERT INTO {table} VALUES ({v})'''
            print(sql)
            try:
                cur.execute(sql)
            except:
                # In case of error, skip the row and reestablish connection
                print('SQL INSERT ERROR')
                cur.close()
                conn.commit()
                conn.close()
                conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
                cur = conn.cursor()
                continue
    else: # Vals is not a list, so execute a single row insert
        try:
            sql = f'''INSERT INTO {table} VALUES ({vals})'''
            print(sql)
        except:
            print('SQL INSERT ERROR')
            conn.commit()
            cur.close()
            if not supplied_conn:
                conn.close()
            return

        cur.execute(sql)
        conn.commit()

    print('SQL INSERTED SUCCESSFULLY')

    conn.commit()
    cur.close()
    if not supplied_conn: # Close the connection unless one was provided outside the function
        conn.close()

    return

def UPDATE(table, where, cols, vals, conn=None, _print=True):
    '''
    Parameters
    ----------
    table : str
        The table to update
    where : str
        The logic to select the row(s) to update
    cols : str
        The columns to update
    vals : str, list
        The values to use in the update
    conn : psycopg2 Connection object
        The database connection
    _print : bool
        whether to print the query

    Raises
    ----------
    LookupError
        If an error occurrs during the update execution, throws an exception
    '''
    supplied_conn = True
    # CONNECT TO DATABASE
    if conn == None:
        supplied_conn = False
        conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()

    # BUILD QUERY
    if len(cols.split(', ')) > 1:
        sql = f'''UPDATE {table} SET ({cols}) = ({vals}) WHERE {where}'''
    else:
        sql = f'''UPDATE {table} SET {cols} = {vals} WHERE {where}'''

    if _print: print(sql)

    # PERFORM UPDATE AND COMMIT
    try:
        cur.execute(sql)
        conn.commit()
        if _print: print('SQL UPDATED SUCCESSFULLY')
    except:
        print('SQL UPDATE ERROR')
        if not supplied_conn:
            conn.close()
        raise LookupError

    cur.close()
    if not supplied_conn: # Close the connection unless one was provided outside the function
        conn.close()

    return

def DELETE(table, where, conn=None):
    '''
    Parameters
    ----------
    table : str
        The table to delete from
    where : str
        The logic to select the row(s) to delete
    conn : psycopg2 Connection object
        The database connection
    '''
    supplied_conn = True
    # CONNECT TO DATABASE
    if conn == None:
        supplied_conn = False
        conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()

    sql = f"""DELETE FROM {table} WHERE {where}"""
    print(sql)

    # PERFORM DELETION AND COMMIT
    try:
        cur.execute(sql)
        conn.commit()
        print('SQL DELETED SUCCESSFULLY')
    except:
        print('SQL DELETE ERROR')
        if not supplied_conn:
            conn.close()
        raise LookupError

    cur.close()
    if not supplied_conn: # Close the connection unless one was provided outside the function
        conn.close()

    return

def SELECT(table, where=None, cols='*', extra='', conn=None, _print=True):
    '''
    Parameters
    ----------
    table : str
        The table to select from
    where : str
        The logic to select the row(s)
    cols : str
        Which columns to select (defaut: all)
    extra : str
        Appends any extra logic to the query (i.e. ORDER BY)
    conn : psycopg2 Connection object
        The database connection
    _print : bool
        whether to print the query

    Returns
    ----------
    result : list, dict, None
        If a single row is returned by the query, returns a dict of {column: value}
        If multiple rows are returned by the query, returns a list of dicts: [{col1: x, col2: y}, {col1: a, col2: b}]
        None, if no rows were found by the query

    Raises
    ----------
    LookupError
        If an error occurrs during the select execution, throws an exception
    '''

    supplied_conn = True
    # CONNECT TO DATABASE
    if conn == None:
        supplied_conn = False
        conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()

    # BUILD QUERY
    if where:
        sql = f"SELECT {cols} FROM {table} WHERE {where} {extra}"
    else:
        sql = f"SELECT {cols} FROM {table} {extra}"

    if _print: print(sql)

    # EXECUTE QUERY
    try:
        cur.execute(sql)
    except:
        print('SQL SELECT ERROR')
        cur.close()
        conn.close()
        raise LookupError
        return

    rows = cur.fetchall()

    if not supplied_conn: # Close the connection unless one was provided outside the function
        conn.close()

    if rows == None: # Return None if no rows were found
        return None

    # FORMAT RESULT
    result = []

    # GET COLUMN NAMES
    if cols == '*':
        # If all columns were requested, get names from cursor object
        colnames = [desc[0] for desc in cur.description]
    else:
        # If specific columns were requested, get names from col param
        colnames = cols.split(', ')
    cur.close()

    # ASSEMBLE RESULT DICTIONARY
    for r in rows:
        tmp = dict.fromkeys(colnames) # Make a temp dictionary for the row
        index = 0
        # For each column, insert values into the corresponding dicitonary entry
        for c in tmp:
            tmp[c] = r[index]
            index += 1
        result.append(tmp) # Append temp dictionary to the result list

    if len(result) == 1: # If only one row is returned, return the isolated dictionary
        return result[0]

    if not result:
        # Unreachable code, but raise an error is ther result list is still somehow empty
        raise LookupError

    return result