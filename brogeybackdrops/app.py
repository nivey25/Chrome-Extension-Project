from flask import Flask, render_template, request, redirect
app = Flask(__name__)

#defaultUrl = "https://variety.com/wp-content/uploads/2020/01/taylor-swift-variety-cover-5-16x9-1000.jpg?w=681&h=383&crop=1"
@app.route('/', methods=["GET", "POST"])
def hello_world():
    if request.method == "GET":
        return render_template("index.html") #, url=defaultUrl
    else:
        image = request.files['imageFile']
        if image.filename != '':
            image.save("./userImages/" + image.filename)
        return redirect("/")
        