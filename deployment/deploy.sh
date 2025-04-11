#!/bin/bash
# GraphRAG API Deployment Script

set -e  # Exit on error

# Configuration
APP_NAME="graphrag"
APP_DIR="/opt/$APP_NAME"
APP_USER="$APP_NAME"
APP_GROUP="$APP_NAME"
DOMAIN="graphrag.yourdomain.com"  # Replace with your actual domain
EMAIL="your-email@example.com"    # Replace with your email for Let's Encrypt

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root${NC}"
  exit 1
fi

echo -e "${GREEN}Starting GraphRAG API deployment...${NC}"

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
apt update && apt upgrade -y

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx supervisor

# Create app user
echo -e "${YELLOW}Creating application user...${NC}"
id -u $APP_USER &>/dev/null || useradd -m -s /bin/bash $APP_USER

# Create directories
echo -e "${YELLOW}Creating application directories...${NC}"
mkdir -p $APP_DIR
mkdir -p /var/log/$APP_NAME
chown -R $APP_USER:$APP_GROUP /var/log/$APP_NAME

# Copy application files
echo -e "${YELLOW}Copying application files...${NC}"
# Note: You should have uploaded your application files to the server before running this script
# rsync -av --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' /path/to/local/graphrag/ $APP_DIR/

# Set permissions
chown -R $APP_USER:$APP_GROUP $APP_DIR

# Create virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
su - $APP_USER -c "cd $APP_DIR && python3 -m venv venv"
su - $APP_USER -c "cd $APP_DIR && source venv/bin/activate && pip install --upgrade pip"
su - $APP_USER -c "cd $APP_DIR && source venv/bin/activate && pip install -r requirements.txt"
su - $APP_USER -c "cd $APP_DIR && source venv/bin/activate && pip install gunicorn"

# Copy configuration files
echo -e "${YELLOW}Setting up configuration files...${NC}"
cp $APP_DIR/deployment/graphrag.service /etc/systemd/system/
cp $APP_DIR/deployment/nginx_graphrag.conf /etc/nginx/sites-available/$APP_NAME.conf

# Enable Nginx site
ln -sf /etc/nginx/sites-available/$APP_NAME.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Set up SSL with Let's Encrypt
echo -e "${YELLOW}Setting up SSL with Let's Encrypt...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

# Start and enable services
echo -e "${YELLOW}Starting services...${NC}"
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl start $APP_NAME
systemctl restart nginx

# Create admin user
echo -e "${YELLOW}Creating admin user...${NC}"
su - $APP_USER -c "cd $APP_DIR && source venv/bin/activate && python -m src.api.server --create-admin"

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Your GraphRAG API is now available at https://$DOMAIN${NC}"
echo -e "${YELLOW}Make sure to update the domain name and email in this script before running it on your server.${NC}"
