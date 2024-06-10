#!/bin/bash



# echo =========== Generation Predictions for English images using UserVideo ==========
# python generate_predictions.py

echo =========== Evaluating has text detector ==========
python eval_has_text.py

echo ==================== Evaluating Detection Performance ======================
python eval_det.py

echo ==================== Evaluating Recognition Performance ======================
python eval_reg.py