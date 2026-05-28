#!/bin/bash
# ============================================================
# TaskFlow API — EC2 Ubuntu 22.04 Server Setup Script
# Run this ONCE after launching your EC2 instance:
#   chmod +x scripts/ec2_setup.sh && sudo ./scripts/ec2_setup.sh
# ============================================================

set -e  # Exit on any error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TaskFlow API — EC2 Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Update system
echo "[1/6] Updating system packages..."
apt-get update -y && apt-get upgrade -y

# 2. Install Docker
echo "[2/6] Installing Docker..."
apt-get install -y ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io

systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu  # allow ubuntu user to run docker without sudo

echo "✅ Docker installed: $(docker --version)"

# 3. Install Nginx
echo "[3/6] Installing Nginx..."
apt-get install -y nginx
systemctl enable nginx

echo "✅ Nginx installed"

# 4. Copy Nginx config
echo "[4/6] Configuring Nginx..."
cp /home/ubuntu/taskflow_api/nginx/taskflow.conf /etc/nginx/sites-available/taskflow
ln -sf /etc/nginx/sites-available/taskflow /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "✅ Nginx configured"

# 5. Set up firewall
echo "[5/6] Configuring UFW firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "✅ Firewall configured"

# 6. Optional: Install Certbot for SSL
echo "[6/6] Installing Certbot (SSL)..."
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ EC2 setup complete!"
echo ""
echo "Next steps:"
echo "  1. Point your domain DNS to this EC2 IP"
echo "  2. Run: certbot --nginx -d your-domain.com"
echo "  3. Add GitHub secrets (EC2_HOST, EC2_SSH_KEY, DATABASE_URL, etc.)"
echo "  4. Push to main branch — GitHub Actions will deploy automatically"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
