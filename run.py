import os
from app import create_app, db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Project": Project, "Task": Task}


@app.cli.command("seed")
def seed_db():
    """Seed database with sample data for demo."""
    from app.utils.helpers import slugify
    from datetime import datetime, timedelta

    print("Seeding database...")

    admin = User(username="emmanuel", email="emmanuel@taskflow.com",
                 full_name="Emmanuel Amponsah", is_admin=True)
    admin.set_password("admin123")

    dev = User(username="dev_user", email="dev@taskflow.com", full_name="Dev User")
    dev.set_password("dev123")

    db.session.add_all([admin, dev])
    db.session.flush()

    project = Project(
        name="TaskFlow API Development",
        slug="taskflow-api-development",
        description="Building the TaskFlow REST API with Flask, Docker, and AWS.",
        status="active",
        color="#6366f1",
        owner_id=admin.id,
        due_date=(datetime.utcnow() + timedelta(days=30)).date(),
    )
    project.members.append(dev)
    db.session.add(project)
    db.session.flush()

    tasks_data = [
        {"title": "Setup Flask project structure", "status": "done", "priority": "high"},
        {"title": "Implement JWT authentication", "status": "done", "priority": "critical"},
        {"title": "Build Projects CRUD API", "status": "in_progress", "priority": "high"},
        {"title": "Build Tasks CRUD API", "status": "in_progress", "priority": "high"},
        {"title": "Integrate AWS S3 file uploads", "status": "todo", "priority": "high"},
        {"title": "Write Pytest test suite", "status": "todo", "priority": "medium"},
        {"title": "Dockerize the application", "status": "todo", "priority": "medium"},
        {"title": "Setup GitHub Actions CI/CD", "status": "todo", "priority": "medium"},
        {"title": "Deploy to AWS EC2", "status": "todo", "priority": "critical"},
        {"title": "Configure Nginx reverse proxy", "status": "todo", "priority": "medium"},
    ]

    for i, t in enumerate(tasks_data):
        task = Task(
            title=t["title"],
            status=t["status"],
            priority=t["priority"],
            project_id=project.id,
            creator_id=admin.id,
            assignee_id=admin.id if i % 2 == 0 else dev.id,
            order=i,
        )
        db.session.add(task)

    db.session.commit()
    print("✅ Database seeded!")
    print("   Admin: emmanuel@taskflow.com / admin123")
    print("   Dev:   dev@taskflow.com / dev123")


if __name__ == "__main__":
    app.run(debug=True)
