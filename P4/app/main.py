import os
import secrets
import subprocess
import uuid

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Directories for storing files
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Serve processed files statically
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Video Monster API</title>
            <style>
                body {
                    background-image: url('https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?fm=jpg&q=60&w=3000&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxleHBsb3JlLWZlZWR8NXx8fGVufDB8fHx8fA%3D%3D');
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    font-family: Arial, sans-serif;
                    color: #fff;
                    margin: 0;
                    padding: 0;
                }
                h1 {
                    text-align: center;
                    margin-top: 20px;
                    color: #ffd200;
                    font-size: 48px;
                }
                ol {
                    margin: 20px auto;
                    max-width: 800px;
                    background: rgba(0, 0, 0, 0.7);
                    color: #fff;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                li {
                    margin-bottom: 10px;
                }
                p {
                    text-align: center;
                    margin: auto;
                    max-width: 500px;
                    background: rgba(0, 0, 0, 0.7);
                    color: #fff;
                    border-radius: 20px;
                    padding: 20px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
            </style>
        </head>
        <body>
            <h1>Welcome to our API ! </h1>
            <p>This API now supports two endpoints:</p>
            <ol>
                <li><strong>Convert and Encrypt to HLS:</strong> Upload a video to convert it into HLS format and apply AES-128 encryption via FFmpeg.</li>
                <li><strong>Convert to MPEG-DASH:</strong> Upload a video to convert it into MPEG-DASH format.</li>
            </ol>
            <p>Click <a href="/docs">here</a> to explore the API documentation!</p>
        </body>
    </html>
    """

def generate_key_info_file(output_folder):
    """
    Generates an AES-128 key and creates a key info file required by FFmpeg.
    The key info file has three lines:
      1. The URL to the key (this can be a public URL or a relative path if you serve the key)
      2. The local file path where FFmpeg will write the key
      3. The 128-bit (16 bytes) encryption key in hex format
    """
    # Generate a 16-byte (128-bit) key in hexadecimal
    key = secrets.token_hex(16)
    key_filename = "enc.key"
    key_file_path = os.path.join(output_folder, key_filename)
    
    # Save the key to a file so FFmpeg can use it
    with open(key_file_path, "w") as key_file:
        key_file.write(key)
    
    # URL where the key is served. Adjust this if you plan to serve keys securely.
    key_uri = f"http://localhost:80/processed/{os.path.basename(output_folder)}/{key_filename}"
    
    key_info_path = os.path.join(output_folder, "key_info.txt")
    with open(key_info_path, "w") as info_file:
        info_file.write(f"{key_uri}\n{key_file_path}\n{key}\n")
    
    return key_info_path

@app.post("/convert_and_encrypt_hls/")
async def convert_and_encrypt_hls(request: Request, file: UploadFile = File(...)):
    """
    Converts an uploaded video to HLS and encrypts it using AES-128 via FFmpeg.
    """
    # Generate a unique filename for the upload
    file_ext = file.filename.split(".")[-1]
    video_filename = f"{uuid.uuid4()}.{file_ext}"
    video_path = os.path.join(UPLOAD_DIR, video_filename)

    # Save the uploaded file
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    # Create an output directory for the processed video
    output_folder_name = video_filename.rsplit(".", 1)[0]
    output_folder = os.path.join(PROCESSED_DIR, output_folder_name)
    os.makedirs(output_folder, exist_ok=True)

    # Define the output HLS playlist path
    output_hls_path = os.path.join(output_folder, "package.m3u8")

    # Generate the key info file (this creates the AES key and a key info file for FFmpeg)
    key_info_path = generate_key_info_file(output_folder)

    # Run FFmpeg command to generate encrypted HLS
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-hls_time", "10",
        "-hls_playlist_type", "vod",
        "-hls_key_info_file", key_info_path,
        "-f", "hls",
        output_hls_path
    ]

    try:
        result = subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={"error": "FFmpeg processing failed", "details": e.stderr.decode()}
        )

    # Construct the URL to access the encrypted HLS stream
    base_url = str(request.base_url)
    encrypted_hls_url = f"{base_url}processed/{output_folder_name}/package.m3u8"

    return JSONResponse(content={"encrypted_hls_url": encrypted_hls_url})


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





