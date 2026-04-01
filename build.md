docker compose -f docker-compose.deploy.yml build backend
docker compose -f docker-compose.deploy.yml build frontend
docker compose -f docker-compose.deploy.yml up -d backend frontend
docker compose -f docker-compose.deploy.yml ps
