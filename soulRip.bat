@echo off
docker-compose down --volumes
docker-compose build
docker-compose up -d
docker exec -it soulripper bash
