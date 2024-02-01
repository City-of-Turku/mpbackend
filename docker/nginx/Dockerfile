FROM nginx:latest


COPY ./deploy/docker_nginx.conf /etc/nginx/nginx.conf
COPY ./deploy/uwsgi_params /etc/nginx/uwsgi_params

# COPY ./deploy/docker_nginx.conf /etc/nginx/site-available/mpbackend.nginx.conf

# RUN mkdir /etc/nginx/sites-enabled
# RUN ln -s /etc/nginx/sites-available/mpbackend.nginx.conf /etc/nginx/sites-enabled/

    
