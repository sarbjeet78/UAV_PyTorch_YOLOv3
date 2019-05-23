#! /usr/bin/env python

import argparse
import os
import numpy as np
import json
from voc import parse_voc_annotation
from yolo_2 import create_yolov3_model
from generator_2 import BatchGenerator
from utils.utils import normalize, evaluate
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.optimizers import Adam
from keras.models import load_model

def _main_(args):
    config_path = args.conf

    with open(config_path) as config_buffer:    
        config = json.loads(config_buffer.read())

    ###############################
    #   Create the validation generator
    ###############################  
    valid_ints, labels = parse_voc_annotation(
        config['valid']['valid_annot_folder'], 
        config['valid']['valid_image_folder'], 
        config['valid']['cache_name'],
        config['model']['labels']
    )

    labels = labels.keys() if len(config['model']['labels']) == 0 else config['model']['labels']
    labels = sorted(labels)
   
    valid_generator = BatchGenerator(
        instances           = valid_ints, 
        anchors             = config['model']['anchors'],   
        labels              = labels,        
        downsample          = 32, # ratio between network input's size and network output's size, 32 for YOLOv3
        max_box_per_image   = 0,
        batch_size          = config['train']['batch_size'],
        min_net_size        = config['model']['min_input_size'],
        max_net_size        = config['model']['max_input_size'],   
        shuffle             = True, 
        jitter              = 0.0, 
        norm                = normalize
    )

    ###############################
    #   Load the model and do evaluation
    ###############################
    os.environ['CUDA_VISIBLE_DEVICES'] = config['train']['gpus']

    infer_model = load_model(config['train']['saved_weights_name'])

    # compute mAP for all the classes
    average_precisions, recall, precision= evaluate(infer_model, valid_generator)

    # print the score
    for (c,ap),(c,prec),(c,call) in zip(average_precisions.items(),precision.items(),recall.items()):
        print("+ Class {c} - AP: {ap}, precision: {prec}, recall: {call}".format(c=c, ap=ap,prec=prec,call=call))
    map = np.mean(list(average_precisions.values()))
    mprec=np.mean(list(precision.values()))
    mrecall=np.mean(list(recall.values()))
    print("mAP: {map}, mprec: {mprec}, mrecall: {mrecall}".format(map=map,mprec=mprec,mrecall=mrecall))

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Evaluate YOLO_v3 model on any dataset')
    argparser.add_argument('-c', '--conf', default='config.json', help='path to configuration file')
    
    args = argparser.parse_args()
    _main_(args)
