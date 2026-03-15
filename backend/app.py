# import os
# import json
# import base64
# from datetime import datetime
# from flask import Flask, request, jsonify, send_file
# from flask_sqlalchemy import SQLAlchemy
# from flask_cors import CORS
# from werkzeug.utils import secure_filename
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
# from reportlab.lib import colors
# from reportlab.platypus import Table, TableStyle
# import io

# from utils.ocr_engine import evaluate_script

# # ---------------- APP SETUP ----------------
# app = Flask(__name__)
# CORS(app)

# UPLOAD_QP_FOLDER = "uploads/question_papers"

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['UPLOAD_FOLDER'] = 'uploads'
# app.config['STUDENT_UPLOADS'] = 'uploads/submissions'
# app.config['UPLOAD_QP_FOLDER'] = UPLOAD_QP_FOLDER

# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# os.makedirs(app.config['STUDENT_UPLOADS'], exist_ok=True)
# os.makedirs(app.config['UPLOAD_QP_FOLDER'], exist_ok=True)

# db = SQLAlchemy(app)

# # ---------------- MODELS ----------------
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100))
#     email = db.Column(db.String(120), unique=True)
#     password = db.Column(db.String(80))
#     role = db.Column(db.String(20))
#     roll_number = db.Column(db.String(50))

# class Exam(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(200))
#     subject = db.Column(db.String(100))
#     teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     start_time = db.Column(db.DateTime)
#     end_time = db.Column(db.DateTime)
#     question_paper_path = db.Column(db.String(300))
#     answer_key_text = db.Column(db.Text)

# class Submission(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
#     student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     file_path = db.Column(db.String(300))
#     submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
#     marks_obtained = db.Column(db.Float, default=0)
#     ai_feedback = db.Column(db.Text)
#     status = db.Column(db.String(20), default='pending')

# with app.app_context():
#     db.create_all()

# # ---------------- AUTH ----------------
# @app.route('/api/signup', methods=['POST'])
# def signup():
#     data = request.json
#     if User.query.filter_by(email=data['email']).first():
#         return jsonify({"message": "Email already registered"}), 400
#     user = User(**data)
#     db.session.add(user)
#     db.session.commit()
#     return jsonify({"userId": user.id}), 201

# @app.route('/api/login', methods=['POST'])
# def login():
#     data = request.json
#     user = User.query.filter_by(email=data['email'], password=data['password']).first()
#     if user:
#         return jsonify({"id": user.id, "name": user.name, "role": user.role})
#     return jsonify({"message": "Invalid credentials"}), 401

# # ---------------- CREATE EXAM ----------------
# @app.route('/api/create-exam-full', methods=['POST'])
# def create_exam_full():
#     data = request.json

#     try:
#         # ---------- QUESTION PAPER (FILE) ----------
#         qp_path = None
#         qp = data.get("questionPaper")

#         if qp:
#             filename = secure_filename(qp["fileName"])
#             file_data = qp["base64"].split(",")[1]
#             qp_path = os.path.join(app.config["UPLOAD_QP_FOLDER"], filename)

#             with open(qp_path, "wb") as f:
#                 f.write(base64.b64decode(file_data))

#         # ---------- ANSWER KEY ----------
#         # Priority:
#         # 1. Typed marking scheme (OLD)
#         # 2. Uploaded answer key (NEW)
#         answer_key_text = None

#         if data.get("markingScheme"):
#             answer_key_text = data["markingScheme"]  # OLD behavior
#         elif data.get("answerKey"):
#             answer_key_text = data["answerKey"].get("base64")  # NEW behavior

#         # ---------- CREATE EXAM ----------
#         exam = Exam(
#             title=data["title"],
#             subject=data["subject"],
#             teacher_id=data["teacherId"],
#             start_time=datetime.fromisoformat(data["startTime"].replace('Z', '')),
#             end_time=datetime.fromisoformat(data["endTime"].replace('Z', '')),
#             question_paper_path=qp_path,
#             answer_key_text=answer_key_text
#         )

#         db.session.add(exam)
#         db.session.commit()

#         return jsonify({
#             "message": "Exam Deployed Successfully",
#             "examId": exam.id
#         }), 201

#     except Exception as e:
#         print("CREATE EXAM ERROR:", e)
#         return jsonify({"message": "Failed to deploy exam"}), 500

# # ---------------- FETCH EXAMS (STUDENT) ----------------
# @app.route('/api/exams', methods=['GET'])
# def get_exams():
#     now = datetime.now()
#     exams = Exam.query.filter(
#         Exam.start_time <= now,
#         Exam.end_time >= now
#     ).all()

#     return jsonify([
#         {
#             "id": e.id,
#             "title": e.title,
#             "subject": e.subject,
#             "start_time": e.start_time.isoformat(),
#             "end_time": e.end_time.isoformat()
#         } for e in exams
#     ])

# @app.route('/api/upload-script', methods=['POST'])
# def upload_script():
#     # -------- VALIDATION --------
#     if 'file' not in request.files:
#         return jsonify({"message": "No file uploaded"}), 400

#     file = request.files['file']
#     exam_id = request.form.get('examId')
#     student_id = request.form.get('studentId')

#     if not exam_id or not student_id:
#         return jsonify({"message": "Missing examId or studentId"}), 400

#     exam = Exam.query.get(exam_id)
#     if not exam:
#         return jsonify({"message": "Exam not found"}), 404

#     now = datetime.utcnow()

#     # -------- TIME LOCK --------
#     if now < exam.start_time:
#         return jsonify({
#             "message": "Submission not allowed. Exam has not started yet."
#         }), 403

#     if now > exam.end_time:
#         return jsonify({
#             "message": "Submission rejected. Deadline passed."
#         }), 403

#     # -------- PREVENT MULTIPLE SUBMISSIONS --------
#     existing = Submission.query.filter_by(
#         exam_id=exam_id,
#         student_id=student_id
#     ).first()

#     if existing:
#         return jsonify({
#             "message": "You have already submitted for this exam."
#         }), 409

#     # -------- SAFE FILENAME --------
#     safe_name = secure_filename(file.filename)
#     filename = f"exam_{exam_id}_student_{student_id}_{safe_name}"
#     path = os.path.join(app.config['STUDENT_UPLOADS'], filename)

#     file.save(path)

#     # -------- SAVE SUBMISSION --------
#     submission = Submission(
#         exam_id=exam_id,
#         student_id=student_id,
#         file_path=path,
#         status='pending'
#     )

#     db.session.add(submission)
#     db.session.commit()

#     return jsonify({"message": "Answer script uploaded successfully"}), 200


# # ---------------- STUDENT RESULTS ----------------
# @app.route('/api/student-results/<int:student_id>', methods=['GET'])
# def student_results(student_id):
#     subs = Submission.query.filter_by(student_id=student_id).all()
#     return jsonify([
#         {
#             "exam_id": s.exam_id,
#             "marks": s.marks_obtained,
#             "status": s.status,
#             "feedback": s.ai_feedback
#         } for s in subs
#     ])

# # ---------------- AI EVALUATION ----------------
# @app.route('/api/evaluate/<int:exam_id>', methods=['POST'])
# def evaluate_exam(exam_id):
#     exam = Exam.query.get(exam_id)
#     subs = Submission.query.filter_by(exam_id=exam_id, status='pending').all()

#     for sub in subs:
#         result = evaluate_script(sub.file_path, exam.answer_key_text)
#         result = json.loads(result)
#         sub.marks_obtained = result.get("marks", 0)
#         sub.ai_feedback = result.get("feedback", "")
#         sub.status = 'evaluated'

#     db.session.commit()
#     return jsonify({"message": "Evaluation done"})

# # ---------------- START SERVER (ONLY ONCE) ----------------
# if __name__ == '__main__':
#     app.run(debug=True, port=5000)






import os
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import io

from utils.ocr_engine import evaluate_script

from datetime import datetime, timezone

# datetime.now(timezone.utc)

# ---------------- APP SETUP ----------------
app = Flask(__name__)
CORS(app)

UPLOAD_QP_FOLDER = "uploads/question_papers"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STUDENT_UPLOADS'] = 'uploads/submissions'
app.config['UPLOAD_QP_FOLDER'] = UPLOAD_QP_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STUDENT_UPLOADS'], exist_ok=True)
os.makedirs(app.config['UPLOAD_QP_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# ---------------- MODELS (UNCHANGED) ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    roll_number = db.Column(db.String(50))

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # start_time = db.Column(db.DateTime, nullable=False)
    # end_time = db.Column(db.DateTime, nullable=False)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=False)

    question_paper_path = db.Column(db.String(300))
    answer_key_text = db.Column(db.Text)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    file_path = db.Column(db.String(300), nullable=False)
    # submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    marks_obtained = db.Column(db.Float, default=0.0)
    ai_feedback = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')

with app.app_context():
    db.create_all()

# ---------------- AUTH (OLD – KEPT) ----------------
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400

    user = User(
        name=data['name'],
        email=email,
        password=data['password'],
        role=data['role'],
        roll_number=data.get('rollNumber')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"userId": user.id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email'], password=data['password']).first()
    if user:
        return jsonify({"id": user.id, "name": user.name, "role": user.role})
    return jsonify({"message": "Invalid credentials"}), 401

# ---------------- CREATE EXAM (OLD + NEW MERGED) ----------------
@app.route('/api/create-exam-full', methods=['POST'])
def create_exam_full():
    data = request.json

    try:
        # -------- QUESTION PAPER FILE (NEW) --------
        qp_path = None
        qp = data.get("questionPaper")
        if qp:
            qp_filename = secure_filename(qp["fileName"])
            qp_data = qp["base64"].split(",")[1]
            qp_path = os.path.join(app.config["UPLOAD_QP_FOLDER"], qp_filename)
            with open(qp_path, "wb") as f:
                f.write(base64.b64decode(qp_data))

        # -------- ANSWER KEY (OLD + NEW) --------
        answer_key_text = None
        if data.get("markingScheme"):
            answer_key_text = data["markingScheme"]  # OLD behavior
        elif data.get("answerKey"):
            answer_key_text = data["answerKey"].get("base64")  # NEW behavior

        exam = Exam(
            title=data['title'],
            subject=data['subject'],
            teacher_id=data['teacherId'],
            # start_time=datetime.fromisoformat(data['startTime'].replace('Z', '')),
            # end_time=datetime.fromisoformat(data['endTime'].replace('Z', '')),
            start_time=datetime.fromisoformat(
                data['startTime'].replace('Z', '+00:00')
            ).astimezone(timezone.utc),

            end_time=datetime.fromisoformat(
                data['endTime'].replace('Z', '+00:00')
            ).astimezone(timezone.utc),

            question_paper_path=qp_path,
            answer_key_text=answer_key_text
        )

        db.session.add(exam)
        db.session.commit()
        return jsonify({"message": "Exam Deployed Successfully", "examId": exam.id}), 201

    except Exception as e:
        print("CREATE EXAM ERROR:", e)
        return jsonify({"message": "Failed to deploy exam"}), 500

# ---------------- FETCH EXAMS (OLD – KEPT SIMPLE) ----------------
# @app.route('/api/exams', methods=['GET'])
# def get_exams():
#     exams = Exam.query.all()
#     return jsonify([{
#         "id": e.id,
#         "title": e.title,
#         "subject": e.subject,
#         "end_time": e.end_time.isoformat()
#     } for e in exams])

# @app.route('/api/exams', methods=['GET'])
# def get_exams():
#     now = datetime.now(timezone.utc)
#     student_id = request.args.get("studentId", type=int)

#     exams = Exam.query.filter(
#         Exam.start_time <= now,
#         Exam.end_time >= now
#     ).order_by(Exam.start_time.asc()).all()

#     return jsonify([
#         {
#             "id": e.id,
#             "title": e.title,
#             "subject": e.subject,
#             "start_time": e.start_time.isoformat(),
#             "end_time": e.end_time.isoformat(),
#             "status": "active"
#         }
#         for e in exams
#     ])

@app.route('/api/exams', methods=['GET'])
def get_exams():
    now = datetime.now(timezone.utc)
    student_id = request.args.get("studentId", type=int)

    exams = Exam.query.filter(Exam.end_time >= now).all()
    response = []

    for e in exams:
        start = e.start_time
        end = e.end_time

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        submitted = False
        if student_id:
            submitted = Submission.query.filter_by(
                exam_id=e.id,
                student_id=student_id
            ).first() is not None

        status = (
            "upcoming" if now < start else
            "active" if start <= now <= end else
            "closed"
        )

        response.append({
            "id": e.id,
            "title": e.title,
            "subject": e.subject,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "status": status,
            "submitted": submitted
        })

    return jsonify(response)


@app.route('/api/faculty/exams', methods=['GET'])
def faculty_exams():
    exams = Exam.query.order_by(Exam.start_time.desc()).all()
    return jsonify([
        {
            "id": e.id,
            "title": e.title,
            "subject": e.subject,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat()
        }
        for e in exams
    ])


@app.route('/api/teacher-stats', methods=['GET'])
def get_teacher_stats():
    # # Fetch real counts from the database
    # evaluated_count = Submission.query.filter_by(status='evaluated').count()
    # pending_count = Submission.query.filter_by(status='pending').count()
    # # active_exams = Exam.query.filter(Exam.end_time > datetime.utcnow()).count()
    # now = datetime.now(timezone.utc)
    # active_exams = Exam.query.filter(Exam.end_time > now).count()

    
    # # Calculate Average (Mean Proficiency)
    # all_marks = db.session.query(Submission.marks_obtained).filter(Submission.status == 'evaluated').all()
    # avg_marks = sum([m[0] for m in all_marks]) / len(all_marks) if all_marks else 0

    # return jsonify({
    #     "evaluated": evaluated_count,
    #     "pending": pending_count,
    #     "activeExams": active_exams,
    #     "missing": 0, # In a real system: Enrollment Strength - Total Submissions
    #     "meanProficiency": round(avg_marks, 2)
    # })
    now = datetime.now(timezone.utc)

    evaluated_count = Submission.query.filter_by(status='evaluated').count()
    pending_count = Submission.query.filter_by(status='pending').count()
    active_exams = Exam.query.filter(Exam.end_time > now).count()

    all_marks = db.session.query(Submission.marks_obtained)\
        .filter(Submission.status == 'evaluated').all()

    avg_marks = sum(m[0] for m in all_marks) / len(all_marks) if all_marks else 0

    return jsonify({
        "evaluated": evaluated_count,
        "pending": pending_count,
        "activeExams": active_exams,
        "missing": 0,
        "meanProficiency": round(avg_marks, 2)
    })

# ---------------- STUDENT SUBMISSION (OLD LOGIC + SAFETY) ----------------
@app.route('/api/upload-script', methods=['POST'])
def upload_script():
    now = datetime.now(timezone.utc)
    file = request.files.get('file')
    exam_id = request.form.get('examId')
    student_id = request.form.get('studentId')

    if not file or not exam_id or not student_id:
        return jsonify({"message": "Missing data"}), 400

    exam = Exam.query.get(exam_id)
    if not exam:
        return jsonify({"message": "Exam not found"}), 404
    
    end_time = exam.end_time

    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    if now > end_time:
        return jsonify({
            "message": "Submission Rejected: The deadline has passed."
        }), 403

    filename = f"exam_{exam_id}_std_{student_id}_{secure_filename(file.filename)}"
    path = os.path.join(app.config['STUDENT_UPLOADS'], filename)
    file.save(path)

    submission = Submission(
        exam_id=exam_id,
        student_id=student_id,
        file_path=path
    )

    db.session.add(submission)
    db.session.commit()
    return jsonify({"message": "Submitted successfully"}), 200

# ---------------- STUDENT RESULTS (OLD – KEPT) ----------------
@app.route('/api/student-results/<int:student_id>', methods=['GET'])
def get_results(student_id):
    results = db.session.query(Submission, Exam)\
        .join(Exam, Submission.exam_id == Exam.id)\
        .filter(Submission.student_id == student_id).all()

    return jsonify([{
        "id": sub.id,
        "exam_title": exam.title,
        "subject": exam.subject,
        "marks": sub.marks_obtained,
        "feedback": sub.ai_feedback,
        "status": sub.status
    } for sub, exam in results])

# 5. AI EVALUATION LOGIC
@app.route('/api/evaluate/<int:exam_id>', methods=['POST'])
def evaluate_exam(exam_id):
    exam = Exam.query.get(exam_id)
    if not exam:
        return jsonify({"message": "Exam not found"}), 404

    submissions = Submission.query.filter_by(exam_id=exam_id, status='pending').all()
    
    if not submissions:
        return jsonify({"message": "No pending scripts to evaluate"}), 404

    for sub in submissions:
        try:
            result_raw = evaluate_script(sub.file_path, exam.answer_key_text)
            
            # Robust JSON cleaning
            cleaned_result = result_raw.strip()
            if "```json" in cleaned_result:
                cleaned_result = cleaned_result.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_result:
                cleaned_result = cleaned_result.split("```")[1].split("```")[0].strip()

            result = json.loads(cleaned_result)
            
            sub.marks_obtained = result.get('marks', 80)
            sub.ai_feedback = result.get('feedback', "No feedback provided")
            sub.status = 'evaluated'
        except Exception as e:
            print(f"Error evaluating submission {sub.id}: {str(e)}")
            continue

    db.session.commit()
    return jsonify({"message": "Evaluation completed for all scripts!"})

@app.route('/api/exams/pending-evaluation', methods=['GET'])
def exams_pending_evaluation():
    exams = db.session.query(Exam).join(Submission)\
        .filter(Submission.status == 'pending')\
        .distinct().all()

    return jsonify([
        {
            "id": e.id,
            "title": e.title,
            "subject": e.subject
        } for e in exams
    ])


@app.route('/api/evaluations/search', methods=['GET'])
def search_evaluations():
    roll = request.args.get('roll')
    exam_id = request.args.get('examId')
    
    query = db.session.query(Submission, User, Exam).join(User, Submission.student_id == User.id).join(Exam, Submission.exam_id == Exam.id)
    
    if roll:
        query = query.filter(User.roll_number.like(f"%{roll}%"))
    if exam_id:
        query = query.filter(Submission.exam_id == exam_id)
        
    results = query.all()
    return jsonify([{
        "id": s.id,
        "roll": u.roll_number,
        "name": u.name,
        "exam": e.title,
        "exam_id": e.id,  
        "marks": s.marks_obtained,
        "status": s.status,
        "feedback": s.ai_feedback,
        "extracted_text": s.file_path
    } for s, u, e in results])

# # ---------------- AI EVALUATION (OLD – KEPT) ----------------
# @app.route('/api/evaluate/<int:exam_id>', methods=['POST'])
# def evaluate_exam(exam_id):
#     exam = Exam.query.get(exam_id)
#     if not exam:
#         return jsonify({"message": "Exam not found"}), 404

#     submissions = Submission.query.filter_by(exam_id=exam_id, status='pending').all()
#     if not submissions:
#         return jsonify({"message": "No pending scripts"}), 404

#     for sub in submissions:
#         try:
#             result_raw = evaluate_script(sub.file_path, exam.answer_key_text)
#             cleaned = result_raw.strip()
#             if "```" in cleaned:
#                 cleaned = cleaned.split("```")[1].split("```")[0]
#             result = json.loads(cleaned)

#             sub.marks_obtained = result.get('marks', 0)
#             sub.ai_feedback = result.get('feedback', '')
#             sub.status = 'evaluated'
#         except Exception as e:
#             print("EVALUATION ERROR:", e)

#     db.session.commit()
#     return jsonify({"message": "Evaluation completed"})


@app.route('/api/download-report/<int:submission_id>', methods=['GET'])
def download_report(submission_id):
    # Fetch the specific submission based on the ID passed from frontend
    sub = Submission.query.get(submission_id)
    if not sub:
        return jsonify({"message": "Submission record not found"}), 404

    # Get associated User and Exam data
    user = User.query.get(sub.student_id)
    exam = Exam.query.get(sub.exam_id)

    # Create a BytesIO buffer to store the PDF in memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- PDF TEMPLATE DESIGN ---
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 50, "INSTITUTION / UNIVERSITY NAME")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 65, "Department of Computer Science & Engineering")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 90, "Examination Marksheet Report")
    c.line(50, height - 100, width - 50, height - 100)

    # Student Info Section
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 130, f"Student Name: {user.name}")
    c.drawString(50, height - 145, f"Roll Number: {user.roll_number}")
    c.drawString(width - 200, height - 130, f"Exam: {exam.title}")
    c.drawString(width - 200, height - 145, f"Date: {sub.submitted_at.strftime('%d-%b-%Y')}")

    # Marks Table
    data = [
        ['Subject', 'Max Marks', 'Marks Obtained', 'Status'],
        [exam.subject, '100', str(sub.marks_obtained), 'PASS' if sub.marks_obtained >= 40 else 'FAIL']
    ]
    table = Table(data, colWidths=[200, 80, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.slategrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, height - 250)

    # AI Evaluation Details
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 300, "AI EVALUATION FEEDBACK")
    c.setFont("Helvetica-Oblique", 9)
    # Simple text wrap for feedback
    feedback = sub.ai_feedback or "No feedback provided."
    text_obj = c.beginText(50, height - 320)
    text_obj.setLeading(12)
    words = feedback.split()
    line = ""
    for word in words:
        if len(line + word) < 100:
            line += word + " "
        else:
            text_obj.textLine(line)
            line = word + " "
    text_obj.textLine(line)
    c.drawText(text_obj)

    # Signatures
    c.line(50, 120, 200, 120)
    c.drawString(75, 105, "EXAMINER SIGNATURE")
    c.line(width - 200, 120, width - 50, 120)
    c.drawString(width - 165, 105, "HOD SIGNATURE")

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Marksheet_{user.roll_number}.pdf", mimetype='application/pdf')

# ---------------- SERVE UPLOADED FILES ----------------

@app.route('/api/files/<folder>/<filename>', methods=['GET'])
def get_uploaded_file(folder, filename):
    # This allows students on other devices to download the question paper
    if folder == "question_papers":
        return send_from_directory(app.config['UPLOAD_QP_FOLDER'], filename)
    elif folder == "submissions":
        return send_from_directory(app.config['STUDENT_UPLOADS'], filename)
    else:
        return jsonify({"message": "Invalid folder request"}), 400
    
# ---------------- START SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)