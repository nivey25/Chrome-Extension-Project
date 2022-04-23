import os
import imghdr
from cs50 import SQL
from flask import Flask, current_app, render_template, request, redirect, session
from flask_session import Session
# denotes this as a flask app
app = Flask(__name__)
# session variables
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# necessary for image upload safety
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']

app.config['UPLOAD_PATH'] = 'static/userImages/'
# connect to database
db = SQL("sqlite:///userdata.db")

# image validation, function taken from https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

def findPhotos(groupCode):
    path = db.execute('SELECT photoPATH FROM basicdata WHERE code=:code;', code=groupCode)
    mainName = os.path.splitext(path[0]['photoPath'])[0]
    num = mainName[len(mainName)-1]
    return int(num)

def codeExists(code):
    num = db.execute("SELECT COUNT(*) FROM basicdata WHERE code='{}';".format(code))
    if num[0]['COUNT(*)'] == 1:
        return True
    return False

# display the main page
@app.route('/')
def main_page():
    if "code" not in session:
        session["code"] = "start"
        session["message"] = ""
        session["display_alert"] = "False"
    picture = db.execute("SELECT photoPath FROM basicdata WHERE code=:code;", code=session["code"])
    return render_template("index.html", picture=picture, code=session["code"], display_alert=session["display_alert"], message=session["message"])

# registering new code       
@app.route('/register', methods=["POST"])
def register():
    session["message"] = ""
    session["display_alert"] = "False"
    image = request.files['imageFile']
    newCode = request.form.get("userCode")
    if image.filename != '' and newCode != '':
        if " " in str(image.filename) or " " in newCode:
            session["message"] = "Spaces are not allowed in code or file names!"
            session["display_alert"] = "True"
            return redirect("/")
        file_ext = os.path.splitext(image.filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(image.stream):
            session["message"] = "Sorry, invalid file!"
            session["display_alert"] = "True"
            return redirect("/")
        if codeExists(newCode):
            session["message"] = "Sorry, that code is taken!"
            session["display_alert"] = "True"
            return redirect("/")
        session["code"] = newCode
        filename = newCode + "_1" + file_ext
        photoPath = os.path.join(app.config['UPLOAD_PATH'], filename)
        image.save(photoPath)
        db.execute("INSERT INTO basicdata (code, photoPath) VALUES (:code, :photoPath);", code=session["code"], photoPath=photoPath)
        return redirect("/")
    session["message"] = "Some fields are blank, try again!"
    session["display_alert"] = "True"
    return redirect("/")

# connecting to existing
@app.route('/existing', methods=["POST"])
def existing():
    session["message"] = ""
    session["display_alert"] = "False"
    joinCode = request.form.get("existingCode")
    if joinCode != '':
        if codeExists(joinCode):
            session["code"] = joinCode
            return redirect("/")
        session["message"] = "Code does not exist, please register it!"
        session["display_alert"] = "True"
        return redirect("/")
    session["message"] = "Field is blank, try again!"
    session["display_alert"] = "True"
    return redirect("/")

# Add new pictures to your group (also later images)
@app.route('/upload', methods=["POST"])
def upload():
    session["message"] = ""
    session["display_alert"] = "False"
    image = request.files['shareFile']
    if image.filename != '':
        if session["code"] == "start":
            session["message"] = "You are not on a group code, try again!"
            session["display_alert"] = "True"
            return redirect("/")
        file_ext = os.path.splitext(image.filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(image.stream):
            session["message"] = "Sorry, invalid file!"
            session["display_alert"] = "True"
            return redirect("/")
        num = findPhotos(session["code"]) + 1
        filename = session["code"] + "_" + str(num) + file_ext
        photoPath = os.path.join(app.config['UPLOAD_PATH'], filename)
        image.save(photoPath)
        db.execute("UPDATE basicdata SET photoPath = :photoPath WHERE code = :code;", photoPath=photoPath, code=session["code"])
        os.remove(app.config['UPLOAD_PATH'] + "/" + session["code"] + "_" + str(num-1) + file_ext)
        return redirect("/")
    session["message"] = "No file uploaded, try again!"
    session["display_alert"] = "True"
    return redirect("/")

@app.before_request
def make_session_permanent():
    session.permanent = True