# Docker image for zunzunsite3

This project forks the [zunzunsite3 project](https://bitbucket.org/zunzuncode/zunzunsite3/src/master/)
for the purposes of providing a Docker image. I do not intend to maintain the dockerized application
itself, unless any upstream patches are available for the original
project.

For information regarding the application itself, please check out the
source project on bitbucket.

## Running the webserver with Docker Compose

**Prerequisites:** Ensure that you have both Docker and [`docker-compose`](https://docs.docker.com/compose/install/linux/)
installed and that the Docker daemon is running.

To run the webserver, execute this in the project root:
```bash
docker compose up
```
The startup might take a moment, just wait for the System check log line. 
Then the web app will be accessible at `http://localhost:8000/`

To stop it, kill the process. Alternatively you can run this in the root dir:
```bash
docker compose down
```
