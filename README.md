[![Docker Stars Shield](https://img.shields.io/docker/stars/toru2220/youtube-dl-you-get-server.svg?style=flat-square)](https://hub.docker.com/r/toru2220/youtube-dl-you-get-server/)
[![Docker Pulls Shield](https://img.shields.io/docker/pulls/toru2220/youtube-dl-you-get-server.svg?style=flat-square)](https://hub.docker.com/r/toru2220/youtube-dl-you-get-server/)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://raw.githubusercontent.com/manbearwiz/youtube-dl-server/master/LICENSE)

# youtube-dl-you-get-server

Very spartan Web and REST interface for downloading youtube videos onto a server. [`starlette`](https://github.com/encode/starlette) + [`youtube-dl`](https://github.com/rg3/youtube-dl) + [`you-get`](https://you-get.org/)


![screenshot](https://github.com/toru2220/youtube-dl-you-get-server/raw/main/youtube-dl-server.png)

## Running

### Docker CLI

This example uses the docker run command to create the container to run the app. Here we also use host networking for simplicity. Also note the `-v` argument. This directory will be used to output the resulting videos

```shell
docker run -d --net="host" --name youtube-dl -v /home/core/youtube-dl:/data toru2220/youtube-dl-you-get-server
```

### Docker Compose

This is an example service definition that could be put in `docker-compose.yml`. This service uses a VPN client container for its networking.

```yml
  youtube-dl:
    image: "toru2220/youtube-dl-you-get-server"
    network_mode: "service:vpn"
    volumes:
      - /home/core/youtube-dl:/data
      - /home/core/youtube-dl2:/data2
      - /home/core/youtube-dl3:/data3
    restart: always
```

### Python

If you have python ^3.6.0 installed in your PATH you can simply run like this, providing optional environment variable overrides inline.

```shell
YDL_SERVER_PORT=8123 YDL_UPDATE_TIME=False python3 -u ./youtube-dl-server.py
```

In this example, `YDL_UPDATE_TIME=False` is the same as the command line option `--no-mtime`.

## Usage

### Start a download remotely

Downloads can be triggered by supplying the `{{url}}` of the requested video through the Web UI or through the REST interface via curl, etc.

#### HTML

Just navigate to `http://{{host}}:8080/youtube-dl` and enter the requested `{{url}}`.

#### Curl

```shell
curl -X POST --data-urlencode "url={{url}}" http://{{host}}:8080/youtube-dl/q
```

#### Fetch

```javascript
fetch(`http://${host}:8080/youtube-dl/q`, {
  method: "POST",
  body: new URLSearchParams({
    url: url,
    format: "bestvideo",
    savelocation: "data",
  }),
});
```

#### Bookmarklet

Add the following bookmarklet to your bookmark bar so you can conviently send the current page url to your youtube-dl-server instance.

```javascript
javascript:!function(){fetch("http://${host}:8080/youtube-dl/q",{body:new URLSearchParams({url:window.location.href,format:"bestvideo",savelocation:"data"}),method:"POST"})}();
```

## Implementation

The server uses [`starlette`](https://github.com/encode/starlette) for the web framework and [`youtube-dl`](https://github.com/rg3/youtube-dl) to handle the downloading. The integration with youtube-dl makes use of their [python api](https://github.com/rg3/youtube-dl#embedding-youtube-dl).

This docker image is based on [`python:alpine`](https://registry.hub.docker.com/_/python/) and consequently [`alpine:3.8`](https://hub.docker.com/_/alpine/).

