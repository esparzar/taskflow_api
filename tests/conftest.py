import pytest
from app import create_app, db as _db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
        _db.session.remove()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(db):
    u = User(username="testuser", email="test@example.com", full_name="Test User")
    u.set_password("testpass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def admin(db):
    u = User(username="admin", email="admin@example.com", full_name="Admin", is_admin=True)
    u.set_password("adminpass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def user2(db):
    u = User(username="user2", email="user2@example.com", full_name="User Two")
    u.set_password("pass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth(client, user):
    resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth(client, admin):
    resp = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "adminpass123"})
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project(db, user):
    p = Project(
        name="Test Project",
        slug="test-project",
        description="A test project",
        status="active",
        owner_id=user.id,
    )
    db.session.add(p)
    db.session.commit()
    return p


@pytest.fixture
def task(db, project, user):
    t = Task(
        title="Test Task",
        description="A test task",
        status="todo",
        priority="medium",
        project_id=project.id,
        creator_id=user.id,
    )
    db.session.add(t)
    db.session.commit()
    return t
