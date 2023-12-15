import sqlite3
from os import path, mkdir


#--------- Main Query Function ---------#

def execute_query(db_filepath:str, qry:str, params:tuple|list=(), commit:bool=False) -> list:
    """Opens a connection, executes the passed query code, and closes the connection.
    If `commit` is True, then it will also commit any transactiona (ex: a query with 'INSERT' statement)"""
    assert isinstance(qry, str), "the query provided must be a string"
    assert isinstance(params, (tuple, list)), "the query placeholder parameters must be a tuple or a list"

    def dict_factory(cursor:sqlite3.Cursor, row:tuple):                             # taken from python docs: https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}

    con = sqlite3.connect(db_filepath)                                              # open connection to the database file
    con.row_factory = dict_factory                                                  # set row factory to make all query results dicts (default is tuples)
    try:
        result = con.execute(qry, params).fetchall()                                # execute the query and get the results
        if commit:
            con.commit()
    finally:
        con.close()                                                                 # close the connection (this is in a try/finally so that the connection always gets closed)
    return result


#--------- Media Database Setup ---------#

def setup_media_database(db_dirpath:str):
    """Pass in a path for a directory to use for the entire database, and get back the paths 
    for the SQLite '.db' database file and a corresponding media directory (holds media files 
    refferenced by the database). If the directory has already been setup, then nothing will 
    be adjusted.
    
    This uses a pre-defined directory/file structure, and these items created within the supplied 
    directory path should not be changed. In particular, the `MEDIA_DIR`, `DB_FILE` variables which 
    this function returns, should be used for any of the functions below which accept a `db_filepath`
    argument."""
    if not path.isdir(db_dirpath):
        mkdir(db_dirpath)                                                           # if it doesn't exist yet, create the directory from the provided path
    CREATE_TABLE_QRY = path.join(path.dirname(__file__), "schema_setup.sql")        # the path for the file with the media table creation query code
    MEDIA_DIR = path.join(db_dirpath, "media")                                      # the path for media directory
    DB_FILE = path.join(db_dirpath, "entries.db")                                   # the path for the databse file
    if not path.isdir(MEDIA_DIR):
        mkdir(MEDIA_DIR)                                                            # create the media directory if it doesn't already exist
    if not path.isfile(DB_FILE):
        with open(DB_FILE, 'w'):                                                    # create the database file if it doesn't already exist
            pass
    with open(CREATE_TABLE_QRY, 'r') as sql_file:
        table_creation_query = sql_file.read()                                      # get the query code to create the table (only if it doesn't already exist) from the 'create_media_table.sql' file
    execute_query(DB_FILE, table_creation_query, commit=True)                       # execute the query
    # ensure that the existing media table has the same schema as defined in the `table_creation_query` code:
    test_table_creation_query = table_creation_query.replace("IF NOT EXISTS media ", "test_media")
    execute_query(DB_FILE, test_table_creation_query, commit=True)                  # create a new table with the same creation code, and make sure it's created
    qry = """
        SELECT sql FROM sqlite_schema
        WHERE name = ?
        LIMIT 1
    """
    existing_table_creation_schema = execute_query(DB_FILE, qry, ('media',))[0].get('sql')                              # get the exsiting internal media table creation sql code 
    intended_table_creation_schema = execute_query(DB_FILE, qry, ('test_media',))[0].get('sql')                         # then the internal test_media tbale creation code
    execute_query(DB_FILE, "DROP TABLE test_media", commit=True)                                                        # imediately delete the test_media table    
    intended_table_creation_schema = intended_table_creation_schema.replace('test_media', 'media ', 1)                  # must change 'test-media' to 'media'
    assert existing_table_creation_schema == intended_table_creation_schema, "existing media table has invalid schema"  # ensure that the existing and test media tables have the same creation schema code
    return MEDIA_DIR, DB_FILE


#--------- General Pre-Made Database Query Functions ---------#

#--- Support Functions ---#

def _get_media_table_columns(db_filepath:str):
    result = execute_query(db_filepath, "PRAGMA table_info(media);")
    return [column_info.get("name") for column_info in result] + ['rowid']          # 'rowid' needs to be added, as it's a hidden column but is still SELECTable and very useful in a query

def _check_column_names(db_filepath:str, columns:list):
    """Check that all elements in `columns` match exisiting column names"""
    for column_name in columns:
        assert column_name in _get_media_table_columns(db_filepath), f'"{column_name}" is not one of the names of the table columns'

def _check_column_type(db_filepath:str, column:str, col_types:tuple):
    """Return True if the datatype of 'column' is one of the datatypes in `col_types`"""
    _check_column_names(db_filepath, [column])
    qry = f"""
    SELECT type FROM pragma_table_info('media')
    WHERE name = ?;
    """
    column_datatype = execute_query(db_filepath, qry, (column,))
    column_datatype = column_datatype[0]['type']
    return column_datatype in col_types

#--- Create ---#

def new_entry(db_filepath:str, entry_data:dict) -> int:
    """Create a new media entry. The `entry_data` dict can be passed in
    specifying "media" table columns (keys) and corresponding values. 'title'
    is the only column which MUST be included; all others are optional.
    Returns the rowid of the created entry."""
    _check_column_names(db_filepath, entry_data.keys())                             # check that all keys of the `entry_data` correspond to exisiting column names
    columns = ', '.join(entry_data.keys())                                          # join `entry_data` keys into single string for query
    placeholders = '?, ' * len(entry_data.keys())                                   # generate enough placeholders to match the the number of key/values           
    placeholders = placeholders.removesuffix(', ')                                  # remove the last ', ' in string
    qry = f"""  
    INSERT INTO media ({columns})
    VALUES({placeholders});
    """
    execute_query(db_filepath, qry, tuple(entry_data.values()), commit=True)        # create the new entry
    qry = """
        SELECT rowid FROM media
        ORDER BY rowid DESC
        LIMIT 1;
    """
    id = execute_query(db_filepath, qry)
    id = id[0]['rowid']                                                             # extract rowid from dict value within list
    return id                                                                       # return the rowid of the entry just created

#--- Read ---#

def get_entries_by_ids(db_filepath:str, ids:list, columns:list):
    """Get all entries with the rowids in `ids` list arg, with 
    column data according to the column names in `columns` list arg"""
    _check_column_names(db_filepath, columns)                                       # check that all elements in `columns` match exisiting column names
    columns = ', '.join(columns)                                                    # join `columns` into single string for query
    qry = f"""
    SELECT {columns} FROM media
    WHERE rowid = ?"""
    for x in range(len(ids) - 1):
        qry += " OR rowid = ?"                                                      # adjust query to include code to for each id in `ids`
    qry += ";"
    return execute_query(db_filepath, qry, ids)                                     # execute query and return row/entries                              

def get_recent_entries(db_filepath:str, columns:list, limit:int=1000000):
    """Get `limit` number of most recent entries, with column 
    data according to the column names in `columns` list arg"""
    _check_column_names(db_filepath, columns)                                       # check that all elements in `columns` match exisiting column names
    columns = ', '.join(columns)                                                    # join `columns` into single string for query
    qry = f"""
    SELECT {columns} FROM media
    ORDER BY rowid DESC
    LIMIT ?;
    """
    return execute_query(db_filepath, qry, (limit, ))

def get_entries_matching_num_range(db_filepath:str, columns:list, column_to_match:str, low:int, high:int):
    """Get all entries whose `column_to_match` number value is between the `low` and `high` values, with column 
    data according to the column names in `columns` list arg. The column to match must use a number data type."""
    _check_column_names(db_filepath, columns)                                       # check that all elements in `columns` match exisiting column names
    # check that the column to match has a number-based datatype (and is an existing column name):
    assert _check_column_type(db_filepath, column_to_match, ("INT", "REAL")), f'the datatype of "{column_to_match}" is not a number type'
    # perform main query:
    columns = ', '.join(columns)                                                    # join `columns` into single string for query
    qry = f"""
    SELECT {columns} FROM media
    WHERE {column_to_match} BETWEEN ? and ?
    """
    return execute_query(db_filepath, qry, (low, high))

def get_entries_matching_str_pattern(db_filepath:str, columns:list, column_to_match:str, pattern:str):
    """Get all entries whose `column_to_match` value *generally* matches the string `pattern`, with column 
    data according to the column names in `columns` list arg. The column to match must use a string data type."""
    _check_column_names(db_filepath, columns)                                       # check that all elements in `columns` match exisiting column names
    # check that the column to match has a number-based datatype (and is an existing column name):
    assert _check_column_type(db_filepath, column_to_match, ("TEXT",)), f'the datatype of "{column_to_match}" is not string type'
    # perform main query:
    columns = ', '.join(columns)                                
    qry = f"""
    SELECT {columns} FROM media
    """
    # split the string by whitespace and creates an SQL 'LIKE' statement for each individual element:
    pattern_tokens = tuple('%'+token+'%' for token in pattern.split())
    for n in range(len(pattern_tokens)):
        if n == 0:
            qry += f" WHERE {column_to_match} LIKE ?"
        else:
            qry += f" OR {column_to_match} LIKE ?"
    qry += ';'
    return execute_query(db_filepath, qry, pattern_tokens)

#--- Update ---#

def set_entry(db_filepath:str, rowid:int, entry_data:dict):
    """Update the media entry at `rowid` arg. `entry_data` must be a dict with 
    keys corresponding to table columns and values to be applied to them."""
    row = execute_query(db_filepath, "SELECT title FROM media WHERE rowid = ?;", (rowid,))
    assert row, f'"{rowid}" rowid does not correspond to any row in the "media" table'      # make sure that a row at provided `rowid` exists
    _check_column_names(db_filepath, entry_data.keys())                             # check that all keys of the `entry_data` correspond to exisiting column names
    cols_vals = ""
    for col_name in entry_data.keys():                                              # create the code string (column names and the values to assign them) for the SET command
        cols_vals += f"{col_name} = ?, "
    cols_vals.removesuffix(', ')                                                    # remove ', ' from end of string
    qry = f"""
    UPDATE media
    SET {cols_vals}
    WHERE rowid = ?;
    """
    params = tuple(entry_data.values()) + (rowid,)                                  # get query paramteres (query palceholder values) from `entry_data` values and the `rowid`
    execute_query(db_filepath, qry, params, commit=True)

#--- Delete ---#

def delete_entry(db_filepath:str, rowid:int):
    assert isinstance(rowid, int), "`rowid` must be an int"
    qry = """
    DELETE FROM media
    WHERE rowid = ?;
    """
    execute_query(db_filepath, qry, (rowid,), commit=True)
