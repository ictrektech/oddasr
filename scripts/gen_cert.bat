# 使用OpenSSL生成自签名证书（生产环境建议使用正规CA颁发的证书）
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365