import os, sys, subprocess

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates
from starlette.background import BackgroundTask

import uvicorn
import re
from youtube_dl import YoutubeDL
from collections import ChainMap

templates = Jinja2Templates(directory="")

app_defaults = {
    "YDL_FORMAT": "bestvideo+bestaudio/best",
    "YDL_EXTRACT_AUDIO_FORMAT": None,
    "YDL_EXTRACT_AUDIO_QUALITY": "192",
    "YDL_RECODE_VIDEO_FORMAT": None,
    "YDL_OUTPUT_TEMPLATE": "/data/%(title).80s [%(id)s].%(ext)s",
    "YDL_ARCHIVE_FILE": None,
    "YDL_SERVER_HOST": "0.0.0.0",
    "YDL_SERVER_PORT": 8080,
    "YDL_UPDATE_TIME": "True",
}

async def dl_queue_list(request):
    return templates.TemplateResponse("index.html", {"request": request})

async def q_put(request):
    form = await request.form()
    url = form.get("url").strip()
    options = {"format": form.get("format"), "tool": form.get("tool"), "savelocation": form.get("savelocation")}

    if not url:
        return JSONResponse(
            {"success": False, "error": "/q called without a 'url' in form data"}
        )

    task = BackgroundTask(download, url, options)

    print("Added url " + url + " to the download queue")
    return JSONResponse(
        {"success": True, "url": url, "options": options}, background=task
    )


async def update_route(scope, receive, send):
    task = BackgroundTask(update)

    return JSONResponse({"output": "Initiated package update"}, background=task)


def update():
    try:
        output = subprocess.check_output(
            [sys.executable, "-m", "pip", "install", "--upgrade", "youtube-dl", "you-get"]
        )

        print(output.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print(e.output)

def get_ydl_options(request_options):
    request_vars = {
        "YDL_EXTRACT_AUDIO_FORMAT": None,
        "YDL_RECODE_VIDEO_FORMAT": None,
    }

    requested_format = request_options.get("format", "bestvideo")

    if requested_format in ["aac", "flac", "mp3", "m4a", "opus", "vorbis", "wav"]:
        request_vars["YDL_EXTRACT_AUDIO_FORMAT"] = requested_format
    elif requested_format == "bestaudio":
        request_vars["YDL_EXTRACT_AUDIO_FORMAT"] = "best"
    elif requested_format in ["mp4", "flv", "webm", "ogg", "mkv", "avi"]:
        request_vars["YDL_RECODE_VIDEO_FORMAT"] = requested_format

    requested_location = request_options.get("format", "savelocation")

    if requested_location in ["data", "data2", "data3"]:
        request_vars["YDL_OUTPUT_TEMPLATE"] = "/" + requested_location + "/%(title).80s [%(id)s].%(ext)s"

    ydl_vars = ChainMap(request_vars, os.environ, app_defaults)

    postprocessors = []

    if ydl_vars["YDL_EXTRACT_AUDIO_FORMAT"]:
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": ydl_vars["YDL_EXTRACT_AUDIO_FORMAT"],
                "preferredquality": ydl_vars["YDL_EXTRACT_AUDIO_QUALITY"],
            }
        )

    if ydl_vars["YDL_RECODE_VIDEO_FORMAT"]:
        postprocessors.append(
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": ydl_vars["YDL_RECODE_VIDEO_FORMAT"],
            }
        )


    return {
        "format": ydl_vars["YDL_FORMAT"],
        "postprocessors": postprocessors,
        "outtmpl": ydl_vars["YDL_OUTPUT_TEMPLATE"],
        "download_archive": ydl_vars["YDL_ARCHIVE_FILE"],
        "updatetime": ydl_vars["YDL_UPDATE_TIME"] == "True",
    }


def download(url, request_options):

    tool = request_options.get("tool", "youtube-dl")

    print("download start")
    print("param:%s" % request_options)

    if tool == "youtube-dl":
        print("via you-get")
        youtube_dl(url, request_options)

    else:
        print("via youtube-dl")
        you_get(url, request_options)

def youtube_dl(url, request_options):
    with YoutubeDL(get_ydl_options(request_options)) as ydl:
        ydl.download([url])

def you_get(url, request_options):

    try:
        output = subprocess.check_output(
            ["/usr/local/bin/you-get", url, "-o",request_options.get("savelocation","/data/")]
        )

        print(output.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print(e.output)

routes = [
    Route("/youtube-dl", endpoint=dl_queue_list),
    Route("/youtube-dl/q", endpoint=q_put, methods=["POST"]),
    Route("/youtube-dl/update", endpoint=update_route, methods=["PUT"]),
    Mount("/youtube-dl/static", app=StaticFiles(directory="static"), name="static"),
]

app = Starlette(debug=True, routes=routes)

print("Updating youtube-dl to the newest version")
update()

app_vars = ChainMap(os.environ, app_defaults)

if __name__ == "__main__":
    uvicorn.run(
        app, host=app_vars["YDL_SERVER_HOST"], port=int(app_vars["YDL_SERVER_PORT"])
    )
