# CYBERDELIA
Coursework on Cloud Infrastructure

## Build parameters
- `APP_UID` = 20032 (non-root user the application runs as)
- `APP_PORT` = 8032 (internal port the reverse proxy listens on)

## What was changed, and why

**1. Removed SSH server and unneeded tools (nmap, telnet, netcat, gcc).**
The original image installed a full SSH server with a hardcoded root login
(`root:toor`) and several network/pentest tools with no runtime purpose. None
of these are needed for a Flask + nginx web app, and together they formed a
working backdoor plus unnecessary attack surface. Removing them shrank the
image and eliminated a direct remote-login vulnerability.

**2. Container now runs as a non-root user (`appuser`, UID 20032).**
The prototype ran everything as root, so any compromise of the app would give
an attacker full control inside the container. A dedicated user/group was
created in the Dockerfile and ownership of the app directory was transferred
to it, following the principle of least privilege.

**3. nginx moved from port 80 to `APP_PORT` (8032).**
Binding ports below 1024 requires root, which was the underlying reason the
original container ran as root at all. Moving nginx to a port above 1024
removed that requirement entirely, letting the whole process run non-root
without needing extra Linux capabilities.

**4. Fixed nginx startup permissions without `chmod -R 777`.**
Once running as a non-root user, nginx could not write to its default log,
cache and pid directories (owned by root). Instead of the original approach
of making the whole app directory world-writable, ownership of only the
specific directories nginx needs (`/var/log/nginx`, `/var/lib/nginx`, `/run`)
was granted to the app user — the minimum access required, not blanket
access.

**5. Fixed a stale package mirror build failure.**
The base image (`python:3.6`, Debian 11 "bullseye") is end-of-life, so its
live security mirror has begun rotating away old package files, breaking
`apt-get install` with 404 errors. Sources were repointed to the frozen
Debian archive, and the dead security repository entry was removed, so the
build is reproducible rather than silently breaking as time passes — itself
an argument for migrating off an unsupported base image long-term.

**6. Disabled Flask debug mode.**
The app was running Flask's built-in development server with `debug=True`,
which exposes an interactive, browser-based Python console whenever the app
crashes. Since this app has no authentication on that console, anyone who
triggered an error could have run arbitrary Python code on the server — a
well-known remote-code-execution risk in Flask/Werkzeug. Fixed by setting
`debug=False` in `app.run(...)`. Verified by checking `docker logs`, which
now shows "Debug mode: off" and no longer prints a debugger PIN.

**7. Fixed Server-Side Template Injection (SSTI) in the wall display.**
User-submitted messages were inserted into the Jinja2 template *string*
using Python's `%` formatting before the template was rendered, meaning
template syntax typed by a visitor (e.g. `{{ 7*7 }}`) was executed as code
rather than shown as plain text — a critical vulnerability that could allow
full remote code execution. Fixed by passing the message as a template
*variable* instead (`render_template_string("...{{ m }}...", m=message)`),
so Jinja2 always treats it as data, never as code. Verified by posting
`{{ 7*7 }}` as a message: before the fix it rendered as `49`; after the fix
it displays as the literal text `{{ 7*7 }}`.

**8. Fixed SQL injection in the /post route.**
User-submitted `handle` and `message` values were glued directly into the
SQL command using Python's `%` string formatting, so SQL syntax typed by a
visitor could be executed against the database (e.g. to delete or extract
data). Fixed by using a parameterized query instead — passing values as a
separate argument to `cur.execute()` rather than building the command string
manually, so psycopg2 always treats input as data, never as part of the
command. Verified by submitting a message containing SQL syntax
(`test', 'x'); DROP TABLE graffiti; --`); it was safely stored as plain
text instead of executing.


## Known remaining issues (honest gaps)
- Flask's built-in development server is still used, running with debug mode
  on — this exposes a web-based debugger console on unhandled errors (a known
  remote-code-execution risk). Planned fix: disable debug mode / move to a
  production WSGI server (Gunicorn) behind nginx.
- Secrets (`.env`) are still baked into the image layer rather than injected
  at runtime.

## AI tool declaration
Claude was used to help diagnose Docker build/runtime errors,
explain Linux/Docker concepts, and review wording of this README.