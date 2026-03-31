
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from functools import wraps
from random import Random
from datetime import datetime, timedelta
import re
import math

app = Flask(__name__)
app.secret_key = "aqbobek-smart-portal-secret"

SUBJECTS = [
    "Математика",
    "Физика",
    "Химия",
    "Английский язык",
    "Казахский язык",
    "Русский язык",
    "Всемирная история",
    "История Казахстана",
    "Основы права",
    "География",
]

SUBJECT_ICONS = {
    "Математика": "calculate",
    "Физика": "science",
    "Химия": "biotech",
    "Английский язык": "language",
    "Казахский язык": "translate",
    "Русский язык": "text_fields",
    "Всемирная история": "public",
    "История Казахстана": "temple_buddhist",
    "Основы права": "gavel",
    "География": "explore",
}

SUBJECT_WEAKNESS_HOMEWORK = {
    "Математика": "Решить 6 задач на тригонометрию и 4 задачи на производную.",
    "Физика": "Решить 5 задач на импульс, силу и взаимодействие тел.",
    "Химия": "Составить 3 уравнения реакций и заполнить таблицу по строению вещества.",
    "Английский язык": "Выучить 12 слов, прочитать текст и ответить на 5 вопросов.",
    "Казахский язык": "Повторить синтаксис и написать 8 предложений с разными типами связи.",
    "Русский язык": "Повторить пунктуацию и вставить знаки препинания в 10 предложений.",
    "Всемирная история": "Составить хронологию событий XX века в 2 блоках.",
    "История Казахстана": "Сделать конспект по теме Алаш Орда и ответить на 7 вопросов.",
    "Основы права": "Разобрать 5 ситуационных задач по Конституции и правам граждан.",
    "География": "Нанести на карту 5 объектов и объяснить особенности климата региона.",
}

ROLE_LABELS = {
    "student": "Ученик",
    "teacher": "Учитель",
}

PROFILE_PRESETS = {
    "high": {
        "avg": 4.75,
        "spread": [5, 5, 5, 4, 5, 4],
        "streak": 8,
        "sleep": 7,
        "manual_xp": 80,
        "manual_points": 40,
        "coins_bonus": 20,
    },
    "medium": {
        "avg": 4.15,
        "spread": [5, 4, 4, 4, 3, 5],
        "streak": 4,
        "sleep": 6,
        "manual_xp": 30,
        "manual_points": 15,
        "coins_bonus": 10,
    },
    "risk": {
        "avg": 3.45,
        "spread": [4, 3, 4, 3, 2, 4],
        "streak": 1,
        "sleep": 5,
        "manual_xp": 0,
        "manual_points": 0,
        "coins_bonus": 0,
    },
}

TEACHER_LOGIN = "teacher.aqbobek"
TEACHER_PASSWORD = "Teach2026!"
TEACHER_NAME = "Айжан Тулеубекова"

DEMO_STUDENTS = [
    ("Алихан", "Сагындыков", "alikhan.sagyndykov", "Aqbo2026!", "high", "10 А"),
    ("Дана", "Нуртаева", "dana.nurtaeva", "Dana2026!", "high", "10 А"),
    ("Айбек", "Жумабаев", "aibek.zhumabayev", "Aibek2026!", "medium", "10 Б"),
    ("Аружан", "Серикқызы", "aruzhan.serikkyzy", "Aru2026!", "high", "10 А"),
    ("Нурали", "Тлегенов", "nurali.tlegenov", "Nurali2026!", "risk", "10 Б"),
    ("Мадина", "Омарова", "madina.omarova", "Madina2026!", "high", "10 А"),
    ("Еркебулан", "Бекмуханов", "erkebulan.bekmukhanov", "Erk2026!", "risk", "10 В"),
    ("Аяулым", "Исакова", "ayaulym.isakova", "Aya2026!", "medium", "10 А"),
    ("Тимур", "Кенжебаев", "timur.kenzhebaev", "Timur2026!", "high", "10 Б"),
    ("Аидана", "Каирбекова", "aidana.kairbekova", "Aidana2026!", "medium", "10 В"),
    ("Нурсая", "Ашимова", "nursaya.ashimova", "Nursa2026!", "risk", "10 А"),
]

PARENTS_POOL = [
    ("Мама", "Алия", "87010000001"),
    ("Папа", "Марат", "87010000002"),
    ("Опекун", "Ержан", "87010000003"),
]

CLASS_ANNOUNCEMENTS = [
    {
        "title": "Школьный ивент",
        "text": "Case Championship состоится в пятницу. Подготовка идёт по графику."
    },
    {
        "title": "Важно для 10 классов",
        "text": "Сдача проектов по информатике переносится на пятницу."
    }
]

GLOBAL_STATE = {
    "class_homework": [],
    "announcements": CLASS_ANNOUNCEMENTS.copy()
}

def slugify(value):
    value = value.strip().lower()
    value = value.replace("ё", "е")
    value = re.sub(r"[^a-zа-я0-9]+", ".", value, flags=re.IGNORECASE)
    value = re.sub(r"\.+", ".", value).strip(".")
    return value

def role_guard(required_role):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("login"))
            if user["role"] != required_role:
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapper
    return decorator

def current_user():
    login_value = session.get("user_login")
    if not login_value:
        return None
    return USERS.get(login_value)

def create_marks(seed, preset_key):
    preset = PROFILE_PRESETS[preset_key]
    rng = Random(seed)
    diary = {}
    for index, subject in enumerate(SUBJECTS):
        base = preset["spread"][index % len(preset["spread"])]
        marks = []
        for _ in range(4):
            shift = rng.choice([-1, 0, 0, 1])
            value = max(2, min(5, base + shift))
            marks.append(value)
        diary[subject] = {
            "marks": marks,
            "theme": SUBJECT_WEAKNESS_HOMEWORK[subject].split(" и ")[0] if subject in SUBJECT_WEAKNESS_HOMEWORK else "Текущая тема"
        }
    return diary

def create_student(first_name, last_name, login, password, preset_key, grade):
    seed = sum(ord(c) for c in login)
    diary = create_marks(seed, preset_key)
    preset = PROFILE_PRESETS[preset_key]
    parent1 = PARENTS_POOL[seed % len(PARENTS_POOL)]
    parent2 = PARENTS_POOL[(seed + 1) % len(PARENTS_POOL)]
    full_name = f"{first_name} {last_name}"
    homework = []
    for subject in SUBJECTS[:3]:
        homework.append({
            "subject": subject,
            "title": f"Мини-задание по теме {subject}",
            "status": "new",
            "xp": 25,
            "from_teacher": "Система",
            "created_at": "Сегодня"
        })
    achievements = ["Первые шаги", "Учебный старт"]
    return {
        "login": login,
        "password": password,
        "role": "student",
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "grade": grade,
        "parents": [
            {
                "relation": parent1[0],
                "name": parent1[1],
                "phone": parent1[2]
            },
            {
                "relation": parent2[0],
                "name": parent2[1],
                "phone": parent2[2]
            }
        ],
        "diary": diary,
        "homework": homework,
        "extra_lessons": [],
        "notifications": [],
        "achievements": achievements,
        "streak": preset["streak"],
        "sleep_hours": preset["sleep"],
        "manual_xp": preset["manual_xp"],
        "manual_points": preset["manual_points"],
        "coins_bonus": preset["coins_bonus"],
        "event_title": "Case Championship",
        "event_time": datetime(2026, 4, 3, 14, 0),
        "avatar_seed": full_name,
    }

def create_teacher():
    return {
        "login": TEACHER_LOGIN,
        "password": TEACHER_PASSWORD,
        "role": "teacher",
        "first_name": "Айжан",
        "last_name": "Тулеубекова",
        "full_name": TEACHER_NAME,
        "grade": "Учитель",
        "subject": "Информатика",
        "avatar_seed": TEACHER_NAME,
    }

USERS = {TEACHER_LOGIN: create_teacher()}
for student in DEMO_STUDENTS:
    USERS[student[2]] = create_student(student[0], student[1], student[2], student[3], student[4], student[5])

def mark_xp(mark):
    return {2: 0, 3: 8, 4: 18, 5: 30}.get(mark, 0)

def subject_average(marks):
    return round(sum(marks) / len(marks), 2) if marks else 0

def calculate_student_metrics(student):
    subject_rows = []
    total_avg = 0
    total_marks = 0
    total_xp = 0
    for subject in SUBJECTS:
        marks = student["diary"][subject]["marks"]
        avg = subject_average(marks)
        percent = round(avg / 5 * 100, 1)
        total_avg += avg
        total_marks += len(marks)
        total_xp += sum(mark_xp(mark) for mark in marks)
        subject_rows.append({
            "name": subject,
            "icon": SUBJECT_ICONS.get(subject, "school"),
            "avg": avg,
            "percent": percent,
            "marks": marks,
            "theme": student["diary"][subject]["theme"]
        })
    overall_avg = round(total_avg / len(SUBJECTS), 2)
    completed_homework = len([item for item in student["homework"] if item["status"] == "done"])
    pending_homework = len([item for item in student["homework"] if item["status"] != "done"])
    extra_lessons = len(student["extra_lessons"])
    xp = total_xp + student["manual_xp"] + completed_homework * 20 + student["streak"] * 6 + extra_lessons * 12
    coins = 40 + xp // 14 + student["coins_bonus"]
    level = 1 + xp // 250
    progress = xp % 250
    to_next = 250 - progress if progress != 0 else 0
    weakest_avg = min(row["avg"] for row in subject_rows)
    risk = int(round((5 - overall_avg) * 20 + max(0, 4.3 - weakest_avg) * 22 + pending_homework * 4 + max(0, 6 - student["streak"]) * 2))
    risk = max(0, min(100, risk))
    mastery = round(overall_avg / 5 * 100, 1)
    title = "Лидер обучения"
    if level >= 6:
        title = "Элитный ученик"
    elif level >= 4:
        title = "Сильный игрок"
    elif level >= 2:
        title = "Стабильный прогресс"
    badge_pool = []
    if student["streak"] >= 5:
        badge_pool.append("Серия дней")
    if overall_avg >= 4.5:
        badge_pool.append("Отличник")
    if completed_homework >= 3:
        badge_pool.append("Дисциплина")
    if extra_lessons >= 1:
        badge_pool.append("Прокачка")
    if not badge_pool:
        badge_pool.append("Старт")
    return {
        "subject_rows": subject_rows,
        "overall_avg": overall_avg,
        "mastery": mastery,
        "xp": xp,
        "coins": coins,
        "level": level,
        "progress": progress,
        "to_next": to_next,
        "title": title,
        "risk": risk,
        "completed_homework": completed_homework,
        "pending_homework": pending_homework,
        "extra_lessons": extra_lessons,
        "badges": badge_pool,
    }

def calculate_class_metrics():
    subject_avgs = {}
    for subject in SUBJECTS:
        all_marks = []
        for user in USERS.values():
            if user["role"] == "student":
                all_marks.extend(user["diary"][subject]["marks"])
        subject_avgs[subject] = subject_average(all_marks)
    class_avg = round(sum(subject_avgs.values()) / len(subject_avgs), 2)
    weak_subjects = [subject for subject, avg in subject_avgs.items() if avg < 4.2]
    top_students = []
    risk_students = []
    for user in USERS.values():
        if user["role"] != "student":
            continue
        metrics = calculate_student_metrics(user)
        top_students.append((user, metrics))
        risk_students.append((user, metrics))
    top_students.sort(key=lambda item: item[1]["overall_avg"], reverse=True)
    risk_students.sort(key=lambda item: item[1]["risk"], reverse=True)
    return {
        "subject_avgs": subject_avgs,
        "class_avg": class_avg,
        "weak_subjects": weak_subjects,
        "top_students": top_students[:5],
        "risk_students": [item for item in risk_students if item[1]["risk"] >= 45][:5],
    }

def ai_student_insights(student, metrics):
    messages = []
    if metrics["risk"] >= 60:
        messages.append({
            "type": "danger",
            "title": "Зона риска",
            "text": "Текущий темп говорит, что нужно добавить поддержку и упростить ближайшие цели."
        })
    if student["sleep_hours"] < 7:
        messages.append({
            "type": "warning",
            "title": "Сон слабый",
            "text": "Недосып заметно режет концентрацию и память."
        })
    if metrics["overall_avg"] >= 4.6:
        messages.append({
            "type": "success",
            "title": "Очень сильный темп",
            "text": "Можно идти в более сложные задания и сохранять высокий уровень."
        })
    if not messages:
        messages.append({
            "type": "info",
            "title": "Баланс нормальный",
            "text": "Пока лучше делать короткие и регулярные подходы без перегруза."
        })
    weakest = min(metrics["subject_rows"], key=lambda x: x["avg"])
    messages.append({
        "type": "info",
        "title": "Точечная рекомендация",
        "text": f"Быстрее всего прокачается предмет {weakest['name']}. Тема: {weakest['theme']}."
    })
    return messages

def ai_teacher_insights(class_metrics):
    text_blocks = []
    if class_metrics["weak_subjects"]:
        weak_list = ", ".join(class_metrics["weak_subjects"][:3])
        text_blocks.append({
            "type": "warning",
            "title": "Классовая слабая зона",
            "text": f"Проблемные темы сейчас сосредоточены в: {weak_list}. Лучше дать одно общее закрепляющее задание."
        })
    if class_metrics["risk_students"]:
        risk_names = ", ".join(item[0]["full_name"] for item in class_metrics["risk_students"])
        text_blocks.append({
            "type": "danger",
            "title": "Ученики в зоне риска",
            "text": f"Нужно точечное внимание: {risk_names}."
        })
    if not text_blocks:
        text_blocks.append({
            "type": "success",
            "title": "Класс выглядит устойчиво",
            "text": "Можно повышать сложность без потери темпа."
        })
    return text_blocks

def generate_homework_text(subject, avg):
    base = SUBJECT_WEAKNESS_HOMEWORK.get(subject, "Повторить тему и решить 5 практических заданий.")
    if avg < 3.6:
        return f"Интенсивное задание по предмету «{subject}»: {base} Дополнительно сделать самопроверку по ключевым ошибкам."
    return f"Закрепляющее задание по предмету «{subject}»: {base}"

def add_notification(student, text):
    student["notifications"].insert(0, {
        "text": text,
        "created_at": datetime.now().strftime("%d.%m %H:%M")
    })
    student["notifications"] = student["notifications"][:12]

def save_grade(student, subject, mark, source):
    student["diary"][subject]["marks"].append(mark)
    add_notification(student, f"Новая оценка по {subject}: {mark} от {source}")
    if mark == 5:
        student["manual_xp"] += 10
        student["manual_points"] += 5
    elif mark == 4:
        student["manual_xp"] += 6
        student["manual_points"] += 3
    elif mark == 3:
        student["manual_xp"] += 2
    else:
        student["manual_xp"] += 0

def assign_extra_lesson(student, subject, title, source="Учитель"):
    student["extra_lessons"].append({
        "subject": subject,
        "title": title,
        "status": "planned",
        "created_at": datetime.now().strftime("%d.%m %H:%M"),
        "from_teacher": source
    })
    add_notification(student, f"Назначено доп. занятие по {subject}: {title}")
    student["manual_xp"] += 8
    student["manual_points"] += 4

def assign_class_homework(subject, text, source="ИИ"):
    item = {
        "subject": subject,
        "title": text,
        "status": "new",
        "xp": 30,
        "from_teacher": source,
        "created_at": datetime.now().strftime("%d.%m %H:%M")
    }
    GLOBAL_STATE["class_homework"].insert(0, item)
    for user in USERS.values():
        if user["role"] != "student":
            continue
        user["homework"].insert(0, dict(item))
        add_notification(user, f"Общее домашнее задание по {subject} добавлено")

def format_countdown(target):
    now = datetime.now()
    diff = max(target - now, timedelta())
    total = int(diff.total_seconds())
    days = total // 86400
    hours = (total % 86400) // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "iso": target.strftime("%Y-%m-%dT%H:%M:%S")
    }

@app.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user["role"] == "teacher":
        return redirect(url_for("teacher_dashboard"))
    return redirect(url_for("student_dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip().lower()
        password = request.form.get("password", "").strip()
        user = USERS.get(login_value)
        if user and user["password"] == password:
            session["user_login"] = login_value
            return redirect(url_for("index"))
        flash("Неверный логин или пароль")
    return render_template("login.html", users=USERS)

@app.route("/register", methods=["POST"])
def register():
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    password = request.form.get("password", "").strip()
    grade = request.form.get("grade", "10 А").strip()
    if not first_name or not last_name or not password:
        flash("Заполни имя, фамилию и пароль")
        return redirect(url_for("login"))
    base_login = slugify(f"{first_name}.{last_name}")
    login_value = base_login
    counter = 2
    while login_value in USERS:
        login_value = f"{base_login}{counter}"
        counter += 1
    USERS[login_value] = create_student(first_name, last_name, login_value, password, "medium", grade)
    session["user_login"] = login_value
    flash(f"Аккаунт создан: {login_value}")
    return redirect(url_for("student_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user["role"] == "teacher":
        return redirect(url_for("teacher_dashboard"))
    return redirect(url_for("student_dashboard"))

@app.route("/student")
@role_guard("student")
def student_dashboard():
    student = current_user()
    metrics = calculate_student_metrics(student)
    class_metrics = calculate_class_metrics()
    alerts = ai_student_insights(student, metrics)
    countdown = format_countdown(student["event_time"])
    leaderboard = class_metrics["top_students"][:5]
    return render_template(
        "student_dashboard.html",
        user=student,
        metrics=metrics,
        alerts=alerts,
        countdown=countdown,
        leaderboard=leaderboard,
        class_metrics=class_metrics,
        subjects=SUBJECTS,
        logged_in=True
    )

@app.route("/teacher")
@role_guard("teacher")
def teacher_dashboard():
    class_metrics = calculate_class_metrics()
    alerts = ai_teacher_insights(class_metrics)
    students = []
    for user in USERS.values():
        if user["role"] != "student":
            continue
        metrics = calculate_student_metrics(user)
        students.append((user, metrics))
    students.sort(key=lambda item: item[1]["risk"], reverse=True)
    return render_template(
        "teacher_dashboard.html",
        user=current_user(),
        class_metrics=class_metrics,
        alerts=alerts,
        students=students,
        subjects=SUBJECTS,
        homework_queue=GLOBAL_STATE["class_homework"][:5],
        logged_in=True
    )

@app.route("/cabinet")
@app.route("/cabinet/<login_value>")
def cabinet(login_value=None):
    user = current_user()
    target_login = login_value
    if not user:
        return redirect(url_for("login"))
    if not target_login:
        target_login = user["login"]
    target = USERS.get(target_login)
    if not target:
        abort(404)
    if user["role"] == "student" and user["login"] != target_login:
        return redirect(url_for("cabinet", login_value=user["login"]))
    metrics = calculate_student_metrics(target)
    return render_template(
        "cabinet.html",
        user=user,
        target=target,
        metrics=metrics,
        logged_in=True,
        role_label=ROLE_LABELS.get(target["role"], "Пользователь")
    )

@app.route("/ai")
def ai_page():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user["role"] == "student":
        metrics = calculate_student_metrics(user)
        insights = ai_student_insights(user, metrics)
        return render_template(
            "ai.html",
            user=user,
            role="student",
            metrics=metrics,
            insights=insights,
            class_metrics=calculate_class_metrics(),
            logged_in=True
        )
    class_metrics = calculate_class_metrics()
    insights = ai_teacher_insights(class_metrics)
    return render_template(
        "ai.html",
        user=user,
        role="teacher",
        metrics=None,
        insights=insights,
        class_metrics=class_metrics,
        logged_in=True
    )

@app.route("/kiosk")
@role_guard("teacher")
def kiosk():
    class_metrics = calculate_class_metrics()
    countdown = format_countdown(datetime(2026, 4, 3, 14, 0))
    return render_template(
        "kiosk.html",
        user=current_user(),
        class_metrics=class_metrics,
        countdown=countdown,
        homework_queue=GLOBAL_STATE["class_homework"][:8],
        announcements=GLOBAL_STATE["announcements"],
        logged_in=True
    )

@app.route("/grade", methods=["POST"])
@role_guard("teacher")
def grade():
    student_login = request.form.get("student_login", "")
    subject = request.form.get("subject", "")
    mark_raw = request.form.get("mark", "")
    try:
        mark = int(mark_raw)
    except ValueError:
        flash("Оценка должна быть числом")
        return redirect(url_for("teacher_dashboard"))
    if student_login not in USERS or USERS[student_login]["role"] != "student":
        flash("Ученик не найден")
        return redirect(url_for("teacher_dashboard"))
    if subject not in SUBJECTS or mark < 2 or mark > 5:
        flash("Проверь предмет и оценку")
        return redirect(url_for("teacher_dashboard"))
    save_grade(USERS[student_login], subject, mark, current_user()["full_name"])
    flash("Оценка добавлена")
    return redirect(url_for("teacher_dashboard"))

@app.route("/lesson", methods=["POST"])
@role_guard("teacher")
def lesson():
    student_login = request.form.get("student_login", "")
    subject = request.form.get("subject", "")
    title = request.form.get("title", "").strip()
    if student_login not in USERS or USERS[student_login]["role"] != "student":
        flash("Ученик не найден")
        return redirect(url_for("teacher_dashboard"))
    if subject not in SUBJECTS:
        flash("Проверь предмет")
        return redirect(url_for("teacher_dashboard"))
    if not title:
        title = f"Дополнительное занятие по теме {subject}"
    assign_extra_lesson(USERS[student_login], subject, title, current_user()["full_name"])
    flash("Дополнительное занятие назначено")
    return redirect(url_for("teacher_dashboard"))

@app.route("/complete_homework", methods=["POST"])
@role_guard("student")
def complete_homework():
    subject = request.form.get("subject", "")
    title = request.form.get("title", "")
    student = current_user()
    for item in student["homework"]:
        if item["subject"] == subject and item["title"] == title and item["status"] != "done":
            item["status"] = "done"
            student["manual_xp"] += item.get("xp", 15)
            student["manual_points"] += 6
            add_notification(student, f"Домашнее задание по {subject} отмечено как выполненное")
            break
    return redirect(url_for("student_dashboard"))

@app.route("/generate_homework", methods=["POST"])
@role_guard("teacher")
def generate_homework():
    class_metrics = calculate_class_metrics()
    if not class_metrics["weak_subjects"]:
        flash("Слабых тем для генерации пока нет")
        return redirect(url_for("teacher_dashboard"))
    subject = class_metrics["weak_subjects"][0]
    avg = class_metrics["subject_avgs"][subject]
    text = generate_homework_text(subject, avg)
    assign_class_homework(subject, text, "AI Mentor")
    flash("ИИ сгенерировал и раздал домашнее задание всему классу")
    return redirect(url_for("teacher_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
