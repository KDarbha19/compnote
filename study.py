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

#@study_bp.route('/generate')