docker rm -f desk
docker build -t desk .
docker run -p 5000:5000 --name desk desk
