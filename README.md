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



# Evaluation

```
$ ./eval.sh 
=========== Generation Predictions for 10 images using UserVideo ==========
self.cfg --#Config (path: test_detector_configs/tt_fast_base_tt_640_finetune_ic17mlt.py): {'model': {'type': 'FAST', 'backbone': {'type': 'fast_backbone', 'config': 'test_detector_configs/nas_fast_base.config'}, 'neck': {'type': 'fast_neck', 'config': 'test_detector_configs/nas_fast_base.config'}, 'detection_head': {'type': 'fast_head', 'config': 'test_detector_configs/nas_fast_base.config', 'pooling_size': 9, 'dropout_ratio': 0.1, 'loss_text': {'type': 'DiceLoss', 'loss_weight': 0.5}, 'loss_kernel': {'type': 'DiceLoss', 'loss_weight': 1.0}, 'loss_emb': {'type': 'EmbLoss_v1', 'feature_dim': 4, 'loss_weight': 0.25}}}, 'repeat_times': 10, 'data': {'batch_size': 16, 'train': {'type': 'FAST_TT', 'split': 'train', 'is_transform': True, 'img_size': 640, 'short_size': 640, 'pooling_size': 9, 'read_type': 'cv2', 'repeat_times': 10}, 'test': {'type': 'FAST_TT', 'split': 'test', 'short_size': 640, 'read_type': 'pil'}}, 'train_cfg': {'lr': 0.001, 'schedule': 'polylr', 'epoch': 30, 'optimizer': 'Adam', 'pretrain': 'pretrained/fast_base_ic17mlt_640.pth', 'save_interval': 1}, 'test_cfg': {'min_score': 0.85, 'min_area': 250, 'bbox_type': 'rect', 'result_path': 'outputs/submit_tt/'}}
Loading model and optimizer from checkpoint 'pretrained/fast_base_tt_640_finetune_ic17mlt.pth'
INFO:root:Loading model and optimizer from checkpoint 'pretrained/fast_base_tt_640_finetune_ic17mlt.pth'
eval_data\images\FF2_EN_1.jpg
<PIL.Image.Image image mode=RGB size=100x100 at 0x20110AA29F0>
Images differ by 125
Images are more than 7 hamming distance. Proceed with OCR
INFO:root:OCR found text: Crew: Coptoin Ceci We ore obout t0 orrive! cecil:Good. 1 ,
INFO:root:Time taken: 0.26425909996032715 seconds
found text ocr----
Crew: Coptoin Ceci We ore obout t0 orrive! cecil:Good. 1 ,
----
Time taken: 0.26425909996032715 seconds
finished ocr - Crew: Coptoin Ceci We ore obout t0 orrive! cecil:Good. 1 , 
eval_data\images\FF2_EN_2.jpg
eval_data\images\FF2_EN_3.jpg
eval_data\images\FF2_EN_4.jpg
eval_data\images\FF2_EN_5.jpg
<PIL.Image.Image image mode=RGB size=879x601 at 0x200FF501580>
Images differ by 20
Images are more than 7 hamming distance. Proceed with OCR
INFO:root:OCR found text: Crew: Why are We robbing crystols from nnocent People? Crew: Thot' s our duty.
INFO:root:Time taken: 0.15877485275268555 seconds
found text ocr----
Crew: Why are We robbing crystols from nnocent People? Crew: Thot' s our duty.
----
Time taken: 0.15877485275268555 seconds
finished ocr - Crew: Why are We robbing crystols from nnocent People? Crew: Thot' s our duty. 
eval_data\images\FF2_EN_6.jpg
<PIL.Image.Image image mode=RGB size=879x601 at 0x200FF28E120>
Images differ by 33
Images are more than 7 hamming distance. Proceed with OCR
INFO:root:OCR found text: Crew:do We red Iy have t0 keep doing this?
INFO:root:Time taken: 5.086591005325317 seconds
found text ocr----
Crew:do We red Iy have t0 keep doing this?
----
Time taken: 5.136143445968628 seconds
finished ocr - Crew:do We red Iy have t0 keep doing this? 
eval_data\images\FF2_EN_7.jpg
<PIL.Image.Image image mode=RGB size=879x601 at 0x200FF8010A0>
Images differ by 0
Difference is less than 10%. No need to call OCR again.
eval_data\images\FF2_EN_8.jpg
eval_data\images\FF2_EN_9.jpg
eval_data\images\FF2_EN_10.jpg
=========== Evaluating has text detector ==========
Precision : 1.0, Recall : 0.4, F1 : 0.5714285714285715, Accuracy : 0.4
Incorrect filenames ['FF2_EN_10', 'FF2_EN_2', 'FF2_EN_3', 'FF2_EN_4', 'FF2_EN_8', 'FF2_EN_9']
==================== Evaluating Detection Performance ======================
{'recall': 0.3612068965517242,
 'precision': 0.35204059324045833,
 'hmean': 0.35656484450205095,
 'IoU': 0.2342075581100041}
==================== Evaluating Recognition Performance ======================
Average Character Error Rate (CER): 13.09%
Average Word Error Rate (WER): 23.53%

Wrong Characters:
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth: 
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: , Ground Truth: l,
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: 0, Ground Truth: o
Filename: FF2_EN_1, Predicted: o, Ground Truth: a
Filename: FF2_EN_1, Predicted: c, Ground Truth: C
Filename: FF2_EN_1, Predicted: . 1 , Ground Truth:
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted: , Ground Truth: i
Filename: FF2_EN_5, Predicted: o, Ground Truth: a
Filename: FF2_EN_5, Predicted:  , Ground Truth:
Filename: FF2_EN_6, Predicted: d I, Ground Truth: all
Filename: FF2_EN_6, Predicted: 0, Ground Truth: o
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?

Wrong Words:
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?
Filename: FF2_EN_1, Predicted: Coptoin Ceci, Ground Truth: Captain Cecil,
Filename: FF2_EN_1, Predicted: ore obout t0 orrive! cecil:Good. 1 ,, Ground Truth: are about to arrive! Cecil:Good,
Filename: FF2_EN_5, Predicted: crystols, Ground Truth: crystals
Filename: FF2_EN_5, Predicted: nnocent, Ground Truth: innocent
Filename: FF2_EN_5, Predicted: Thot' s, Ground Truth: That's
Filename: FF2_EN_6, Predicted: red Iy, Ground Truth: really
Filename: FF2_EN_6, Predicted: t0, Ground Truth: to
Filename: FF2_EN_7, Predicted: , Ground Truth: Crew:do We really have to keep doing this?

```