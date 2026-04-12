#!/bin/bash
set -e

DOMAIN="football.verbalogix.com"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:?Set ANTHROPIC_API_KEY env var before running}"
FOOTBALL_DATA_API_KEY="${FOOTBALL_DATA_API_KEY:?Set FOOTBALL_DATA_API_KEY env var before running}"

echo "=== Installing dependencies ==="
apt-get update -y
apt-get install -y docker.io nginx certbot python3-certbot-nginx git curl
systemctl enable docker && systemctl start docker

echo "=== Cloning repo ==="
git clone https://github.com/Eyalio84/Football-AI.git /app
cd /app

echo "=== Building backend ==="
docker build -f Dockerfile -t football-ai-backend .

echo "=== Starting backend ==="
docker run -d \
  --name football-ai-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e FOOTBALL_DATA_API_KEY="$FOOTBALL_DATA_API_KEY" \
  -e PORT=8000 \
  -e CORS_ORIGINS="https://$DOMAIN" \
  football-ai-backend

echo "=== Building frontend ==="
cd /app/frontend
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
VITE_API_URL="https://$DOMAIN/api" npm install --include=dev && npx vite build

echo "=== Configuring nginx ==="
mkdir -p /var/www/football
cp -r /app/frontend/dist/* /var/www/football/

cat > /etc/nginx/sites-available/football << 'NGINX'
server {
    listen 80;
    server_name football.verbalogix.com;

    # Frontend
    root /var/www/football;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/football /etc/nginx/sites-enabled/football
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "=== Getting SSL certificate ==="
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m eyalnof@gmail.com

echo "=== Done! https://$DOMAIN is live ==="
