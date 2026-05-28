def test_create_project(client, auth):
    r = client.post("/api/projects/", json={
        "name": "My New Project",
        "description": "Flask API project",
        "status": "planning",
    }, headers=auth)
    assert r.status_code == 201
    data = r.get_json()
    assert data["name"] == "My New Project"
    assert data["slug"] == "my-new-project"


def test_create_project_unauthenticated(client):
    r = client.post("/api/projects/", json={"name": "Fail"})
    assert r.status_code == 401


def test_get_projects(client, project, auth):
    r = client.get("/api/projects/", headers=auth)
    assert r.status_code == 200
    data = r.get_json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_get_project_detail(client, project, auth):
    r = client.get(f"/api/projects/{project.id}", headers=auth)
    assert r.status_code == 200
    data = r.get_json()
    assert data["id"] == project.id
    assert "task_stats" in data


def test_update_project(client, project, auth):
    r = client.put(f"/api/projects/{project.id}", json={"status": "active"}, headers=auth)
    assert r.status_code == 200
    assert r.get_json()["status"] == "active"


def test_delete_project(client, db, user, auth):
    from app.models.project import Project
    p = Project(name="To Delete", slug="to-delete", owner_id=user.id)
    db.session.add(p)
    db.session.commit()
    r = client.delete(f"/api/projects/{p.id}", headers=auth)
    assert r.status_code == 204


def test_project_stats(client, project, auth):
    r = client.get(f"/api/projects/{project.id}/stats", headers=auth)
    assert r.status_code == 200
    data = r.get_json()
    assert "task_stats" in data
    assert "priority_breakdown" in data
