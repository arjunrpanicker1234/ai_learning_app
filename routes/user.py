from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, session
from flask_login import login_required, current_user
from models import db, Skill, Assessment, Resource, ChatSession, ChatMessage, Question, Tutor, User, TutorRequest
from services.llm_service import LLMService
from services.pdf_service import PDFService
import logging

user_bp = Blueprint('user', __name__, url_prefix='/user')
logging.basicConfig(level=logging.DEBUG)
llm_service = LLMService()
pdf_service = PDFService()

@user_bp.route('/send_message', methods=['POST'], endpoint='user_send_message')
@login_required
def send_message():
    try:
        session_id = request.form.get('session_id')
        message_content = request.form.get('message')
        is_user = request.form.get('is_user', 'true').lower() == 'true'
        logging.debug(f"Received message from user: {message_content}, session_id: {session_id}, is_user: {is_user}")

        session = ChatSession.query.get(session_id)
        if not session:
            error_message = f"Invalid session ID: {session_id}"
            logging.error(error_message)
            return jsonify({'error': error_message}), 400

        # Save user message
        user_msg = ChatMessage(
            session_id=session.id,
            is_user=True,
            content=message_content
        )
        db.session.add(user_msg)
        db.session.commit()
        logging.debug(f"Saved user message: {user_msg.content}")

        # Get relevant resources for context
        skill = Skill.query.get(session.skill_id)
        resources = Resource.query.filter_by(skill_id=session.skill_id).limit(3).all()
        context = "\n".join([r.content for r in resources if r.content])
        logging.debug(f"Context from resources: {context}")

        # Extract and chunk text from PDF files
        pdf_chunks = []
        for resource in resources:
            if resource.content_type == "pdf":
                pdf_chunks.extend(pdf_service.extract_and_chunk(resource.file_path))
        logging.debug(f"Extracted PDF chunks: {pdf_chunks}")

        # Combine the PDF chunks with the existing context
        context += "\n".join(pdf_chunks)

        # Generate AI response
        ai_response = llm_service.answer_question(skill.name, message_content, context)
        logging.debug(f"AI response: {ai_response}")

        # Save AI message
        ai_msg = ChatMessage(
            session_id=session.id,
            is_user=False,
            content=ai_response
        )
        db.session.add(ai_msg)
        db.session.commit()
        logging.debug(f"Saved AI message: {ai_msg.content}")

        return jsonify({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'content': user_msg.content,
                'timestamp': user_msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            },
            'ai_message': {
                'id': ai_msg.id,
                'content': ai_msg.content,
                'timestamp': ai_msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        logging.error(f"Error in send_message: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

def assessment_result(skill_id):
    # Fetch user's assessment result (dummy logic here)
    user_score = 4  # Example score

    flash(f"Your assessment score for {skill_id} is {user_score}/5", "success")
    
    return redirect(url_for('user.view_tutors', skill_id=skill_id))
@user_bp.route('/request_tutor/<int:tutor_id>/<int:skill_id>', methods=['POST'])
@login_required
def request_tutor(tutor_id, skill_id):
    tutor = User.query.filter_by(id=tutor_id, is_tutor=True).first()

    if not tutor:
        flash("Tutor not found!", "danger")
        return redirect(url_for('user.view_tutors', skill_id=skill_id))

    # Check for existing requests
    existing_request = TutorRequest.query.filter_by(
        user_id=current_user.id, tutor_id=tutor_id, skill_id=skill_id
    ).first()

    if existing_request:
        flash("You have already sent a request for this tutor.", "info")
        return redirect(url_for('user.view_tutors', skill_id=skill_id))

    # Create a new request
    new_request = TutorRequest(user_id=current_user.id, tutor_id=tutor_id, skill_id=skill_id, status="Pending")
    db.session.add(new_request)
    db.session.commit()

    flash("Tutor request sent! Please wait for approval.", "success")
    return redirect(url_for('user.view_tutors', skill_id=skill_id))
@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_tutor:
        return redirect(url_for('tutor.dashboard'))

    # Fetch user assessments
    user_assessments = Assessment.query.filter_by(user_id=current_user.id).all()
    
    # If no assessment, show available skills
    if not user_assessments:
        skills = Skill.query.all()
        return render_template('user/dashboard.html', skills=skills, show_assessment_prompt=True)

    # Fetch pending tutor requests
    pending_requests = TutorRequest.query.filter_by(user_id=current_user.id, status="Pending").all()

    # Fetch approved tutors
    approved_tutors = TutorRequest.query.filter_by(user_id=current_user.id, status="Approved").all()

    # Get assessed skills and proficiency levels
    assessed_skills = {
        a.skill_id: {"proficiency_level": a.proficiency_level, "score": a.score} for a in user_assessments
    }

    return render_template(
        'user/dashboard.html',
        skills=Skill.query.all(),
        assessed_skills=assessed_skills,
        pending_requests=pending_requests,
        approved_tutors=approved_tutors,
        show_assessment_prompt=False
    )


def load_questions_from_csv(skill_name):
    csv_file_path = os.path.join("static", "data", "questions.csv")  # Correct path

    questions = []
    try:
        with open(csv_file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["skill_name"].strip().lower() == skill_name.lower():
                    questions.append({
                        "question_text": row["question_text"],
                        "options": [row["option1"], row["option2"], row["option3"], row["option4"]],
                        "correct_answer": int(row["correct_option"]) - 1  # Convert to zero-based index
                    })
    except Exception as e:
        print(f"Error loading CSV file: {e}")

    return questions

@user_bp.route('/start_assessment/<int:skill_id>')
@login_required
def start_assessment(skill_id):
    skill = Skill.query.get_or_404(skill_id)

    # Fetch questions from CSV instead of the database
    questions = load_questions_from_csv(skill.name)

    if not questions:
        flash("No questions found for this skill.", "danger")
        return redirect(url_for('user.dashboard'))

    # Store questions in session
    session['assessment_questions'] = questions
    session['current_skill_id'] = skill_id

    return render_template('user/assessment.html', skill=skill, questions=questions, enumerate=enumerate)

@user_bp.route('/view_resources/<int:skill_id>')
@login_required
def view_resources(skill_id):
    skill = Skill.query.get_or_404(skill_id)

    # Fetch the most recent proficiency level from the user's assessment
    assessment = Assessment.query.filter_by(
        user_id=current_user.id,
        skill_id=skill_id
    ).order_by(Assessment.completed_at.desc()).first()

    proficiency = assessment.proficiency_level if assessment else 1  # Default to 1 if no assessment is found

    # Get resources matching or near the user's proficiency level (within +/- 1)
    resources = Resource.query.filter(
        Resource.skill_id == skill_id,
        db.func.abs(Resource.proficiency_level - proficiency) <= 1
    ).all()

    # Render resources page and check if assessment was taken
    return render_template('user/resources.html',
                           skill=skill,
                           proficiency=proficiency,
                           resources=resources,
                           assessment_taken=bool(assessment))

@user_bp.route('/submit_assessment', methods=['POST'])
@login_required
def submit_assessment():
    if 'assessment_questions' not in session:
        flash('Assessment session expired', 'danger')
        return redirect(url_for('user.dashboard'))
    
    questions = session.pop('assessment_questions')
    skill_id = session.pop('current_skill_id')

    correct_count = 0
    for i, q in enumerate(questions):
        user_answer = request.form.get(f"q{i}")
        if user_answer == q['options'][q['correct_answer']]:
            correct_count += 1

    proficiency_level = min(5, max(1, correct_count))

    # Save assessment result
    new_assessment = Assessment(
        user_id=current_user.id,
        skill_id=skill_id,
        proficiency_level=proficiency_level,
        score=correct_count
    )
    db.session.add(new_assessment)
    db.session.commit()

    flash(f"You scored {correct_count}/10 in {Skill.query.get(skill_id).name}.", "success")

    # Redirect to view tutors after assessment
    return redirect(url_for('user.view_tutors', skill_id=skill_id))
@user_bp.route('/tutors/<int:skill_id>')
@login_required
def view_tutors(skill_id):
    skill = Skill.query.get_or_404(skill_id)

    # Get tutors who uploaded resources
    tutors = (
        User.query
        .join(Resource, Resource.uploaded_by == User.id)
        .filter(Resource.skill_id == skill_id, User.is_tutor == True)
        .distinct()
        .all()
    )

    # Check if the user has sent a request for this skill
    existing_request = TutorRequest.query.filter_by(
        user_id=current_user.id, skill_id=skill_id
    ).first()

    return render_template(
        'user/tutor_list.html', skill=skill, tutors=tutors, existing_request=existing_request
    )


@user_bp.route('/debug_tutor_requests')
def debug_tutor_requests():
    requests = TutorRequest.query.all()
    return jsonify([
        {"user_id": r.user_id, "tutor_id": r.tutor_id, "skill_id": r.skill_id, "status": r.status}
        for r in requests
    ])


@user_bp.route('/ai_tutor/<int:skill_id>')
@login_required
def ai_tutor(skill_id):
    skill = Skill.query.get_or_404(skill_id)

    # Fetch approved tutor resources
    resources = Resource.query.filter_by(skill_id=skill_id).all()

    return redirect(url_for('user.start_chat', skill_id=skill_id))

@user_bp.route('/chat/<int:skill_id>')
@login_required
def start_chat(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    
    # Find or create chat session
    chat_session = ChatSession.query.filter_by(
        user_id=current_user.id,
        skill_id=skill_id
    ).order_by(ChatSession.created_at.desc()).first()
    
    if not chat_session:
        chat_session = ChatSession(
            user_id=current_user.id,
            skill_id=skill_id
        )
        db.session.add(chat_session)
        db.session.commit()
    
    messages = ChatMessage.query.filter_by(session_id=chat_session.id).order_by(ChatMessage.timestamp).all()
    
    return render_template('user/chat.html',
                          skill=skill,
                          session=chat_session,
                          messages=messages)

@user_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    session_id = request.form.get('session_id', type=int)
    message_content = request.form.get('message')
    
    if not session_id or not message_content:
        return jsonify({'error': 'Missing data'}), 400
    
    # Verify session belongs to user
    chat_session = ChatSession.query.get_or_404(session_id)
    if chat_session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        is_user=True,
        content=message_content
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # Get relevant resources for context
    skill = Skill.query.get(chat_session.skill_id)
    resources = Resource.query.filter_by(skill_id=chat_session.skill_id).limit(3).all()
    context = "\n".join([r.content for r in resources if r.content])
    
    # Generate AI response
    ai_response = llm_service.answer_question(skill.name, message_content, context)
    
    # Save AI message
    ai_msg = ChatMessage(
        session_id=session_id,
        is_user=False,
        content=ai_response
    )
    db.session.add(ai_msg)
    db.session.commit()
    
    return jsonify({
        'user_message': {
            'id': user_msg.id,
            'content': user_msg.content,
            'timestamp': user_msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        },
        'ai_message': {
            'id': ai_msg.id,
            'content': ai_msg.content,
            'timestamp': ai_msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    })