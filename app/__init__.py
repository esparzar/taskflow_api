from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api
from config import config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    authorizations = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter: **Bearer &lt;your JWT token&gt;**",
        }
    }

    api = Api(
        app,
        version="1.0",
        title="TaskFlow API",
        description=(
            "A production-ready Task & Project Management REST API. "
            "Built with Flask, PostgreSQL, JWT Auth, AWS S3, deployed on AWS EC2."
        ),
        doc="/docs",
        authorizations=authorizations,
        security="Bearer Auth",
        contact="Emmanuel Amponsah",
        contact_url="https://github.com/esparzar",
        license="MIT",
    )

    from app.routes.auth import auth_ns
    from app.routes.projects import projects_ns
    from app.routes.tasks import tasks_ns
    from app.routes.uploads import uploads_ns
    from app.routes.users import users_ns

    api.add_namespace(auth_ns, path="/api/auth")
    api.add_namespace(users_ns, path="/api/users")
    api.add_namespace(projects_ns, path="/api/projects")
    api.add_namespace(tasks_ns, path="/api/tasks")
    api.add_namespace(uploads_ns, path="/api/uploads")

    @app.route("/health")
    def health():
        return {"status": "healthy", "version": "1.0.0"}, 200

    return app
