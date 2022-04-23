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
db = SQL("sqlite:///chromeExt.db")

# image validation, function taken from https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

# returns the number of images uploaded for the group
# add milestones later
def findPhotoNum(groupCode):
    path = db.execute('SELECT photoPATH FROM groupdata WHERE code=:code;', code=groupCode)
    mainName = os.path.splitext(path[0]['photoPath'])[0]
    num = mainName[len(mainName)-1]
    return int(num)

# checks if the value already exists
def valueExists(table, key, value):
    num = db.execute("SELECT COUNT(*) FROM {} WHERE {}='{}';".format(table, key, value))
    if num[0]['COUNT(*)'] == 1:
        return True
    return False

def validateNewInfo(code, pin):
    if len(pin) == 4 and pin.isnumeric():
        if len(code) == 5 and code.isalpha():
            return True
    return False

def badUser(user):
    if user != None and user != '':
        if user.isalnum():
            return False
    return True


# display the main page
@app.route('/')
def start_page():
    if "display_alert" not in session:
        session["message"] = ""
        session["display_alert"] = "False"
    if "code" not in session:
        return render_template("start.html", display_alert=session["display_alert"], message=session["message"])
    return redirect("/home")

@app.route('/newuser', methods=["POST"])
def newUser():
    session["message"] = ""
    session["display_alert"] = "False"
    newUser = request.form.get("newUsername")
    if badUser(newUser):
        session["message"] = "Sorry that username is not valid"
        session["display_alert"] = "True"
        return redirect("/")
    if valueExists("userData", "username", newUser):
        session["message"] = "Sorry that username is taken!"
        session["display_alert"] = "True"
        return redirect("/")
    session["user"] = newUser
    session["code"] = "start"
    db.execute("INSERT INTO userdata (username, curr_code) VALUES (:user, :code);", user=session["user"], code="start")
    return redirect("/home")

@app.route('/home')
def main_page():
    picture = db.execute("SELECT photoPath FROM groupdata WHERE code=:code;", code=session["code"])
    return render_template("index.html", picture=picture, code=session["code"], display_alert=session["display_alert"], message=session["message"])

# registering new code       
@app.route('/register', methods=["POST"])
def register():
    session["message"] = ""
    session["display_alert"] = "False"

    image = request.files['firstImage']
    newCode = request.form.get("newCode")
    if image.filename != '' and newCode != '':
        if " " in str(image.filename) or " " in newCode:
            session["message"] = "Spaces are not allowed in code or file names!"
            session["display_alert"] = "True"
            return redirect("/home")
        file_ext = os.path.splitext(image.filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(image.stream):
            session["message"] = "Sorry, invalid file!"
            session["display_alert"] = "True"
            return redirect("/home")
        if valueExists("groupdata", "code", newCode):
            session["message"] = "Sorry, that code is taken!"
            session["display_alert"] = "True"
            return redirect("/home")
        session["code"] = newCode
        filename = newCode + "_1" + file_ext
        photoPath = os.path.join(app.config['UPLOAD_PATH'], filename)
        image.save(photoPath)
        db.execute("INSERT INTO groupdata (code, photoPath) VALUES (:code, :photoPath);", code=session["code"], photoPath=photoPath)
        return redirect("/home")
    session["message"] = "Some fields are blank, try again!"
    session["display_alert"] = "True"
    return redirect("/home")

# connecting to existing
@app.route('/existing', methods=["POST"])
def existing():
    session["message"] = ""
    session["display_alert"] = "False"
    joinCode = request.form.get("existingCode")
    if joinCode != '':
        if valueExists("groupdata", "code", joinCode):
            session["code"] = joinCode
            return redirect("/home")
        session["message"] = "Code does not exist, please register it!"
        session["display_alert"] = "True"
        return redirect("/home")
    session["message"] = "Field is blank, try again!"
    session["display_alert"] = "True"
    return redirect("/home")

# Add new pictures to your group (also later images)
@app.route('/upload', methods=["POST"])
def upload():
    session["message"] = ""
    session["display_alert"] = "False"
    image = request.files['shareImage']
    if image.filename != '':
        if session["code"] == "start":
            session["message"] = "You are not on a group code, try again!"
            session["display_alert"] = "True"
            return redirect("/home")
        file_ext = os.path.splitext(image.filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(image.stream):
            session["message"] = "Sorry, invalid file!"
            session["display_alert"] = "True"
            return redirect("/home")
        num = findPhotoNum(session["code"]) + 1
        filename = session["code"] + "_" + str(num) + file_ext
        photoPath = os.path.join(app.config['UPLOAD_PATH'], filename)
        image.save(photoPath)
        db.execute("UPDATE groupdata SET photoPath = :photoPath WHERE code = :code;", photoPath=photoPath, code=session["code"])
        os.remove(app.config['UPLOAD_PATH'] + "/" + session["code"] + "_" + str(num-1) + file_ext)
        return redirect("/home")
    session["message"] = "No file uploaded, try again!"
    session["display_alert"] = "True"
    return redirect("/home")

@app.before_request
def make_session_permanent():
    session.permanent = True