#Program to plot BOR and BCM outputs after calibration
## output: *.png

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
import subFuncPlotImage_Fillter as sbf
from matplotlib.offsetbox import AnchoredText


def create_new_name(name):
    date = datetime.datetime.strptime(i[0:16], '%Y-%m-%d %H:%M')
    date = date + datetime.timedelta(minutes=1)
    name_new = date.strftime('%d_%^b_%Y_%H_%M')
    return name_new


bor_data_path = '/../..'

# here I create a folder in which I save the plots 
try:
    os.mkdir('plots')
    print("Directory plots Created") 
except FileExistsError:
    print("Directory plots already exists")
    
# number of turns before the abort to plot (it depends on how many turns you save in the calibrated file)
num_cols = 8

plt.rcParams.update({
          'font.size': 20,
          'figure.figsize': (40, 20),  #figure with 8 columns use (40,20), 10 use (50,20), 20 use (100, 20)
          'axes.grid': False,
          'grid.linestyle': '-',
          'grid.alpha': 0.2,
          'lines.markersize': 5.0,
          'xtick.minor.visible': True,
          'xtick.direction': 'in',
          'xtick.major.size': 10.0,
          'xtick.minor.size': 5.0,
          'xtick.top': True,
          'ytick.minor.visible': True,
          'ytick.direction': 'in',
          'ytick.major.size': 10.0,
          'ytick.minor.size': 5.0,
          'ytick.right': True,
          'errorbar.capsize': 0.0,
        })

# I use 'offline' a txt file filled with abort timestamps from 'http://kekb-co-web.kek.jp/doc/abort/timestamp_onetable.php',
# so the input 'online' can also be that 

bcm_abort_txt = open('/../.txt','r')
bcm_abort_list = []

bcm_path_to_file_ler = '/../../'

bor = {}

months = {}
months['02'] = 'FEB'
months['03'] = 'MAR'
months['04'] = 'APR'
months['05'] = 'MAY'
months['06'] = 'JUN'

pathSlideDataFile   = 'SLIDE_FIRSTBUNCH_SearchSlidePy.list'

slope = 0.00748668
intrcpt = -0.0115363

for i in bcm_abort_txt:
    name = i[8:10] + '_' + months[i[5:7]] + '_' + i[0:4] + '_' + i[11:13] + '_' + i[14:15]
    time = i[0:4] + '_' + i[5:7] + '_' + i[8:10] + '_' + i[11:13] + '_' + i[14:16] + '_' + i [17:19]
    bcm_abort_list.append(name)
    bcm_name = i[0:4] + i[5:7] + i[8:10] + '_' + i[11:13] + i[14:15]
    
    try:
        os.mkdir(f'plots/{time}')
        print(f"Directory plots/{time} Created") 
    except FileExistsError:
        print(f"Directory plots/{time} already exists")

    bor_ver_file = next((elem for elem in Path(bor_data_path).glob(f'*V{name}*.csv') if elem),None)
    if bor_ver_file == None:
        name_new = create_new_name(i)
        bor_ver_file = next((elem for elem in Path(bor_data_path).glob(f'*V{str(name_new)}*.csv') if elem),None)
    
    bor_hor_file = next((elem for elem in Path(bor_data_path).glob(f'*H{name}*.csv') if elem),None)
    if bor_hor_file == None:
        name_new = create_new_name(i)
        bor_hor_file = next((elem for elem in Path(bor_data_path).glob(f'*H{str(name_new)}*.csv') if elem),None)
        
    bor_b_file = next((elem for elem in Path(bor_data_path).glob(f'*B{name}*.csv') if elem),None)
    if bor_b_file == None:
        name_new = create_new_name(i)
        bor_b_file = next((elem for elem in Path(bor_data_path).glob(f'*B{str(name_new)}*.csv') if elem),None)
        
    #bor_l_file = next((elem for elem in Path(bor_data_path).glob(f'*L{name}*.csv') if elem),None)
    #if bor_l_file == None:
    #    name_new = create_new_name(i)
    #    bor_l_file = next((elem for elem in Path(bor_data_path).glob(f'*L{str(name_new)}*.csv') if elem),None)
        
    extline_file = next((elem for elem in Path(bor_data_path).glob(f'*B{name}*extline') if elem),None)
    if extline_file == None:
        name_new = create_new_name(i)
        extline_file = next((elem for elem in Path(bor_data_path).glob(f'*B{str(name_new)}*extline') if elem),None)
    
    for folder_name, subfolders, filenames in os.walk(bcm_path_to_file_ler):
        for subfolder in subfolders:
            bcm_loss_file = next((elem for elem in Path(bcm_path_to_file_ler+subfolder).glob(f'{bcm_name}*_LERbcm.ascii2') if elem),None)
            if bcm_loss_file:
                break
        if bcm_loss_file:
            break
    
    last_turn = np.genfromtxt(extline_file,dtype=int,delimiter=',')[1] 
    slide_bcm = sbf.getSlideFromFile( pathSlideDataFile, bor_b_file )
    slide_bcm_loss = sbf.getSlideFromFile( pathSlideDataFile, bor_l_file )
        
        
    if bor_ver_file == None or bor_hor_file == None or bor_b_file == None: #or bor_l_file == None:
        print('File missing for', time)
        continue

    bor['ver'] = pd.read_csv(bor_ver_file)  
    bor['hor'] = pd.read_csv(bor_hor_file)
    bor['b'] = pd.read_csv(bor_b_file)
    bor['loss'] = np.genfromtxt(bcm_loss_file,dtype=int)
    
    
    n_buckets = {}
    k=0
    fig,ax = plt.subplots(nrows=4,ncols=num_cols,sharex=True)
    ax = ax.flatten()
    plt.subplots_adjust(wspace=0, hspace=0)
    for bor_type in ['hor','ver','b','loss']:
        n_turns = len(bor[bor_type])
        for turn in range(n_turns-num_cols,n_turns):
            if bor_type != 'loss' and bor_type != 'b':
                n_buckets[bor_type] = len(bor[bor_type].iloc[turn])
                x_1 = range(1,int(n_buckets[bor_type]/2))
                y_1 = bor[bor_type].iloc[turn][1:int(n_buckets[bor_type]/2)]
                x_2 = range(int(n_buckets[bor_type]/2),n_buckets[bor_type])
                y_2 = bor[bor_type].iloc[turn][int(n_buckets[bor_type]/2):]
            elif bor_type == 'loss':
                n_buckets[bor_type] = 5120
                x_1 = range(0,int(n_buckets[bor_type]/2))
                y_1 = np.multiply([row[3] for row in bor['loss'][((last_turn-4000-n_turns+turn+1)*5120):((last_turn-3999-n_turns+turn+1)*5120)][0:int(5120/2)]],slope)+intrcpt
                x_2 = range(int(n_buckets[bor_type]/2),n_buckets[bor_type])
                y_2 = np.multiply([row[3] for row in bor['loss'][((last_turn-4000-n_turns+turn+1)*5120):((last_turn-3999-n_turns+turn+1)*5120)][int(5120/2):5120]],slope)+intrcpt
            elif bor_type == 'b':
                n_buckets[bor_type] = len(bor[bor_type].iloc[turn])
                x_1 = range(1,int(n_buckets[bor_type]/2))
                y_1 = bor[bor_type].iloc[turn][1:int(n_buckets[bor_type]/2)]
                x_2 = range(int(n_buckets[bor_type]/2),n_buckets[bor_type])
                y_2 = bor[bor_type].iloc[turn][int(n_buckets[bor_type]/2):] 

            if bor_type == 'hor':
                ax[k].scatter(x_1,y_1, color = 'fuchsia')
                ax[k].scatter(x_2,y_2, color = 'fuchsia')
            if bor_type == 'ver':
                ax[k].scatter(x_1,y_1, color = 'red')
                ax[k].scatter(x_2,y_2, color = 'red')
            elif bor_type == 'b':
                ax[k].plot(x_1,y_1, color = 'black')
                ax[k].plot(x_2,y_2, color = 'black')
            else:
                ax[k].plot(x_1,y_1, color = 'black', alpha=0.7)
                ax[k].plot(x_2,y_2, color = 'black', alpha=0.7)

            if turn == n_turns-num_cols and bor_type != 'b' and bor_type != 'loss':
                ax[k].set_ylabel(f'Output (mm)', fontsize=18)
                anchored_text = AnchoredText(f'BOR(LER{bor_type})', loc='upper left', prop=dict(size=30, fontweight="bold"), frameon=False)
                ax[k].add_artist(anchored_text)
                ax[k].set_yticks([-0.4,-0.2,0,0.2,0.4])
            elif turn == n_turns-num_cols and bor_type == 'b':
                ax[k].set_ylabel(f'Output (mA)', fontsize=18)
                anchored_text = AnchoredText(f'BCM(LER)', loc='upper left', prop=dict(size=30, fontweight="bold"), frameon=False)
                ax[k].add_artist(anchored_text)
                ax[k].set_yticks([0,0.5,1])
            elif turn == n_turns-num_cols and bor_type == 'loss':
                ax[k].set_ylabel(f'BCM LER loss (mA)', fontsize=18)
                anchored_text = AnchoredText(f'BCM loss(LER)', loc='upper left', prop=dict(size=30, fontweight="bold"), frameon=False)
                ax[k].add_artist(anchored_text)
                ax[k].set_yticks([0,0.2,0.4])
            else:
                ax[k].set_yticklabels([])
            ax[k].set_xticks([n_buckets[bor_type]/4,n_buckets[bor_type]/4*2,n_buckets[bor_type]/4*3,n_buckets[bor_type]])
            ax[k].set_xlabel('Bucket N', loc='center', fontsize=18)
            ax[k].set_xlim(0,5120)
            if bor_type != 'b' and bor_type != 'loss':
                ax[k].set_ylim(-0.6,0.6)
                ax[k].hlines(0, 0, 5120, color='black')
            elif bor_type == 'loss':
                ax[k].set_ylim(0,0.6)
            else:
                ax[k].set_ylim(0,1.5)
            if bor_type == 'hor':
                if turn == n_turns-num_cols:
                    ax[k].set_title(f'{time} \n\nTurn {last_turn-n_turns+turn+1}', fontsize=20)
                else:
                    ax[k].set_title(f'Turn {last_turn-n_turns+turn+1}', fontsize=20)
            k+=1



    plt.savefig(f'plots/{time}/BOR_LER_output_{num_cols}_turns_{time}.png', bbox_inches='tight', facecolor='white')
    plt.clf()
    plt.close() 