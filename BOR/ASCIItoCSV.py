#Program to convert ASCII files to csv, after calibration
## output: *.csv

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from numpy import trapz
import matplotlib.pyplot as plt
import math
import pickle
import argparse
import datetime
import re
import requests
import time
from glob import glob
from urllib.request import urlopen
from bs4 import BeautifulSoup
import collections

# I use 'offline' a txt file filled with abort timestamps from 'http://....php',
# so the input 'online' can also be that 

def create_new_name(name):
    date = datetime.datetime.strptime(name[0:16], '%Y-%m-%d %H:%M')
    date = date + datetime.timedelta(minutes=1)
    name_new = date.strftime('%d_%^b_%Y_%H_%M')
    return name_new

def skip_file(bor_file,skip_var):
    if os.path.exists(str(bor_file).replace('.ASCII_LowPassFilter','_LowPassFilter.csv')):
        print('>> ' + str(bor_file).replace('.ASCII_LowPassFilter','_LowPassFilter.csv') + ' exist')
        skip_var = 1
        
def convert_file(bor_file,skip_var):
    if skip_var == 0:
        bor = np.genfromtxt(bor_file,dtype=float,delimiter=',')  
        df = pd.DataFrame(bor)#.replace(np.nan, 0)
        df.to_csv(str(bor_file).replace('.ASCII_LowPassFilter','_LowPassFilter.csv'))
        print( ">> " + str(bor_file) + " -> " + str(bor_file).replace('.ASCII_LowPassFilter','_LowPassFilter.csv') )

bcm_abort_txt = open('.txt','r')
bcm_abort_list = []

bor_data_path = '/.../...'

months = {}
months['02'] = 'FEB'
months['03'] = 'MAR'
months['04'] = 'APR'
months['05'] = 'MAY'
months['06'] = 'JUN'

# i is the timestamp

for i in bcm_abort_txt:
    ver_skip = 0
    hor_skip = 0
    b_skip = 0
    l_skip = 0
    name = i[8:10] + '_' + months[i[5:7]] + '_' + i[0:4] + '_' + i[11:13] + '_' + i[14:15]
    print(name)
    bcm_abort_list.append(name)
    
    bor_ver_file = next((elem for elem in Path(bor_data_path).glob(f'*V{name}*.ASCII_LowPassFilter') if elem),None)
    if bor_ver_file == None:
        name_new = create_new_name(i)
        bor_ver_file = next((elem for elem in Path(bor_data_path).glob(f'*V{name_new}*.ASCII_LowPassFilter') if elem),None)
    skip_file(bor_ver_file,ver_skip)
        
    bor_hor_file = next((elem for elem in Path(bor_data_path).glob(f'*H{name}*.ASCII_LowPassFilter') if elem),None)
    if bor_hor_file == None:
        name_new = create_new_name(i)
        bor_hor_file = next((elem for elem in Path(bor_data_path).glob(f'*H{name_new}*.ASCII_LowPassFilter') if elem),None)
    skip_file(bor_hor_file,hor_skip)
        
    bor_b_file = next((elem for elem in Path(bor_data_path).glob(f'*B{name}*.ASCII_LowPassFilter') if elem),None)
    if bor_b_file == None:
        name_new = create_new_name(i)
        bor_b_file = next((elem for elem in Path(bor_data_path).glob(f'*B{name_new}*.ASCII_LowPassFilter') if elem),None)
    skip_file(bor_b_file,b_skip)
        
    bor_l_file = next((elem for elem in Path(bor_data_path).glob(f'*L{name}*.ASCII_LowPassFilter') if elem),None)
    if bor_l_file == None:
        name_new = create_new_name(i)
        bor_l_file = next((elem for elem in Path(bor_data_path).glob(f'*L{name_new}*.ASCII_LowPassFilter') if elem),None)
    skip_file(bor_l_file,l_skip)
        
    if bor_ver_file == None or bor_hor_file == None or bor_b_file == None or bor_l_file == None:
        continue
    
    convert_file(bor_ver_file,ver_skip)
    convert_file(bor_hor_file,hor_skip)
    convert_file(bor_b_file,b_ski)
    convert_file(bor_l_file,l_skip)
    
print('Done')