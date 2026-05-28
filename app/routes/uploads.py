from flask import request, current_app
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.task import Task, Attachment
from app.services.s3_service import s3_service
from app.utils.helpers import allowed_file

uploads_ns = Namespace("uploads", description="File upload to AWS S3")


@uploads_ns.route("/task/<int:task_id>")
class TaskUpload(Resource):
    @jwt_required()
    @uploads_ns.response(201, "File uploaded to S3")
    @uploads_ns.response(400, "Invalid file or file too large")
    def post(self, task_id):
        """
        Upload a file attachment to a task.
        File is stored in AWS S3. Max size 10MB.
        Supported: pdf, png, jpg, jpeg, gif, docx, xlsx, txt
        """
        task = Task.query.get_or_404(task_id)
        user_id = get_jwt_identity()

        if "file" not in request.files:
            return {"message": "No file provided. Use form-data with key 'file'."}, 400

        file = request.files["file"]
        if file.filename == "":
            return {"message": "No file selected"}, 400

        allowed = current_app.config["ALLOWED_EXTENSIONS"]
        if not allowed_file(file.filename, allowed):
            return {
                "message": f"File type not allowed. Allowed types: {', '.join(allowed)}"
            }, 400

        content_type = file.content_type or "application/octet-stream"

        try:
            result = s3_service.upload_file(
                file_obj=file,
                original_filename=file.filename,
                content_type=content_type,
                folder=f"tasks/{task_id}/attachments",
            )
        except ValueError as e:
            return {"message": str(e)}, 500

        file.seek(0, 2)  # seek to end to get size
        file_size = file.tell()

        attachment = Attachment(
            filename=result["filename"],
            original_filename=file.filename,
            file_size=file_size,
            content_type=content_type,
            s3_key=result["s3_key"],
            s3_url=result["s3_url"],
            uploaded_by_id=user_id,
            task_id=task_id,
        )
        db.session.add(attachment)
        db.session.commit()

        return {
            "message": "File uploaded successfully to S3",
            "attachment": attachment.to_dict(),
        }, 201


@uploads_ns.route("/attachment/<int:attachment_id>")
class AttachmentDetail(Resource):
    @jwt_required()
    def get(self, attachment_id):
        """Get a presigned download URL for an attachment (valid 1 hour)"""
        attachment = Attachment.query.get_or_404(attachment_id)
        try:
            url = s3_service.generate_presigned_url(attachment.s3_key, expiration=3600)
            return {
                "download_url": url,
                "filename": attachment.original_filename,
                "expires_in": "1 hour",
            }, 200
        except ValueError as e:
            return {"message": str(e)}, 500

    @jwt_required()
    @uploads_ns.response(204, "Attachment deleted from S3")
    def delete(self, attachment_id):
        """Delete an attachment from S3 and the database"""
        user_id = get_jwt_identity()
        attachment = Attachment.query.get_or_404(attachment_id)

        if attachment.uploaded_by_id != user_id:
            return {"message": "You can only delete your own attachments"}, 403

        try:
            s3_service.delete_file(attachment.s3_key)
        except ValueError as e:
            return {"message": str(e)}, 500

        db.session.delete(attachment)
        db.session.commit()
        return "", 204


@uploads_ns.route("/avatar")
class AvatarUpload(Resource):
    @jwt_required()
    @uploads_ns.response(200, "Avatar updated")
    def post(self):
        """Upload a profile avatar image to S3 (jpg, png, gif only)"""
        from app.models.user import User
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        if "file" not in request.files:
            return {"message": "No file provided"}, 400

        file = request.files["file"]
        allowed_avatar = {"png", "jpg", "jpeg", "gif", "webp"}
        if not allowed_file(file.filename, allowed_avatar):
            return {"message": "Avatar must be an image (png, jpg, jpeg, gif, webp)"}, 400

        try:
            result = s3_service.upload_file(
                file_obj=file,
                original_filename=file.filename,
                content_type=file.content_type or "image/jpeg",
                folder=f"avatars/{user_id}",
            )
        except ValueError as e:
            return {"message": str(e)}, 500

        user.avatar_url = result["s3_url"]
        db.session.commit()

        return {"message": "Avatar updated", "avatar_url": user.avatar_url}, 200
