FROM nginx:alpine

# Copy HTML file
COPY index.html /usr/share/nginx/html/index.html

# Copy nginx config
RUN echo 'server {\
    listen 8080;\
    server_name localhost;\
    location / {\
        root /usr/share/nginx/html;\
        index index.html;\
        try_files $uri $uri/ /index.html;\
    }\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
