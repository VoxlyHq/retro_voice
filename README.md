# retro_voiceover

This repo allows you to all voice overs to classic video games. See my (youtube)[] video here about the basics of the project.
Currently the project requires python 3+, runs on OSX and will shortly be ported to windows


You can run it 1 of two modes. Completely from command line, this can take a video stream, or find a window on your operating system with the game running. The second mode, uses an html page and then uploads screenshots to the webserver 


# GIT LFS, large files, the audio files are stored on git lfs 
```bash
git lfs install
git lfs pull
```

# installation

1) setup a venv 
```bash
python3 -m venv venv
source ./venv/bin/activate
```

note this hasn't been tested on non-mac systems.



2) install deps
```bash
pip3 install -r requirements.txt
```

on mac
2a)
```bash
pip3 install -r requirements_osx.txt
```

3) Install (RetroArch)[http://retroarch.com]


4) Download roms and games * No help will be given on this 



# Porting to new operating systems 

find_window_id and capture_window_to_file are only functions that are using specific functions, or should anyways. you can reimplement those.
Fix and requirements.txt issues



# Command line running 


## Run againist a live copy of Retro Arch 

1) Run game inside retroarch

2) 
```bash
python ss.py -w
```

3) goto http://localhost:8000 and see the transcript



## Run on a video file 

1)
```bash
python3 ss.py --video ff2-screenrecord-first4min.mov
```


# Using a javascript UI to upload the videos 
```bash
python webserv.py
```

1) open http://localhost:8000/html_scrape.html

2) Click the button at top

3) Select the retroarch window






## Video input modes

1) Directly from a webcam
```bash
python ss.py -w -is -v webcam
```

2) Directly from a video
```bash
python ss.py -w -is -v ~/Desktop/ff2-screenrecord-first4min.mov
```

## Flask WebRTC server

### Development
1. Install dev packages:
   ```bash
   pip install -r requirements_dev.txt
   ```
2. Copy `.env.default` to `.env` and fill out the env vars.
   - You should set `OAUTHLIB_INSECURE_TRANSPORT=true` in the dev env so OAuth works with `HTTP`,
   in production this should be `false` so that only `HTTPS` is allowed.
   - Leave `DATABASE_URL` empty in the dev env, it'll default to `server/dev.sqlite3`.
3. Create the local db:
   ```bash
   flask --app server/stream_http_video.py create_db
   ```
4. Run the dev server with hot-reloading of the Python code:
   ```bash
   adev runserver server/stream_http_video.py --app-factory aioapp -p 5001
   ```
   Or without hot-reloading:
   ```bash
   python3 -m server.stream_http_video
   ```

## prod

gunicorn -k aiohttp.worker.GunicornWebWorker --bind unix:/tmp/voxly_app.sock server.stream_http_video:aioapp