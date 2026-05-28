from datetime import datetime
from app import db


class Task(db.Model):
    __tablename__ = "tasks"

    PRIORITY_CHOICES = ["low", "medium", "high", "critical"]
    STATUS_CHOICES = ["todo", "in_progress", "review", "done", "cancelled"]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="todo", nullable=False, index=True)
    priority = db.Column(db.String(20), default="medium", nullable=False, index=True)
    due_date = db.Column(db.DateTime, nullable=True)
    estimated_hours = db.Column(db.Float, nullable=True)
    actual_hours = db.Column(db.Float, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)  # for drag-and-drop ordering
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    attachments = db.relationship("Attachment", backref="task", lazy="dynamic", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="task", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_attachments=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "order": self.order,
            "project_id": self.project_id,
            "assignee": self.assignee.to_dict() if self.assignee else None,
            "creator": self.creator.to_dict() if self.creator else None,
            "attachment_count": self.attachments.count(),
            "comment_count": self.comments.count(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        if include_attachments:
            data["attachments"] = [a.to_dict() for a in self.attachments]
        return data

    def __repr__(self):
        return f"<Task {self.title}>"


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    content_type = db.Column(db.String(100), nullable=False)
    s3_key = db.Column(db.String(500), nullable=False)       # S3 object key
    s3_url = db.Column(db.String(1000), nullable=False)      # public/presigned URL
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.original_filename,
            "file_size": self.file_size,
            "file_size_human": self._human_size(),
            "content_type": self.content_type,
            "s3_url": self.s3_url,
            "uploaded_by": self.uploaded_by.to_dict() if self.uploaded_by else None,
            "created_at": self.created_at.isoformat(),
        }

    def _human_size(self):
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def __repr__(self):
        return f"<Attachment {self.original_filename}>"


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship("User", foreign_keys=[author_id])

    def to_dict(self):
        return {
            "id": self.id,
            "body": self.body,
            "author": self.author.to_dict() if self.author else None,
            "task_id": self.task_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
