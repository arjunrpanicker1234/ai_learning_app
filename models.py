from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()  # Initialize SQLAlchemy here
tutor_skills = db.Table('tutor_skills',
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutor.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_tutor = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assessments = db.relationship('Assessment', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
     return check_password_hash(self.password, password)


class Tutor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    hourly_rate = db.Column(db.Float, nullable=True)

    # Many-to-Many relationship with Skill (Corrected)
    skills = db.relationship('Skill', secondary=tutor_skills, backref=db.backref('tutors', lazy=True))

    # Relationship with User
    user = db.relationship('User', backref=db.backref('tutor_profile', uselist=False))

class TutorRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Learner
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Tutor (User, not Tutor model)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)  # Skill ID
    status = db.Column(db.String(20), default="Pending")

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='requests')
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='received_requests')  # Tutor
    skill = db.relationship('Skill', backref='tutor_requests')  # Skill

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    # Relationships with renamed backref
    questions = db.relationship('Question', backref='related_skill', lazy=True)
    resources = db.relationship('Resource', backref='skill', lazy=True)


class Question(db.Model):
    __tablename__ = 'question'
    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey('skill.id'), nullable=False)
    question_text = Column(String, nullable=False)
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    correct_option = Column(Integer, nullable=False)
    difficulty = Column(Integer, nullable=False)

    # Use the backref created in Skill (no need for another explicit relationship)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    proficiency_level = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # Add this field

    # Relationships
    skill = db.relationship('Skill')


class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # 'pdf', 'text', etc.
    content = db.Column(db.Text, nullable=True)  # For text content
    file_path = db.Column(db.String(200), nullable=True)  # For PDFs
    proficiency_level = db.Column(db.Integer, nullable=False)  # 1-5 scale
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    uploader = db.relationship('User')

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='session', lazy=True)
    user = db.relationship('User')
    skill = db.relationship('Skill')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True if from user, False if from system
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)