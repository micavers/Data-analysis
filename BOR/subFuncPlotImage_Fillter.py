import sys
import os
import shutil
import glob
import datetime

import subprocess
import binascii
import copy
import numpy
import pandas
import ast
from scipy import signal
from scipy.signal import butter, lfilter, freqz
#from scipy.optimize import curve_fit
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
mpl.rcParams['agg.path.chunksize'] = 100000

from matplotlib.font_manager import FontProperties

def searchADCFilePaths() :
    pathADCs = []
    pathADCs = glob.glob("./*.ADC")
    pathADCs.sort()
    return pathADCs

def outChangeDirAndExt( inpFilePathName, outDir, extBefor, extAfter ) :
    fileName = os.path.basename( inpFilePathName )
    outFile  = outDir + fileName.replace( extBefor, extAfter )
    return outFile

def changeADCToAscii( tgtFilePath, outFilePath ) :
    rfname = tgtFilePath
    wfname = outFilePath
    rfp = open( rfname, 'rb' )
    wfp = open( wfname, 'w' )
    cntTurn = 0
    while 1 :
        databunch = rfp.read( 5120 )
        cntBunch = 0
        line = ''
        if databunch :
            ary = bytearray( databunch )
            for wks in ary :
                cntBunch = cntBunch + 1
                if ( cntBunch < 5120 ) :
                    line = line + str( wks ) + ','
                    pass
                else :
                    line = line + str( wks )
                    pass
                pass
            wfp.write( line + '\n' )
            cntTurn = cntTurn + 1
            pass
        else :
            break
        pass
    rfp.close()
    wfp.close()
    pass

def extractFilesB( inpPathList ) :
    paths = []
    for path in inpPathList :
        fileName = os.path.basename( path )
        if ( fileName[2:3] == 'B' ) :
            paths.append( path )
            pass
        pass
    paths.sort()
    return paths

def extractFilesV( inpPathList ) :
    paths = []
    for path in inpPathList :
        fileName = os.path.basename( path )
        if ( fileName[2:3] == 'V' ) :
            paths.append( path )
            pass
        pass
    paths.sort()
    return paths

def extractFilesH( inpPathList ) :
    paths = []
    for path in inpPathList :
        fileName = os.path.basename( path )
        if ( fileName[2:3] == 'H' ) :
            paths.append( path )
            pass
        pass
    paths.sort()
    return paths

def extractFilesL( inpPathList ) :
    paths = []
    for path in inpPathList :
        fileName = os.path.basename( path )
        if ( fileName[2:3] == 'L' ) :
            paths.append( path )
            pass
        pass
    paths.sort()
    return paths

def getFillPtnData( filePath ) :
    adcName = os.path.basename( filePath )
    tgtRing  = adcName[1:2].lower() # [h]or[l]
    #tgtType  = adcName[2:3].upper() # [B]or[V]or[H]or[L]
    #adc_id   = os.path.splitext( adcName )[0]

    #--------------------
    # search fill-pattern
    #--------------------
    searchTime    = datetime.datetime.strptime( '20150101000000', '%Y%m%d%H%M%S' )
    fillFilePaths = glob.glob( '/../..fill_' + tgtRing + '_*.dat' )
    for fillFilePath in fillFilePaths :
        fillFileName = os.path.basename( fillFilePath )
        fillFileTime = datetime.datetime.strptime( fillFileName[ 7 : 26 ], '%Y_%m_%d_%H_%M_%S' )
        adcFileTime  = datetime.datetime.strptime( adcName[3:23], '%d_%b_%Y_%H_%M_%S' )
        if ( fillFileTime < adcFileTime ) :
            if ( fillFileTime > searchTime ) :
                searchTime = fillFileTime
                pass
            pass
        pass
    fill_Path = '/../../fill_' + tgtRing + '_' + searchTime.strftime( '%Y_%m_%d_%H_%M_%S' ) + '.dat'
    #--------------------
    # copy fill-pattern file
    #--------------------
    fill_file_name = os.path.basename( fill_Path )
    #shutil.copy( fill_Path, ( './' + fill_file_name ) )

    #--------------------
    # read fill-pattern file
    #--------------------
    rfp_fill = open( fill_Path, 'r' )
    rfp_fill_lines = rfp_fill.readlines()
    rfp_fill.close()

    fill_datas = []

    intWkCnt = 0
    intPilotBunch = 0 # pilot bunch No = 0~
    intCountBunch = 0 # count bunch
    for line in rfp_fill_lines :
        if ( len( line ) > 0 ) :
            if ( ( ( line.strip() )[0:1] ) != '#' ) :
                index = int( ( line[0:6] ).strip() )
                data1 = 0
                if ( float( ( line[6:16] ).strip() ) > 0 ) :
                    data1 = 1
                    intCountBunch = intCountBunch + 1
                    intPilotBunch = intWkCnt
                    pass
                data2 = 0
                if ( float( ( line[16:26] ).strip() ) > 0 ) :
                    data2 = 1
                    pass
                intWkCnt = intWkCnt + 1
                fill_datas.append( data1 )
                pass
            pass
        pass

    print( ">>> fill-pattern: " + fill_file_name + " PilotBunch: " + str( intPilotBunch ) + " CountBunch: " + str( intCountBunch ) )
    return fill_datas, intPilotBunch, intCountBunch

def getSlideFromFile( inpSlideFile, tgtFilePath ) :
    rfname = inpSlideFile
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()
    slide = 0
    for slidedat in rfp_lines :
        wkLine = slidedat.strip()
        if ( len( wkLine ) > 0 ) and ( wkLine[0:1] != '#' ) and ( wkLine.find( ',' ) > 0 ) :
            slidefname = ( ( wkLine.split( ',' ) )[0] ).strip()
            tgtfname   = ( ( os.path.basename( tgtFilePath ) ).split( '.' ) )[0]
            if ( slidefname == tgtfname ) :
                slide = ( ( wkLine.split( ',' ) )[1] ).strip()
                pass
            pass
        pass
    return slide

def editSlide( tgtFilePath, slide, outFilePath ) :
    rfname = tgtFilePath
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()

    wfname = outFilePath
    wfp = open( wfname, 'w' )

    for line in rfp_lines :
        vals_org = line.split( ',' )
        flg_slide = 0
        vals = []
        if ( int( slide ) > 0 ) :
            flg_slide = 1
            for icnt in range( len( vals_org ) - int ( slide ) ) :
                vals.append( vals_org[ icnt + int( slide ) ] )
                pass
            for icnt in range( int( slide ) ) :
                vals.append( 0 )
                pass
            pass
        elif ( int( slide ) < 0 ) :
            flg_slide = 1
            for icnt in range( len( vals_org ) + int ( slide ) ) :
                if ( ( icnt + int( slide ) ) < 0 ) :
                    vals.append( vals_org[ icnt + int( slide ) ] )
                    pass
                else :
                    vals.append( vals_org[ icnt + int( slide ) ] )
                    pass
                pass
            del vals[len( vals_org ):]
            pass
        else :
            for icnt in range( len( vals_org ) ) :
                vals.append( vals_org[ icnt ] )
                pass
            pass

        out = ''
        for val in vals :
            out = out + str( int( val ) ) + ','
            pass
        if ( out[-1] == ',' ) :
            out = out[0 : -1]
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

def editSlideNew( tgtFilePath, slide, outFilePath ) :
    rfname = tgtFilePath
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()

    wfname = outFilePath
    wfp = open( wfname, 'w' )

    k = 0
    n_lines = len(rfp_lines)
    all_lines = [] 
    for line in rfp_lines :
        all_lines.append(line.split( ',' ))
        
    for line in rfp_lines :
        vals_org = line.split( ',' )
        flg_slide = 0
        vals = []
        if ( int( slide ) > 0 ) :
            if k < n_lines-1:
                flg_slide = 1
                for icnt in range( len( vals_org ) - int ( slide ) ) :
                    vals.append( vals_org[ icnt + int( slide ) ] )
                    pass
                for icnt in range( int( slide ) ) :
                    vals.append( all_lines[k+1][ icnt ] )
                    pass
                pass
            else:
                for icnt in range( len( vals_org ) - int ( slide ) ) :
                    vals.append( vals_org[ icnt + int( slide ) ] )
                    pass
                for icnt in range( int( slide ) ) :
                    vals.append( 0 )
                    pass
                pass
        elif ( int( slide ) < 0 ) :
            if k == 0:
                flg_slide = 1
                for icnt in range( - int ( slide ) ) :
                    vals.append( 0 )
                    pass
                for icnt in range( - int ( slide ), len( vals_org ) ) :
                    vals.append( vals_org[ icnt + int( slide ) ] )
                    pass
            else:
                for icnt in range( len( vals_org ) - int ( slide ), len( vals_org ) ) :
                    vals.append( all_lines[k-1][ icnt ] )
                    pass
                for icnt in range( - int ( slide ), len( vals_org ) ) :
                    vals.append( vals_org[ icnt + int( slide ) ] )
                    pass
        else :
            for icnt in range( len( vals_org ) ) :
                vals.append( vals_org[ icnt ] )
                pass
            pass

        out = ''
        for val in vals :
            out = out + str( int( val ) ) + ','
            pass
        if ( out[-1] == ',' ) :
            out = out[0 : -1]
            pass
        wfp.write( out + '\n' )
        pass
        k+=1
    wfp.close()
    pass

def editAttenuator6db( tgtFilePath, outFilePath ) :
    rfname = tgtFilePath
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()

    wfname = outFilePath
    wfp = open( wfname, 'w' )

    for line in rfp_lines :
        vals = line.split( ',' )
        out = ''
        for val in vals :
            val = int( float( val ) * 2 )
            out = out + str( int( val ) ) + ','
            pass
        if ( out[-1] == ',' ) :
            out = out[0 : -1]
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

def editZeroBaseLine( tgtFilePath, outFilePath ) :
    rfname = tgtFilePath
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()

    wfname = outFilePath
    wfp = open( wfname, 'w' )

    #-----------------
    # get base line
    #-----------------
    avr_cnt = 3
    wkBaseADCs = []
    for adcidx in range( 0, 5120 ) :
        wkBaseADCs.append( 0 )
        pass
    for cntline in range( 0, int( avr_cnt ) ) :
        vals  = rfp_lines[ cntline ].split( ',' )
        for cntAdc in range( len( vals ) ) :
            wkBaseADCs[ cntAdc ] = float( wkBaseADCs[ cntAdc ] ) + float( vals[ cntAdc ] )
            pass
        pass
    baseADCs = []
    for adcidx in range( 0, 5120 ) :
        if( float( wkBaseADCs[ adcidx ] ) > float( 0 ) ) :
            baseADCs.append( float( wkBaseADCs[ adcidx ] ) / float( avr_cnt ) )
            pass
        else :
            baseADCs.append( float( 0 ) )
            pass
        pass

    #-----------------
    # edit base line
    #-----------------
    for line in rfp_lines :
        vals = line.split( ',' )
        out = ''
        adcidx = 0
        for val in vals :
            val = int( float( val ) - float( baseADCs[ adcidx ] ) )
            adcidx = adcidx + 1
            out = out + str( int( val ) ) + ','
            pass
        if ( out[-1] == ',' ) :
            out = out[0 : -1]
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

def editFillPtnDeleteZeroList( tgtFilePath, outFilePath ) :
    rfname1 = tgtFilePath
    rfp1 = open( rfname1, 'r' )
    rfp1_lines = rfp1.readlines()
    rfp1.close()

    fills, pilotbunch, countbunch = getFillPtnData( tgtFilePath )

    wfname = outFilePath
    wfp = open( wfname, 'w' )
    for line in rfp1_lines :
        intFillIdx = 0
        out = ''
        vals = line.split( ',' )
        for val in vals :
            if ( float( fills[ intFillIdx ] ) > 0 ) :
                out = out + str( int( val ) ) + ','
                pass
            intFillIdx = intFillIdx + 1
            pass
        if ( out[-1] == ',' ) :
            out = out[0 : -1]
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

def searchDropPoint( tgtFilePath, outFilePath, judgeAmpAd, extractLines ) :
    rfname = tgtFilePath
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()

    wfname = outFilePath
    wfp = open( wfname, 'w' )

    count_line = int( 0 )
    drop_line  = int( 0 )
    for line in rfp_lines :
        ListAd = line.split( ',' )
        wkAdMax = int( 0 )
        wkAdMin = int( 999 )
        for wkAd in ListAd :
            if ( int( wkAd ) >= wkAdMax ) :
                wkAdMax = int( wkAd )
                pass
            if ( int( wkAd ) <= wkAdMin ) :
                wkAdMin = int( wkAd )
                pass
            pass
        if ( ( int( wkAdMax ) - int( wkAdMin ) ) < int( judgeAmpAd ) ) :
            drop_line = int( count_line )
            break
        count_line = int( count_line ) + int( 1 )
        pass

    if ( int( drop_line ) < int( extractLines ) ) :
        drop_line = int( extractLines )
        pass
    ext_line_start = int( drop_line ) - int( extractLines ) + int( 1 )
    ext_line_end   = int( drop_line )

    print( '>>> extract line : ' + str( ext_line_start ) + ',' + str( ext_line_end ) )
    wfp.write( str( ext_line_start ) + ',' + str( ext_line_end ) + '\n' )
    pass

def getBunchCurrentFromB( tgtFilePath ) :

    fills, intPilotBunch, intCountBunch = getFillPtnData( tgtFilePath )

    listBunchCurrent = []
    wkFileADC = os.path.basename( tgtFilePath )
    if ( wkFileADC[2:3] == 'B' ) :
        tgtADCRing = wkFileADC[1:2].upper()
        tgtADC_HV  = wkFileADC[2:3].upper()
        cmdKblog1 = '/../.. -r '
        cmdKblog2 = 'FB' + wkFileADC[1:2] + ':BCM:BCM'
        flgRslt   = 0
        sec_stt_val      = 0
        sec_end_val      = 5

        outRslt   = 0

        #/usr/local/bin/kblogrd -r FBL:BCM:BCM -t 20220315031841-20220315031841 -f free BM/BCM
        #/usr/local/bin/kblogrd -r FBL:BCM:BCM -t 20220315031851-20220315031851 -f free BM/BCM
        # result(5120) :
        #03/15/2022 03:18:51.27  FBL:BCM:BCM     0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00   0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00   0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00    0.000000e+00

        while ( flgRslt == 0 ) :
            sec_stt_val = sec_stt_val - 5
            sec_end_val = sec_end_val - 5
            adcdate_stt = datetime.datetime.strptime( wkFileADC[3:23], '%d_%b_%Y_%H_%M_%S' ) + datetime.timedelta(seconds=int(sec_stt_val))
            adcdate_end = datetime.datetime.strptime( wkFileADC[3:23], '%d_%b_%Y_%H_%M_%S' ) + datetime.timedelta(seconds=int(sec_end_val))
            cmdKblog3   = ' -t '
            cmdKblog4   = adcdate_stt.strftime( '%Y%m%d%H%M%S' ) + '-' + adcdate_end.strftime( '%Y%m%d%H%M%S' )
            cmdKblog5   = ' -f free BM/BCM'
            cmd   = cmdKblog1 + cmdKblog2 + cmdKblog3 + cmdKblog4 + cmdKblog5
            rslt1 = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE )
            rslt2 = rslt1.communicate()

            print( '>>> ' + cmd )
            if ( len( rslt2 ) > 0 ) :
                if ( rslt2[ 0 ].find( cmdKblog2 ) >= 0 ) :
                    rslt3 = rslt2[0]
                    rslt4 = rslt3.split( '\t' )
                    if ( float( rslt4[ 2 + intPilotBunch ] ) != float( 0 ) ) :
                        for rslt4cnt in range( 2, len( rslt4 ) ) :
                            listBunchCurrent.append( rslt4[ rslt4cnt ] )
                            pass
                        pass
                    if ( len( listBunchCurrent ) >= 5120 ) :
                        flgRslt = 1
                        pass
                    else :
                        listBunchCurrent = []
                        pass
                    pass
                pass
            pass
        pass
    return listBunchCurrent

def getLinearSlopeInterceptFromAllB_AllBunch( listPathB, listBunchCurrents ) :
    listFills = []
    for tgtFilePath in listPathB :
        fills, intPilotBunch, intCountBunch = getFillPtnData( tgtFilePath )
        listFills.append( fills )
        pass

    bufAD  = []
    bufCUR = []
    for listIdx in range( len( listFills ) ) :
        fills = listFills[ listIdx ]
        pathB = listPathB[ listIdx ]
        currs = listBunchCurrents[ listIdx ]

        rfp = open( pathB, 'r' )
        rfp_lines = rfp.readlines()
        rfp.close()

        for lineB in rfp_lines :
            vals = lineB.split( ',' )
            for val in vals :
                bufAD.append( val )
                pass
            for valIdx in range( len( fills ) ) :
                if ( fills[ valIdx ] == 1 ) :
                    bufCUR.append( currs[ valIdx ] )
                    pass
                pass
            break ###
            pass
        break ###
        pass

    if ( len( bufAD ) != len( bufCUR ) ) :
        print( ">> reg1dim( x, y ), Unmatch len(x):" + str( len( bufAD ) ) + " len(y):" + str( len( bufCUR ) ) )
        pass

    x = numpy.array( bufAD,  dtype=float )
    y = numpy.array( bufCUR, dtype=float )
    slope, intrcpt = reg1dim( x, y )

    return slope, intrcpt

def reg1dim( x, y ) :
    n = len( x )
    a = ( ( numpy.dot(x, y) - y.sum() * x.sum() / n ) / ( ( x ** 2 ).sum() - x.sum()**2 / n ) )
    b = ( y.sum() - a * x.sum() ) / n
    return a, b

def changeListBToCurList( tgtFilePathB, slope, intercept, outFilePathB ) :
    rfname = tgtFilePathB
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()

    wfname = outFilePathB
    wfp = open( wfname, 'w' )
    for line in rfp_lines :
        ads = line.split( ',' )
        last = len( ads )
        cnt  = 0
        out = ''
        for ad in ads :
            if ( int( ad ) != 0 ) :
                cur = float( ( float( ad ) * float( slope ) ) + float( intercept ) )
                pass
            else :
                cur = 0
                pass
            cnt = cnt + 1
            if ( cnt >= last ) :
                out = out + str( cur )
                pass
            else :
                out = out + str( cur ) + ','
                pass
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

def changeListHVToMmList( tgtFilePathHV, tgtFilePathB, FukumaCoef, outFilePathHV ) :
    rfname1  = tgtFilePathHV
    rfp1 = open( rfname1, 'r' )
    rfp1_lines = rfp1.readlines()
    rfp1.close()

    rfname2  = tgtFilePathB
    rfp2 = open( rfname2, 'r' )
    rfp2_lines = rfp2.readlines()
    rfp2.close()

    wfname  = outFilePathHV
    wfp = open( wfname, 'w' )
    fileBLineCnt = 0
    for line1 in rfp1_lines :
        line1s  = line1.split( ',' )
        fileBs  = rfp2_lines[ fileBLineCnt ].split( ',' )
        out = ''
        intWkAdcCntB  = 0
        for adc in line1s :
            if ( int( adc ) == 0 ) :
                mm = 0
                pass
            else :
                if ( float( fileBs[ intWkAdcCntB ] ) != 0 ) :
                    # adc[count]
                    # MLBs[mA]
                    # FukumaCoef[count/mm/mA]
                    mm = ( ( 1/float( FukumaCoef ) ) * float( adc ) ) / float( fileBs[ intWkAdcCntB ] )
                else :
                    mm = 0
                    pass
                pass
            intWkAdcCntB  = intWkAdcCntB + 1
            if ( intWkAdcCntB >= len( line1s ) ) :
                out = out + str( mm )
                pass
            else :
                out = out + str( mm ) + ','
                pass
            pass
        fileBLineCnt = fileBLineCnt + 1
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

def changeListName( tgtFilePathL, outFilePathL ) :
    rfname1  = tgtFilePathL
    rfp1 = open( rfname1, 'r' )
    rfp1_lines = rfp1.readlines()
    rfp1.close()

    wfname  = outFilePathL
    wfp = open( wfname, 'w' )
    fileBLineCnt = 0
    for line1 in rfp1_lines :
        wfp.write( line1 )
        pass
    wfp.close()
    pass

def swapRowClm( tgtFilePath, outFilePath ) :
    rfname = tgtFilePath
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()

    #print( len( rfp_lines ) )

    rdata = []
    icntrow = 0
    for line in rfp_lines :
        rdata.append([])
        vals = line.split( ',' )
        for val in vals :
            rdata[ icntrow ].append( val )
            pass
        icntrow = icntrow + 1
        pass
    cdata = []
    for cntclm in range( len( rdata[ 0 ] ) ) : # 0~1174
        cdata.append( [] )
        for cntrow in range( len( rdata ) ) :
            cdata[ cntclm ].append( rdata[ cntrow ][ cntclm ] )
            pass
        pass

    wfname = outFilePath
    wfp = open( wfname, 'w' )
    for cntrow in range( len( cdata ) ) :
        out = ''
        for cntclm in range( len( cdata[ cntrow ] ) ) :
            out = out + str( float( cdata[ cntrow ][ cntclm ] ) ) + ','
            pass
        if ( out[-1:] == ',' ) :
            out = out[0:-1]
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

#----------------------------------------
#
#----------------------------------------
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def cutListDropLine( tgtFilePath, drpFilePath, outFilePath ) :
    pfname = drpFilePath
    pfp = open( pfname, 'r' )
    pfp_lines = pfp.readlines()
    pfp.close()
    ext_line_start = int( 5120 ) - int( 1 ) - int( 6 )
    ext_line_end   = int( 5120 ) - int( 1 )
    for line in pfp_lines :
        items = line.split( ',' )
        if len( items ) > 1 :
            ext_line_start = int( items[0] )
            ext_line_end   = int( items[1] )
            break
        pass

    rfname = tgtFilePath
    rfp = open( rfname, 'r' )
    rfp_lines = rfp.readlines()
    rfp.close()

    wfname = outFilePath
    wfp = open( wfname, 'w' )

    count_line = int( 0 )
    wkBuf = []
    for line in rfp_lines :
        if ( ( count_line >= ext_line_start ) and ( count_line <= ext_line_end ) ) :
            wfp.write( line )
            wkBuf.append( line )
            pass
        count_line = int( count_line ) + int( 1 )
        pass

    print( ">>> " + str( drpFilePath ) + ", " + str( ext_line_start ) + " -> " + str( ext_line_end ) + ", " + str( len( wkBuf ) ) )
    wfp.close()
    return ext_line_end

def editZeroToNan( tgtFilePath, outFilePath ) :
    rfname1 = tgtFilePath
    rfp1 = open( rfname1, 'r' )
    rfp1_lines = rfp1.readlines()
    rfp1.close()

    fills, intPilotBunch, intCountBunch = getFillPtnData( tgtFilePath )

    wfname = outFilePath
    wfp = open( wfname, 'w' )
    for line in rfp1_lines :
        intFill_1_cnt = 0
        intFillIdx = 0
        out = ''
        vals = line.split( ',' )
        for val in vals :
            if ( float( fills[ intFillIdx ] ) > 0 ) :
                intFill_1_cnt += 1
                out = out + str( float( val ) ) + ','
                pass
            else :
                out = out + str( float('Nan') ) + ','
                pass
            intFillIdx = intFillIdx + 1
            pass
        if ( out[-1] == ',' ) :
            out = out[0 : -1]
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

def makeImage_scatter_AbtPoint( tgtFilePath, drpFilePath, slide, graph_Xword, ptn ) :
    tgtFileName = ( os.path.basename( tgtFilePath ) )[0:23]

    rfp1 = open( tgtFilePath, 'r' )
    rfp1_lines = rfp1.readlines()
    rfp1.close()

    ax = []
    fig = plt.figure(figsize=( 20.0, 20.0 )) # figsize=( horizontal[inches], vertical[inches] )

    rfp1_lines_Extract = rfp1_lines[:-1]
    graph_row = len( rfp1_lines_Extract )

    #--------------------------
    # make Graph X range
    #--------------------------
    maxs = []
    mins = []
    for rcnt in range( graph_row ) :
        wkline = rfp1_lines[ rcnt ]
        wkys = ( wkline.strip() ).split(',')
        vals = []
        for yval in wkys :
            if ( float( yval ) == float( 'Nan' ) ) :
                vals.append( float( 0 ) )
                pass
            else :
                vals.append( float( yval ) )
                pass
            pass
        maxs.append( max( vals ) )
        mins.append( min( vals ) )
        pass
    yMax = max( maxs )
    yMin = min( mins )

    rfp2 = open( drpFilePath, 'r' )
    rfp2_lines = rfp2.readlines()
    rfp2.close()
    for line in rfp2_lines :
        items = line.split( ',' )
        ext_line_start = int( items[0] )
        ext_line_end   = int( items[1] )
        break
    dropTurns = list( range( ext_line_start, ( ext_line_end + 1 ) ) )

    #--------------------------
    # make Graph
    #--------------------------
    for rcnt in range( graph_row ) :
        ax.append( fig.add_subplot( graph_row, 1, ( rcnt + 1 ) ) )

        wkline = rfp1_lines[ rcnt ]
        wkline.strip()
        wkys = wkline.split(',')
        y = []
        for yval in wkys :
            y.append( float( yval ) )
            pass
        x = range( 0, len( y ) )

        if ( rcnt == 0 ) :
            ax[ rcnt ].set_title( tgtFileName, loc='center' )
            pass
        ax[ rcnt ].scatter( x, y, color = "navy", s=10.0 )
        xticks = [0, 1000, 2000, 3000, 4000, 5000]
        ax[ rcnt ].set_xlim( [ float( xticks[ 0 ] ), float( 5120 ) ] )
        ax[ rcnt ].set_xticks( xticks )
        ax[ rcnt ].set_xticklabels( xticks) #, fontproperties=fp )
        ax[ rcnt ].set_ylim( [ float( yMin ), float( yMax ) ] )
        ax[ rcnt ].grid(which = "both", axis = "x", color = "black", linestyle = "--", linewidth = 1)
        ax[ rcnt ].grid(which = "both", axis = "y", color = "black", linestyle = "--", linewidth = 1)

        setword = "turn-" + str( int( graph_row ) - int( rcnt ) ) + '\n' + str( graph_Xword )
        #setword = "turn-" + str( dropTurns[ rcnt ] ) + '\n' + str( graph_Xword )
        ax[ rcnt ].set_ylabel( setword) #, fontproperties=fp )
        pass

    outFile = "graph_" + tgtFileName + "_slide" + str( int( slide ) ) + "_AbortPoint" + str( ptn ) + ".png" 
    plt.savefig( outFile, bbox_inches='tight' )
    plt.close()
    print( ">>> makePlotImage : -> " + str( outFile ) )
    pass

def editFillPtnPresZeroList( tgtFilePath, outFilePath ) :
    rfname1 = tgtFilePath
    rfp1 = open( rfname1, 'r' )
    rfp1_lines = rfp1.readlines()
    rfp1.close()

    fills, intPilotBunch, intCountBunch = getFillPtnData( tgtFilePath )

    wfname = outFilePath
    wfp = open( wfname, 'w' )
    for line in rfp1_lines :
        intFillIdx = 0
        out = ''
        vals = line.split( ',' )
        for val in vals :
            if ( float( fills[ intFillIdx ] ) > 0 ) :
                out = out + str( int( val ) ) + ','
                pass
            else :
                out = out + str( int( 0 ) ) + ','
                pass
            intFillIdx = intFillIdx + 1
            pass
        if ( out[-1] == ',' ) :
            out = out[0 : -1]
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass

def editFillterLowpass( tgtFilePath, outFilePath1 ) :
    rfp1 = open( tgtFilePath, 'r' )
    rfp1_lines = rfp1.readlines() # rfp1_lines = swap data( row=bunch, clm=cycle )
    rfp1.close()
    #print( len( rfp1_lines ) ) # 1174 ( from 5120 )

    fills, intPilotBunch, intCountBunch = getFillPtnData( tgtFilePath )

    list_AfterFillterFFT_Y = []
    for line in rfp1_lines :
        vals = line.split( ',' )

        tgtvals1 = []
        tgtvals2 = []
        for fcnt in range( len( fills ) ) :
            if ( fcnt <= 2500 ) :
                if ( fills[ fcnt ] == 1 ) :
                    tgtvals1.append( float( vals[ fcnt ] ) )
                    pass
                pass
            else :
                if ( fills[ fcnt ] == 1 ) :
                    tgtvals2.append( float( vals[ fcnt ] ) )
                    pass
                pass
            pass

        margin = 20
        addMargin_tgtvals1 = []
        for mcnt in range( margin ) :
            addMargin_tgtvals1.append( tgtvals1[ 0 ] )
            pass
        addMargin_tgtvals1.extend( tgtvals1 )

        addMargin_tgtvals2 = []
        for mcnt in range( margin ) :
            addMargin_tgtvals2.append( tgtvals2[ 0 ] )
            pass
        addMargin_tgtvals2.extend( tgtvals2 )

        #------------------
        # LowPass Fillter
        #------------------
        #order = 6         # default
        order = 1
        #fs = 30.0         # default
        fs = 99.4          # [kHz]
        cutoff = 3.667 * 1 # OK = 0[kHz] ~ 3.3667[kHz]
        data_filt1 = butter_lowpass_filter( addMargin_tgtvals1, cutoff, fs, order)
        data_filt2 = butter_lowpass_filter( addMargin_tgtvals2, cutoff, fs, order)
        data_filt1 = data_filt1[ margin : ]
        data_filt2 = data_filt2[ margin : ]
        data_filt = list( data_filt1 )
        data_filt.extend( data_filt2 )

        #------------------
        rsltvals = []
        data_filt_cnt = 0
        for fval in fills :
            if ( fval == 1 ) :
                rsltvals.append( data_filt[ data_filt_cnt ] )
                data_filt_cnt += 1
                pass
            else :
                rsltvals.append( float( 'nan' ) )
                pass
            pass

        #------------------

        y = copy.copy( rsltvals )
        list_AfterFillterFFT_Y.append( y )
        pass

    wfname = outFilePath1
    wfp = open( wfname, 'w' )
    for y_vals in list_AfterFillterFFT_Y :
        out = "" 
        for y_val in y_vals :
            out = out + str( float( y_val ) ) + ','
            pass
        if ( out[-1:] == ',' ) :
            out = out[0:-1]
            pass
        wfp.write( out + '\n' )
        pass
    wfp.close()
    pass