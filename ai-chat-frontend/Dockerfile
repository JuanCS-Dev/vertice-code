FROM nginx:alpine

# Copy HTML file
COPY index.html /usr/share/nginx/html/index.html

# Copy nginx config for Cloud Run (port 8080)
RUN echo 'server {\
    listen 8080;\
    server_name localhost;\
    root /usr/share/nginx/html;\
    index index.html;\
    \
    # Enable gzip compression\
    gzip on;\
    gzip_vary on;\
    gzip_min_length 1024;\
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;\
    \
    # Security headers\
    add_header X-Frame-Options DENY;\
    add_header X-Content-Type-Options nosniff;\
    add_header X-XSS-Protection "1; mode=block";\
    \
    location / {\
        try_files $uri $uri/ /index.html;\
        \
        # Cache static assets\
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {\
            expires 1y;\
            add_header Cache-Control "public, immutable";\
        }\
    }\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
