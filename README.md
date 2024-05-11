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

To run the webserver, execute this in the project root (depending on your system you might have to prefix the command 
with `sudo`/`su` or `root`):
```bash
docker compose up
```
The startup might take a moment, just wait for the System check log line. 
Then the web app will be accessible at `http://localhost:8000/`

To stop it, kill the process. Alternatively you can run this in the root dir:
```bash
docker compose down
```

### Changing the webserver's host port

It might be necessary to map the webserver container to a different host port, for example if you have a different
process running on `8000` on your host system already. If needed, you can adapt the `docker-compose.yaml` accordingly by
defining a different host port in the _ports_ section. In this example the host port would be `1234`, making the
webserver accessible at that port exactly:

```yaml
ports:
  - "1234:8000"
```
