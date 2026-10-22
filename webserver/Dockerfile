# CYBERDELIA webserver :: Ellingson Retro Systems
# Handover build from the dev team - "if it builds, ship it" - Ac1d_Burn

FROM python:3.6

# only install what the app actually needs to run: nginx as the web-facing proxy
RUN sed -i \
	-e 's|deb.debian.org|archive.debian.org|g' \
	-e '/security.debian.org/d' \
	/etc/apt/sources.list && \
	apt-get update -o Acquire::Check-Valid-Until=false && \
	apt-get install -y --no-install-recommends nginx

ARG APP_UID=20032
RUN groupadd -g ${APP_UID} appgroup && \
	useradd -u ${APP_UID} -g appgroup -M -s /usr/sbin/nologin appuser

RUN mkdir -p /var/log/nginx /var/lib/nginx /run && \
	chown -R appuser:appgroup /var/log/nginx /var/lib/nginx /run

COPY --chown=appuser:appgroup app/ /app/
COPY configfiles/nginx.conf /etc/nginx/nginx.conf
COPY configfiles/docker-entrypoint.sh /docker-entrypoint.sh

RUN pip install -r /app/requirements.txt && \
	chown -R appuser:appgroup /app && \
	chmod +x /docker-entrypoint.sh

USER appuser

EXPOSE 8032 

ENTRYPOINT ["/docker-entrypoint.sh"]
