import os
import uuid
import subprocess
from flask import Flask, render_template, request, send_file, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "brian-secret")

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")

        if not file or not file.filename:
            flash("لطفاً یک فایل انتخاب کنید.")
            return redirect(url_for("index"))

        ext = file.filename.rsplit(".", 1)[-1].lower()

        if ext not in ("ppt", "pptx"):
            flash("فقط فایل PPT و PPTX مجاز است.")
            return redirect(url_for("index"))

        uid = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, uid + "." + ext)
        pdf_path = os.path.join(UPLOAD_FOLDER, uid + ".pdf")

        try:
            file.save(input_path)

            subprocess.run(
                [
                    "libreoffice",
                    "-env:UserInstallation=file:///tmp/lo_" + uid,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", UPLOAD_FOLDER,
                    input_path
                ],
                check=True,
                timeout=120,
                capture_output=True
            )

            if not os.path.exists(pdf_path):
                raise RuntimeError("PDF ساخته نشد")

            response = send_file(
                pdf_path,
                as_attachment=True,
                download_name="converted.pdf"
            )

            @response.call_on_close
            def cleanup():
                for path in (input_path, pdf_path):
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except OSError:
                        pass

            return response

        except Exception as error:
            print(error)
            flash("تبدیل انجام نشد. دوباره تلاش کنید.")
            return redirect(url_for("index"))

        finally:
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except OSError:
                    pass

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
