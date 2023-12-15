from flask import Flask, request, jsonify, send_from_directory
from os import path, mkdir
import db_functions
from sys import argv

#--- Database Object ---#

class DB:
    dir = path.join(path.dirname(__file__), 'database')
    file = ''
    media = ''

    @classmethod
    def setup_database(cls, db_dir:str=dir):
        cls.file, cls.media = db_functions.setup_media_database(db_dir)


#--- ... ---#

ALLOWED_FILE_EXTENSIONS = {'', }


#--- Main Flask Functions ---#

app = Flask(__name__)

@app.route('/')
def get_main_page():
    return send_from_directory('static', 'index.html')

@app.get('/api/recent')
def get_recent_entries():
    return jsonify(db_functions.get_recent_entries(DB.file, ['title', 'type', 'description'], 100))

@app.post('/api/general-search')
def get_entries():
    """Get all entries whose 'title', 'description', or 'genre' column values contain the search pattern,
    in order by 'title' matches first, and the other column matches second. If no pattern is provided, 
    just return recent entries instead"""
    search_data = request.get_json()['search']
    if search_data:
        title_matches = db_functions.get_entries_matching_str_pattern(DB.file, ['title', 'type', 'description'], 'title', search_data)
        description_matches = db_functions.get_entries_matching_str_pattern(DB.file, ['title', 'type', 'description'], 'description', search_data)
        genre_matches = db_functions.get_entries_matching_str_pattern(DB.file, ['title', 'type', 'description'], 'genre', search_data)
        second_entries = description_matches + [row for row in genre_matches if row not in description_matches]
        second_entries.sort(key=lambda x: x['title'])
        entries = title_matches + [row for row in second_entries if row not in title_matches]    
    else:
        entries = db_functions.get_recent_entries(DB.file, ['title', 'type', 'description'], 100)
    return jsonify(entries)

# @app.post('/api/new')
# def create_media_entry():
#     data = request.get_json()

#     data.pop('file-path')           # <<< this needs to be here until more code can handle the various file uploads
#     new_entry_rowid = db_functions.new_entry(title, data)
#     return jsonify(db_functions.get_entry_by_id(new_entry_rowid))


#--- Starting Script ---#

if __name__ == "__main__":
    try:
        DB.setup_database(argv[1])
    except:
        DB.setup_database()
    app.run(debug=True)
