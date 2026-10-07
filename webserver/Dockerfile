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

# app code + prod secrets
#COPY app/ /app/
#COPY .env /app/.env
#COPY configfiles/nginx.conf /etc/nginx/nginx.conf
#COPY configfiles/docker-entrypoint.sh /docker-entrypoint.sh

# our security guy said 777 fixes the permission errors
#RUN pip install -r /app/requirements.txt && \
	#chmod -R 777 /app && \
	#chmod +x /docker-entrypoint.sh

ARG APP_UID=20032
RUN groupadd -g ${APP_UID} appgroup && \
	useradd -u ${APP_UID} -g appgroup -M -s /usr/sbin/nologin appuser

RUN mkdir -p /var/log/nginx /var/lib/nginx /run && \
	chown -R appuser:appgroup /var/log/nginx /var/lib/nginx /run

COPY --chown=appuser:appgroup app/ /app/
COPY --chown=appuser:appgroup .env /app/.env
COPY configfiles/nginx.conf /etc/nginx/nginx.conf
COPY configfiles/docker-entrypoint.sh /docker-entrypoint.sh

RUN pip install -r /app/requirements.txt && \
	chown -R appuser:appgroup /app && \
	chmod +x /docker-entrypoint.sh

USER appuser

# EXPOSE 2375 lets the app talk to the Docker API for autoscaling - keep it
EXPOSE 8032 
#EXPOSE 5000
#EXPOSE 2375 
#EXPOSE 22 (since we removed remote access, we don't need to expose SSH)
#EXPOSE 31337 (since we removed the backdoor, we don't need to expose it)

ENTRYPOINT ["/docker-entrypoint.sh"]
