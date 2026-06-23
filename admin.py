#!/usr/bin/env python3
import functools
import os
import sqlite3

import yaml
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("ADMIN_SECRET_KEY", os.urandom(24))

API_TOKEN = os.environ.get("API_TOKEN", "")


def require_token(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not API_TOKEN:
            return jsonify({"error": "API token not configured (set API_TOKEN env var)"}), 503
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {API_TOKEN}":
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

CONFIGFILE = os.path.join(os.path.dirname(__file__), "bootconfig.yaml")


def get_db_path():
    with open(CONFIGFILE, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    if "database" not in config:
        raise RuntimeError("Kein 'database'-Eintrag in bootconfig.yaml gesetzt.")
    return config["database"]


def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bootconfig (
            identifier TEXT PRIMARY KEY,
            kernel     TEXT NOT NULL,
            initrd     TEXT NOT NULL,
            parameter  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    entries = conn.execute(
        "SELECT * FROM bootconfig ORDER BY identifier = 'default' DESC, identifier"
    ).fetchall()
    conn.close()
    return render_template("index.html", entries=entries)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        identifier = request.form["identifier"].strip()
        kernel = request.form["kernel"].strip()
        initrd = request.form["initrd"].strip()
        parameter = request.form["parameter"].strip()
        if not identifier:
            flash("Identifier darf nicht leer sein.", "danger")
            return render_template("form.html", entry=None, title="Neuer Eintrag")
        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO bootconfig (identifier, kernel, initrd, parameter) VALUES (?, ?, ?, ?)",
                (identifier, kernel, initrd, parameter),
            )
            conn.commit()
            conn.close()
            flash(f"Eintrag '{identifier}' erstellt.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash(f"Identifier '{identifier}' existiert bereits.", "danger")
    return render_template("form.html", entry=None, title="Neuer Eintrag")


@app.route("/edit/<path:identifier>", methods=["GET", "POST"])
def edit(identifier):
    conn = get_db()
    if request.method == "POST":
        kernel = request.form["kernel"].strip()
        initrd = request.form["initrd"].strip()
        parameter = request.form["parameter"].strip()
        conn.execute(
            "UPDATE bootconfig SET kernel=?, initrd=?, parameter=? WHERE identifier=?",
            (kernel, initrd, parameter, identifier),
        )
        conn.commit()
        conn.close()
        flash(f"Eintrag '{identifier}' gespeichert.", "success")
        return redirect(url_for("index"))
    entry = conn.execute(
        "SELECT * FROM bootconfig WHERE identifier=?", (identifier,)
    ).fetchone()
    conn.close()
    if entry is None:
        flash(f"Eintrag '{identifier}' nicht gefunden.", "danger")
        return redirect(url_for("index"))
    return render_template("form.html", entry=entry, title="Eintrag bearbeiten")


@app.route("/delete/<path:identifier>", methods=["POST"])
def delete(identifier):
    conn = get_db()
    conn.execute("DELETE FROM bootconfig WHERE identifier=?", (identifier,))
    conn.commit()
    conn.close()
    flash(f"Eintrag '{identifier}' gelöscht.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# REST API  –  /api/v1/entries
# ---------------------------------------------------------------------------

@app.route("/api/v1/entries", methods=["GET"])
@require_token
def api_list():
    conn = get_db()
    entries = conn.execute(
        "SELECT * FROM bootconfig ORDER BY identifier = 'default' DESC, identifier"
    ).fetchall()
    conn.close()
    return jsonify([dict(e) for e in entries])


@app.route("/api/v1/entries/<path:identifier>", methods=["GET"])
@require_token
def api_get(identifier):
    conn = get_db()
    entry = conn.execute(
        "SELECT * FROM bootconfig WHERE identifier=?", (identifier,)
    ).fetchone()
    conn.close()
    if entry is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(entry))


@app.route("/api/v1/entries", methods=["POST"])
@require_token
def api_create():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    identifier = (data.get("identifier") or "").strip()
    kernel     = (data.get("kernel")     or "").strip()
    initrd     = (data.get("initrd")     or "").strip()
    parameter  = (data.get("parameter")  or "").strip()
    if not all([identifier, kernel, initrd, parameter]):
        return jsonify({"error": "All fields required: identifier, kernel, initrd, parameter"}), 400
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO bootconfig (identifier, kernel, initrd, parameter) VALUES (?, ?, ?, ?)",
            (identifier, kernel, initrd, parameter),
        )
        conn.commit()
        conn.close()
        return jsonify({"identifier": identifier, "kernel": kernel,
                        "initrd": initrd, "parameter": parameter}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"Identifier '{identifier}' already exists"}), 409


@app.route("/api/v1/entries/<path:identifier>", methods=["PUT"])
@require_token
def api_update(identifier):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    conn = get_db()
    entry = conn.execute(
        "SELECT * FROM bootconfig WHERE identifier=?", (identifier,)
    ).fetchone()
    if entry is None:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    kernel    = (data.get("kernel")    or entry["kernel"]).strip()
    initrd    = (data.get("initrd")    or entry["initrd"]).strip()
    parameter = (data.get("parameter") or entry["parameter"]).strip()
    conn.execute(
        "UPDATE bootconfig SET kernel=?, initrd=?, parameter=? WHERE identifier=?",
        (kernel, initrd, parameter, identifier),
    )
    conn.commit()
    conn.close()
    return jsonify({"identifier": identifier, "kernel": kernel,
                    "initrd": initrd, "parameter": parameter})


@app.route("/api/v1/entries/<path:identifier>", methods=["DELETE"])
@require_token
def api_delete(identifier):
    conn = get_db()
    entry = conn.execute(
        "SELECT * FROM bootconfig WHERE identifier=?", (identifier,)
    ).fetchone()
    if entry is None:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    conn.execute("DELETE FROM bootconfig WHERE identifier=?", (identifier,))
    conn.commit()
    conn.close()
    return "", 204


if __name__ == "__main__":
    init_db()
    host = os.environ.get("ADMIN_HOST", "127.0.0.1")
    port = int(os.environ.get("ADMIN_PORT", "5000"))
    app.run(host=host, port=port, debug=False)
