from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.project import Project
from app.utils.helpers import slugify, paginate_query, project_member_required

projects_ns = Namespace("projects", description="Project management")

project_input = projects_ns.model("ProjectInput", {
    "name": fields.String(required=True, example="Website Redesign"),
    "description": fields.String(example="Full redesign of the company website"),
    "status": fields.String(enum=["planning", "active", "on_hold", "completed", "archived"], default="planning"),
    "color": fields.String(example="#6366f1"),
    "due_date": fields.String(example="2025-12-31"),
    "is_private": fields.Boolean(default=False),
})


@projects_ns.route("/")
class ProjectList(Resource):
    @jwt_required()
    @projects_ns.response(200, "Paginated list of projects")
    @projects_ns.param("status", "Filter by status")
    @projects_ns.param("page", "Page number", type=int)
    def get(self):
        """List all projects the current user owns or is a member of"""
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        owned = Project.query.filter_by(owner_id=user_id)
        member_of = user.projects.filter(Project.owner_id != user_id)

        status = request.args.get("status")
        if status:
            owned = owned.filter_by(status=status)
            member_of = member_of.filter_by(status=status)

        all_projects = owned.union(member_of).order_by(Project.updated_at.desc())
        return paginate_query(all_projects), 200

    @jwt_required()
    @projects_ns.expect(project_input, validate=True)
    @projects_ns.response(201, "Project created")
    def post(self):
        """Create a new project"""
        user_id = get_jwt_identity()
        data = request.get_json()

        slug = slugify(data["name"])
        if Project.query.filter_by(slug=slug).first():
            slug = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        due_date = None
        if data.get("due_date"):
            from datetime import date
            due_date = date.fromisoformat(data["due_date"])

        project = Project(
            name=data["name"],
            slug=slug,
            description=data.get("description", ""),
            status=data.get("status", "planning"),
            color=data.get("color", "#6366f1"),
            due_date=due_date,
            is_private=data.get("is_private", False),
            owner_id=user_id,
        )
        db.session.add(project)
        db.session.commit()
        return project.to_dict(), 201


@projects_ns.route("/<int:project_id>")
class ProjectDetail(Resource):
    @jwt_required()
    def get(self, project_id):
        """Get a project with its tasks and members"""
        user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        if project.is_private and not project_member_required(project):
            return {"message": "Access denied"}, 403
        return project.to_dict(include_tasks=True, include_members=True), 200

    @jwt_required()
    @projects_ns.expect(project_input)
    def put(self, project_id):
        """Update a project (owner only)"""
        user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        if project.owner_id != user_id:
            return {"message": "Only the project owner can update it"}, 403

        data = request.get_json()
        for field in ["name", "description", "status", "color", "is_private"]:
            if field in data:
                setattr(project, field, data[field])
        if "due_date" in data and data["due_date"]:
            from datetime import date
            project.due_date = date.fromisoformat(data["due_date"])

        db.session.commit()
        return project.to_dict(), 200

    @jwt_required()
    @projects_ns.response(204, "Project deleted")
    def delete(self, project_id):
        """Delete a project and all its tasks (owner only)"""
        user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        if project.owner_id != user_id:
            return {"message": "Only the project owner can delete it"}, 403
        db.session.delete(project)
        db.session.commit()
        return "", 204


@projects_ns.route("/<int:project_id>/members")
class ProjectMembers(Resource):
    @jwt_required()
    def post(self, project_id):
        """Add a member to a project (owner only)"""
        user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        if project.owner_id != user_id:
            return {"message": "Only the project owner can add members"}, 403

        data = request.get_json()
        member = User.query.filter_by(email=data.get("email")).first()
        if not member:
            return {"message": "User not found"}, 404
        if member in project.members or member.id == project.owner_id:
            return {"message": "User is already a member"}, 409

        project.members.append(member)
        db.session.commit()
        return {"message": f"{member.username} added to project", "member": member.to_dict()}, 201

    @jwt_required()
    def delete(self, project_id):
        """Remove a member from a project (owner only)"""
        user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        if project.owner_id != user_id:
            return {"message": "Only the project owner can remove members"}, 403

        data = request.get_json()
        member = User.query.get(data.get("user_id"))
        if not member or member not in project.members:
            return {"message": "User is not a project member"}, 404

        project.members.remove(member)
        db.session.commit()
        return {"message": f"{member.username} removed from project"}, 200


@projects_ns.route("/<int:project_id>/stats")
class ProjectStats(Resource):
    @jwt_required()
    def get(self, project_id):
        """Get detailed project statistics"""
        project = Project.query.get_or_404(project_id)
        if project.is_private and not project_member_required(project):
            return {"message": "Access denied"}, 403

        from app.models.task import Task
        tasks = Task.query.filter_by(project_id=project_id)
        overdue = [
            t for t in tasks.filter(Task.due_date < datetime.utcnow(), Task.status != "done").all()
        ]
        return {
            "project": project.name,
            "task_stats": project.get_task_stats(),
            "overdue_tasks": len(overdue),
            "members": len(project.members) + 1,  # +1 for owner
            "priority_breakdown": {
                p: tasks.filter_by(priority=p).count()
                for p in ["low", "medium", "high", "critical"]
            },
        }, 200
