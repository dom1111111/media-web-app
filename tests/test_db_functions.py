"""
Test out the functions for setting up and using the media database.

This module can be run from terminal while the current directory is 
the top level project directory, using the following methods:

    - Use the Pytest framework: `pytest ./tests/test_db_functions.py`

    - Use just plain python: `python -m tests.test_db_functions`

Can also get print output for certain test function, as long as 
`PRINT_OUTPUT` is set to True. (this won't do anything if using pytest)
"""

from os import path, remove, rmdir, mkdir
from media_web_app import db_functions


TEST_DB_DIR = path.join(path.dirname(__file__), 'test_db_dir')

PRINT_OUTPUT = True                                                         # set this to True to have test functions print out return values and other values related to the things they're testing

def optional_print(*args):
    if PRINT_OUTPUT:
        print(*args)

def cleanup_testing_files_dirs(test_db_dir:str, media_dir:str='', db_file:str=''):
    """used to cleanup the files/dirs created from 
    `db_functions.setup_media_database` at the end of tests"""
    if path.isdir(media_dir):
        rmdir(media_dir)
    if path.isfile(db_file):
        remove(db_file)
    if path.isdir(test_db_dir):
        rmdir(test_db_dir)


#--- Sample DB Entry Data ---#

TEST_ENTRIES = [
    {
        'title':        "The Big Event",
        'type':         "movie",
        'description':  "Bad thing happen. Will protagonist save the day, or will evil prevail?!",
        'genre':        "Romantic Comedy",
        'released':     2054,
        'length':       108
    },
    {
        'title':        "Companions",
        'type':         "show",
        'description':  "4 close people get into to all sorts of adventures ... together.",
        'genre':        "Historical Sci-Fi Drama",
        'released':     1992
    },
    {
        'title':        "A Pothos Named Peter",
        'type':         "movie",
        'description':  "Peter is just your everyday house plant, with dreams of going to the big city. Unbeknownst to them, they're about to get more than they bargained for! Follow the true story of Peter, and learn how to fall in love all over again, for the first time.",
        'genre':        "Documentary",
        'released':     2109,
        'length':       73
    }
]


#--------- Test Functions ---------#

def test_execute_query():
    if not path.isdir(TEST_DB_DIR):
        mkdir(TEST_DB_DIR)
    TEST_DB_FILE = path.join(TEST_DB_DIR, 'test1.db')
    with open(TEST_DB_FILE, 'w'):                                           # create the test databse file
        pass
    try:
        # create a table:
        q1 = """
            CREATE TABLE IF NOT EXISTS test_table (
                title TEXT NOT NULL,
                content TEXT,
                date INT
            );
        """
        db_functions.execute_query(TEST_DB_FILE, q1, commit=True)
        # check table schema
        q2 = "PRAGMA table_info(test_table)"
        r2 = db_functions.execute_query(TEST_DB_FILE, q2)
        for x in r2:
            x.pop('cid')
        r2.sort(key=lambda x: x['name'])                                    # remove 'cid' and sort the result so that there's no ambiguity
        for col in r2:
            optional_print(col)
        expected_r2 = [
            {'name': 'content', 'type': 'TEXT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
            {'name': 'date', 'type': 'INT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
            {'name': 'title', 'type': 'TEXT', 'notnull': 1, 'dflt_value': None, 'pk': 0}
        ]
        assert r2 == expected_r2
        # create some table rows and check those:
        q3 = """
            INSERT INTO test_table (title, content, date)
            VALUES (?, ?, ?)
        """
        db_functions.execute_query(TEST_DB_FILE, q3, ('Something', 'A thing that exists', 20231111))
        r3 = db_functions.execute_query(TEST_DB_FILE, "SELECT * FROM test_table")
        optional_print(r3)
        assert not r3                                                       # result of a general SELECT query should be empty, because `commit` arg was not True
        db_functions.execute_query(TEST_DB_FILE, q3, ('Something', 'A thing that exists', 20231111), commit=True)
        r3a = db_functions.execute_query(TEST_DB_FILE, "SELECT * FROM test_table")
        optional_print(r3a)
        assert r3a                                                          # now the general SELECT query should have this first entry           
    finally:
        cleanup_testing_files_dirs(TEST_DB_DIR, db_file=TEST_DB_FILE)       # delete the created directory and file once done test (regardless of pass or fail)


def test_db_setup():
    try:
        MEDIA_DIR, DB_FILE = db_functions.setup_media_database(TEST_DB_DIR)
        optional_print(MEDIA_DIR)
        optional_print(DB_FILE)
        # check that the correct paths are returned:
        assert MEDIA_DIR == path.join(TEST_DB_DIR, 'media')
        assert DB_FILE == path.join(TEST_DB_DIR, 'entries.db')
        # check that the 'media' table has the correct structure (is done by the setup function itself also)
        q1 = "PRAGMA table_info(media)"
        r1 = db_functions.execute_query(DB_FILE, q1)
        for x in r1:
            x.pop('cid')
        r1.sort(key=lambda x: x['name'])                                    # remove 'cid' and sort the result so that there's no ambiguity
        for col in r1:
            optional_print(col)
        expected_r1 = [
            {'name': 'description', 'type': 'TEXT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
            {'name': 'genre', 'type': 'TEXT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
            {'name': 'length', 'type': 'INT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
            {'name': 'path', 'type': 'TEXT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
            {'name': 'released', 'type': 'INT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
            {'name': 'thumbnail', 'type': 'TEXT', 'notnull': 0, 'dflt_value': None, 'pk': 0},
            {'name': 'title', 'type': 'TEXT', 'notnull': 1, 'dflt_value': None, 'pk': 0},
            {'name': 'type', 'type': 'TEXT', 'notnull': 0, 'dflt_value': None, 'pk': 0}
        ]
        assert r1 == expected_r1
        # check that 'media' is the only thing in the database schema:
        q2 = "SELECT name FROM sqlite_schema"
        r1 = db_functions.execute_query(DB_FILE, q2)
        optional_print(r1)
        assert len(r1) == 1 and r1[0].get('name') == 'media'
    # delete the created directories and file once done test:
    finally:
        cleanup_testing_files_dirs(TEST_DB_DIR, MEDIA_DIR, DB_FILE)


def test_support_functions():
    MEDIA_DIR, DB_FILE = db_functions.setup_media_database(TEST_DB_DIR)
    try:
        column_names = ['description', 'genre', 'length', 'path', 'released', 'rowid', 'thumbnail', 'title', 'type']
        # 1) test get-media-table-columns function
        media_table_columns = db_functions._get_media_table_columns(DB_FILE)
        optional_print(media_table_columns)
        assert sorted(media_table_columns) == column_names
        # 2) test function which checks if the supplied column names exist
        db_functions._check_column_names(DB_FILE, column_names)             # this function has its own assert, so none is needed right here
        try:
            db_functions._check_column_names(DB_FILE, column_names + ['author'])
            result1 = True
        except:
            result1 = False
        assert not result1                                                  # make sure that the function's assert fails when passing in a string which *doesn't* match to any column name
        # 3) test the column type checking function
        result2 = db_functions._check_column_type(DB_FILE, 'description', ('TEXT',))
        result3 = db_functions._check_column_type(DB_FILE, 'path', ('INT',))
        optional_print(result2, result3)
        assert result2 and not result3                                      # ensure it returns True when the type is correct, and False when the type in incorrect
    finally:
        cleanup_testing_files_dirs(TEST_DB_DIR, MEDIA_DIR, DB_FILE)         # delete the created directories and file once done test (regardless of pass or fail)


def test_create_entry():
    MEDIA_DIR, DB_FILE = db_functions.setup_media_database(TEST_DB_DIR)
    try:
        rowid = db_functions.new_entry(DB_FILE, TEST_ENTRIES[0])
        optional_print(rowid)
        assert rowid == 1                                                   # this is the first entry, so the rowid should be 1
        qry = f"""
            SELECT * FROM media
            WHERE rowid = ?;
        """
        result = db_functions.execute_query(DB_FILE, qry, (rowid,))[0]      # get the entry just created by rowid (result is always a list of dicts, so take the first list element)
        optional_print(result)
        expected_result = {
            'title':        "The Big Event",
            'type':         "movie",
            'thumbnail':    None,
            'description':  "Bad thing happen. Will protagonist save the day, or will evil prevail?!",
            'genre':        "Romantic Comedy",
            'released':     2054,
            'length':       108,
            'path':         None
        }
        assert result == expected_result
    finally:
        cleanup_testing_files_dirs(TEST_DB_DIR, MEDIA_DIR, DB_FILE)


def test_get_entry_by_id():
    MEDIA_DIR, DB_FILE = db_functions.setup_media_database(TEST_DB_DIR)
    rowids = [db_functions.new_entry(DB_FILE, entry) for entry in TEST_ENTRIES]         # create 3 new entries and get their rowids
    try:
        optional_print(rowids)
        result = db_functions.get_entries_by_ids(DB_FILE, rowids, ('title', 'type'))    # now try to get back the 'title' and 'type' of each entry, using their id
        optional_print(result)
        expected_result = [{'title': "The Big Event", 'type': "movie"}, {'title': "Companions", 'type': "show"}, {'title': "A Pothos Named Peter", 'type': "movie"}]
        assert result == expected_result
    finally:
        cleanup_testing_files_dirs(TEST_DB_DIR, MEDIA_DIR, DB_FILE)


def test_get_recent_entries():
    MEDIA_DIR, DB_FILE = db_functions.setup_media_database(TEST_DB_DIR)
    for entry in TEST_ENTRIES:
        db_functions.new_entry(DB_FILE, entry)                              # create 3 new entries
    try:
        result = db_functions.get_recent_entries(DB_FILE, ('rowid', 'title', 'type'), limit=2)   # now try to get back the 'rowid', 'title' and 'type' of the most recent 2 entries
        optional_print(result)
        expected_result = [{'rowid': 3, 'title': "A Pothos Named Peter", 'type': "movie"}, {'rowid': 2, 'title': "Companions", 'type': "show"}]
        assert result == expected_result
    finally:
        cleanup_testing_files_dirs(TEST_DB_DIR, MEDIA_DIR, DB_FILE)


def test_get_entries_matching_num_range():
    MEDIA_DIR, DB_FILE = db_functions.setup_media_database(TEST_DB_DIR)
    for entry in TEST_ENTRIES:
        db_functions.new_entry(DB_FILE, entry)                              # create 3 new entries
    try:
        # first test that that the function catches that 'genre' is not a number type, and fails:
        try:
            r1 = db_functions.get_entries_matching_num_range(DB_FILE, ('title', 'released'), 'genre', 1975, 2075)
        except:
            r1 = None
        assert not r1
        # now test that the function returns the expected entries, being matched by 'released':
        result = db_functions.get_entries_matching_num_range(DB_FILE, ('title', 'released'), 'released', 1975, 2075)
        optional_print(result)
        expected_result = [{'title': "The Big Event", 'released': 2054}, {'title': "Companions", 'released': 1992}]
        assert result == expected_result
    finally:
        cleanup_testing_files_dirs(TEST_DB_DIR, MEDIA_DIR, DB_FILE)


def test_get_entries_matching_str_pattern():
    MEDIA_DIR, DB_FILE = db_functions.setup_media_database(TEST_DB_DIR)
    for entry in TEST_ENTRIES:
        db_functions.new_entry(DB_FILE, entry)                              # create 3 new entries
    try:
        # try to find all entries which have the word 'of' in their description
        r1 = db_functions.get_entries_matching_str_pattern(DB_FILE, ('title',), 'description', "of")
        optional_print(r1)
        r1.sort(key=lambda x: x['title'])                                           # sort the results so that order isn't a factor
        expected_r1 = [{'title': "A Pothos Named Peter"}, {'title': "Companions"}]  # only the entries with these titles have " of " in their description, so this is the only result that should show up
        assert r1 == expected_r1
        # try to find all entries which have the word any of the words in "evil close thing" within their description 
        # (the function should split the string by whitespace, and try to match any of the resulting tokens)
        r2 = db_functions.get_entries_matching_str_pattern(DB_FILE, ('title',), 'description', "evil close thing")
        optional_print(r2)
        r2.sort(key=lambda x: x['title'])
        expected_r2 = [{'title': "Companions"}, {'title': "The Big Event"}, ]       # only the entries with these titles have "evil", "close", or "thing" in their description, so this is the only result that should show up
        assert r2 == expected_r2
    finally:
        cleanup_testing_files_dirs(TEST_DB_DIR, MEDIA_DIR, DB_FILE)



#--------- Main Script (if pytest isn't used) ---------#

if __name__ == "__main__":
    print()
    test_execute_query()
    test_db_setup()
    test_support_functions()
    test_create_entry()
    test_get_entry_by_id()
    test_get_recent_entries()
    test_get_entries_matching_num_range()
    test_get_entries_matching_str_pattern()
