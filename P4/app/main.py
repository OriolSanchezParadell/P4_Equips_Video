from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import subprocess
import os
import uuid

app = FastAPI()

# Directories for storing files
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Serve processed files statically
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

@app.post("/convert_to_hls/")
async def convert_video(request: Request, file: UploadFile = File(...)):
    # Generate a unique filename
    file_ext = file.filename.split(".")[-1]
    video_filename = f"{uuid.uuid4()}.{file_ext}"
    video_path = os.path.join(UPLOAD_DIR, video_filename)

    # Save uploaded file
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    # Create output directory
    output_folder_name = video_filename.rsplit(".", 1)[0]
    output_folder = os.path.join(PROCESSED_DIR, output_folder_name)
    os.makedirs(output_folder, exist_ok=True)

    # Define output HLS playlist path
    output_hls_path = os.path.join(output_folder, "package.m3u8")

    # Run FFmpeg command to generate HLS
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-hls_time", "10",
        "-hls_playlist_type", "vod",
        "-f", "hls",
        output_hls_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "FFmpeg processing failed", "details": e.stderr.decode()})

    # Get base URL from request
    base_url = str(request.base_url)

    # Construct the full URL for accessing the HLS video
    hls_url = f"{base_url}processed/{output_folder_name}/package.m3u8"

    return JSONResponse(content={"hls_url": hls_url})


@app.post("/convert_to_Mpeg-Dash/")
async def convert_video_dash(request: Request, file: UploadFile = File(...)):
    # Generate a unique filename
    file_ext = file.filename.split(".")[-1]
    video_filename = f"{uuid.uuid4()}.{file_ext}"
    video_path = os.path.join(UPLOAD_DIR, video_filename)

    # Save uploaded file
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    # Create output directory
    output_folder_name = video_filename.rsplit(".", 1)[0]
    output_folder = os.path.join(PROCESSED_DIR, output_folder_name)
    os.makedirs(output_folder, exist_ok=True)

    # Define output MPEG-DASH path
    output_dash_path = os.path.join(output_folder, "package.mpd")

    # Run FFmpeg command to generate MPEG-DASH
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-c:v", "libvpx-vp9",
        "-c:a", "aac",
        "-f", "dash",
        output_dash_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "FFmpeg processing failed", "details": e.stderr.decode()})

    # Get base URL from request
    base_url = str(request.base_url)

    # Construct the full URL for accessing the MPEG-DASH video
    dash_url = f"{base_url}processed/{output_folder_name}/package.mpd"

    return JSONResponse(content={"dash_url": dash_url})





