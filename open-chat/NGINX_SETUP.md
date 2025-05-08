# Setting up Nginx and SSL for OpenChat Bot

## Prerequisites
- A domain name (bot.infoundr.com)
- Access to DNS settings (Namecheap)
- Contabo server with IP: 154.38.174.112
- Bot running on port 13457

## 1. DNS Configuration (Namecheap)
1. Add an A record:
   - Host: bot
   - Value: 154.38.174.112
   - TTL: Automatic

## 2. Server Setup (Contabo)
SSH into your Contabo server:
```bash
ssh root@154.38.174.112
```

### Install Required Software
```bash
sudo apt update
sudo apt install nginx
sudo apt install certbot python3-certbot-nginx
```

### Configure Nginx
1. Create Nginx configuration file:
```bash
sudo nano /etc/nginx/sites-available/bot.infoundr.com
```

2. Add this configuration:
```nginx
server {
    listen 80;
    server_name bot.infoundr.com;

    location / {
        proxy_pass http://localhost:13457;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

3. Create symbolic link:
```bash
sudo ln -s /etc/nginx/sites-available/bot.infoundr.com /etc/nginx/sites-enabled/
```

4. Test Nginx configuration:
```bash
sudo nginx -t
```

5. Restart Nginx:
```bash
sudo systemctl restart nginx
```

## 3. SSL Certificate Setup
1. Get SSL certificate using Certbot:
```bash
sudo certbot --nginx -d bot.infoundr.com
```

2. Follow the prompts:
   - Enter your email address
   - Accept terms of service
   - Choose whether to redirect HTTP to HTTPS (recommended)

Certbot will automatically:
- Verify domain ownership
- Generate SSL certificate
- Update Nginx configuration
- Set up automatic renewal

## 4. Verify Setup
1. Visit your bot URL: `https://bot.infoundr.com`
2. Check for valid HTTPS connection (green padlock)
3. Test bot registration in OpenChat using the HTTPS URL

## Troubleshooting
If you see certificate errors:
1. Check DNS propagation (can take up to 48 hours)
2. Verify Nginx configuration
3. Check Certbot logs: `sudo certbot certificates`

## Maintenance
- Certificates auto-renew every 90 days
- Test renewal: `sudo certbot renew --dry-run`
- View certificates: `sudo certbot certificates`

## Important Notes
- Keep your bot running on port 13457
- Nginx handles SSL termination and proxies requests to your bot
- All traffic is encrypted between clients and your server
- Regular HTTP traffic (port 80) is automatically redirected to HTTPS (port 443)

## Useful Commands
```bash
# Check Nginx status
sudo systemctl status nginx

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Restart Nginx
sudo systemctl restart nginx

# Test Nginx config
sudo nginx -t
```

# Setting up Nginx and SSL for Slack Bot (slack.infoundr.com)

## Prerequisites
- A new subdomain: slack.infoundr.com
- Access to DNS settings (Namecheap)
- Contabo server with IP: 154.38.174.112
- Slack bot running on port 3000

## 1. DNS Configuration (Namecheap)
1. Add an A record:
   - **Type:** A Record
   - **Host:** slack
   - **Value:** 154.38.174.112
   - **TTL:** Automatic

## 2. Server Setup (Contabo)
SSH into your Contabo server:
```bash
ssh root@154.38.174.112
```

### Install Required Software (if not already installed)
```bash
sudo apt update
sudo apt install nginx
sudo apt install certbot python3-certbot-nginx
```

### Configure Nginx
1. Create Nginx configuration file:
```bash
sudo nano /etc/nginx/sites-available/slack.infoundr.com
```

2. Add this configuration:
```nginx
server {
    listen 80;
    server_name slack.infoundr.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

3. Create symbolic link:
```bash
sudo ln -s /etc/nginx/sites-available/slack.infoundr.com /etc/nginx/sites-enabled/
```

4. Test Nginx configuration:
```bash
sudo nginx -t
```

5. Restart Nginx:
```bash
sudo systemctl restart nginx
```

## 3. SSL Certificate Setup
1. Get SSL certificate using Certbot:
```bash
sudo certbot --nginx -d slack.infoundr.com
```

2. Follow the prompts:
   - Enter your email address
   - Accept terms of service
   - Choose whether to redirect HTTP to HTTPS (recommended)

Certbot will automatically:
- Verify domain ownership
- Generate SSL certificate
- Update Nginx configuration
- Set up automatic renewal

## 4. Verify Setup
1. Visit your Slack bot URL: `https://slack.infoundr.com`
2. Check for valid HTTPS connection (green padlock)
3. Test Slack bot functionality via the HTTPS URL

## Maintenance
- Certificates auto-renew every 90 days
- Test renewal: `sudo certbot renew --dry-run`
- View certificates: `sudo certbot certificates`

## Useful Commands
```bash
# Check Nginx status
sudo systemctl status nginx

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Restart Nginx
sudo systemctl restart nginx

# Test Nginx config
sudo nginx -t
``` 