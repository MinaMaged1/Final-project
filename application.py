import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from datetime import datetime


app = Flask(__name__)


app.config["TEMPLATES_AUTO_RELOAD"] = True



@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")


EDIT = "off"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not email:
            return apology("missing email")
        if not password:
            return apology("missing password")
        if password != confirmation:
            return apology("the password don't match")
        emails = db.execute("SELECT email FROM users")
        for i in range(len(emails)):
            if email == emails[i]["email"]:
                return apology("used email")
        #if len(password) < 8:
            #return apology("the password is too short")
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (email, password) VALUES(?, ?)", email, hashed_password)
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["POST", "GET"])
def login():

    session.clear()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email:
            return apology("missing Email")
        if not password:
            return apology("must provide password")
        data = db.execute("SELECT * FROM users WHERE email=?", email)
        if len(data) < 1 or not check_password_hash(data[0]["password"], password):
            return apology("Invalid Email and/or password", 403)

        session["user_id"] = data[0]["id"]
        return redirect("/indexq")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/make", methods=["POST", "GET"])
@login_required
def make():
    if request.method == "POST":
        name = request.form.get("quiz_name")
        user_id = session.get("user_id")
        code = request.form.get("code")
        if not name:
            return apoloyg("missing name")
        if isinstance(int(code), int) == False:
            return apology("the code must be numeric")
        if not code or len(code) > 8 or len(code) < 8:
            return apology("less than min")
        db.execute("INSERT INTO quizzes (quiz_name, user_id, code) VALUES(?, ?, ?)", name, user_id, code)
        global QUIZ_ID
        global QUIZ_NAME
        QUIZ_NAME = name
        QUIZ_ID = int(code)

        return redirect("/questions")
    else:
        return render_template("make.html")


@app.route("/questions", methods=["post", "get"])
def questions():
    global EDIT
    if request.method == "POST":
        if not request.form.get("answer1_redirect"):
            question = request.form.get("question")
            answer1 = request.form.get("answer1")
            answer2 = request.form.get("answer2")
            answer3 = request.form.get("answer3")
            answer4 = request.form.get("answer4")
            answer = request.form.get("answer")
            print("1")
            quiz_id = db.execute("SELECT id FROM quizzes WHERE code=(?)", QUIZ_ID)
            quiz_id = quiz_id[0]["id"]
            p_questions = db.execute("SELECT question, number FROM question WHERE quiz_id=(?)", quiz_id)
            number = len(p_questions) + 1
            for i in range(len(p_questions)):
                if number == p_questions[i]["number"]:
                    number += 1
            db.execute("INSERT INTO question (quiz_id, question, answer1, answer2, answer3, answer4, the_answer, number) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            quiz_id, question, answer1, answer2, answer3, answer4, answer, number)
            return redirect("/indexq")
        else:
            if EDIT == "on":
                return redirect("/change")
            else:
                question = request.form.get("question_redirect")
                answer1 = request.form.get("answer1_redirect")
                answer2 = request.form.get("answer2_redirect")
                print(question, answer1)
                print("3")
                data = db.execute("SELECT * FROM question WHERE question=(?) AND answer1=(?) AND answer2=(?)", question, answer1, answer2)
                data2 = data[0]
                EDIT = "on"
                return render_template("questions_edit.html", data2=data2)

    else:
        quiz_id = db.execute("SELECT id FROM quizzes WHERE code=(?)", QUIZ_ID)
        quiz_id = quiz_id[0]["id"]
        questions = db.execute("SELECT * FROM question WHERE quiz_id=(?)", quiz_id)
        number = len(questions) + 1
        return render_template("questions.html", number=number)


@app.route("/indexq")
@login_required
def indexq():
    user_id = session.get("user_id")
    quizzes = db.execute("SELECT * FROM quizzes WHERE user_id=(?)", user_id)
    taken_quizzes = db.execute("SELECT * FROM take WHERE user_id=(?)", user_id)
    for quiz in taken_quizzes:
        quiz_id = quiz["quiz_id"]
        name = db.execute("SELECT quiz_name FROM quizzes WHERE id=(?)", quiz_id)
        name = name[0]["quiz_name"]
        quiz["quiz_id"] = name
    return render_template("indexq.html", quizzes=quizzes, takes=taken_quizzes)


@app.route("/edit", methods=["post", "get"])
@login_required
def edit():
    user_id = session.get("user_id")
    code = request.form.get("quiz")
    quiz_id = db.execute("SELECT id FROM quizzes WHERE code=(?)", code)
    global QUIZ_ID
    QUIZ_ID = code
    if len(quiz_id) >= 1:
        quiz_id = quiz_id[0]["id"]
    questions = db.execute("SELECT * FROM question WHERE quiz_id=(?) ORDER BY number", quiz_id)
    return render_template("edit.html", data=questions, quiz_id=quiz_id, code=code)


@app.route("/change", methods=["post", "get"])
@login_required
def change():
    quiz_id = request.form.get("quiz_id")
    print("2")
    question_number = request.form.get("question_number")
    print(quiz_id)
    print(question_number)
    question = request.form.get("question")
    print(question)
    answer1 = request.form.get("answer1")
    answer2 = request.form.get("answer2")
    answer3 = request.form.get("answer3")
    answer4 = request.form.get("answer4")
    answer = request.form.get("answer")
    print(answer4)
    return redirect("/indexq")


@app.route("/delete", methods=["post", "get"])
def delete():
    if request.form.get("quiz_delete") == "no":
        quiz_id = request.form.get("quiz_id")
        number = request.form.get("number")
        question_number = db.execute("SELECT question FROM question WHERE quiz_id=(?)", quiz_id)
        question_number = len(question_number)
        n = question_number - int(number)
        db.execute("DELETE FROM question WHERE quiz_id=(?) AND number=(?)", quiz_id, number)
        for i in range(n):
            new_number = i + int(number)
            db.execute("UPDATE question SET number=number-1 WHERE number=(?)", new_number)
        return redirect("/indexq")
    elif request.form.get("quiz_delete") == "yes":
        code = request.form.get("delete")
        quiz_id = db.execute("SELECT id FROM quizzes WHERE code=(?)", code)
        quiz_id = quiz_id[0]["id"]
        db.execute("DELETE FROM quizzes WHERE id=(?)", quiz_id)
        db.execute("DELETE FROM question WHERE quiz_id=(?)", quiz_id)
        return redirect("/indexq")


@app.route("/create", methods=["post", "get"])
def create():
    quiz_id = request.form.get("quiz_id")
    QUIZ_ID = request.form.get("code")
    questions = db.execute("SELECT * FROM question WHERE quiz_id=(?)", quiz_id)
    number = len(questions) + 1
    return redirect("/questions")


@app.route("/take", methods=["post", "get"])
@login_required
def take():
    if request.method == "POST":
        code = request.form.get("code")
        user_id = session.get("user_id")
        quiz_id = db.execute("SELECT id FROM quizzes WHERE code=(?)", code)
        quiz_id = quiz_id[0]["id"]
        questions = db.execute("SELECT * FROM question WHERE quiz_id=(?)", quiz_id)
        answers = db.execute("SELECT answer1, answer2, answer3, answer4 FROM question WHERE quiz_id=(?)", quiz_id)
        return render_template("take_quiz.html", questions=questions, quiz_id=quiz_id)
    else:
        return render_template("take_code.html")


@app.route("/review", methods=["post", "get"])
@login_required
def review():
    if request.method == "POST":
        user_id = session.get("user_id")
        quiz_id = request.form.get("quiz_id")
        questions = db.execute("SELECT number, the_answer FROM question WHERE quiz_id=(?)", quiz_id)
        n = 0
        for i in questions:
            question_id = "answer"+str(i["number"])
            answer = request.form.get(question_id)
            if answer == i["the_answer"]:
                n += 1
        all_question = len(questions)
        percentage = n/all_question * 100
        date_time = datetime.now()
        date = date_time.strftime("%Y-%m-%d")
        time = date_time.strftime("%H:%M:%S")
        db.execute("INSERT INTO take (quiz_id, take_time, take_date, user_id, score, total) VALUES(?, ?, ?, ?, ?, ?)",
        quiz_id, time, date, user_id, n, all_question)
        return render_template("score.html", score=n, length=all_question, percentage=percentage)


@app.route("/result", methods=["POST", "GET"])
@login_required
def result():
    code = request.form.get("result")
    quiz_id = db.execute("SELECT id FROM quizzes WHERE code=(?)", code)
    quiz_id = quiz_id[0]["id"]
    results = db.execute("SELECT * FROM take WHERE quiz_id=(?)", quiz_id)
    for result in results:
        user_id = result["user_id"]
        user_name = db.execute("SELECT email FROM users WHERE id=(?)", user_id)
        user_name = user_name[0]["email"]
        result["user_id"] = user_name
    return render_template("results.html", results=results)


#@app.route("/reset password")