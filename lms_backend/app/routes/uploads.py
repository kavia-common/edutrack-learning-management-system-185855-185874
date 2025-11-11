import os
from flask import request, current_app
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

blp = Blueprint(
    "Uploads",
    "uploads",
    url_prefix="/api/uploads",
    description="File upload endpoint",
)


@blp.route("/")
class UploadFile(MethodView):
    """
    PUBLIC_INTERFACE
    Upload a file (multipart/form-data with key 'file').
    Returns a JSON with the normalized relative path to the stored file.
    """
    @jwt_required()
    def post(self):
        file_storage = request.files.get("file")
        if file_storage is None:
            return {"message": "No file provided"}, 400
        if not file_storage.filename:
            return {"message": "Empty filename"}, 400

        filename = secure_filename(file_storage.filename)
        upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        save_path = os.path.join(upload_dir, filename)
        file_storage.save(save_path)

        normalized_path = "/" + save_path
        normalized_path = normalized_path.replace("//", "/")

        return {"message": "Uploaded", "path": normalized_path}, 201
