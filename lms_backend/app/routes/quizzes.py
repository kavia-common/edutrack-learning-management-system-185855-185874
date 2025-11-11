from flask import request
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Quiz, Question, QuizOption, Submission
from .. import db
from ..security import require_roles
from ..services import grade_quiz

blp = Blueprint(
    "Quizzes",
    "quizzes",
    url_prefix="/api/quizzes",
    description="Quiz creation and submission endpoints",
)


@blp.route("/course/<int:course_id>")
class QuizList(MethodView):
    """
    PUBLIC_INTERFACE
    List or create quizzes under a course.
    """
    def get(self, course_id: int):
        quizzes = Quiz.query.filter_by(course_id=course_id).all()
        return [{"id": q.id, "title": q.title, "passing_score": q.passing_score} for q in quizzes]

    @jwt_required()
    @require_roles(["instructor", "admin"])
    def post(self, course_id: int):
        data = request.get_json() or {}
        q = Quiz(course_id=course_id, title=data.get("title", "Untitled Quiz"), passing_score=int(data.get("passing_score", 70)))
        db.session.add(q)
        db.session.commit()
        return {"id": q.id, "message": "Created"}, 201


@blp.route("/<int:quiz_id>/questions")
class QuizQuestions(MethodView):
    """
    PUBLIC_INTERFACE
    Add questions with options; expects:
        {
          "text": "Q1?",
          "options": [{"text": "A"}, {"text": "B"}],
          "correct_index": 0
        }
    """
    @jwt_required()
    @require_roles(["instructor", "admin"])
    def post(self, quiz_id: int):
        data = request.get_json() or {}
        text = data.get("text")
        options = data.get("options", [])
        correct_index = int(data.get("correct_index", 0))
        q = Question(quiz_id=quiz_id, text=text)
        db.session.add(q)
        db.session.flush()
        option_models = []
        for opt in options:
            o = QuizOption(question_id=q.id, text=opt.get("text"))
            db.session.add(o)
            db.session.flush()
            option_models.append(o)
        if option_models:
            q.correct_option_id = option_models[min(max(correct_index, 0), len(option_models) - 1)].id
        db.session.commit()
        return {"id": q.id, "message": "Question added"}, 201


@blp.route("/<int:quiz_id>/submit")
class QuizSubmit(MethodView):
    """
    PUBLIC_INTERFACE
    Submit quiz answers: { "answers": { "question_id": "option_id", ... } }
    Returns score and whether passed.
    """
    @jwt_required()
    def post(self, quiz_id: int):
        data = request.get_json() or {}
        answers = {int(k): int(v) for k, v in (data.get("answers") or {}).items()}
        quiz = Quiz.query.get_or_404(quiz_id)
        score = grade_quiz(quiz, answers)
        ident = get_jwt_identity()
        sub = Submission(user_id=ident.get("id"), quiz_id=quiz_id, score=score)
        db.session.add(sub)
        db.session.commit()
        return {"score": score, "passed": score >= quiz.passing_score}
