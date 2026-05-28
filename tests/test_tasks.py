def test_create_task(client, project, auth):
    r = client.post(f"/api/tasks/project/{project.id}", json={
        "title": "Implement S3 upload",
        "priority": "high",
        "status": "todo",
    }, headers=auth)
    assert r.status_code == 201
    data = r.get_json()
    assert data["title"] == "Implement S3 upload"
    assert data["priority"] == "high"


def test_get_tasks(client, project, task, auth):
    r = client.get(f"/api/tasks/project/{project.id}", headers=auth)
    assert r.status_code == 200
    data = r.get_json()
    assert len(data["items"]) >= 1


def test_filter_tasks_by_status(client, project, task, auth):
    r = client.get(f"/api/tasks/project/{project.id}?status=todo", headers=auth)
    assert r.status_code == 200
    for item in r.get_json()["items"]:
        assert item["status"] == "todo"


def test_get_task_detail(client, task, auth):
    r = client.get(f"/api/tasks/{task.id}", headers=auth)
    assert r.status_code == 200
    data = r.get_json()
    assert data["id"] == task.id
    assert "attachments" in data
    assert "comments" in data


def test_update_task_status(client, task, auth):
    r = client.put(f"/api/tasks/{task.id}", json={"status": "in_progress"}, headers=auth)
    assert r.status_code == 200
    assert r.get_json()["status"] == "in_progress"


def test_mark_task_done(client, task, auth):
    r = client.put(f"/api/tasks/{task.id}", json={"status": "done"}, headers=auth)
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "done"
    assert data["completed_at"] is not None


def test_add_comment(client, task, auth):
    r = client.post(f"/api/tasks/{task.id}/comments",
                    json={"body": "This is blocked by auth service."},
                    headers=auth)
    assert r.status_code == 201
    assert r.get_json()["body"] == "This is blocked by auth service."


def test_delete_task(client, task, auth):
    r = client.delete(f"/api/tasks/{task.id}", headers=auth)
    assert r.status_code == 204


def test_archive_task(client, db, project, user, auth):
    from app.models.task import Task
    t = Task(title="Archive me", project_id=project.id, creator_id=user.id)
    db.session.add(t)
    db.session.commit()
    r = client.post(f"/api/tasks/{t.id}/archive", headers=auth)
    assert r.status_code == 200
