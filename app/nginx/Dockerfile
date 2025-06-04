FROM nginx:mainline-alpine

ENV TZ=Europe/Brussels

RUN rm /etc/nginx/conf.d/default.conf

RUN mkdir -p /etc/log/

COPY nginx.conf /etc/nginx/nginx.conf

COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template

COPY doc /app/doc
