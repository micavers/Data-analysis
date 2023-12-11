
#Program to calibrate ASCII files, required SLIDE_FIRSTBUNCH_SearchSlidePy.list
## output: *.ASCII_LowPassFilter, *.ASCII_extline

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

# I use 'offline' a txt file filled with abort timestamps from 'http:/.. .php',
# so the input 'online' can also be that 

def create_new_name(name):
    date = datetime.datetime.strptime(i[0:16], '%Y-%m-%d %H:%M')
    date = date + datetime.timedelta(minutes=1)
    name_new = date.strftime('%d_%^b_%Y_%H_%M')
    return name_new

bcm_abort_txt = open('/../.txt','r')
bcm_abort_list = []

bor_data_path = '/../..'

months = {}
months['02'] = 'FEB'
months['03'] = 'MAR'
months['04'] = 'APR'
months['05'] = 'MAY'
months['06'] = 'JUN'

pathSlideDataFile   = 'SLIDE_FIRSTBUNCH_SearchSlidePy.list'

Vcoef = 110.22 # FukumaPrm[count/mA/mm]
Hcoef = -102.03 # FukumaPrm[count/mA/mm]

slope = 0.00748668/2 #myBCMCal[mA/count]
intrcpt = -0.0115363/2 #myBCMCal[mA]

# i is the timestamp

for i in bcm_abort_txt:
    name = i[8:10] + '_' + months[i[5:7]] + '_' + i[0:4] + '_' + i[11:13] + '_' + i[14:16]
    time = i[0:4] + '_' + i[5:7] + '_' + i[8:10] + '_' + i[11:13] + '_' + i[14:16] + '_' + i[17:19]

    bor_ver_file = next((elem for elem in Path(bor_data_path).glob(f'*V{name}*.ASCII') if elem),None)
    if bor_ver_file == None:
        name_new = create_new_name(i)
        bor_ver_file = next((elem for elem in Path(bor_data_path).glob(f'*V{name_new}*.ASCII') if elem),None)
    
    bor_hor_file = next((elem for elem in Path(bor_data_path).glob(f'*H{name}*.ASCII') if elem),None)
    if bor_hor_file == None:
        name_new = create_new_name(i)
        bor_hor_file = next((elem for elem in Path(bor_data_path).glob(f'*H{name_new}*.ASCII') if elem),None)
        
    bor_b_file = next((elem for elem in Path(bor_data_path).glob(f'*B{name}*.ASCII') if elem),None)
    if bor_b_file == None:
        name_new = create_new_name(i)
        bor_b_file = next((elem for elem in Path(bor_data_path).glob(f'*B{name_new}*.ASCII') if elem),None)
        
    bor_l_file = next((elem for elem in Path(bor_data_path).glob(f'*L{name}*.ASCII') if elem),None)
    if bor_l_file == None:
        name_new = create_new_name(i)
        bor_l_file = next((elem for elem in Path(bor_data_path).glob(f'*L{name_new}*.ASCII') if elem),None)
        
    for tgtFilePath in [bor_ver_file, bor_hor_file, bor_b_file, bor_l_file]:
        slide = sbf.getSlideFromFile( pathSlideDataFile, tgtFilePath )
        print(str(tgtFilePath)[39:62],'slide:',slide)
        sbf.editSlideNew(tgtFilePath, 
                         slide, 
                         str(tgtFilePath).replace('.ASCII','.ASCII_att') 
                        )
        sbf.editAttenuator6db(str(tgtFilePath).replace('.ASCII','.ASCII_att'), 
                              str(tgtFilePath).replace('.ASCII','.ASCII_att') 
                             )
        if 'MLB' in str(tgtFilePath):
            sbf.editFillPtnDeleteZeroList(str(tgtFilePath).replace('.ASCII','.ASCII_att'), 
                                          str(tgtFilePath).replace('.ASCII','.ASCII_extline') 
                                         )
        if 'MLB' in str(tgtFilePath) or 'LL' in str(tgtFilePath):
            sbf.editFillPtnPresZeroList(str(tgtFilePath).replace('.ASCII','.ASCII_att'), 
                                        str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur') 
                                       )
        else:
            sbf.editFillPtnPresZeroList(str(tgtFilePath).replace('.ASCII','.ASCII_att'), 
                                        str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                                       )
        

    for tgtFilePath in [bor_b_file]:
        judgeAmpAd   = int( 10 ) # 10 : if ( ( adc_val_max - adc_val_min ) < 10 )
        extractLines = int( 20 )  # number of turns before the abort that I want to save
        start,stop = sbf.searchDropPoint(str(tgtFilePath).replace('.ASCII','.ASCII_extline'), 
                                         str(tgtFilePath).replace('.ASCII','.ASCII_extline'), 
                                         judgeAmpAd, 
                                         extractLines
                                        )
        sbf.changeListBToCurList(str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur'), 
                                 slope, 
                                 intrcpt, 
                                 str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur') 
                                )
        
    for tgtFilePath in [bor_l_file]:
        sbf.editZeroBaseLine(str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur'), 
                             str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur') 
                            )
        sbf.changeListBToCurList(str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur'), 
                                 slope, 
                                 intrcpt, 
                                 str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur') 
                                )

    for tgtFilePath in [bor_ver_file, bor_hor_file, bor_l_file]:
        if 'MLV' in str(tgtFilePath):
            sbf.editZeroBaseLine(str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter'), 
                                 str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                                )
            sbf.changeListHVToMmList(str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter'), 
                                     str(bor_b_file).replace('.ASCII','.ASCII_BtoCur'), 
                                     Vcoef, 
                                     str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                                    )
        elif 'MLH' in str(tgtFilePath):
            sbf.editZeroBaseLine(str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter'), 
                                 str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                                )
            sbf.changeListHVToMmList(str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter'), 
                                     str(bor_b_file).replace('.ASCII','.ASCII_BtoCur'), 
                                     Hcoef, 
                                     str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') )
        elif 'MLL' in str(tgtFilePath):
            sbf.editZeroBaseLine(str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur'), 
                                 str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur') 
                                )

    for tgtFilePath in [bor_ver_file, bor_hor_file, bor_b_file, bor_l_file]:
        if 'MLB' in str(tgtFilePath) or 'MLL' in str(tgtFilePath):
            sbf.editFillterLowpass(str(tgtFilePath).replace('.ASCII','.ASCII_BtoCur'), 
                                   str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                                  )
            sbf.cutListDropLine(str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter'), 
                                str(bor_b_file).replace('.ASCII','.ASCII_extline'), 
                                str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                               )
        else:
            sbf.editFillterLowpass(str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter'), 
                                   str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                                  )
            sbf.cutListDropLine(str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter'), 
                                str(bor_b_file).replace('.ASCII','.ASCII_extline'), 
                                str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                               )

        sbf.editZeroToNan(str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter'), 
                          str(tgtFilePath).replace('.ASCII','.ASCII_LowPassFilter') 
                         )
        
    os.system(f'rm {bor_data_path}/*ASCII_att')
    os.system(f'rm {bor_data_path}/*ASCII_BtoCur')
    print(time,'Done')