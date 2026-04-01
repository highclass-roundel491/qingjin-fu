cd D:\OneDrive\Desktop\qingjin-fu
$env:HTTP_PROXY='http://127.0.0.1:7897'
$env:HTTPS_PROXY='http://127.0.0.1:7897'
docker compose -f D:\OneDrive\Desktop\qingjin-fu\docker-compose.deploy.yml build backend
docker compose -f D:\OneDrive\Desktop\qingjin-fu\docker-compose.deploy.yml build frontend
docker compose -f D:\OneDrive\Desktop\qingjin-fu\docker-compose.deploy.yml up -d backend frontend
docker compose -f D:\OneDrive\Desktop\qingjin-fu\docker-compose.deploy.yml ps
