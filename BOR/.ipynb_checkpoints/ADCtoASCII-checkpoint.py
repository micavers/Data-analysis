#Program to convert ADC files to ASCII, before calibration
## output: *.ASCII

import sys
import os
import shutil
import glob
import datetime
from pathlib import Path
import subFuncSlideBunch as sbf


pathTargetADCFile = ''

for i in Path(pathTargetADCFile).glob('*.ADC'):
    tgtFilePath = str(i)
    outFilePath = str(i).replace('ADC','ASCII')
    if os.path.exists(outFilePath):
        print('>> ' + outFilePath + ' exist')
        continue
    sbf.changeADCToAscii( tgtFilePath, outFilePath )
    print( ">> " + tgtFilePath + " -> " + outFilePath )