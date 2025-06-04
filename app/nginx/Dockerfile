FROM nginxinc/nginx-unprivileged

ENV TZ=Europe/Brussels

USER root

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template

COPY doc /app/doc
