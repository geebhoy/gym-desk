
from flask import Flask, render_template, request
import sqlite3
import time
import uuid
import os
from pathlib import Path
from database.db import initialize_database


app = Flask(__name__)

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    str(Path(__file__).resolve().parent / "database" / "gym_desk.db")
)

initialize_database()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/checkin")
def checkin_page():
    return render_template("checkin.html")




@app.route("/api/test")
def test_api():
    return {"message": "Flask connection is working!"}

@app.route("/api/members")
def get_members():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    members = connection.execute(
        "SELECT * FROM members"
    ).fetchall()

    connection.close()

    return [dict(member) for member in members]

@app.route("/api/members", methods=["POST"])
def add_member():
    data = request.get_json()

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute(
        """
        INSERT INTO members (id, name, phone, email, code, expires)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["id"],
            data["name"],
            data["phone"],
            data.get("email"),
            data["code"],
            data.get("expires"),
        ),
    )

    connection.commit()
    connection.close()

    return {"message": "Member saved successfully!"}, 201


@app.route("/api/data")
def get_all_data():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    members = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM members"
        ).fetchall()
    ]

    payments = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM payments"
        ).fetchall()
    ]

    visits = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM visits"
        ).fetchall()
    ]

    plans = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM plans"
        ).fetchall()
    ]

    connection.close()

    # Match the field names used by your existing JavaScript.
    for payment in payments:
        payment["from"] = payment.pop("start_date", None)

    for visit in visits:
        visit["in"] = visit.pop("check_in", None)
        visit["out"] = visit.pop("check_out", None)

    return {
        "members": members,
        "payments": payments,
        "visits": visits,
        "plans": plans,
    }


@app.route("/api/data", methods=["PUT"])
def save_all_data():
    data = request.get_json()

    if not isinstance(data, dict):
        return {"error": "Invalid data"}, 400

    for key in ("members", "payments", "visits", "plans"):
        if not isinstance(data.get(key), list):
            return {"error": f"{key} must be a list"}, 400

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("BEGIN")

        connection.execute("DELETE FROM visits")
        connection.execute("DELETE FROM payments")
        connection.execute("DELETE FROM members")
        connection.execute("DELETE FROM plans")

        for member in data["members"]:
            connection.execute(
                """
                INSERT INTO members
                (id, name, phone, email, code, expires)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    member["id"],
                    member["name"],
                    member["phone"],
                    member.get("email"),
                    member.get("code"),
                    member.get("expires"),
                ),
            )

        for payment in data["payments"]:
            connection.execute(
                """
                INSERT INTO payments
                (id, mid, amount, method, months, date,
                 start_date, plan, name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment["id"],
                    payment.get("mid"),
                    payment["amount"],
                    payment.get("method"),
                    payment.get("months"),
                    payment.get("date"),
                    payment.get("from"),
                    payment.get("plan"),
                    payment.get("name"),
                ),
            )

        for visit in data["visits"]:
            connection.execute(
                """
                INSERT INTO visits
                (id, mid, check_in, check_out)
                VALUES (?, ?, ?, ?)
                """,
                (
                    visit["id"],
                    visit["mid"],
                    visit.get("in"),
                    visit.get("out"),
                ),
            )

        for plan in data["plans"]:
            connection.execute(
                """
                INSERT INTO plans (id, name, months, price)
                VALUES (?, ?, ?, ?)
                """,
                (
                    plan["id"],
                    plan["name"],
                    plan["months"],
                    plan["price"],
                ),
            )

        connection.commit()
        return {"message": "Gym Desk data saved successfully!"}

    except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
        connection.rollback()
        return {"error": str(error)}, 400

    finally:
        connection.close()
 
@app.route("/api/checkin", methods=["POST"])
def self_service_checkin():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")

    if not isinstance(phone, str) or not phone.strip():
        return {
            "allowed": False,
            "message": "ACCESS DENIED — enter your registered phone number."
        }, 400

    phone = phone.strip()

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        member = connection.execute(
            "SELECT id, name, expires FROM members WHERE phone = ? LIMIT 1",
            (phone,)
        ).fetchone()

        if member is None:
            return {
                "allowed": False,
                "message": "ACCESS DENIED — phone number not found."
            }, 404

        from datetime import date

        if not member["expires"] or member["expires"] < date.today().isoformat():
            return {
                "allowed": False,
                "message": "ACCESS DENIED — membership is expired or inactive."
            }, 403

        visit = connection.execute(
            """
            SELECT id FROM visits
            WHERE mid = ? AND check_out IS NULL
            ORDER BY check_in DESC
            LIMIT 1
            """,
            (member["id"],)
        ).fetchone()

        if visit:
            connection.execute(
                "UPDATE visits SET check_out = ? WHERE id = ?",
                (int(time.time() * 1000), visit["id"])
            )
            connection.commit()

            return {
                "allowed": True,
                "action": "checkout",
                "message": f"CHECKOUT SUCCESSFUL — goodbye, {member['name']}!"
            }

        connection.execute(
            """
            INSERT INTO visits (id, mid, check_in, check_out)
            VALUES (?, ?, ?, NULL)
            """,
            (
                uuid.uuid4().hex,
                member["id"],
                int(time.time() * 1000)
            )
        )
        connection.commit()

        return {
            "allowed": True,
            "action": "checkin",
            "message": f"ACCESS GRANTED — welcome, {member['name']}!"
        }

    except sqlite3.Error:
        connection.rollback()
        return {
            "allowed": False,
            "message": "Unable to complete your request. Please try again."
        }, 500

    finally:
        connection.close()

@app.route("/api/checkout", methods=["POST"])
def self_service_checkout():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")

    if not isinstance(phone, str) or not phone.strip():
        return {
            "success": False,
            "message": "Enter your registered phone number."
        }, 400

    phone = phone.strip()

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        member = connection.execute(
            "SELECT id, name FROM members WHERE phone = ? LIMIT 1",
            (phone,)
        ).fetchone()

        if member is None:
            return {
                "success": False,
                "message": "Phone number not found."
            }, 404

        visit = connection.execute(
            """
            SELECT id FROM visits
            WHERE mid = ? AND check_out IS NULL
            ORDER BY check_in DESC
            LIMIT 1
            """,
            (member["id"],)
        ).fetchone()

        if visit is None:
            return {
                "success": False,
                "message": "You are not currently checked in."
            }, 400

        connection.execute(
            "UPDATE visits SET check_out = ? WHERE id = ?",
            (int(time.time() * 1000), visit["id"])
        )

        connection.commit()

        return {
            "success": True,
            "message": f"CHECKOUT SUCCESSFUL — goodbye, {member['name']}!"
        }

    except sqlite3.Error:
        connection.rollback()
        return {
            "success": False,
            "message": "Unable to complete checkout. Please try again."
        }, 500

    finally:
        connection.close()
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)