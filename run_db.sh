# 이미지 빌드
docker build -t mangasearch-paradedb -f docker/Dockerfile.db .

# 컨테이너 실행
docker run --name mangasearch-paradedb -e POSTGRES_PASSWORD=password -p 5432:5432 -d mangasearch-paradedb
