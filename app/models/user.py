from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Team membership association table
project_members = db.Table(
    "project_members",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("role", db.String(20), default="member"),  # owner, admin, member
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)  # stored in S3
    bio = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    owned_projects = db.relationship("Project", backref="owner", lazy="dynamic", foreign_keys="Project.owner_id")
    assigned_tasks = db.relationship("Task", backref="assignee", lazy="dynamic", foreign_keys="Task.assignee_id")
    created_tasks = db.relationship("Task", backref="creator", lazy="dynamic", foreign_keys="Task.creator_id")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_stats=False):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        if include_stats:
            data["stats"] = {
                "projects_owned": self.owned_projects.count(),
                "tasks_assigned": self.assigned_tasks.count(),
                "tasks_created": self.created_tasks.count(),
            }
        return data

    def __repr__(self):
        return f"<User {self.username}>"
