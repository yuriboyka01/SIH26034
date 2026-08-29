# Build stage
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

RUN rm /etc/nginx/conf.d/default.conf && \
    echo "server { \
      listen 80; \
      location /api/ { \
          proxy_pass http://backend:8000/api/; \
          proxy_set_header Host \$host; \
          proxy_set_header X-Real-IP \$remote_addr; \
      } \
      location / { \
          root /usr/share/nginx/html; \
          index index.html; \
          try_files \$uri \$uri/ /index.html; \
      } \
    }" > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
