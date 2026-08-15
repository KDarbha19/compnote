from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db, StudySet, Flashcard, QuizResult
from ai import generate_flashcards, generate_quiz, generate_title
import pypdf
import io

study_bp = Blueprint('study', __name__)

#Dashboard
@study_bp.route('/')
@study_bp.route('/dashboard')
@login_required
def dashboard():
    #Main page, shows all study sets belonging to the logged in user
    study_sets = StudySet.query.filter_by(user_id=current_user.id)\
        .order_by(StudySet.created_at.desc()).all()

    #Build stats for each study set to show on dashboard
    sets_with_stats = []
    for s in study_sets:
        latest_quiz = QuizResult.query.filter_by(study_set_id=s.id)\
            .order_by(QuizResult.taken_at.desc()).first()

        sets_with_stats.append({
            'study_set' : s,
            'card_count' : len(s.flashcards),
            'quiz_count' : len(s.quiz_results),
            'latest_score' : f"{latest_quiz.score}/{latest_quiz.total}" if latest_quiz else None
        })

    return render_template('dashboard.html', sets = sets_with_stats)

#Create Study Set
@study_bp.route('/create')
@login_required
def create():
    #Page where user uploads PDF or pastes text
    return render_template('create.html')

@study_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """
    Receives text or PDF, generates flashcards, saves to db
    Return JSON so frontend can show loading state
    """

    text = ''

    #PDF Upload
    if 'pdf' in request.files and request.files['pdf'].filename:
        pdf_file = request.files['pdf']
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_file.read()))
            for page in reader.pages:
                text += page.extract_text() + '\n'
        except Exception as e:
            return jsonify({'error': f'Could not read PDF: {str(e)}'}), 400

    elif request.form.get('text'):
        text = request.form.get('text').strip()

    else:
        return jsonify({'error' : 'Please upload a PDF or paste text!'}), 400

    if len(text) < 100:
        return jsonify({'error' : 'Text is too short! Please provide more content.'}), 400

    try:
        #Generate title and flashcards
        title = generate_title(text)
        cards_data = generate_flashcards(text, num_cards=10)

        if not cards_data:
            return jsonify({'error' : 'Could not generate flashcards. Please try again with different content.'}), 500

        #Save study set to db
        study_set = StudySet(
            title = title,
            source_text = text[:5000],
            user_id = current_user.id
        )
        db.session.add(study_set)
        db.session.flush() #get the study_set.id before committing

        #Save each flashcard
        for card in cards_data:
            flashcard = Flashcard(
                question = card['question'],
                answer = card['answer'],
                study_set_id = study_set.id
            )
            db.session.add(flashcard)

        db.session.commit()
        return jsonify({'redirect' : url_for('study.view_set', set_id = study_set.id)})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error' : f'Generation failed: {str(e)}'}), 500

#View Study Set
@study_bp.route('/set/<int:set_id>')
@login_required
def view_set(set_id):
    #Show flashcards for a specific study set
    study_set = StudySet.query.filter_by(
        id = set_id,
        user_id = current_user.id #user can only see their own sets
    ).first_or_404()

    cards_data = [{
        'id': card.id,
        'question': card.question,
        'answer': card.answer
    } for card in study_set.flashcards]

    return render_template('study.html', study_set=study_set, cards_data=cards_data)

#Quiz
@study_bp.route('/quiz/<int:set_id>')
@login_required
def quiz(set_id):
    #Generates and shows a quiz for a study set
    study_set = StudySet.query.filter_by(
        id = set_id,
        user_id = current_user.id
    ).first_or_404()

    questions = generate_quiz(study_set.source_text, num_questions=5)

    if not questions:
        flash('Could not generate quiz, try again later.', 'error')
        return redirect(url_for('study.view_set', set_id=set_id))

    return render_template('quiz.html', study_set = study_set, questions = questions)

@study_bp.route('/quiz/<int:set_id>/submit', methods=['POST'])
@login_required
def submit_quiz(set_id):
    #Recieves quiz answers, scores them, saves result
    study_set = StudySet.query.filter_by(
        id = set_id,
        user_id = current_user.id
    ).first_or_404()

    data = request.get_json()
    answers = data.get('answers', []) #List of selected option indices
    questions = data.get('questions', []) #list of question dicts(question + correct answer)

    if not answers or not questions:
        return jsonify({'error' : 'No answers submitted!'}), 400

    #Score quiz
    score = 0
    results = []
    for i, question in enumerate(questions):
        if i < len(answers):
            correct = question['correct_index']
            selected = answers[i]
            is_correct = selected == correct
            if is_correct:
                score += 1
            results.append({
                'question' : question['question'],
                'options' : question['options'],
                'correct_index' : correct,
                'selected_index' : selected,
                'is_correct' : is_correct
            })

    #Save results to db
    quiz_result = QuizResult(
        score = score,
        total = len(questions),
        study_set_id = study_set.id
    )
    db.session.add(quiz_result)
    db.session.commit()

    return jsonify({
        'score' : score,
        'total' : len(questions),
        'results' : results
    })

#Update flashcard difficulty
@study_bp.route('/card/<int:card_id>/difficulty', methods=['POST'])
@login_required
def update_difficulty(card_id):
    """
    When reviewing flashcards user marks each as easy, med, hard
    This updates the card's difficulty in the database for spaced repetition
    """

    card = Flashcard.query.get_or_404(card_id)

    #Make sure the card belongs to the current user
    if card.study_set.user_id != current_user.id:
        return jsonify({'error' : 'Unauthorized'}), 403

    difficulty = request.get_json().get('difficulty')
    if difficulty not in ('easy', 'medium', 'hard'):
        return jsonify({'error' : 'Invalid difficulty'}), 400

    card.difficulty = difficulty
    card.review_count += 1
    db.session.commit()

    return jsonify({'success' : True})

#Delete study set
@study_bp.route('/set/<int:set_id>/delete', methods=['POST'])
@login_required
def delete_set(set_id):
    #Delete study set and all flashcards + quiz results associated
    study_set = StudySet.query.filter_by(
        id = set_id,
        user_id = current_user.id
    ).first_or_404()

    db.session.delete(study_set)
    db.session.commit()

    return redirect(url_for('study.dashboard'))

    