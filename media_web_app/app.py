from flask import Flask, request, jsonify, send_from_directory
from os import path
from database_interface import MediaDB
from sys import argv

#--- Database Path ---#

DB_PATH = path.join(path.dirname(__file__), 'database', 'db.db')
media_db = MediaDB(DB_PATH)


#--- ... ---#

ALLOWED_FILE_EXTENSIONS = {'', }


#--- Main Flask Functions ---#

app = Flask(__name__)

@app.route('/')
def get_main_page():
    return send_from_directory('static', 'index.html')

@app.get('/api/all')
def get_all_entries():
    return jsonify(media_db.get_recent_entries(100))

@app.post('/api/search')
def get_entries():
    search_data = request.get_json()['search']
    if search_data:
        entries = media_db.get_entries_general_matches(search_data)
    else:
        entries = media_db.get_recent_entries(100)
    return jsonify(entries)

@app.post('/api/new')
def create_media_entry():
    data = request.get_json()
    title = data.pop('title')
    data.pop('file-path')           # <<< this needs to be here until more code can handle the various file uploads
    new_entry_rowid = media_db.new_entry(title, data)
    return jsonify(media_db.get_entry_by_id(new_entry_rowid))

if __name__ == "__main__":
    # DB_DIRPATH = argv[1]
    app.run(debug=True)
