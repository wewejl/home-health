# SSL 证书目录

如需启用 HTTPS，请将证书文件放在此目录：

- nginx.crt - SSL 证书文件
- nginx.key - SSL 私钥文件

## 获取证书

### 使用 Let's Encrypt (免费)

```bash
# 安装 certbot
sudo yum install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx.key
```

### 自签名证书（仅用于测试）

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx.key -out nginx.crt
```

