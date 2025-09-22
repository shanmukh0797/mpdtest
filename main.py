from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import glob

app = FastAPI(title="Video Player", description="DASH Video Player with MPD files")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files to serve video files with cache control
from fastapi.responses import FileResponse
from fastapi import HTTPException

@app.get("/videos/{video_name}/{mpd_file}")
async def serve_mpd(video_name: str, mpd_file: str):
    """Serve MPD files with proper headers to prevent caching issues"""
    file_path = f"videos/{video_name}/{mpd_file}"
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="application/dash+xml",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    else:
        raise HTTPException(status_code=404, detail="MPD file not found")

# Mount static files to serve video files
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

@app.get("/", response_class=HTMLResponse)
async def render_videos():
    """Render all videos from the videos folder with their master MPD files"""
    
    # Find all video directories
    video_dirs = [d for d in os.listdir("videos") if os.path.isdir(os.path.join("videos", d))]
    
    # Find master MPD files in each video directory
    videos_data = []
    for video_dir in video_dirs:
        video_path = os.path.join("videos", video_dir)
        # Look for master MPD file (matches directory name)
        master_mpd = os.path.join(video_path, f"{video_dir}.mpd")
        
        if os.path.exists(master_mpd):
            videos_data.append({
                "name": video_dir,
                "mpd_file": f"http://127.0.0.1:8000/videos/{video_dir}/{video_dir}.mpd",
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
                    <button class="play-button" onclick="loadVideo({i}, '{video['mpd_file']}?t=' + Date.now())">
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
                
                console.log('Loading video:', mpdUrl);
                
                // Initialize DASH player
                if (video.dashPlayer) {
                    video.dashPlayer.destroy();
                }
                
                try {
                    video.dashPlayer = dashjs.MediaPlayer().create();
                    
                    // Configure DASH player
                    video.dashPlayer.updateSettings({
                        'debug': {
                            'logLevel': dashjs.Debug.LOG_LEVEL_DEBUG
                        }
                    });
                    
                    video.dashPlayer.initialize(video, mpdUrl, true);
                    
                    // Update button text
                    button.textContent = '🔄 Loading...';
                    button.disabled = true;
                    
                    // Enable button when video is ready
                    video.addEventListener('loadeddata', () => {
                        console.log('Video loaded successfully');
                        button.textContent = '▶ Playing';
                        button.disabled = false;
                    });
                    
                    // Handle successful load
                    video.dashPlayer.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, () => {
                        console.log('Stream initialized');
                    });
                    
                    // Handle errors
                    video.dashPlayer.on(dashjs.MediaPlayer.events.ERROR, (e) => {
                        console.error('DASH Error:', e);
                        button.textContent = '❌ Error - Check Console';
                        button.disabled = false;
                    });
                    
                    // Handle network errors
                    video.dashPlayer.on(dashjs.MediaPlayer.events.ERROR, (e) => {
                        if (e.error && e.error.code === dashjs.MediaPlayer.events.ERROR_CODES.MANIFEST_LOAD_ERROR) {
                            console.error('Manifest load error:', e);
                            button.textContent = '❌ Manifest Error';
                        }
                    });
                    
                } catch (error) {
                    console.error('Failed to initialize DASH player:', error);
                    button.textContent = '❌ Init Error';
                    button.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/test-mpd/{video_name}")
async def test_mpd(video_name: str):
    """Test endpoint to check if MPD file is accessible"""
    mpd_path = f"videos/{video_name}/{video_name}.mpd"
    if os.path.exists(mpd_path):
        return {"status": "exists", "path": mpd_path, "url": f"http://127.0.0.1:8000/videos/{video_name}/{video_name}.mpd"}
    else:
        return {"status": "not_found", "path": mpd_path}

@app.get("/api/videos")
async def get_videos_list():
    """API endpoint to get list of all available videos and their master MPD files"""
    video_dirs = [d for d in os.listdir("videos") if os.path.isdir(os.path.join("videos", d)) and d != "export"]
    
    videos_data = []
    for video_dir in video_dirs:
        video_path = os.path.join("videos", video_dir)
        # Look for master MPD file (matches directory name)
        master_mpd = os.path.join(video_path, f"{video_dir}.mpd")
        
        if os.path.exists(master_mpd):
            videos_data.append({
                "name": video_dir,
                "mpd_file": f"http://127.0.0.1:8000/videos/{video_dir}/{video_dir}.mpd",
                "display_name": video_dir.replace("_", " ").title()
            })
    
    videos_data.sort(key=lambda x: x["name"])
    return {"videos": videos_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
