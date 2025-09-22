from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
import os
import glob
import mimetypes

# Helper function to get base URL from request
def get_base_url(request: Request) -> str:
    """Extract base URL from the request"""
    return f"{request.url.scheme}://{request.url.netloc}"

# Custom static file handler that properly handles MPD files
class CustomStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        
        # Check if the file is an MPD file and set correct MIME type
        if hasattr(response, 'path') and response.path and response.path.endswith('.mpd'):
            response.media_type = "text/plain"
            # Match Bitmovin's exact configuration
            response.headers["Content-Type"] = "text/plain; charset=utf-8"
            response.headers["Cache-Control"] = "public, max-age=3600"
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,HEAD"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

app = FastAPI(title="Video Player", description="DASH Video Player with MPD files")

# Custom endpoint specifically for MPD files to ensure proper headers
@app.get("/videos/{video_folder}/{mpd_file}")
async def serve_mpd_file(video_folder: str, mpd_file: str):
    """Serve MPD files with correct MIME type and headers for browser display"""
    if not mpd_file.endswith('.mpd'):
        raise HTTPException(status_code=404, detail="Not an MPD file")
    
    file_path = os.path.join("videos", video_folder, mpd_file)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="text/plain",
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,HEAD",
            "Access-Control-Allow-Headers": "*"
        }
    )

# Mount static files for other video files (segments, etc.)
app.mount("/videos", CustomStaticFiles(directory="videos"), name="videos")

@app.get("/", response_class=HTMLResponse)
async def render_videos(request: Request):
    """Render all videos from the videos folder with their master MPD files"""
    
    # Get base URL from request
    base_url = get_base_url(request)
    
    # Find all video directories
    video_dirs = [d for d in os.listdir("videos") if os.path.isdir(os.path.join("videos", d)) and d != "export"]
    
    # Find only master MPD files in each video directory
    videos_data = []
    for video_dir in video_dirs:
        video_path = os.path.join("videos", video_dir)
        # Look for master MPD file that matches the directory name
        master_mpd = os.path.join(video_path, f"{video_dir}.mpd")
        
        if os.path.exists(master_mpd):
            videos_data.append({
                "name": video_dir,
                "mpd_file": f"{base_url}/videos/{video_dir}/{video_dir}.mpd",
                "display_name": video_dir.replace("_", " ").title()
            })
    
    # Sort videos by name
    videos_data.sort(key=lambda x: x["name"])
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Player - DASH Videos</title>
        <script src="https://cdn.dashjs.org/latest/dash.all.min.js"></script>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }}
            h1 {{
                text-align: center;
                color: #333;
                margin-bottom: 30px;
                border-bottom: 3px solid #007bff;
                padding-bottom: 10px;
            }}
            .video-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .video-card {{
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                background: #fafafa;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .video-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            .video-title {{
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
                font-size: 16px;
            }}
            .video-player {{
                width: 100%;
                height: 200px;
                background: #000;
                border-radius: 4px;
                margin-bottom: 10px;
            }}
            .play-button {{
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
                font-size: 14px;
                transition: background-color 0.2s;
            }}
            .play-button:hover {{
                background: #0056b3;
            }}
            .mpd-info {{
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }}
            .no-videos {{
                text-align: center;
                color: #666;
                font-style: italic;
                margin-top: 50px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 DASH Video Player</h1>
            <div class="video-grid">
    """
    
    if not videos_data:
        html_content += '<div class="no-videos">No videos found in the videos folder.</div>'
    else:
        for i, video in enumerate(videos_data):
            html_content += f"""
                <div class="video-card">
                    <div class="video-title">{video['display_name']}</div>
                    <video id="player{i}" class="video-player" controls preload="none">
                        Your browser does not support the video tag.
                    </video>
                    <button class="play-button" onclick="loadVideo({i}, '{video['mpd_file']}')">
                        ▶ Play Video
                    </button>
                    <div class="mpd-info">MPD: {video['mpd_file']}</div>
                </div>
            """
    
    html_content += """
            </div>
        </div>
        
        <script>
            function loadVideo(playerId, mpdUrl) {
                const video = document.getElementById(`player${playerId}`);
                const button = event.target;
                
                // Initialize DASH player
                if (video.dashPlayer) {
                    video.dashPlayer.destroy();
                }
                
                video.dashPlayer = dashjs.MediaPlayer().create();
                video.dashPlayer.initialize(video, mpdUrl, true);
                
                // Update button text
                button.textContent = '🔄 Loading...';
                button.disabled = true;
                
                // Enable button when video is ready
                video.addEventListener('loadeddata', () => {
                    button.textContent = '▶ Playing';
                    button.disabled = false;
                });
                
                // Handle errors
                video.dashPlayer.on(dashjs.MediaPlayer.events.ERROR, (e) => {
                    console.error('DASH Error:', e);
                    button.textContent = '❌ Error';
                    button.disabled = false;
                });
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/api/videos")
async def get_videos_list(request: Request):
    """API endpoint to get list of all available videos and their MPD files"""
    # Get base URL from request
    base_url = get_base_url(request)
    
    video_dirs = [d for d in os.listdir("videos") if os.path.isdir(os.path.join("videos", d)) and d != "export"]
    
    videos_data = []
    for video_dir in video_dirs:
        video_path = os.path.join("videos", video_dir)
        # Look for master MPD file that matches the directory name
        master_mpd = os.path.join(video_path, f"{video_dir}.mpd")
        
        if os.path.exists(master_mpd):
            videos_data.append({
                "name": video_dir,
                "mpd_file": f"{base_url}/videos/{video_dir}/{video_dir}.mpd",
                "display_name": video_dir.replace("_", " ").title()
            })
    
    videos_data.sort(key=lambda x: x["name"])
    return {"videos": videos_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
