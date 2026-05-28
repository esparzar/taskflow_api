from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from app import db
from app.models.user import User

auth_ns = Namespace("auth", description="Authentication")

register_model = auth_ns.model("Register", {
    "username": fields.String(required=True, example="emmanuel"),
    "email": fields.String(required=True, example="emmanuel@example.com"),
    "password": fields.String(required=True, example="secure123"),
    "full_name": fields.String(example="Emmanuel Amponsah"),
})

login_model = auth_ns.model("Login", {
    "email": fields.String(required=True, example="emmanuel@example.com"),
    "password": fields.String(required=True, example="secure123"),
})


@auth_ns.route("/register")
class Register(Resource):
    @auth_ns.expect(register_model, validate=True)
    @auth_ns.response(201, "Registered successfully")
    @auth_ns.response(409, "Email or username taken")
    def post(self):
        """Register a new user account"""
        data = request.get_json()

        if User.query.filter_by(email=data["email"]).first():
            return {"message": "Email already registered"}, 409
        if User.query.filter_by(username=data["username"]).first():
            return {"message": "Username already taken"}, 409
        if len(data["password"]) < 6:
            return {"message": "Password must be at least 6 characters"}, 400

        user = User(
            username=data["username"],
            email=data["email"],
            full_name=data.get("full_name", ""),
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()

        return {
            "message": "Account created successfully",
            "access_token": create_access_token(identity=user.id),
            "refresh_token": create_refresh_token(identity=user.id),
            "user": user.to_dict(),
        }, 201


@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.response(200, "Login successful")
    @auth_ns.response(401, "Invalid credentials")
    def post(self):
        """Login and receive JWT access + refresh tokens"""
        data = request.get_json()
        user = User.query.filter_by(email=data["email"]).first()

        if not user or not user.check_password(data["password"]):
            return {"message": "Invalid email or password"}, 401
        if not user.is_active:
            return {"message": "Account is deactivated"}, 403

        user.last_login = datetime.utcnow()
        db.session.commit()

        return {
            "access_token": create_access_token(identity=user.id),
            "refresh_token": create_refresh_token(identity=user.id),
            "user": user.to_dict(),
        }, 200


@auth_ns.route("/refresh")
class Refresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """Get a new access token using your refresh token"""
        user_id = get_jwt_identity()
        return {"access_token": create_access_token(identity=user_id)}, 200


@auth_ns.route("/me")
class Me(Resource):
    @jwt_required()
    def get(self):
        """Get current authenticated user profile"""
        user = User.query.get_or_404(get_jwt_identity())
        return user.to_dict(include_stats=True), 200

    @jwt_required()
    def put(self):
        """Update current user profile"""
        user = User.query.get_or_404(get_jwt_identity())
        data = request.get_json()

        for field in ["full_name", "bio"]:
            if field in data:
                setattr(user, field, data[field])

        if "username" in data:
            existing = User.query.filter_by(username=data["username"]).first()
            if existing and existing.id != user.id:
                return {"message": "Username already taken"}, 409
            user.username = data["username"]

        if "password" in data:
            if len(data["password"]) < 6:
                return {"message": "Password must be at least 6 characters"}, 400
            user.set_password(data["password"])

        db.session.commit()
        return user.to_dict(), 200
