import os
import imghdr
from cs50 import SQL
from flask import Flask, abort, current_app, render_template, request, redirect, session
from flask_session import Session
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
app.config['UPLOAD_PATH'] = 'static/userImages'
db = SQL("sqlite:///userdata.db")

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
        if "code" not in session:
            session["code"] = "start"
            session["message"] = ""
            session["display_alert"] = "False"
        picture = db.execute("SELECT photoPath FROM basicdata WHERE code=:code", code=session["code"])
        return render_template("index.html", picture=picture, code=session["code"], display_alert=session["display_alert"], message=session["message"])
    else:
        session["message"] = ""
        session["display_alert"] = "False"
        image = request.files['imageFile']
        newCode = request.form.get("userCode")
        if image.filename != '' and newCode != '':
            file_ext = os.path.splitext(image.filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(image.stream):
                abort(400)
            num = db.execute("SELECT COUNT(*) FROM basicdata WHERE code='{}';".format(newCode))
            if num[0]['COUNT(*)'] == 1:
                session["message"] = "Sorry, that code is taken!"
                session["display_alert"] = "True"
                return redirect("/")
            image.save(os.path.join(app.config['UPLOAD_PATH'], image.filename))
            session["code"] = newCode
            photoPath = app.config['UPLOAD_PATH'] + "/" + image.filename
            db.execute("INSERT INTO basicdata (code, photoPath) VALUES (:code, :photoPath)", code=session["code"], photoPath=photoPath)
            return redirect("/")
        session["message"] = "Some fields are blank, try again!"
        session["display_alert"] = "True"
        return redirect("/")
        
