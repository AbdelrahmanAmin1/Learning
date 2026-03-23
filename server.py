from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "alkttab.sqlite3"
HOST = os.environ.get("ALKTTAB_HOST", "0.0.0.0")
PORT = int(os.environ.get("ALKTTAB_PORT", "8000"))
TOKEN_DAYS = 30
PASSWORD_ITERATIONS = 200_000
DEFAULT_TEACHER_EMAIL = os.environ.get("ALKTTAB_TEACHER_EMAIL", "teacher@alkttab.local")
DEFAULT_TEACHER_PASSWORD = os.environ.get("ALKTTAB_TEACHER_PASSWORD", "Teach2026!")

SITE_INFO = {
    "title": "الكتّاب | اقرأ ورتّل",
    "channel_url": "https://www.youtube.com/@ALKTTAB/",
    "phone": "0593781376",
    "whatsapp": "0593781376",
    "emails": ["kttababdelbaky@gmail.com", "boda2010100@gmail.com"],
}

LEVEL_DATA = [
    {
        "slug": "level-1",
        "title": "المستوى الأول",
        "subtitle": "التأسيس في القراءة والكتابة",
        "age_label": "من 5 إلى 8 سنوات",
        "playlist_id": "PLqWeHwX9XMzEgnXnBG5V6s-y4W_Y1T-tj",
        "playlist_url": "https://www.youtube.com/playlist?list=PLqWeHwX9XMzEgnXnBG5V6s-y4W_Y1T-tj",
        "note": "يبني الطفل من معرفة الحروف حتى القراءة الصحيحة للحركات والمدود والسكون.",
        "outcomes": [
            "التعرف إلى الحروف وأصواتها",
            "قراءة الكلمات البسيطة تدريجيًا",
            "التعامل مع الحركات والمدود والسكون",
        ],
        "skills": [
            "الحروف المجردة وأسماؤها",
            "أشكال الحرف في أول ووسط وآخر الكلمة",
            "الفتح والمد بالألف",
            "الكسر والمد بالياء",
            "الضم والمد بالواو",
            "السكون وأمثلة قرآنية مبسطة",
        ],
        "lessons": [
            {"title": "الحروف المجردة وأسماؤها", "summary": "تعرف الطفل على شكل الحرف واسمه وصوته تمهيدًا للقراءة السليمة."},
            {"title": "أشكال الحرف في الكلمة", "summary": "التمييز بين أول ووسط وآخر الكلمة مع أمثلة بصرية سهلة."},
            {"title": "الفتح والمد بالألف", "summary": "التدريب على نطق الفتح ثم الانتقال إلى المد بالألف داخل الكلمات."},
            {"title": "الكسر والمد بالياء", "summary": "تثبيت الكسرة وتمييز المد بالياء مع تطبيقات متدرجة."},
            {"title": "الضم والمد بالواو", "summary": "قراءة الضمة ثم المد بالواو بأسلوب سهل ومناسب للأطفال."},
            {"title": "السكون والتطبيقات", "summary": "إتقان السكون وربطه بمقاطع وكلمات قصيرة وأمثلة قرآنية."},
        ],
        "hints": [
            ("قائمة التشغيل", "مرتبطة بالدروس بالترتيب نفسه"),
            ("الهدف", "تأسيس الطفل في القراءة من الصفر"),
            ("الكتاب المناسب", "حقيبة المستوى الأول"),
        ],
    },
    {
        "slug": "level-2",
        "title": "المستوى الثاني",
        "subtitle": "الإملاء والمهارات المتقدمة",
        "age_label": "بعد إتقان الأساسيات",
        "playlist_id": "PLqWeHwX9XMzEzvfjzW32Y-sWdzTGyCx_i",
        "playlist_url": "https://www.youtube.com/playlist?list=PLqWeHwX9XMzEzvfjzW32Y-sWdzTGyCx_i",
        "note": "ينتقل الطالب إلى التنوين والشدة والهمزات مع تركيز أكبر على الإملاء الدقيق.",
        "outcomes": [
            "قراءة أوضح للكلمات المركبة",
            "تحسين الإملاء ومواطن الهمزات",
            "الاستعداد للقراءة المتقنة والنصوص الأطول",
        ],
        "skills": [
            "التنوين بأنواعه الثلاثة",
            "الشدة بتدرجها الكامل",
            "همزة الوصل في الأسماء والأفعال والـ التعريف",
            "همزة القطع في أول ووسط وآخر الكلمة",
            "تطبيقات إملائية وتمارين تثبيت",
        ],
        "lessons": [
            {"title": "مدخل إلى التنوين", "summary": "فهم تنوين الفتح والضم والكسر مع أمثلة مبسطة وتمارين نطق."},
            {"title": "تدريبات التنوين في القراءة", "summary": "تطبيق التنوين داخل كلمات وجمل قصيرة مناسبة للطفل."},
            {"title": "الشدة: التهيئة والتعرف", "summary": "شرح الشدة وأثرها الصوتي بطريقة واضحة وعملية."},
            {"title": "الشدة في الكلمات والجمل", "summary": "ربط الشدة بالقراءة والإملاء مع تدريب متكرر ومتدرج."},
            {"title": "همزة الوصل", "summary": "فهم مواضع همزة الوصل في الأسماء والأفعال والـ التعريف."},
            {"title": "همزة القطع والتطبيق الإملائي", "summary": "تمييز همزة القطع في مواضعها مع تدريبات إملائية مباشرة."},
        ],
        "hints": [
            ("قائمة التشغيل", "مرتبطة بدروس الإملاء والتجويد المبسط"),
            ("الهدف", "إتقان التنوين والشدة والهمزات"),
            ("الكتاب المناسب", "حقيبة المستوى الثاني"),
        ],
    },
]

BOOK_DATA = [
    {
        "title": "حقيبة المستوى الأول",
        "badge": "الأكثر طلبًا",
        "price_label": "اطلب السعر عبر واتساب",
        "description": "تأسيس القراءة بالحروف والحركات والمدود والسكون مع أنشطة وواجبات متابعة.",
        "tags": ["قراءة", "أوراق عمل", "متابعة منزلية"],
    },
    {
        "title": "حقيبة المستوى الثاني",
        "badge": "لمن أكمل التأسيس",
        "price_label": "اطلب السعر عبر واتساب",
        "description": "محتوى التنوين والشدة والهمزات مع تدريبات إملائية عملية ومراجعات.",
        "tags": ["إملاء", "شدة", "همزات"],
    },
    {
        "title": "دليل المعلّم",
        "badge": "للمعلمين",
        "price_label": "متاح عند الطلب",
        "description": "ملاحظات تربوية وشرح درسًا درسًا لمساندة المعلم في الشرح والمتابعة.",
        "tags": ["إرشادات تربوية", "شرح الدروس", "متابعة الصف"],
    },
    {
        "title": "التجويد الميسر للأطفال",
        "badge": "مرحلة لاحقة",
        "price_label": "متاح عند الطلب",
        "description": "منتج مناسب بعد التأسيس، يربط الطفل بالقراءة المتقنة وأمثلة التجويد المبسطة.",
        "tags": ["قرآن", "تجويد مبسط", "مرحلة متقدمة"],
    },
]


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt_bytes = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, PASSWORD_ITERATIONS)
    return f"{salt_bytes.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        expected = hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
        return hmac.compare_digest(expected, digest_hex)
    except Exception:
        return False


def require_email(value: str) -> str:
    email = value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ApiError(400, "يرجى إدخال بريد إلكتروني صحيح.")
    return email


def require_non_empty(value: str, message: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ApiError(400, message)
    return cleaned


def normalize_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned.startswith(("http://", "https://")):
        return cleaned
    return f"https://{cleaned}"


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS levels (
              slug TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              subtitle TEXT NOT NULL,
              age_label TEXT NOT NULL,
              playlist_id TEXT NOT NULL,
              playlist_url TEXT NOT NULL,
              note TEXT NOT NULL,
              sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS level_outcomes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              level_slug TEXT NOT NULL REFERENCES levels(slug) ON DELETE CASCADE,
              content TEXT NOT NULL,
              sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS level_skills (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              level_slug TEXT NOT NULL REFERENCES levels(slug) ON DELETE CASCADE,
              content TEXT NOT NULL,
              sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lessons (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              level_slug TEXT NOT NULL REFERENCES levels(slug) ON DELETE CASCADE,
              title TEXT NOT NULL,
              summary TEXT NOT NULL,
              sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS level_hints (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              level_slug TEXT NOT NULL REFERENCES levels(slug) ON DELETE CASCADE,
              label TEXT NOT NULL,
              value TEXT NOT NULL,
              sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS books (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              badge TEXT NOT NULL,
              price_label TEXT NOT NULL,
              description TEXT NOT NULL,
              sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS book_tags (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
              content TEXT NOT NULL,
              sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              role TEXT NOT NULL CHECK (role IN ('teacher', 'student')),
              name TEXT NOT NULL,
              email TEXT NOT NULL UNIQUE COLLATE NOCASE,
              password_hash TEXT NOT NULL,
              phone TEXT,
              guardian_name TEXT,
              guardian_phone TEXT,
              level_slug TEXT REFERENCES levels(slug),
              teacher_progress INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS auth_tokens (
              token TEXT PRIMARY KEY,
              user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              created_at TEXT NOT NULL,
              expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lesson_completion (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
              completed_at TEXT NOT NULL,
              UNIQUE(student_id, lesson_id)
            );

            CREATE TABLE IF NOT EXISTS teaching_sessions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              level_slug TEXT NOT NULL REFERENCES levels(slug) ON DELETE CASCADE,
              title TEXT NOT NULL,
              date TEXT NOT NULL,
              time TEXT NOT NULL,
              zoom_link TEXT,
              material_title TEXT,
              material_link TEXT,
              notes TEXT,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS attendance (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              level_slug TEXT NOT NULL REFERENCES levels(slug) ON DELETE CASCADE,
              lecture_title TEXT NOT NULL,
              lecture_date TEXT NOT NULL,
              status TEXT NOT NULL CHECK (status IN ('present', 'absent', 'excused')),
              UNIQUE(student_id, lecture_title, lecture_date)
            );

            CREATE TABLE IF NOT EXISTS contact_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              phone TEXT NOT NULL,
              topic TEXT NOT NULL,
              message TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
        seed_reference_data(conn)
        seed_teacher_account(conn)
        conn.commit()
    finally:
        conn.close()


def seed_reference_data(conn: sqlite3.Connection) -> None:
    levels_count = conn.execute("SELECT COUNT(*) AS count FROM levels").fetchone()["count"]
    if levels_count == 0:
        for level_index, level in enumerate(LEVEL_DATA, start=1):
            conn.execute(
                """
                INSERT INTO levels (slug, title, subtitle, age_label, playlist_id, playlist_url, note, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    level["slug"],
                    level["title"],
                    level["subtitle"],
                    level["age_label"],
                    level["playlist_id"],
                    level["playlist_url"],
                    level["note"],
                    level_index,
                ),
            )
            for index, item in enumerate(level["outcomes"], start=1):
                conn.execute(
                    "INSERT INTO level_outcomes (level_slug, content, sort_order) VALUES (?, ?, ?)",
                    (level["slug"], item, index),
                )
            for index, item in enumerate(level["skills"], start=1):
                conn.execute(
                    "INSERT INTO level_skills (level_slug, content, sort_order) VALUES (?, ?, ?)",
                    (level["slug"], item, index),
                )
            for index, lesson in enumerate(level["lessons"], start=1):
                conn.execute(
                    "INSERT INTO lessons (level_slug, title, summary, sort_order) VALUES (?, ?, ?, ?)",
                    (level["slug"], lesson["title"], lesson["summary"], index),
                )
            for index, item in enumerate(level["hints"], start=1):
                conn.execute(
                    "INSERT INTO level_hints (level_slug, label, value, sort_order) VALUES (?, ?, ?, ?)",
                    (level["slug"], item[0], item[1], index),
                )

    books_count = conn.execute("SELECT COUNT(*) AS count FROM books").fetchone()["count"]
    if books_count == 0:
        for index, book in enumerate(BOOK_DATA, start=1):
            cursor = conn.execute(
                """
                INSERT INTO books (title, badge, price_label, description, sort_order)
                VALUES (?, ?, ?, ?, ?)
                """,
                (book["title"], book["badge"], book["price_label"], book["description"], index),
            )
            for tag_index, tag in enumerate(book["tags"], start=1):
                conn.execute(
                    "INSERT INTO book_tags (book_id, content, sort_order) VALUES (?, ?, ?)",
                    (cursor.lastrowid, tag, tag_index),
                )


def seed_teacher_account(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT id FROM users WHERE lower(email) = lower(?)", (DEFAULT_TEACHER_EMAIL,)).fetchone()
    if row:
        return
    conn.execute(
        """
        INSERT INTO users (role, name, email, password_hash, phone, created_at)
        VALUES ('teacher', ?, ?, ?, ?, ?)
        """,
        ("المعلم الرئيسي", DEFAULT_TEACHER_EMAIL, hash_password(DEFAULT_TEACHER_PASSWORD), SITE_INFO["phone"], now_iso()),
    )


def cleanup_expired_tokens(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM auth_tokens WHERE expires_at < ?", (now_iso(),))


def revoke_user_tokens(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM auth_tokens WHERE user_id = ?", (user_id,))


def issue_token(conn: sqlite3.Connection, user_id: int) -> str:
    cleanup_expired_tokens(conn)
    revoke_user_tokens(conn, user_id)
    token = secrets.token_urlsafe(32)
    expires_at = (now_utc() + timedelta(days=TOKEN_DAYS)).isoformat()
    conn.execute(
        "INSERT INTO auth_tokens (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now_iso(), expires_at),
    )
    conn.commit()
    return token


def revoke_token(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
    conn.commit()


def get_user_by_token(conn: sqlite3.Connection, token: str | None) -> sqlite3.Row | None:
    if not token:
        return None
    cleanup_expired_tokens(conn)
    return conn.execute(
        """
        SELECT users.*
        FROM auth_tokens
        JOIN users ON users.id = auth_tokens.user_id
        WHERE auth_tokens.token = ?
          AND auth_tokens.expires_at >= ?
        """,
        (token, now_iso()),
    ).fetchone()


def serialize_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "role": row["role"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"] or "",
        "guardian_name": row["guardian_name"] or "",
        "guardian_phone": row["guardian_phone"] or "",
        "level_id": row["level_slug"],
    }


def serialize_sessions(rows: list[sqlite3.Row]) -> list[dict]:
    return [
        {
            "id": row["id"],
            "level_id": row["level_slug"],
            "level_title": row["level_title"],
            "title": row["title"],
            "date": row["date"],
            "time": row["time"],
            "zoom_link": row["zoom_link"] or "",
            "material_title": row["material_title"] or "",
            "material_link": row["material_link"] or "",
            "notes": row["notes"] or "",
        }
        for row in rows
    ]


def get_all_levels(conn: sqlite3.Connection) -> list[dict]:
    levels = conn.execute("SELECT * FROM levels ORDER BY sort_order").fetchall()
    output = []
    for row in levels:
        slug = row["slug"]
        outcomes = conn.execute(
            "SELECT content FROM level_outcomes WHERE level_slug = ? ORDER BY sort_order", (slug,)
        ).fetchall()
        skills = conn.execute(
            "SELECT content FROM level_skills WHERE level_slug = ? ORDER BY sort_order", (slug,)
        ).fetchall()
        lessons = conn.execute(
            "SELECT id, title, summary, sort_order FROM lessons WHERE level_slug = ? ORDER BY sort_order", (slug,)
        ).fetchall()
        hints = conn.execute(
            "SELECT label, value FROM level_hints WHERE level_slug = ? ORDER BY sort_order", (slug,)
        ).fetchall()
        output.append(
            {
                "id": slug,
                "title": row["title"],
                "subtitle": row["subtitle"],
                "age": row["age_label"],
                "playlist_id": row["playlist_id"],
                "playlist_url": row["playlist_url"],
                "note": row["note"],
                "outcomes": [item["content"] for item in outcomes],
                "skills": [item["content"] for item in skills],
                "lessons": [
                    {"id": item["id"], "title": item["title"], "summary": item["summary"], "sort_order": item["sort_order"]}
                    for item in lessons
                ],
                "hints": [{"label": item["label"], "value": item["value"]} for item in hints],
            }
        )
    return output


def get_all_books(conn: sqlite3.Connection) -> list[dict]:
    books = conn.execute("SELECT * FROM books ORDER BY sort_order").fetchall()
    output = []
    for row in books:
        tags = conn.execute("SELECT content FROM book_tags WHERE book_id = ? ORDER BY sort_order", (row["id"],)).fetchall()
        output.append(
            {
                "id": row["id"],
                "title": row["title"],
                "badge": row["badge"],
                "price_label": row["price_label"],
                "description": row["description"],
                "tags": [item["content"] for item in tags],
            }
        )
    return output


def get_next_session(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute(
        """
        SELECT teaching_sessions.*, levels.title AS level_title
        FROM teaching_sessions
        JOIN levels ON levels.slug = teaching_sessions.level_slug
        WHERE (teaching_sessions.date || 'T' || teaching_sessions.time) >= ?
        ORDER BY teaching_sessions.date, teaching_sessions.time
        LIMIT 1
        """,
        (now_utc().strftime("%Y-%m-%dT%H:%M"),),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "level_id": row["level_slug"],
        "level_title": row["level_title"],
        "title": row["title"],
        "date": row["date"],
        "time": row["time"],
    }


def build_public_bootstrap(conn: sqlite3.Connection) -> dict:
    return {
        "site": SITE_INFO,
        "levels": get_all_levels(conn),
        "books": get_all_books(conn),
        "next_session": get_next_session(conn),
    }


def get_level_row(conn: sqlite3.Connection, level_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM levels WHERE slug = ?", (level_id,)).fetchone()
    if not row:
        raise ApiError(404, "المستوى المطلوب غير موجود.")
    return row


def get_lesson_count(conn: sqlite3.Connection, level_id: str) -> int:
    return conn.execute("SELECT COUNT(*) AS count FROM lessons WHERE level_slug = ?", (level_id,)).fetchone()["count"]


def get_completed_lesson_ids(conn: sqlite3.Connection, student_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT lesson_id FROM lesson_completion WHERE student_id = ? ORDER BY lesson_id",
        (student_id,),
    ).fetchall()
    return [row["lesson_id"] for row in rows]


def get_lesson_percent(conn: sqlite3.Connection, student_row: sqlite3.Row) -> int:
    lesson_count = get_lesson_count(conn, student_row["level_slug"])
    if lesson_count <= 0:
        return 0
    completed = len(get_completed_lesson_ids(conn, student_row["id"]))
    return round((completed / lesson_count) * 100)


def get_student_dashboard(conn: sqlite3.Connection, student_row: sqlite3.Row) -> dict:
    completed_ids = get_completed_lesson_ids(conn, student_row["id"])
    lesson_percent = get_lesson_percent(conn, student_row)
    teacher_progress = max(0, min(int(student_row["teacher_progress"] or 0), 100))
    overall_percent = max(teacher_progress, lesson_percent)
    attendance_rows = conn.execute(
        """
        SELECT lecture_title, lecture_date, status
        FROM attendance
        WHERE student_id = ?
        ORDER BY lecture_date DESC, id DESC
        """,
        (student_row["id"],),
    ).fetchall()
    session_rows = conn.execute(
        """
        SELECT teaching_sessions.*, levels.title AS level_title
        FROM teaching_sessions
        JOIN levels ON levels.slug = teaching_sessions.level_slug
        WHERE teaching_sessions.level_slug = ?
        ORDER BY teaching_sessions.date, teaching_sessions.time
        """,
        (student_row["level_slug"],),
    ).fetchall()
    return {
        "user": serialize_user(student_row),
        "teacher_progress": teacher_progress,
        "lesson_percent": lesson_percent,
        "overall_percent": overall_percent,
        "completed_lesson_ids": completed_ids,
        "attendance": [
            {"lecture_title": row["lecture_title"], "date": row["lecture_date"], "status": row["status"]}
            for row in attendance_rows
        ],
        "sessions": serialize_sessions(session_rows),
    }


def get_teacher_students(conn: sqlite3.Connection, level_id: str) -> list[dict]:
    students = conn.execute(
        """
        SELECT *
        FROM users
        WHERE role = 'student' AND level_slug = ?
        ORDER BY created_at DESC, name COLLATE NOCASE
        """,
        (level_id,),
    ).fetchall()
    output = []
    for student in students:
        lesson_percent = get_lesson_percent(conn, student)
        teacher_progress = max(0, min(int(student["teacher_progress"] or 0), 100))
        output.append(
            {
                "id": student["id"],
                "name": student["name"],
                "email": student["email"],
                "phone": student["phone"] or "",
                "guardian_name": student["guardian_name"] or "",
                "guardian_phone": student["guardian_phone"] or "",
                "teacher_progress": teacher_progress,
                "lesson_percent": lesson_percent,
                "overall_percent": max(teacher_progress, lesson_percent),
            }
        )
    return output


def get_teacher_dashboard(conn: sqlite3.Connection, level_id: str) -> dict:
    get_level_row(conn, level_id)
    students = get_teacher_students(conn, level_id)
    session_rows = conn.execute(
        """
        SELECT teaching_sessions.*, levels.title AS level_title
        FROM teaching_sessions
        JOIN levels ON levels.slug = teaching_sessions.level_slug
        ORDER BY teaching_sessions.date DESC, teaching_sessions.time DESC, teaching_sessions.id DESC
        """
    ).fetchall()
    total_students = conn.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'student'").fetchone()["count"]
    total_sessions = conn.execute("SELECT COUNT(*) AS count FROM teaching_sessions").fetchone()["count"]
    average_progress = round(sum(student["overall_percent"] for student in students) / len(students)) if students else 0
    return {
        "selected_level_id": level_id,
        "metrics": {
            "total_students": total_students,
            "level_students": len(students),
            "average_progress": average_progress,
            "total_sessions": total_sessions,
        },
        "students": students,
        "sessions": serialize_sessions(session_rows),
    }


def get_auth_token_from_headers(headers) -> str | None:
    auth_value = headers.get("Authorization", "")
    if not auth_value.startswith("Bearer "):
        return None
    return auth_value.split(" ", 1)[1].strip()


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0") or 0)
        if content_length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(content_length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError(400, "تعذر قراءة البيانات المرسلة.") from exc

    def require_user(self, conn: sqlite3.Connection, role: str | None = None) -> tuple[sqlite3.Row, str]:
        token = get_auth_token_from_headers(self.headers)
        user = get_user_by_token(conn, token)
        if not user:
            raise ApiError(401, "يجب تسجيل الدخول أولًا.")
        if role and user["role"] != role:
            raise ApiError(403, "ليست لديك صلاحية للوصول إلى هذا الإجراء.")
        return user, token or ""

    def api_error(self, status: int, message: str) -> None:
        self.send_json(status, {"ok": False, "message": message})

    def handle_api(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        method = self.command.upper()
        conn = get_connection()
        try:
            if method == "GET" and path == "/api/health":
                self.send_json(200, {"ok": True, "message": "healthy"})
                return

            if method == "GET" and path == "/api/public/bootstrap":
                self.send_json(200, {"ok": True, "data": build_public_bootstrap(conn)})
                return

            if method == "POST" and path == "/api/auth/login":
                payload = self.read_json_body()
                email = require_email(str(payload.get("email", "")))
                password = require_non_empty(str(payload.get("password", "")), "يرجى إدخال كلمة المرور.")
                user = conn.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
                if not user or not verify_password(password, user["password_hash"]):
                    raise ApiError(401, "بيانات الدخول غير صحيحة.")
                token = issue_token(conn, user["id"])
                self.send_json(200, {"ok": True, "data": {"token": token, "user": serialize_user(user)}})
                return

            if method == "POST" and path == "/api/auth/register":
                payload = self.read_json_body()
                name = require_non_empty(str(payload.get("name", "")), "يرجى إدخال اسم الطالب.")
                email = require_email(str(payload.get("email", "")))
                phone = require_non_empty(str(payload.get("phone", "")), "يرجى إدخال رقم الهاتف.")
                guardian_name = require_non_empty(str(payload.get("guardian_name", "")), "يرجى إدخال اسم ولي الأمر.")
                guardian_phone = require_non_empty(str(payload.get("guardian_phone", "")), "يرجى إدخال رقم ولي الأمر.")
                level_id = require_non_empty(str(payload.get("level_id", "")), "يرجى اختيار المستوى.")
                password = require_non_empty(str(payload.get("password", "")), "يرجى إدخال كلمة المرور.")
                if len(password) < 6:
                    raise ApiError(400, "يجب أن تكون كلمة المرور 6 أحرف على الأقل.")
                get_level_row(conn, level_id)
                exists = conn.execute("SELECT id FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
                if exists:
                    raise ApiError(409, "هذا البريد مستخدم بالفعل.")
                cursor = conn.execute(
                    """
                    INSERT INTO users (
                      role, name, email, password_hash, phone, guardian_name,
                      guardian_phone, level_slug, teacher_progress, created_at
                    ) VALUES ('student', ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """,
                    (name, email, hash_password(password), phone, guardian_name, guardian_phone, level_id, now_iso()),
                )
                conn.commit()
                user = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
                token = issue_token(conn, user["id"])
                self.send_json(201, {"ok": True, "data": {"token": token, "user": serialize_user(user)}})
                return

            if method == "POST" and path == "/api/auth/logout":
                _, token = self.require_user(conn)
                revoke_token(conn, token)
                self.send_json(200, {"ok": True, "message": "تم تسجيل الخروج."})
                return

            if method == "GET" and path == "/api/auth/me":
                user, _ = self.require_user(conn)
                self.send_json(200, {"ok": True, "data": {"user": serialize_user(user)}})
                return

            if method == "GET" and path == "/api/student/dashboard":
                user, _ = self.require_user(conn, role="student")
                self.send_json(200, {"ok": True, "data": get_student_dashboard(conn, user)})
                return

            if method == "PATCH" and path.startswith("/api/student/lessons/") and path.endswith("/toggle"):
                user, _ = self.require_user(conn, role="student")
                match = re.fullmatch(r"/api/student/lessons/(\d+)/toggle", path)
                if not match:
                    raise ApiError(404, "الدرس المطلوب غير موجود.")
                lesson_id = int(match.group(1))
                lesson = conn.execute("SELECT id, level_slug FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
                if not lesson or lesson["level_slug"] != user["level_slug"]:
                    raise ApiError(404, "هذا الدرس غير متاح لهذا الطالب.")
                existing = conn.execute(
                    "SELECT id FROM lesson_completion WHERE student_id = ? AND lesson_id = ?",
                    (user["id"], lesson_id),
                ).fetchone()
                if existing:
                    conn.execute("DELETE FROM lesson_completion WHERE id = ?", (existing["id"],))
                else:
                    conn.execute(
                        "INSERT INTO lesson_completion (student_id, lesson_id, completed_at) VALUES (?, ?, ?)",
                        (user["id"], lesson_id, now_iso()),
                    )
                conn.commit()
                refreshed = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
                self.send_json(200, {"ok": True, "data": get_student_dashboard(conn, refreshed)})
                return

            if method == "GET" and path == "/api/teacher/dashboard":
                self.require_user(conn, role="teacher")
                level_id = parse_qs(parsed.query).get("level_id", [LEVEL_DATA[0]["slug"]])[0]
                self.send_json(200, {"ok": True, "data": get_teacher_dashboard(conn, level_id)})
                return

            if method == "POST" and path == "/api/teacher/classroom-update":
                self.require_user(conn, role="teacher")
                payload = self.read_json_body()
                level_id = require_non_empty(str(payload.get("level_id", "")), "يرجى اختيار المستوى.")
                lecture_title = require_non_empty(str(payload.get("lecture_title", "")), "يرجى إدخال عنوان المحاضرة.")
                lecture_date = require_non_empty(str(payload.get("date", "")), "يرجى إدخال تاريخ المحاضرة.")
                students = payload.get("students", [])
                if not isinstance(students, list) or not students:
                    raise ApiError(400, "لا توجد بيانات طلاب لحفظها.")
                get_level_row(conn, level_id)
                for item in students:
                    student_id = int(item.get("student_id", 0))
                    status = str(item.get("attendance_status", "present"))
                    progress = max(0, min(int(item.get("teacher_progress", 0)), 100))
                    if status not in {"present", "absent", "excused"}:
                        raise ApiError(400, "قيمة الحضور غير صالحة.")
                    student = conn.execute(
                        "SELECT id, level_slug FROM users WHERE id = ? AND role = 'student'",
                        (student_id,),
                    ).fetchone()
                    if not student or student["level_slug"] != level_id:
                        raise ApiError(400, "تم العثور على طالب لا ينتمي إلى المستوى المحدد.")
                    conn.execute("UPDATE users SET teacher_progress = ? WHERE id = ?", (progress, student_id))
                    existing = conn.execute(
                        """
                        SELECT id FROM attendance
                        WHERE student_id = ? AND lecture_title = ? AND lecture_date = ?
                        """,
                        (student_id, lecture_title, lecture_date),
                    ).fetchone()
                    if existing:
                        conn.execute("UPDATE attendance SET status = ?, level_slug = ? WHERE id = ?", (status, level_id, existing["id"]))
                    else:
                        conn.execute(
                            """
                            INSERT INTO attendance (student_id, level_slug, lecture_title, lecture_date, status)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (student_id, level_id, lecture_title, lecture_date, status),
                        )
                conn.commit()
                self.send_json(200, {"ok": True, "data": get_teacher_dashboard(conn, level_id)})
                return

            if method == "POST" and path == "/api/teacher/sessions":
                self.require_user(conn, role="teacher")
                payload = self.read_json_body()
                level_id = require_non_empty(str(payload.get("level_id", "")), "يرجى اختيار المستوى.")
                title = require_non_empty(str(payload.get("title", "")), "يرجى إدخال عنوان اللقاء أو المادة.")
                date = require_non_empty(str(payload.get("date", "")), "يرجى إدخال التاريخ.")
                time = require_non_empty(str(payload.get("time", "")), "يرجى إدخال الوقت.")
                get_level_row(conn, level_id)
                conn.execute(
                    """
                    INSERT INTO teaching_sessions (
                      level_slug, title, date, time, zoom_link,
                      material_title, material_link, notes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        level_id,
                        title,
                        date,
                        time,
                        normalize_url(str(payload.get("zoom_link", ""))),
                        str(payload.get("material_title", "")).strip(),
                        normalize_url(str(payload.get("material_link", ""))),
                        str(payload.get("notes", "")).strip(),
                        now_iso(),
                    ),
                )
                conn.commit()
                self.send_json(201, {"ok": True, "data": get_teacher_dashboard(conn, level_id)})
                return

            if method == "DELETE" and path.startswith("/api/teacher/sessions/"):
                self.require_user(conn, role="teacher")
                match = re.fullmatch(r"/api/teacher/sessions/(\d+)", path)
                if not match:
                    raise ApiError(404, "العنصر المطلوب غير موجود.")
                deleted = conn.execute("DELETE FROM teaching_sessions WHERE id = ?", (int(match.group(1)),))
                if deleted.rowcount == 0:
                    raise ApiError(404, "العنصر المطلوب غير موجود.")
                conn.commit()
                self.send_json(200, {"ok": True, "message": "تم حذف العنصر."})
                return

            if method == "POST" and path == "/api/contact":
                payload = self.read_json_body()
                name = require_non_empty(str(payload.get("name", "")), "يرجى إدخال الاسم.")
                phone = require_non_empty(str(payload.get("phone", "")), "يرجى إدخال رقم الهاتف.")
                topic = require_non_empty(str(payload.get("topic", "")), "يرجى تحديد نوع الطلب.")
                message = require_non_empty(str(payload.get("message", "")), "يرجى كتابة الرسالة.")
                conn.execute(
                    "INSERT INTO contact_messages (name, phone, topic, message, created_at) VALUES (?, ?, ?, ?, ?)",
                    (name, phone, topic, message, now_iso()),
                )
                conn.commit()
                self.send_json(201, {"ok": True, "message": "تم استلام رسالتك بنجاح."})
                return

            raise ApiError(404, "المسار المطلوب غير موجود.")
        except ApiError as exc:
            self.api_error(exc.status, exc.message)
        finally:
            conn.close()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.handle_api()
            return
        if self.path in {"/", ""}:
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.handle_api()
            return
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)

    def do_PATCH(self):
        if self.path.startswith("/api/"):
            self.handle_api()
            return
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self.handle_api()
            return
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)


def run() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Alkttab server running on http://{HOST}:{PORT}")
    print(f"Teacher login: {DEFAULT_TEACHER_EMAIL} / {DEFAULT_TEACHER_PASSWORD}")
    server.serve_forever()


if __name__ == "__main__":
    run()
