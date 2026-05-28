from datetime import datetime
from app import db
from app.models.user import project_members


class Project(db.Model):
    __tablename__ = "projects"

    STATUS_CHOICES = ["planning", "active", "on_hold", "completed", "archived"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="planning", nullable=False)
    color = db.Column(db.String(7), default="#6366f1")  # hex color for UI
    due_date = db.Column(db.Date, nullable=True)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    tasks = db.relationship("Task", backref="project", lazy="dynamic", cascade="all, delete-orphan")
    members = db.relationship("User", secondary=project_members, backref=db.backref("projects", lazy="dynamic"))

    def get_task_stats(self):
        total = self.tasks.count()
        done = self.tasks.filter_by(status="done").count()
        in_progress = self.tasks.filter_by(status="in_progress").count()
        return {
            "total": total,
            "done": done,
            "in_progress": in_progress,
            "todo": self.tasks.filter_by(status="todo").count(),
            "completion_pct": round((done / total * 100), 1) if total > 0 else 0,
        }

    def to_dict(self, include_tasks=False, include_members=False):
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "status": self.status,
            "color": self.color,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "is_private": self.is_private,
            "owner": self.owner.to_dict() if self.owner else None,
            "task_stats": self.get_task_stats(),
            "member_count": len(self.members),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_tasks:
            data["tasks"] = [t.to_dict() for t in self.tasks.order_by("created_at")]
        if include_members:
            data["members"] = [m.to_dict() for m in self.members]
        return data

    def __repr__(self):
        return f"<Project {self.name}>"
