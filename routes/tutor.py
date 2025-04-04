from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Skill, Resource, User
from services.pdf_service import PDFService
import os
from config import Config
from datetime import datetime
tutor_bp = Blueprint('tutor', __name__)
pdf_service = PDFService()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

from flask import send_from_directory, current_app
from models import TutorRequest  # Import the TutorRequest model

@tutor_bp.route('/pending_requests')
@login_required
def pending_requests():
    if not current_user.is_tutor:
        return redirect(url_for('user.dashboard'))

    pending_requests = TutorRequest.query.filter_by(tutor_id=current_user.id, status='pending').all()
    return render_template('tutor/pending_requests.html', pending_requests=pending_requests)

@tutor_bp.route('/serve_file/<path:filename>')
@login_required
def serve_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@tutor_bp.route('/tutors/<int:skill_id>')
@login_required
def tutors_by_skill(skill_id):
    """List tutors based on selected skill."""
    skill = Skill.query.get_or_404(skill_id)
    
    # Query tutors who have uploaded resources or have the selected skill
    tutors = User.query.filter_by(is_tutor=True).all()  # This might later be filtered more deeply

    return render_template('tutor/tutors_by_skill.html', skill=skill, tutors=tutors)

@tutor_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_tutor:
        return redirect(url_for('user.dashboard'))

    tutor_profile = current_user.tutor_profile  # Get tutor profile
    tutor_skills = tutor_profile.skills if tutor_profile else []  # Get tutor skills
    tutor_resources = Resource.query.filter_by(uploaded_by=current_user.id).all()
    has_resources = bool(tutor_resources)

    # Fetch pending tutor requests
    pending_requests = TutorRequest.query.filter_by(tutor_id=current_user.id, status="Pending").all()

    return render_template('tutor/dashboard.html',
                           tutor_skills=tutor_skills,
                           tutor_resources=tutor_resources,
                           has_resources=has_resources,
                           pending_requests=pending_requests)
@tutor_bp.route('/add_skill', methods=['GET', 'POST'])
@login_required
def add_skill():
    if not current_user.is_tutor:
        return redirect(url_for('user.dashboard'))

    tutor_profile = current_user.tutor_profile
    if not tutor_profile:
        flash("You need to create a tutor profile first!", "danger")
        return redirect(url_for('tutor.dashboard'))

    if request.method == 'POST':
        skill_id = request.form.get('skill_id', type=int)
        skill = Skill.query.get(skill_id)

        if not skill:
            flash("Skill not found.", "danger")
            return redirect(url_for('tutor.add_skill'))

        # Add skill only if it's not already selected
        if skill not in tutor_profile.skills:
            tutor_profile.skills.append(skill)
            db.session.commit()
            flash("Skill added successfully!", "success")
        else:
            flash("You already have this skill.", "info")

        return redirect(url_for('tutor.dashboard'))

    # Fetch all available skills
    available_skills = Skill.query.all()
    return render_template('tutor/add_skill.html', available_skills=available_skills)

@tutor_bp.route('/upload_resource', methods=['GET', 'POST'])
@login_required
def upload_resource():
    if not current_user.is_tutor:
        return redirect(url_for('user.dashboard'))

    # Get tutor's skills
    tutor_profile = current_user.tutor_profile
    skills = tutor_profile.skills if tutor_profile else []

    if not skills:
        flash("Please add at least one skill before uploading resources.", "warning")
        return redirect(url_for('tutor.add_skill'))

    if request.method == 'POST':
        skill_id = request.form.get('skill_id', type=int)
        title = request.form.get('title')
        proficiency_level = request.form.get('proficiency_level', type=int)
        file = request.files.get('file')

        # Validate input
        if not skill_id or not title or not proficiency_level or not file:
            flash('All fields are required.', 'danger')
            return redirect(url_for('tutor.upload_resource'))

        # Save file
        filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{file.filename}")
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save resource to database
        new_resource = Resource(
            skill_id=skill_id,
            title=title,
            content_type='pdf',
            file_path=file_path,
            proficiency_level=proficiency_level,
            uploaded_by=current_user.id
        )
        db.session.add(new_resource)
        db.session.commit()

        flash('Resource uploaded successfully!', 'success')
        return redirect(url_for('tutor.dashboard'))

    return render_template('tutor/upload_resource.html', skills=skills)


@tutor_bp.route('/approve_request/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    request = TutorRequest.query.get_or_404(request_id)
    
    if not current_user.is_tutor or request.tutor_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('tutor.dashboard'))

    # Approve the request
    request.status = "Approved"
    db.session.commit()

    flash(f"Request from {request.learner.username} approved!", "success")
    return redirect(url_for('tutor.dashboard'))

@tutor_bp.route('/reject_request/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    if not current_user.is_tutor:
        return redirect(url_for('user.dashboard'))

    request_entry = TutorRequest.query.get_or_404(request_id)
    request_entry.status = "Rejected"

    db.session.flush()  # Ensure changes are recognized
    db.session.commit()

    flash('Request rejected.', 'danger')
    return redirect(url_for('tutor.dashboard'))

@tutor_bp.route('/view_resources')
@login_required
def view_resources():
    if not current_user.is_tutor:
        return redirect(url_for('user.dashboard'))
    
    # Get all resources uploaded by the tutor
    resources = Resource.query.filter_by(uploaded_by=current_user.id).all()
    
    return render_template('tutor/view_resource.html', resources=resources)


@tutor_bp.route('/delete_resource/<int:resource_id>', methods=['POST'])
@login_required
def delete_resource(resource_id):
    if not current_user.is_tutor:
        return redirect(url_for('user.dashboard'))

    resource = Resource.query.get_or_404(resource_id)

    # Ensure the resource belongs to the current tutor
    if resource.uploaded_by != current_user.id:
        flash("You don't have permission to delete this resource.", "danger")
        return redirect(url_for('tutor.view_resources'))

    # Remove file from server
    file_path = resource.file_path
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete from database
    db.session.delete(resource)
    db.session.commit()
    
    flash("Resource deleted successfully!", "success")
    return redirect(url_for('tutor.view_resources'))
