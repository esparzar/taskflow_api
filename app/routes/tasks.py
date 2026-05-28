from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.project import Project
from app.models.task import Task, Comment
from app.models.user import User
from app.utils.helpers import paginate_query, project_member_required

tasks_ns = Namespace("tasks", description="Task management")

task_input = tasks_ns.model("TaskInput", {
    "title": fields.String(required=True, example="Implement JWT auth"),
    "description": fields.String(example="Add login/register endpoints with JWT"),
    "status": fields.String(enum=["todo", "in_progress", "review", "done", "cancelled"], default="todo"),
    "priority": fields.String(enum=["low", "medium", "high", "critical"], default="medium"),
    "due_date": fields.String(example="2025-09-30T17:00:00"),
    "estimated_hours": fields.Float(example=4.5),
    "assignee_id": fields.Integer(example=2),
    "order": fields.Integer(example=0),
})

comment_input = tasks_ns.model("CommentInput", {
    "body": fields.String(required=True, example="This is blocked by the auth service."),
})


@tasks_ns.route("/project/<int:project_id>")
class TaskList(Resource):
    @jwt_required()
    @tasks_ns.param("status", "Filter by status")
    @tasks_ns.param("priority", "Filter by priority")
    @tasks_ns.param("assignee_id", "Filter by assignee user ID", type=int)
    def get(self, project_id):
        """Get all tasks in a project (with filters)"""
        project = Project.query.get_or_404(project_id)
        if project.is_private and not project_member_required(project):
            return {"message": "Access denied"}, 403

        query = Task.query.filter_by(project_id=project_id, is_archived=False)

        if status := request.args.get("status"):
            query = query.filter_by(status=status)
        if priority := request.args.get("priority"):
            query = query.filter_by(priority=priority)
        if assignee_id := request.args.get("assignee_id", type=int):
            query = query.filter_by(assignee_id=assignee_id)

        query = query.order_by(Task.order, Task.created_at.desc())
        return paginate_query(query), 200

    @jwt_required()
    @tasks_ns.expect(task_input, validate=True)
    @tasks_ns.response(201, "Task created")
    def post(self, project_id):
        """Create a new task in a project"""
        user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        if not project_member_required(project):
            return {"message": "You must be a project member to create tasks"}, 403

        data = request.get_json()

        due_date = None
        if data.get("due_date"):
            due_date = datetime.fromisoformat(data["due_date"])

        task = Task(
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "todo"),
            priority=data.get("priority", "medium"),
            due_date=due_date,
            estimated_hours=data.get("estimated_hours"),
            assignee_id=data.get("assignee_id"),
            order=data.get("order", 0),
            project_id=project_id,
            creator_id=user_id,
        )
        db.session.add(task)
        db.session.commit()
        return task.to_dict(), 201


@tasks_ns.route("/<int:task_id>")
class TaskDetail(Resource):
    @jwt_required()
    def get(self, task_id):
        """Get a single task with attachments and comments"""
        task = Task.query.get_or_404(task_id)
        data = task.to_dict(include_attachments=True)
        data["comments"] = [c.to_dict() for c in task.comments.order_by(Comment.created_at).all()]
        return data, 200

    @jwt_required()
    @tasks_ns.expect(task_input)
    def put(self, task_id):
        """Update a task"""
        user_id = get_jwt_identity()
        task = Task.query.get_or_404(task_id)
        project = Project.query.get_or_404(task.project_id)
        if not project_member_required(project):
            return {"message": "Access denied"}, 403

        data = request.get_json()
        for field in ["title", "description", "status", "priority", "estimated_hours", "actual_hours", "assignee_id", "order"]:
            if field in data:
                setattr(task, field, data[field])

        if "due_date" in data and data["due_date"]:
            task.due_date = datetime.fromisoformat(data["due_date"])

        if data.get("status") == "done" and not task.completed_at:
            task.completed_at = datetime.utcnow()
        elif data.get("status") != "done":
            task.completed_at = None

        db.session.commit()
        return task.to_dict(), 200

    @jwt_required()
    @tasks_ns.response(204, "Task deleted")
    def delete(self, task_id):
        """Delete a task (creator or project owner only)"""
        user_id = get_jwt_identity()
        task = Task.query.get_or_404(task_id)
        project = Project.query.get(task.project_id)
        if task.creator_id != user_id and project.owner_id != user_id:
            return {"message": "Access denied"}, 403
        db.session.delete(task)
        db.session.commit()
        return "", 204


@tasks_ns.route("/<int:task_id>/archive")
class TaskArchive(Resource):
    @jwt_required()
    def post(self, task_id):
        """Archive a task (soft delete)"""
        task = Task.query.get_or_404(task_id)
        task.is_archived = True
        db.session.commit()
        return {"message": "Task archived"}, 200


@tasks_ns.route("/<int:task_id>/comments")
class TaskComments(Resource):
    @jwt_required()
    def get(self, task_id):
        """Get all comments for a task"""
        task = Task.query.get_or_404(task_id)
        comments = task.comments.order_by(Comment.created_at).all()
        return [c.to_dict() for c in comments], 200

    @jwt_required()
    @tasks_ns.expect(comment_input, validate=True)
    def post(self, task_id):
        """Add a comment to a task"""
        user_id = get_jwt_identity()
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        comment = Comment(body=data["body"], task_id=task_id, author_id=user_id)
        db.session.add(comment)
        db.session.commit()
        return comment.to_dict(), 201


@tasks_ns.route("/<int:task_id>/comments/<int:comment_id>")
class CommentDetail(Resource):
    @jwt_required()
    def delete(self, task_id, comment_id):
        """Delete a comment (author only)"""
        user_id = get_jwt_identity()
        comment = Comment.query.get_or_404(comment_id)
        if comment.author_id != user_id:
            return {"message": "Access denied"}, 403
        db.session.delete(comment)
        db.session.commit()
        return "", 204
