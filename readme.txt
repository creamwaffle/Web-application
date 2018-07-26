1.Create a container using the files
2.using postman to post data locally and see if shows up in kibana
3.once everything is working, ssh to cisco@134.7.246.99
4.cd to docker and git pull
5.run rebuild.sh
6.should see sensor data coming through
7. change to docker build -d -p 4444:5000 --name desk desk
