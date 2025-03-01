from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
from dct import insert, extract

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/insert", methods=["GET", "POST"])
def insert_page():
    if request.method == "POST":
        if "image" not in request.files or request.files["image"].filename == "":
            flash("No image selected", "danger")
            return redirect(url_for("insert_page"))

        image_file = request.files["image"]
        message = request.form.get("message", "").strip()

        if not message:
            flash("No message entered", "danger")
            return redirect(url_for("insert_page"))

        image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_file.filename)
        image_file.save(image_path)

        try:
            embedded_image_path = insert(image_path, message)
            return send_file(embedded_image_path, as_attachment=True)
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("insert.html")

@app.route("/extract", methods=["GET", "POST"])
def extract_page():
    secret_message = None

    if request.method == "POST":
        if "image" not in request.files or request.files["image"].filename == "":
            flash("No image selected", "danger")
            return redirect(url_for("extract_page"))

        image_file = request.files["image"]
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_file.filename)
        image_file.save(image_path)

        try:
            secret_message = extract(image_path)
            flash(f"Secret Message: {secret_message}", "success")
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("extract.html", secret_message=secret_message)

if __name__ == "__main__":
    app.run(debug=True)
