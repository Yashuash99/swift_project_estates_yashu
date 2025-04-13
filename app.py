from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId


app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB config
app.config["MONGO_URI"] = "mongodb://localhost:27017/swift_estates"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

@app.route("/")
def index():
    properties = mongo.db.properties.find()
    return render_template("index.html", properties=properties)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = mongo.db.users
        existing_user = users.find_one({"email": request.form["email"]})
        if existing_user:
            flash("Email already registered")
            return redirect(url_for("register"))
        hashed_pw = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        users.insert_one({"email": request.form["email"], "password": hashed_pw, "favorites": []})
        session["email"] = request.form["email"]
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = mongo.db.users.find_one({"email": request.form["email"]})
        if user and bcrypt.check_password_hash(user["password"], request.form["password"]):
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))
    properties = mongo.db.properties.find({"owner": session["email"]})
    return render_template("dashboard.html", properties=properties)

@app.route("/add", methods=["GET", "POST"])
def add_property():
    if "email" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        mongo.db.properties.insert_one({
            "title": request.form["title"],
            "price": request.form["price"],
            "description": request.form["description"],
            "owner": session["email"]
        })
        return redirect(url_for("dashboard"))
    return render_template("add_property.html")

@app.route("/edit/<property_id>", methods=["GET", "POST"])
def edit_property(property_id):
    property = mongo.db.properties.find_one({"_id": ObjectId(property_id)})
    if request.method == "POST":
        mongo.db.properties.update_one({"_id": ObjectId(property_id)}, {
            "$set": {
                "title": request.form["title"],
                "price": request.form["price"],
                "description": request.form["description"]
            }
        })
        return redirect(url_for("dashboard"))
    return render_template("edit_property.html", property=property)

@app.route("/delete/<property_id>")
def delete_property(property_id):
    mongo.db.properties.delete_one({"_id": ObjectId(property_id)})
    return redirect(url_for("dashboard"))

@app.route("/all")
def all_properties():
    properties = mongo.db.properties.find()
    return render_template("all_properties.html", properties=properties)



if __name__ == "__main__":
    app.run(debug=True)
