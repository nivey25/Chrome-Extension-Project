import os
import imghdr
from flask import Flask, abort, current_app, render_template, request, redirect
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
app.config['UPLOAD_PATH'] = 'static/userImages'

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

#defaultUrl = "https://variety.com/wp-content/uploads/2020/01/taylor-swift-variety-cover-5-16x9-1000.jpg?w=681&h=383&crop=1"
@app.route('/', methods=["GET", "POST"])
def hello_world():
    if request.method == "GET":
        return render_template("index.html") #, url=defaultUrl
    else:
        image = request.files['imageFile']
        if image.filename != '':
            file_ext = os.path.splitext(image.filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(image.stream):
                abort(400)
            image.save(os.path.join(app.config['UPLOAD_PATH'], image.filename))
        return redirect("/")
        