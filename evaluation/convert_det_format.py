from pathlib import Path

import json
import zipfile
import rrc_evaluation_funcs
import argparse



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Detectiton bounding box format to formaat compatible with evaluate_detection.py")
    parser.add_argument('-m', '--model_type', type=str, required=True,  choices=['east', 'craft', 'fast'])
    args = parser.parse_args()

    model_type = args.model_type

    tmp_path = Path('eval_data/tmp')
    tmp_path.mkdir(exist_ok=True)

    json_file_path = f'eval_data/detection_{model_type}.json'
    output_zip_file = f'eval_data/detection_{model_type}.zip'
    
    data = json.load(open(json_file_path))

    txt_files = []

    for i in data:
        fname = f'eval_data/tmp/{i['filename'].split('.')[0]}.txt'
        txt_files.append(fname)
        print(fname)
        with open(fname, 'w') as f:
            if model_type == 'craft':
                for j in i['predictions'][0]:
                    if j:
                        #(Xmin, Xmax, Ymin, Ymax)
                        j = [j[0], j[2], j[1], j[3], '*']
            if model_type == 'east':
                for j in i['predictions']:
                    if j:
                        j = j + ['*']

                        
            f.write(','.join([str(k) for k in j])+'\n')


    with zipfile.ZipFile(output_zip_file, 'w') as f:
        for i in txt_files:
            f.write(i)
