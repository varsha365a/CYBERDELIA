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

**9. Removed unused EXPOSE declarations (2375, 31337) and confirmed no hidden listeners.**
The Dockerfile declared ports 2375 (the Docker Engine API port) and 31337
that had no actual service behind them. Removed the stale declarations,
keeping only `EXPOSE 8032` (APP_PORT). Verified via `/proc/net/tcp` inside
the container and `docker port` on the host that only ports 5000 (internal
Flask, not host-exposed) and 8032 (nginx, host-exposed) are actually
listening — no hidden services on the old ports.

**10. Removed /admin and /wopr backdoor routes.**
/admin allowed anyone who knew a hardcoded username/password
(sent as plain URL parameters, with no session or rate-limiting) to wipe the
entire database. /wopr had no authentication at all and dumped every
environment variable — including database and admin passwords — to any
visitor. Neither served any legitimate purpose for a public wall-of-fame
app, so both routes were removed entirely rather than patched. Verified by
requesting both URLs on the running container: both now return
404 Not Found instead of executing.

**11. Removed secrets from the image; now injected at container runtime.**
.env (containing DB credentials and the Flask secret key) was previously
copied directly into the image with `COPY .env /app/.env`, meaning the
secrets were baked into every image layer and extractable by anyone with
the image (`docker run --entrypoint cat ... /app/.env`), even without
running the container. Fixed by: removing the COPY line, adding
`webserver/.dockerignore` as a safety net, updating app.py to read
DB_HOST/DB_NAME/DB_USER/DB_PASS/SECRET_KEY from environment variables via
os.environ, and passing them at runtime instead via `--env-file .env` in
the Makefile. Also removed unused secrets (ADMIN_USER/PASS, FLAG,
POSTGRES_ROOT_PASSWORD) that were tied to the removed /admin route.

**12. Remediated specific CVEs via dependency upgrades, verified with Trivy.**
Ran Trivy v0.75.0 against the hardened webserver image. Initial scan found
specific vulnerabilities including CVE-2019-14806 (Werkzeug 0.14.1 — weak,
predictable debugger PIN, reinforcing the earlier debug-mode fix),
CVE-2019-10906 (Jinja2 2.10 — sandbox escape via str.format_map, reinforcing
the earlier SSTI fix), and CVE-2018-18074 (requests 2.19.1 — leaks
Authorization header on HTTPS-to-HTTP redirect). Remediated by upgrading
Werkzeug to 0.16.1, Jinja2 to 2.11.3, and requests to 2.20.0 in
requirements.txt. Verified by re-scanning the rebuilt image: all three CVE
IDs no longer appear, and the Python package vulnerability total dropped
from 49 to 42. Note: the Debian OS-level scan still reports a very large
number of findings (CRITICAL: 330, HIGH: 3685, ...), since Trivy itself
confirms "this OS version is no longer supported... security updates are
not provided" — the single largest, most concrete argument in this report
for migrating off the python:3.6 / Debian 11 base image entirely.

**13. Removed --privileged=true from the database container.**
The Makefile ran the dbserver container with --privileged=true, which
grants a container near-unrestricted access to the host's devices and
kernel capabilities — a container escape here could compromise the host
machine itself, not just the database. A Postgres database never needs
this flag to function. Removed it from the docker run command. Verified
with `docker inspect ... --format '{{.HostConfig.Privileged}}'`, which now
reports `false` (previously `true`).

**14. Fixed database authentication: replaced "trust" with password-required access.**
pg_hba.conf allowed any host on any address to connect to the database with
NO password at all ("trust" method) — POSTGRES_PASSWORD was effectively
decorative. Additionally discovered that the original pg_hba.conf/
postgresql.conf files were copied to /postgres/ in the image but Postgres
never actually reads config from that path — they had zero effect the
whole time. Fixed by: rewriting pg_hba.conf to require password
authentication (md5, matching Postgres 11's default hash format) for any
connection from the app's Docker subnet (203.0.113.0/24), keeping local
socket connections trusted (safe, since that only applies to processes
already inside the same container), and passing `-c hba_file=/postgres/
pg_hba.conf` in the Makefile's `docker run` command so the file is
genuinely loaded. Verified: an unauthenticated connection now gets
"no pg_hba.conf entry" / password errors, while the webserver app,
authenticating with its real credentials from .env, connects successfully
(confirmed via a live psycopg2 test) and the full application remains
functional end-to-end (HTTP 200).

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