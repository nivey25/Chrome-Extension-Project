import os
import imghdr
from cs50 import SQL
from flask import Flask, abort, current_app, render_template, request, redirect
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
app.config['UPLOAD_PATH'] = 'static/userImages'
db = SQL("sqlite:///userdata.db")

code = "start"

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

@app.route('/', methods=["GET", "POST"])
def hello_world():
    if request.method == "GET":
        picture = db.execute("SELECT photoPath FROM basicdata WHERE code=:code", code=code)
        return render_template("index.html", picture=picture)
    else:
        image = request.files['imageFile']
        if image.filename != '':
            file_ext = os.path.splitext(image.filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(image.stream):
                abort(400)
            image.save(os.path.join(app.config['UPLOAD_PATH'], image.filename))
            #code = "no"
            #photoPath = app.config['UPLOAD_PATH'] + "/" + image.filename
            #db.execute("INSERT INTO basicdata (code, photoPath) VALUES (:code, :photoPath)", code=code, photoPath=photoPath)
        return redirect("/")
        