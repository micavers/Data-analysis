
#Program to search for BOR and BCM bunch slide
## output: SLIDE_FIRSTBUNCH_SearchSlidePy.list

import sys
import os
import shutil
import glob
import datetime
import re
import subprocess
import binascii
import copy
import numpy
import pandas
from scipy import signal
from scipy.optimize import curve_fit
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
mpl.rcParams['agg.path.chunksize'] = 100000



adc_data_path = '/../..' 

#----------------------------------------------------
# getADCsPath(directory, ext='ADC|adc') -> return : list
#----------------------------------------------------
def getADCsPath(directory, ext='ADC|adc'):
    return [os.path.join(root, f)
            for root, _, files in os.walk(directory) for f in files
            if re.match(r'([\w]+.(?:' + ext + '))', f.lower()) ]

#----------------------------------------------------
# getFillPtnData( tgtRing, fillFilePath ) -> return : list, pilotbunch, countbunch
#----------------------------------------------------
def getFillPtnData( adc_Path ) :
    adcName = os.path.basename( adc_path )
    tgtRing  = adcName[1:2].lower() # [h]or[l]
    #--------------------
    # search fill-pattern
    #--------------------
    searchTime    = datetime.datetime.strptime( '20150101000000', '%Y%m%d%H%M%S' )
    fillFilePaths = glob.glob( '/../../fill_' + tgtRing + '_*.dat' )
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
    rfp_fill = open( ( fill_Path ), 'r' )
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

    #print( ">>> fill-pattern: " + fill_file_name + " PilotBunch: " + str( intPilotBunch ) + " CountBunch: " + str( intCountBunch ) )
    return fill_datas, intPilotBunch, intCountBunch

#----------------------------------------------------
# checkSlideFillPtn1PosOneSide( adc_path, fill_datas ) -> return : slide
#----------------------------------------------------
def checkSlideFillPtn1PosOneSide( adc_path, fill_datas ) :
    #--------------------
    # read ADC file
    #--------------------
    rfp = open( adc_path, 'rb' )

    list_5120_wigth = [0] * 5120
    #loop = int( 4096 / 2 )
    loop = int( 5 )
    for loopCnt in range( loop ) :
        line = rfp.read( 5120 )
        baseAry =  bytearray( line )
        editAry2 = list( baseAry )
        editAry2.extend( list( baseAry ) )
        wkPks = []
        for idx in range( len( editAry2 ) ) :
            if( idx < ( ( 5120 * 2 ) - 5 ) ) :
                wkPk = max( editAry2[ idx : ( idx + 5 ) ] )
                wkPks.append( wkPk )
                pass
            pass
        maxPk = max( wkPks )
        minPk = min( wkPks )
        brdrline = float( float( float( maxPk ) - float( minPk ) ) / 2 ) + float( minPk )

        editAry3 = []
        for wkv1 in editAry2 :
            if ( wkv1 > brdrline ) :
                editAry3.append( 1 )
                pass
            else :
                editAry3.append( 0 )
                pass
            pass

        listSlideOkPer = {}
        for slide in range( 5120 ) :
            line_cnt_ok = 0
            for fill_idx in range( len( fill_datas ) ) :
                if ( int( editAry3[ slide + fill_idx ] ) == int( fill_datas [ fill_idx ] ) ) :
                    line_cnt_ok += 1
                    pass
                pass
            listSlideOkPer.update( { int( slide ) : ( float( float( line_cnt_ok ) / 5120 ) ) } )
            pass
        sortListSlideOkPer = sorted( listSlideOkPer.items(),  key=lambda x:x[1], reverse=True )

        ### debug out ###
        wkOutStr = "" 
        for wkdic in sortListSlideOkPer[0:5] :
            match_per = float( wkdic[1] ) * 100
            rslt_idx  = int( wkdic[0] )
            wkOutStr  = wkOutStr + "slide:" + str( str( rslt_idx ).ljust(4) ) +"="+ str( '{:.02f}'.format(match_per) ) + "%, " 
            pass
        #print( ">>> line:" + str( str( int( loopCnt ) ).rjust(4) ) + " -> " + wkOutStr )
        ### debug out ##

        weight = 10
        for dic in sortListSlideOkPer[0:weight] :
            list_5120_wigth[ int( dic[0] ) ] = float( list_5120_wigth[ int( dic[0] ) ] ) + float( dic[1] )
            pass
        pass

    #------------------------------
    # Judge
    #------------------------------
    weightMaxVal = float( 0 )
    weightMaxIdx = int( 0 )
    for w_cnt in range( len( list_5120_wigth ) ) :
        tgtWeight = float( list_5120_wigth[ int( w_cnt ) ] )
        if ( float( tgtWeight ) > float( weightMaxVal ) ) :
            weightMaxVal = float( tgtWeight )
            weightMaxIdx = int( w_cnt )
            #print( ">>> Idx:" + str( weightMaxIdx ) + " -> Weight:" + str( weightMaxVal ) )
            pass
        pass
    #------------------------------
    if ( int( weightMaxIdx ) > 2500 ) :
        weightMaxIdx = int( weightMaxIdx ) - 5120
        pass
    return weightMaxIdx

#----------------------------------------------------
# checkSlideFillPtn1PosBothSide( adc_path, fill_datas ) -> return : slide
#----------------------------------------------------
def checkSlideFillPtn1PosBothSide( adc_path, fill_datas ) :
    #--------------------
    # read ADC file
    #--------------------
    rfp = open( adc_path, 'rb' )

    list_5120_wigth = [0] * 5120
    #loop = int( 4096 / 2 )
    loop = int( 5 )

    #------------------------------
    # Check Forward Data
    #------------------------------
    for loopCnt in range( loop ) :
        line = rfp.read( 5120 )
        baseAry =  bytearray( line )
        editAry2 = list( baseAry )
        editAry2.extend( list( baseAry ) )
        wkPks = []
        for idx in range( len( editAry2 ) ) :
            if( idx < ( ( 5120 * 2 ) - 5 ) ) :
                wkPk = max( editAry2[ idx : ( idx + 5 ) ] )
                wkPks.append( wkPk )
                pass
            pass
        maxPk = max( wkPks )
        minPk = min( wkPks )
        brdrline = float( float( float( maxPk ) - float( minPk ) ) / 2 ) + float( minPk )

        editAry3 = []
        for wkv1 in editAry2 :
            if ( wkv1 > brdrline ) :
                editAry3.append( 1 )
                pass
            else :
                editAry3.append( 0 )
                pass
            pass

        listSlideOkPer = {}
        for slide in range( 5120 ) :
            line_cnt_ok = 0
            for fill_idx in range( len( fill_datas ) ) :
                if ( int( editAry3[ slide + fill_idx ] ) == int( fill_datas [ fill_idx ] ) ) :
                    line_cnt_ok += 1
                    pass
                pass
            listSlideOkPer.update( { int( slide ) : ( float( float( line_cnt_ok ) / 5120 ) ) } )
            pass
        sortListSlideOkPer = sorted( listSlideOkPer.items(),  key=lambda x:x[1], reverse=True )

        ### debug out ###
        wkOutStr = "" 
        for wkdic in sortListSlideOkPer[0:5] :
            match_per = float( wkdic[1] ) * 100
            rslt_idx  = int( wkdic[0] )
            wkOutStr  = wkOutStr + "slide:" + str( str( rslt_idx ).ljust(4) ) +"="+ str( '{:.02f}'.format(match_per) ) + "%, " 
            pass
        #print( ">>> line:" + str( str( int( loopCnt ) ).rjust(4) ) + " -> " + wkOutStr )
        ### debug out ##

        weight = 10
        for dic in sortListSlideOkPer[0:weight] :
            list_5120_wigth[ int( dic[0] ) ] = float( list_5120_wigth[ int( dic[0] ) ] ) + float( dic[1] )
            pass
        pass

    #------------------------------
    # Check Reverse Data
    #------------------------------
    for loopCnt in range( loop ) :
        line = rfp.read( 5120 )
        baseAry =  bytearray( line )
        editAry2 = list( baseAry )
        editAry2.extend( list( baseAry ) )

        #------------
        # Reverse
        #------------
        rvs_editAry2 = []
        for wkv in editAry2 :
            rvs_editAry2.append( wkv * -1 )
            pass

        wkPks = []
        for idx in range( len( rvs_editAry2 ) ) :
            if( idx < ( ( 5120 * 2 ) - 5 ) ) :
                wkPk = max( rvs_editAry2[ idx : ( idx + 5 ) ] )
                wkPks.append( wkPk )
                pass
            pass
        maxPk = max( wkPks )
        minPk = min( wkPks )
        brdrline = float( float( float( maxPk ) - float( minPk ) ) / 2 ) + float( minPk )

        editAry3 = []
        for wkv1 in rvs_editAry2 :
            if ( wkv1 > brdrline ) :
                editAry3.append( 1 )
                pass
            else :
                editAry3.append( 0 )
                pass
            pass

        listSlideOkPer = {}
        for slide in range( 5120 ) :
            line_cnt_ok = 0
            for fill_idx in range( len( fill_datas ) ) :
                if ( int( editAry3[ slide + fill_idx ] ) == int( fill_datas [ fill_idx ] ) ) :
                    line_cnt_ok += 1
                    pass
                pass
            listSlideOkPer.update( { int( slide ) : ( float( float( line_cnt_ok ) / 5120 ) ) } )
            pass
        sortListSlideOkPer = sorted( listSlideOkPer.items(),  key=lambda x:x[1], reverse=True )

        ### debug out ###
        wkOutStr = "" 
        for wkdic in sortListSlideOkPer[0:5] :
            match_per = float( wkdic[1] ) * 100
            rslt_idx  = int( wkdic[0] )
            wkOutStr  = wkOutStr + "slide:" + str( str( rslt_idx ).ljust(4) ) +"="+ str( '{:.02f}'.format(match_per) ) + "%, " 
            pass
        #print( ">>> line:" + str( str( int( loopCnt ) + 5 ).rjust(4) ) + " -> " + wkOutStr )
        ### debug out ##

        weight = 10
        for dic in sortListSlideOkPer[0:weight] :
            list_5120_wigth[ int( dic[0] ) ] = float( list_5120_wigth[ int( dic[0] ) ] ) + float( dic[1] )
            pass
        pass

    #------------------------------
    # Judge
    #------------------------------
    weightMaxVal = float( 0 )
    weightMaxIdx = int( 0 )
    for w_cnt in range( len( list_5120_wigth ) ) :
        tgtWeight = float( list_5120_wigth[ int( w_cnt ) ] )
        if ( float( tgtWeight ) > float( weightMaxVal ) ) :
            weightMaxVal = float( tgtWeight )
            weightMaxIdx = int( w_cnt )
            #print( ">>> Idx:" + str( weightMaxIdx ) + " -> Weight:" + str( weightMaxVal ) )
            pass
        pass
    #------------------------------
    if ( int( weightMaxIdx ) > 2500 ) :
        weightMaxIdx = int( weightMaxIdx ) - 5120
        pass
    return weightMaxIdx

#----------------------------------------------------
# checkSlideFFTPeakBunch( adc_path, fill_datas ) -> return : peak bunch No.
#----------------------------------------------------
def checkSlideFFTPeakBunch( adc_path, fill_datas ) :
    adc_name = os.path.basename( adc_path )
    tgtRing  = adc_name[1:2].lower() # [h]or[l]
    tgtType  = adc_name[2:3].upper() # [B]or[V]or[H]or[L]

    area_s = 35
    area_e = 48
    if ( tgtType == "L" ) :
        area_s = 3
        area_e = 8
        pass

    #--------------------
    # read ADC file
    #--------------------
    rfp = open( adc_path, 'rb' )
    adcs2048 = []
    adcs4096 = []
    for loopCnt in range( 2048 ) :
        cntBunch = 0
        databunch = rfp.read( 5120 )
        if ( databunch ) :
            line = []
            ary = bytearray( databunch )
            for wks in ary :
                cntBunch = cntBunch + 1
                if ( cntBunch < 5120 ) :
                    line.append( int( str( wks ) ) )
                    pass
                pass
            adcs2048.append( list( line ) )
            pass
        pass
    adcs4096.extend( adcs2048 )
    adcs4096.extend( adcs2048 )
    #--------------------
    # swap
    #--------------------
    rdata = []
    icntrow = 0
    for line in adcs4096 :
        rdata.append([])
        for val in line :
            rdata[ icntrow ].append( val )
            pass
        icntrow = icntrow + 1
        pass
    cdata = []
    for cntclm in range( len( rdata[ 0 ] ) ) :
        cdata.append( [] )
        for cntrow in range( len( rdata ) ) :
            cdata[ cntclm ].append( rdata[ cntrow ][ cntclm ] )
            pass
        pass
    swaplist = []
    for cntrow in range( len( cdata ) ) :
        swaplist.append( list( cdata[ cntrow ] ) )
        pass
    #--------------------
    # FFT
    #--------------------
    #cntLine = 0 # debug
    freqBase = float( 99.4 )
    listMaxX = []
    listMaxY = []
    for valsline in swaplist : # 5120=len( swaplist ), 4096=len( valsline )
        xbufbase = ( len( valsline ) )
        fftvals = numpy.fft.fft( valsline )      # FFT
        fftabs  = numpy.abs( fftvals )           # ABS
        fftamps = fftabs / ( ( xbufbase ) / 2 )  # Amp
        y1org = fftamps
        x1org = numpy.fft.fftfreq( len( y1org ), d=(1/(freqBase)) )
        items_org = dict( zip( x1org, y1org ) )
        wk_sort_x1org = copy.copy( x1org )
        wk_sort_x1org.sort()
        sort_x1org = []
        sort_y1org = []
        for key in wk_sort_x1org :
            if ( items_org[ key ] > 0 ) :
                sort_x1org.append( key )
                sort_y1org.append( items_org[ key ] )
                pass
            pass

        #------------------------------
        # Check Peak(PilotBunch)
        #------------------------------
        valmaxY = float( 0 )
        valmaxX = float( 0 )
        for hzidx in range( len( sort_x1org ) ) :
            if ( ( float( sort_x1org[ hzidx ] ) > float( area_s ) ) and ( float( sort_x1org[ hzidx ] ) < float( area_e ) ) ) :
                if ( float( sort_y1org[ hzidx ] ) > valmaxY ) :
                    valmaxX = float( sort_x1org[ hzidx ] )
                    valmaxY = float( sort_y1org[ hzidx ] )
                    pass
                pass
            pass
        #print( ">>> " + str( str( int( cntLine ) ).rjust(4) ) + " X=" + str( '{:.04f}'.format( valmaxX ) ) + "[kHz], Y=" + str( valmaxY ) )
        #cntLine += 1
        listMaxX.append( valmaxX )
        listMaxY.append( valmaxY )
        pass

    #------------------------------
    # Judge
    #------------------------------
    #peakBunchNo = numpy.argmax( listMaxY )
    #print( ">>> " + str( str( int( peakBunchNo ) ).rjust(4) ) + " X=" + str( '{:.04f}'.format( listMaxX[ peakBunchNo ] ) ) + "[kHz], Y=" + str( listMaxY[ peakBunchNo ] ) )
    #return peakBunchNo

    dicMaxX = {}
    dicMaxY = {}
    for idx in range( len( listMaxX ) ) :
        dicMaxX.update( { int( idx ) : float( listMaxX[ idx ] ) } )
        pass
    for idx in range( len( listMaxY ) ) :
        dicMaxY.update( { int( idx ) : float( listMaxY[ idx ] ) } )
        pass
    sortDicMaxY = sorted( dicMaxY.items(), key=lambda x:x[1], reverse=True )
    for wkdicY in sortDicMaxY[ 0 : 10 ] :
        wkIdxY = wkdicY[0]
        wkValY = wkdicY[1]
        wkValX = dicMaxX[ wkIdxY ]
        #print( ">>> FFT Peak Bunch:" + str( str( int( wkIdxY ) ).rjust(4) ) + " ( X=" + str( '{:.04f}'.format( wkValX ) ) + "[kHz], Y=" + str( wkValY ) + " )")
        pass
    #------------------------------
    peak_bunch_no = sortDicMaxY[ 0 ][ 0 ]
    return peak_bunch_no

#--------------------------
# main
#--------------------------
pathSlideDataFile   = './SLIDE_FIRSTBUNCH_SearchSlidePy.list'
#wfp = open( pathSlideDataFile, 'w' )

stdoutOrigin=sys.stdout 
sys.stdout = open(pathSlideDataFile, "w")

for adc_path in getADCsPath( f'{adc_data_path}' ) :
    adc_name = os.path.basename( adc_path )
    tgtRing  = adc_name[1:2].lower() # [h]or[l]
    tgtType  = adc_name[2:3].upper() # [B]or[V]or[H]or[L]
    adc_id   = os.path.splitext( adc_name )[0]

    if ( tgtType == "B" ) :
        #print( "------------------" )
        #print( "> check : " + adc_name )
        fills, pilotBunch, cntBunch = getFillPtnData( adc_path )
        #-------------
        slide = checkSlideFillPtn1PosOneSide( adc_path, fills )
        #print( "> " + adc_name + " slide -> " + str( int( slide ) ) + " (Plot)" )
        #wfp.write( "" + adc_id + "," + str( int( slide ) ) + '\n' )
        print("" + adc_id + "," + str( int( slide ) ))
        pass

    if ( tgtType == "H" ) :
        #print( "------------------" )
        #print( "> check : " + adc_name )
        fills, pilotBunch, cntBunch = getFillPtnData( adc_path )
        #-------------
        slide = checkSlideFillPtn1PosBothSide( adc_path, fills )
        #print( "> " + adc_name + " slide -> " + str( int( slide ) ) + " (Plot)" )
        #wfp.write( "# " + adc_id + "," + str( int( slide ) ) + '\n' )
        print("# " + adc_id + "," + str( int( slide ) ))
        #-------------
        pkBunch = checkSlideFFTPeakBunch( adc_path, fills )
        slide = int( pkBunch ) - int( pilotBunch )
        #print( "> " + adc_name + " slide -> " + str( int( slide ) ) + " (FFT)" )
        #wfp.write( "" + adc_id + "," + str( int( slide ) ) + '\n' )
        print("" + adc_id + "," + str( int( slide ) ))
        pass

    if ( tgtType == "V" ) :
        #print( "------------------" )
        #print( "> check : " + adc_name )
        fills, pilotBunch, cntBunch = getFillPtnData( adc_path )
        #-------------
        slide = checkSlideFillPtn1PosBothSide( adc_path, fills )
        #print( "> " + adc_name + " slide -> " + str( int( slide ) ) + " (Plot)" )
        #wfp.write( "# " + adc_id + "," + str( int( slide ) ) + '\n' )
        print("# " + adc_id + "," + str( int( slide ) ))
        #-------------
        pkBunch = checkSlideFFTPeakBunch( adc_path, fills )
        slide = int( pkBunch ) - int( pilotBunch )
        #print( "> " + adc_name + " slide -> " + str( int( slide ) ) + " (FFT)" )
        #wfp.write( "" + adc_id + "," + str( int( slide ) ) + '\n' )
        print("" + adc_id + "," + str( int( slide ) ))
        pass

    if ( tgtType == "L" ) :
        #print( "------------------" )
        #print( "> check : " + adc_name )
        fills, pilotBunch, cntBunch = getFillPtnData( adc_path )
        #-------------
        slide = checkSlideFillPtn1PosBothSide( adc_path, fills )
        #print( "> " + adc_name + " slide -> " + str( int( slide ) ) + " (Plot)" )
        #wfp.write( "" + adc_id + "," + str( int( slide ) ) + '\n' )
        print("" + adc_id + "," + str( int( slide ) ))
        pass
    pass
#wfp.close()
sys.stdout.close()
sys.stdout=stdoutOrigin