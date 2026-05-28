from flask import request
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.utils.helpers import paginate_query

users_ns = Namespace("users", description="User management")


@users_ns.route("/")
class UserList(Resource):
    @jwt_required()
    @users_ns.param("search", "Search by username or email")
    def get(self):
        """Search and list users (for adding to projects)"""
        query = User.query.filter_by(is_active=True)
        if search := request.args.get("search"):
            query = query.filter(
                User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
            )
        return paginate_query(query), 200


@users_ns.route("/<int:user_id>")
class UserProfile(Resource):
    @jwt_required()
    def get(self, user_id):
        """Get a user's public profile"""
        user = User.query.get_or_404(user_id)
        return user.to_dict(include_stats=True), 200
