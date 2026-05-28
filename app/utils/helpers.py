import re
import unicodedata
from flask import request
from functools import wraps
from flask_jwt_extended import get_jwt_identity
from app.models.user import User


def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def paginate_query(query, serializer=None):
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    if serializer:
        items = [serializer(item) for item in pagination.items]
    else:
        items = [item.to_dict() for item in pagination.items]

    return {
        "items": items,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
            "next_page": pagination.next_num if pagination.has_next else None,
            "prev_page": pagination.prev_num if pagination.has_prev else None,
        },
    }


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def admin_required(fn):
    """Decorator: requires authenticated user to be an admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return {"message": "Admin access required"}, 403
        return fn(*args, **kwargs)
    return wrapper


def project_member_required(project):
    """Check if the current user is a member or owner of a project."""
    user_id = get_jwt_identity()
    if project.owner_id == user_id:
        return True
    return any(m.id == user_id for m in project.members)
