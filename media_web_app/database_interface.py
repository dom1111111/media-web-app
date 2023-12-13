import sqlite3
from os import path


#--- Data for Media Table ---#

TABLE_NAME = "Media"

# represents each of the "Media" table's: column name, the SQL data type, and possible values (not present if *any* value is allowed)
TABLE_COLUMN_STRUCTURE = {
    'title':        ('TEXT',),
    'type':         ('TEXT', ('movie', 'show', 'video')), # , 'audio', 'music', 'book', 'text'
    'thumbnail':    ('TEXT',),
    'description':  ('TEXT',),
    'genre':        ('TEXT',),
    'released':     ('INTEGER',),
    'length':       ('INTEGER',),
    'path':         ('TEXT',), # ('TEXT', path.isfile # OR functio to check if a valid url/uri )
}


#--- Media Database Class ---#

class MediaDB:
    def __init__(self, sqlite_db_path:str):
        """connect to a sqlite database file (`.db` suffix) with a "Media" table following the structure defined in this class"""
        self._create_db_attributes(sqlite_db_path)                  # set up all database attributes for the class
        self._create_table()                                        # create a new "Media" table if not already created
        assert {'name': TABLE_NAME} in self.cur.execute("SELECT name FROM sqlite_master").fetchall()    # check that the "Media" table is present in the database

    def _create_db_attributes(self, db_path:str):
        """creates the class atributes for the sqlite3 connection, cursor, and the database files directory path"""
        assert path.isfile(db_path), f'"{db_path}" is not an existing file' # check that the filepath provided is an exisiting file
        self.db_file_dir = path.join(path.dirname(db_path), 'files')        # establish dir path for database files (and check that it exsists)
        assert path.isdir(self.db_file_dir), f'the directory of the database file provided must have a directory called "files"'
        self.con = sqlite3.connect(db_path, check_same_thread=False)        # connect to the database file
        def dict_factory(cursor:sqlite3.Cursor, row:tuple):         # taken from python docs: https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory
            fields = [column[0] for column in cursor.description]
            return {key: value for key, value in zip(fields, row)}
        self.con.row_factory = dict_factory                         # setup so that all query results come out as dicts (default is tuples)
        self.cur = self.con.cursor()                                # create a cursor to perform SQL queries

    def _create_table(self):
        """creates the table to hold all media data, but only if it doesn't already exist"""
        table_data = ', '.join(f"{name} {data[0]}" for name, data in TABLE_COLUMN_STRUCTURE.items())
        qry = f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ({table_data});"
        self.cur.execute(qry)
        self.con.commit()

    #--- Support Methods ---#

    def _get_string_split_pattern_match_query_code(self, column_names:tuple, pattern:str):
        """Splits the string by whitespace and creates an SQL 'LIKE' statement for each individual element.
        Still uses '?' placeholder, so will return the query code and the split values"""
        assert isinstance(column_names, tuple), "`column_names` must be a tuple!"
        pattern_tokens = tuple('%'+token+'%' for token in pattern.split())
        qry_code = f"WHERE {column_names[0]} LIKE ?"
        first = True
        for column in column_names:
            for x in range(len(pattern_tokens)):
                if first:
                    first = False
                    continue
                qry_code += f" OR {column} LIKE ?"
        return qry_code, pattern_tokens * len(column_names)

    #--- Main Accessible Methods ---#

    # Create #

    def new_entry(self, title:str, entry_data:dict={}):
        """Create a new media entry. A `title` is the only required arg, but an `entry_data` dict can be passed in
        specifying "Media" table columns (keys) and corresponding values for the entry"""
        qry = """
        INSERT INTO Media (title)
        VALUES(?);
        """
        self.cur.execute(qry, (title,))
        if entry_data:
            last_id = self.cur.lastrowid
            self.set_entry(last_id, entry_data)
        else:
            self.con.commit()
        return last_id                                              # return the rowid of the entry that was just created

    # Update #

    def set_entry(self, rowid:int, entry_data:dict):
        """Update the media entry at `rowid` arg. `entry_data` must be a dict whose 
        keys are columns in the table. The values will be updated to each of corresponding columns."""
        row = self.cur.execute("SELECT * FROM Media WHERE rowid = ?;", (rowid,)).fetchall()
        assert row, f'"{rowid}" rowid does not correspond to any row in the "Media" table'      # make sure that a row at provided `rowid` exists
        for field in entry_data.keys():
            column_data = TABLE_COLUMN_STRUCTURE.get(field)
            assert column_data, f'"{field}" is not a column within the database "Media" table'  # make sure that all of the entry data dict keys correspond to existing columns with the "Media" table
            if len(column_data) > 1:                                # check that each value for certain columns (with limited acceptable values) is valid
                assert entry_data.get(field) in column_data[1]
                # MAYBE ADD CODE TO HANDLE FUNCTION BASED VALUE CHECKS
        for column, value in entry_data.items():                    # update every single column which had a value provided for it:
            qry = f"""
            UPDATE Media
            SET {column} = ?
            WHERE rowid = ?;
            """
            self.cur.execute(qry, (value, rowid))
        self.con.commit()

    # Read #

    def get_entry_by_id(self, id:int):
        """Get entry with rowid matching `id`"""
        qry = """
        SELECT * FROM Media
        WHERE rowid = ?;
        """
        result = self.cur.execute(qry, (id,))
        return result.fetchall()   

    def get_recent_entries(self, n:int=None):
        """Get most recent `n` entries"""
        qry = """
        SELECT * FROM Media
        """
        if n:
            qry += """
            ORDER BY rowid DESC
            LIMIT ?;
            """
            result = self.cur.execute(qry, (n,))
        else:
            qry += ";"
            result = self.cur.execute(qry)
        return result.fetchall()
    
    def get_entries_matching_column_pattern(self, column:str, pattern:str):
        """Get all entries whose specified `column` matches the supplied `pattern`"""
        assert column in TABLE_COLUMN_STRUCTURE.keys(), f'"{column}" is not one of the names of the table columns'
        match_code, qry_params = self._get_string_split_pattern_match_query_code((column,), pattern)
        qry = "SELECT * FROM Media " + match_code
        print('\n\n', qry, '\n\n')
        print(qry_params)
        result = self.cur.execute(qry, qry_params)
        return result.fetchall()

    def get_entries_general_matches(self, pattern:str):
        """Get all entries whose 'title', 'description', or 'genre' column values contain the pattern,
        in order by 'title' matches first, and the other column matches second."""
        # first get all rows with 'title' containing one or more of the pattern tokens
        match_code, qry_params = self._get_string_split_pattern_match_query_code(('title', ), pattern)
        qry = "SELECT * FROM Media " + match_code + " ORDER BY title ASC"
        result1 = self.cur.execute(qry, qry_params).fetchall()
        # then get all rows with other columns containing one or more of the pattern tokens
        match_code, qry_params = self._get_string_split_pattern_match_query_code(('description', 'genre'), pattern)
        qry = "SELECT * FROM Media " + match_code + " ORDER BY title ASC"
        result2 = self.cur.execute(qry, qry_params).fetchall()
        # return the combination of both rows, with the duplicates removed from the second results
        return result1 + [row for row in result2 if row not in result1]

    # UNFINISHED
    # def get_entries_specific_matches(title:str, length_range:tuple(int), released_range:tuple(int)):
    #     pass

    def get_entry_filepath(self, rowid:int):
        qry = """
        SELECT path FROM Media
        WHERE rowid = ?;
        """
        result = self.cur.execute(qry, (rowid, ))
        assert result.fetchall(), f'"{rowid}" rowid does not correspond to any row in the "Media" table'
        return result.fetchone()[0]

    # Delete #

    def delete_entry(self, rowid:int):
        assert isinstance(rowid, int), "`rowid` must be an int"
        qry = """
        DELETE FROM Media
        WHERE rowid = ?;
        """
        self.cur.execute(qry, (rowid, ))
        self.con.commit()
