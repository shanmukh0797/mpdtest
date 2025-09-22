# MPD Video Server

A FastAPI server for serving DASH video manifest (.mpd) files from a videos folder.

## Features

- Serve .mpd files from the videos directory
- List available videos and .mpd files
- Static file serving for video segments
- RESTful API endpoints

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python main.py
```

The server will start on `http://localhost:8000`

2. Access the interactive API documentation at `http://localhost:8000/docs`

## API Endpoints

### Root
- `GET /` - Basic information about the server

### Videos
- `GET /videos` - List all available video directories
- `GET /mpd` - List all available .mpd files

### MPD Files
- `GET /mpd/{video_name}` - Get the main .mpd file for a specific video

### Health
- `GET /health` - Health check endpoint

## Examples

### List all videos
```bash
curl http://localhost:8000/videos
```

### Get main MPD file for a video
```bash
curl http://localhost:8000/mpd/14173101_3840_2160_60fps
```

### Get specific MPD file
```bash
curl http://localhost:8000/mpd/14173101_3840_2160_60fps/video_720p.mpd
```

### List all MPD files
```bash
curl http://localhost:8000/mpd
```

## Video Structure

The server expects videos to be organized in the following structure:
```
videos/
├── video_folder_1/
│   ├── video_folder_1.mpd
│   ├── video_360p.mpd
│   ├── video_720p.mpd
│   ├── audio/
│   └── video/
└── video_folder_2/
    ├── video_folder_2.mpd
    └── ...
```

## Static File Serving

Video segments and other static files are served from the `/videos` path, so you can access them directly:
- `http://localhost:8000/videos/video_folder/video/720_2400000/dash/segment_1.m4s`
