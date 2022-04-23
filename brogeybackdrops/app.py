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
    path = db.execute('SELECT photoPATH FROM groupData WHERE code=:code;', code=groupCode)
    mainName = os.path.splitext(path[0]['photoPath'])[0]
    num = mainName[len(mainName)-1]
    return int(num)

# checks if the value already exists
def valueExists(table, key, value):
    num = db.execute("SELECT COUNT(*) FROM {} WHERE {}='{}';".format(table, key, value))
    if num[0]['COUNT(*)'] == 1:
        return True
    return False

def badInfo(code, pin):
    if len(pin) == 4 and pin.isnumeric():
        if len(code) == 5 and code.isalpha():
            return False
    return True

def badUser(user):
    if user != None and user != '':
        if user.isalnum() and len(user) > 5:
            return False
    return True

def pinMatch(code_v, pin):
    pin_v = db.execute("SELECT pin FROM groupData WHERE code=:code", code=code_v)
    if pin_v[0]['pin'] == pin:
        return True
    return False

def getCurrCode(username):
    code_v = db.execute("SELECT curr_code FROM userData WHERE username=:user", user=username)
    return code_v[0]['curr_code']


# display the main page
@app.route('/')
def start_page():
    if "display_alert" not in session:
        session["message"] = ""
        session["display_alert"] = "False"
    if "user" not in session:
        return render_template("start.html", display_alert=session["display_alert"], message=session["message"])
    return redirect("/home")

@app.route('/newuser', methods=["POST"])
def newUser():
    session["message"] = ""
    session["display_alert"] = "False"
    newUser = request.form.get("newUsername").lower()
    if badUser(newUser):
        session["message"] = "Sorry that username is not valid"
        session["display_alert"] = "True"
        return redirect("/")
    if valueExists("userData", "username", newUser):
        session["message"] = "Sorry that username is taken!"
        session["display_alert"] = "True"
        return redirect("/")
    session["user"] = newUser
    db.execute("INSERT INTO userData (username, curr_code) VALUES (:user, :code);", user=session["user"], code="start")
    return redirect("/home")

@app.route('/home')
def main_page():
    picture = db.execute("SELECT photoPath FROM groupData WHERE code=:code;", code=getCurrCode(session["user"]))
    return render_template("index.html", picture=picture, display_alert=session["display_alert"], message=session["message"])

# registering new code       
@app.route('/register', methods=["POST"])
def register():
    session["message"] = ""
    session["display_alert"] = "False"

    image = request.files['firstImage']
    newCode = request.form.get("newCode").lower()
    newPin = request.form.get("newPin").lower()
    caption = request.form.get("firstCap")
    if image.filename != '' and newCode != '' and newPin != '':
        if " " in str(image.filename):
            session["message"] = "Spaces are not allowed in file names!"
            session["display_alert"] = "True"
            return redirect("/home")
        file_ext = os.path.splitext(image.filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(image.stream):
            session["message"] = "Sorry, invalid file!"
            session["display_alert"] = "True"
            return redirect("/home")
        if badInfo(newCode, newPin):
            session["message"] = "Code or pin are invalid!"
            session["display_alert"] = "True"
            return redirect("/home")
        if valueExists("groupData", "code", newCode):
            session["message"] = "Sorry, that code is taken!"
            session["display_alert"] = "True"
            return redirect("/home")
        filename = newCode + "_1" + file_ext
        photoPath = os.path.join(app.config['UPLOAD_PATH'], filename)
        image.save(photoPath)
        db.execute("INSERT INTO groupData (code, photoPath, caption, pin) VALUES (:code, :photoPath, :caption, :pin);", code=newCode, photoPath=photoPath, caption=caption, pin=newPin)
        db.execute("UPDATE userData SET curr_code = :code WHERE username = :user;", code=newCode, user=session["user"])
        return redirect("/home")
    session["message"] = "Some fields are blank, try again!"
    session["display_alert"] = "True"
    return redirect("/home")

# connecting to existing
@app.route('/existing', methods=["POST"])
def existing():
    session["message"] = ""
    session["display_alert"] = "False"
    joinCode = request.form.get("existingCode").lower()
    joinPin = request.form.get("existingPin").lower()
    if joinCode != '' and joinPin != '':
        if valueExists("groupdata", "code", joinCode):
            if pinMatch(joinCode, joinPin):
                db.execute("UPDATE userData SET curr_code = :code WHERE username = :user;", code=joinCode, user=session["user"])
                return redirect("/home")
            session["message"] = "Sorry, that pin does not match the code!"
            session["display_alert"] = "True"
            return redirect("/home")
        session["message"] = "Code does not exist, please register it!"
        session["display_alert"] = "True"
        return redirect("/home")
    session["message"] = "Field is blank, try again!"
    session["display_alert"] = "True"
    return redirect("/home")

# Add new pictures to your group
@app.route('/upload', methods=["POST"])
def upload():
    session["message"] = ""
    session["display_alert"] = "False"
    image = request.files['shareImage']
    caption = request.form.get("shareCap")
    if image.filename != '':
        if getCurrCode(session["user"]) == "start":
            session["message"] = "You are not on a group code, try again!"
            session["display_alert"] = "True"
            return redirect("/home")
        file_ext = os.path.splitext(image.filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(image.stream):
            session["message"] = "Sorry, invalid file!"
            session["display_alert"] = "True"
            return redirect("/home")
        num = findPhotoNum(getCurrCode(session["user"])) + 1
        filename = getCurrCode(session["user"]) + "_" + str(num) + file_ext
        photoPath = os.path.join(app.config['UPLOAD_PATH'], filename)
        image.save(photoPath)
        db.execute("UPDATE groupData SET photoPath = :photoPath WHERE code = :code;", photoPath=photoPath, code=getCurrCode(session["user"]))
        db.execute("UPDATE groupData SET caption = :caption WHERE code = :code;", caption=caption, code=getCurrCode(session["user"]))
        os.remove(app.config['UPLOAD_PATH'] + "/" + getCurrCode(session["user"]) + "_" + str(num-1) + file_ext)
        return redirect("/home")
    session["message"] = "No file uploaded, try again!"
    session["display_alert"] = "True"
    return redirect("/home")

@app.before_request
def make_session_permanent():
    session.permanent = True