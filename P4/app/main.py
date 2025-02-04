from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from uuid import uuid4
import subprocess
import os

import ffmpeg
from uuid import uuid4

app = FastAPI()

# Directory to save uploaded and processed files
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Video Monster API</title>
            <style>
                body {
                    background-image: url('https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?fm=jpg&q=60&w=3000&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxleHBsb3JlLWZlZWR8NXx8fGVufDB8fHx8fA%3D%3D'); /* URL de la imagen */
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
                    background: rgba(0, 0, 0, 0.7); /* Fondo semitransparente para el texto */
                    color: #fff;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                p {
                    text-align: center;
                    margin: auto;
                    max-width: 500px;
                    background: rgba(0, 0, 0, 0.7); /* Fondo semitransparente para el texto */
                    color: #fff;
                    border-radius: 20px;
                    padding: 20px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
            </style>
        </head>
        <body>
            <h1>Welcome to the<br>Video API</h1>
            <p>This API empowers you with tools to process videos in various ways:</p>
            <ol>
                <li><strong>Modify Resolution:</strong> Adjust the resolution of your video by specifying the desired width and height. The output will match the resolution you provide.</li>
                <li><strong>Modify the Chroma Subsampling:</strong> Change the chroma subsampling format of a video, allowing you to select between formats like YUV420, YUV422, or YUV444.</li>
                <li><strong>Read Video Info:</strong> Extract essential metadata from your video, including its duration, resolution, codec, and bitrate.</li>
                <li><strong>Create BBB Container:</strong> Generate a custom 20-second MP4 video by cutting the input and including AAC, MP3, and AC3 audio tracks.</li>
                <li><strong>Read MP4 Tracks:</strong> Analyze an MP4 file to identify and count its video and audio tracks, returning a concise summary of its contents.</li>
                <li><strong>Show Macroblocks and Motion Vectors:</strong> Visualize the motion vectors of macroblocks in a video, returning a downloadable file with overlays.</li>
                <li><strong>Show YUV Histogram:</strong> Create a visualization of the YUV histogram for a video and receive a processed file with the histogram included.</li>
                <li><strong>Convert Codecs:</strong> Transform your video into multiple formats such as VP8, VP9, H.265, and AV1, providing separate download links for each version.</li>
                <li><strong>Encoding Ladder:</strong> Generate an encoding ladder with various resolutions and bitrates using advanced encoding techniques, with download links for all output versions.</li>
            </ol>
            <p>Click <a href="/docs">here</a> to explore the available endpoints!</p>
        </body>
    </html>
    """


@app.post("/Modify Resolution")
async def convert_resolution(request: Request, file: UploadFile, width: int = Form(...), height: int = Form(...)):
    """
    - Allows you to modify the resolution of an uploaded video file.
    - You can provide the desired width and height for the output video.
    - The output video will be processed and the new resolution will be applied.
    
    :param file: The uploaded video file to process.
    :param width: The desired width for the output video.
    :param height: The desired height for the output video.
    :return: The processed video with the modified resolution and a download link.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"
        output_path = f"processed/{file_id}_converted_{width}x{height}.mp4"

        # Save the uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Run FFmpeg command to modify the resolution
        ffmpeg.input(input_path).output(output_path, vf=f"scale={width}:{height}").run()

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct the full download URL
        download_url = f"{base_url}/Download?file_path={output_path}"

        # Return the success message with the download link
        return JSONResponse(content={
            "message": "Video processed successfully!",
            "download_link": download_url
        }, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/Modify the Chroma Subsampling")
async def convert_chroma(request: Request, file: UploadFile, chroma_format: str = Form(...)):
    """
    - Allows you to change the chroma subsampling format of an uploaded video.
    - You can select different chroma formats (e.g., YUV420, YUV422, YUV444) for the output video.
    
    :param file: The uploaded video file to process.
    :param chroma_format: The desired chroma subsampling format.
    :return: The processed video with the specified chroma format and a download link.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"
        output_path = f"processed/{file_id}_chroma_{chroma_format}.mp4"

        # Save the uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Run FFmpeg command to change chroma subsampling
        ffmpeg.input(input_path).output(output_path, pix_fmt=chroma_format).run()

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct the full download URL
        download_url = f"{base_url}/Download?file_path={output_path}"

        # Return success message with the download link
        return JSONResponse(content={
            "message": "Video processed successfully!",
            "download_link": download_url
        }, status_code=200)

    except ffmpeg.Error as e:
        # Check if stderr is None before trying to decode it
        error_message = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
        return JSONResponse(content={"error": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.post("/Read video info/")
async def read_video_info(request: Request, file: UploadFile):
    """
    - Allows you to extract and display the metadata of an uploaded video file.
    - You will get information such as duration, bitrate, width, height, codec, and format.
    
    :param file: The uploaded video file to analyze.
    :return: The extracted video metadata and related information.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"

        with open(input_path, "wb") as f:
            f.write(await file.read())

        probe = ffmpeg.probe(input_path)

        format_info = probe.get("format", {})
        streams = probe.get("streams", [])
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})

        duration_seconds = float(format_info.get("duration", 0))
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        formatted_duration = f"{minutes}:{seconds:02}"

        video_info = {
            "Duration (s)": formatted_duration,
            "Bitrate (bps)": int(format_info.get("bit_rate", 0)),
            "Width": video_stream.get("width", "Unknown"),
            "Height": video_stream.get("height", "Unknown"),
            "Codec": video_stream.get("codec_name", "Unknown"),
            "Format": format_info.get("format_name", "Unknown"),
        }

        return JSONResponse(content={"message": "Video info extracted", "video_info": video_info}, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": "FFmpeg failed to extract video info", "details": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": "An unexpected error occurred", "details": str(e)}, status_code=500)


@app.post("/create_bbb_container/")
async def create_bbb_container(request: Request, uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    - Cuts the input video to 20 seconds.
    - Extract audio tracks in AAC, MP3, and AC3 formats.
    - Combine all into a single MP4 file.
    
    :param uploaded_file: The uploaded video file to process.
    :param container_name: Name for the final video (optional).
    :return: The final processed MP4 file and download links for all files.
    """
    try:
        # Generate a unique identifier to avoid overwriting files
        unique_id = str(uuid4())

        # Save the uploaded file locally in the 'processed' folder
        saved_path = f"processed/{unique_id}_{uploaded_file.filename}"
        with open(saved_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Use a default name if no custom name is provided
        if not container_name:
            container_name = f"container_{unique_id}"

        # Paths for intermediate and final outputs
        trimmed_video = f"processed/{container_name}_20s.mp4"
        audio_aac = f"processed/{container_name}_audio.aac"
        audio_mp3 = f"processed/{container_name}_audio.mp3"
        audio_ac3 = f"processed/{container_name}_audio.ac3"
        final_video = f"processed/{container_name}_final.mp4"

        # Trim the video to 20 seconds
        subprocess.run(f"ffmpeg -i {saved_path} -t 20 {trimmed_video}", shell=True)

        # Extract audio in different formats
        subprocess.run(f"ffmpeg -i {trimmed_video} -vn -ac 1 {audio_aac}", shell=True)  # AAC (mono)
        subprocess.run(f"ffmpeg -i {trimmed_video} -vn -b:a 128k {audio_mp3}", shell=True)  # MP3 (stereo, 128k bitrate)
        subprocess.run(f"ffmpeg -i {trimmed_video} -vn -c:a ac3 {audio_ac3}", shell=True)  # AC3 format

        # Combine everything into a single MP4 container
        subprocess.run(
            f"ffmpeg -i {trimmed_video} -i {audio_aac} -i {audio_mp3} -i {audio_ac3} -map 0:v -map 1:a -map 2:a -map 3:a {final_video}",
            shell=True,
        )

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct full download URLs
        cut_video_url = f"{base_url}/Download?file_path={trimmed_video}"
        mp3_audio_url = f"{base_url}/Download?file_path={audio_mp3}"
        aac_audio_url = f"{base_url}/Download?file_path={audio_aac}"
        ac3_audio_url = f"{base_url}/Download?file_path={audio_ac3}"
        final_video_url = f"{base_url}/Download?file_path={final_video}"

        # Return the download links for all the files
        return {
            "message": "Video processed successfully!",
            "download_links": {
                "cut_video": cut_video_url,
                "mp3_audio": mp3_audio_url,
                "aac_audio": aac_audio_url,
                "ac3_audio": ac3_audio_url,
                "final_video": final_video_url,
            }
        }

    except subprocess.CalledProcessError as e:
        return {"error": f"FFmpeg command failed with error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/read_mp4_tracks/")
async def read_mp4_tracks(request: Request, uploaded_file: UploadFile):
    """
    - Allows you to extract track information from an MP4 file.
    - The function counts the number of video and audio tracks and returns a summary.
    
    :param uploaded_file: The uploaded MP4 file to analyze.
    :return: The track info, including the number of video and audio tracks.
    """
    try:
        unique_id = str(uuid4())
        file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        with open(file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        probe = ffmpeg.probe(file_path)

        streams = probe.get("streams", [])
        video_tracks = [s for s in streams if s.get("codec_type") == "video"]
        audio_tracks = [s for s in streams if s.get("codec_type") == "audio"]

        track_info = {
            "video_tracks": len(video_tracks),
            "audio_tracks": len(audio_tracks),
        }

        return JSONResponse(content={"message": "Track info extracted", "track_info": track_info}, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": "FFmpeg failed to extract track info", "details": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": "An unexpected error occurred", "details": str(e)}, status_code=500)


@app.post("/show_macroblocks_motion_vectors/")
async def show_macroblocks_motion_vectors(request: Request, uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    This endpoint processes a video to show the motion vectors of macroblocks.
    It returns a video with motion vectors overlayed, and a download link to access the processed video.
    """
    try:
        unique_id = str(uuid4())
        input_file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        # Save the uploaded file locally
        with open(input_file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Set default name if container_name is not provided
        if not container_name:
            container_name = f"macroblocks_motion_{unique_id}"

        # Define output file path
        output_file_path = f"processed/{container_name}_motion_vectors.mp4"

        # Run FFmpeg command to process motion vectors
        ffmpeg_cmd = f"ffmpeg -flags2 +export_mvs -i {input_file_path} -vf codecview=mv=pf+bf+bb {output_file_path}"
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct the full download URL
        download_url = f"{base_url}/Download?file_path={output_file_path}"

        # Return success message with the download link
        return {
            "message": "Video processed successfully!",
            "download_link": download_url
        }

    except subprocess.CalledProcessError as e:
        return {"error": f"FFmpeg command failed with error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/show_yuv_histogram/")
async def show_yuv_histogram(request: Request, uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    This endpoint generates a YUV histogram visualization of a video.
    It returns a video with the YUV histogram and a download link to access the processed video.
    """
    try:
        unique_id = str(uuid4())
        input_file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        # Save the uploaded file locally
        with open(input_file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Set default name if container_name is not provided
        if not container_name:
            container_name = f"yuv_histogram_{unique_id}"

        # Define output file path
        output_file_path = f"processed/{container_name}_histograms.mp4"

        # Run FFmpeg command to generate YUV histogram
        ffmpeg.input(input_file_path).output(
            output_file_path,
            vf="histogram=display_mode=stack",  # Apply the YUV histogram filter
            vcodec="libx264",  # Use x264 codec for video encoding
            pix_fmt="yuv420p",  # Set pixel format to yuv420p
            preset="fast"  # Use fast encoding preset
        ).overwrite_output().run()

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct the full download URL
        download_url = f"{base_url}/Download?file_path={output_file_path}"

        # Return success message with the download link
        return {
            "message": "Video processed successfully!",
            "download_link": download_url
        }

    except ffmpeg.Error as e:
        return {"error": e.stderr.decode()}
    except Exception as e:
        return {"error": str(e)}


@app.post("/Convert Codecs")
async def convert_codecs(request: Request, file: UploadFile):
    """
    - Allows you to convert an uploaded video file into VP8, VP9, H.265, and AV1 formats.
    - Each codec creates a processed video file.
    - Returns download links for all processed video files.
    
    :param file: The uploaded video file to process.
    :return: Download links for videos in VP8, VP9, H.265, and AV1 formats.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"

        # Save the uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Define output file paths
        vp8_path = f"processed/{file_id}_vp8.webm"
        vp9_path = f"processed/{file_id}_vp9.webm"
        h265_path = f"processed/{file_id}_h265.mp4"
        av1_path = f"processed/{file_id}_av1.mkv"

        # Convert video to different codecs
        ffmpeg.input(input_path).output(vp8_path, vcodec="libvpx", crf=10, bitrate="1M").run()
        ffmpeg.input(input_path).output(vp9_path, vcodec="libvpx-vp9", crf=10, bitrate="1M").run()
        ffmpeg.input(input_path).output(h265_path, vcodec="libx265", crf=23).run()
        ffmpeg.input(input_path).output(av1_path, vcodec="libaom-av1", crf=30).run()

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct download links
        download_links = {
            "vp8": f"{base_url}/Download?file_path={vp8_path}",
            "vp9": f"{base_url}/Download?file_path={vp9_path}",
            "h265": f"{base_url}/Download?file_path={h265_path}",
            "av1": f"{base_url}/Download?file_path={av1_path}",
        }

        # Return the success message with the download links
        return {
            "message": "Videos processed successfully!",
            "download_links": download_links
        }

    except ffmpeg.Error as e:
        return {"error": e.stderr.decode()}
    except Exception as e:
        return {"error": str(e)}


@app.post("/Encoding Ladder")
async def encoding_ladder(request: Request, file: UploadFile):
    """
    - Generate an encoding ladder for an uploaded video file.
    - Each ladder level will include versions of the video at different resolutions and bitrates.
    - Uses the previously implemented resolution modification and codec conversion methods internally.
    - Returns download links for all generated versions.

    :param file: The uploaded video file to process.
    :return: A list of processed videos with download links for each resolution and codec.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"

        # Save the uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Define encoding ladder configurations (resolutions and bitrates)
        ladder = [
            {"width": 426, "height": 240, "bitrate": "500k"},
            {"width": 640, "height": 360, "bitrate": "800k"},
            {"width": 854, "height": 480, "bitrate": "1200k"},
            {"width": 1280, "height": 720, "bitrate": "2500k"},
            {"width": 1920, "height": 1080, "bitrate": "5000k"},
        ]

        # Initialize the output paths for each resolution and codec
        results = []

        # Generate each level of the encoding ladder
        for level in ladder:
            res_width = level["width"]
            res_height = level["height"]
            bitrate = level["bitrate"]

            # Define output paths for each codec
            vp9_output = f"processed/{file_id}_vp9_{res_width}x{res_height}.webm"
            h265_output = f"processed/{file_id}_h265_{res_width}x{res_height}.mp4"

            # Generate VP9 version
            ffmpeg.input(input_path).output(
                vp9_output, vf=f"scale={res_width}:{res_height}", vcodec="libvpx-vp9", bitrate=bitrate
            ).run()

            # Generate H.265 version
            ffmpeg.input(input_path).output(
                h265_output, vf=f"scale={res_width}:{res_height}", vcodec="libx265", bitrate=bitrate
            ).run()

            # Add results for download links
            base_url = f"{request.url.scheme}://{request.url.netloc}"
            results.append({
                "resolution": f"{res_width}x{res_height}",
                "vp9_download": f"{base_url}/Download?file_path={vp9_output}",
                "h265_download": f"{base_url}/Download?file_path={h265_output}",
            })

        # Return the success message with download links for each ladder level
        return{
            "message": "Encoding ladder generated successfully!",
            "results": results
        }

    except ffmpeg.Error as e:
        return {"error": e.stderr.decode()}
    except Exception as e:
        return {"error": str(e)}



@app.get("/Download")
async def download_file(request: Request, file_path: str):
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/octet-stream', filename=os.path.basename(file_path))
    else:
        return JSONResponse(content={"error": "File not found"}, status_code=404)


