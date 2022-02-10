#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     09/02/2022
# Copyright:   (c) Adolfo.Diaz 2022
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ================================================================================================================
## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print(msg)

        try:
            f = open(textFilePath,'a+')
            f.write(msg + " \n")
            f.close
            del f
        except:
            pass

        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError("\n" + msg)

    except:
        pass

## ===================================================================================
def errorMsg():
    try:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]

        if theMsg.find("exit") > -1:
            AddMsgAndPrint("\n\n")
            pass
        else:
            AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

## ================================================================================================================
def tic():
    """ Returns the current time """

    return time.time()

## ================================================================================================================
def toc(_start_time):
    """ Returns the total time by subtracting the start time - finish time"""

    try:

        t_sec = round(time.time() - _start_time)
        (t_min, t_sec) = divmod(t_sec,60)
        (t_hour,t_min) = divmod(t_min,60)

        if t_hour:
            return ('{} hour(s): {} minute(s): {} second(s)'.format(int(t_hour),int(t_min),int(t_sec)))
        elif t_min:
            return ('{} minute(s): {} second(s)'.format(int(t_min),int(t_sec)))
        else:
            return ('{} second(s)'.format(int(t_sec)))

    except:
        errorMsg()

## ================================================================================================================
def splitThousands(someNumber):
    """ will determine where to put a thousands seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

def getNASISbreakdownCounts():
    """ This function will send the bounding coordinates to the 'Web Export Pedon Box' NASIS report
        and return a list of pedons within the bounding coordinates.  Pedons include regular
        NASIS pedons and LAB pedons.  Each record in the report will contain the following values:

            Row_Number,upedonid,peiid,pedlabsampnum,Longstddecimaldegrees,latstddecimaldegrees,Undisclosed Pedon
            24|S1994MN161001|102861|94P0697|-93.5380936|44.0612717|'Y'

        A dictionary will be returned containing something similar:
        {'102857': ('S1954MN161113A', '40A1694', '-93.6499481', '43.8647194','Y'),
        '102858': ('S1954MN161113B', '40A1695', '-93.6455002', '43.8899956','N')}
        theURL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&Lat1=44.070820&Lat2=44.596950&Long1=-91.166274&Long2=-90.311911'

        returns a pedonDictionary"""

        #-------------------------- KSSL Pedon and Undisclosed Metrics ----------------------------------
        #------------------------------------------------------------------------------------------------
        # This section is only to determine how many Lab Pedons and how many undiscolsed pedons there are
        # nationwide.  It is recommended that the WEB_EXPORT_PEDON_BOX_COUNT NASIS report in the KSSL folder
        # be duplicated and modified such that ONLY 2 fields are returned (pedlabsampnum and location) which
        # represent the pedon lab sample number and a boolean indicating if the pedon is undisclosed.
        #
        # Iterate through the getWebExportPedon function 4 times to request all pedons from NASIS and get a
        # Lab pedon and undisclosed count stricly for metrics.

    def runWebMetricReport(coordinates):
        try:
            #AddMsgAndPrint(".\nGetting a NASIS pedon count using the above bounding coordinates")
            URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_NASIS_Pedons_WFS_Metrics_AD' + coordinates

            """ --------------------------------------  Try connecting to NASIS to read the report ------------------------"""
            try:
                theReport = urllib.request.urlopen(URL).readlines()
            except:
                try:
                    AddMsgAndPrint(".\t2nd attempt at requesting data")
                    theReport = urllib.request.urlopen(URL).readlines()

                except:
                    try:
                        AddMsgAndPrint(".\t3rd attempt at requesting data")
                        theReport = urllib.request.urlopen(URL).readlines()

                    except URLError as e:
                        AddMsgAndPrint('URL Error' + str(e),2)
                        return False

                    except HTTPError as e:
                        AddMsgAndPrint('HTTP Error' + str(e),2)
                        return False

                    except socket.timeout as e:
                        AddMsgAndPrint(".\n.\t" + URL)
                        AddMsgAndPrint(".\tServer Timeout Error", 2)
                        return False

                    except socket.error as e:
                        AddMsgAndPrint(".\n.\t" + URL)
                        AddMsgAndPrint(".\tNASIS Reports Website connection failure", 2)
                        return False

            """ --------------------------------------  Read the NASIS report ------------------------------------"""
            undisclosedLab = 0
            disclosedLab = 0
            undisclosedNASIS = 0
            disclosedNASIS = 0
            test = 0
            bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

            peiidList = list()

            # iterate through the report until a valid record is found
            for theValue in theReport:

                # convert from bytes to string and remove white spaces
                theValue = theValue.decode('utf-8').strip()

                # Iterating through the lines in the report
                if bValidRecord:
                    if theValue == "STOP":  # written as part of the report; end of lines
                        break

                    # Found a valid project record i.e. 91P0481|N (only 2 values)
                    else:
                        theRec = theValue.split("|")

                        if len(theRec) != 3:
                            AddMsgAndPrint(".\tNASIS Report: WEB_NASIS_Pedons_WFS_Metrics_AD is not returning the correct amount of values per record",2)
                            return False

                        peiidList.append(theRec[0])
                        continue

                        # Go through the different combinations of metrics
                        # Record is an undisclosed lab pedon
                        if theRec[0] != 'Null' and theRec[1] == 'Y':
                            undisclosedLab+= 1

                        # Record is a disclosed lab pedon
                        elif theRec[0] != 'Null' and theRec[1] == 'N':
                            disclosedLab+=1

                        # Record is an undisclosed NASIS pedon
                        elif theRec[0] == 'Null' and theRec[1] == 'Y':
                            undisclosedNASIS+= 1

                        # Record is an disclosed NASIS pedon
                        elif theRec[0] == 'Null' and theRec[1] == 'N':
                            disclosedNASIS+=1

                        else:
                            AddMsgAndPrint(".\tUnaccounted for combination: " + str(theValue),1)
                        test += 1

                else:
                    if theValue.startswith('<div id="ReportData">START'):
                        bValidRecord = True

##            bCountFailed = False
##            if undisclosedLab + disclosedLab + undisclosedNASIS + disclosedNASIS != test:
##                print(f"{coordinates} did not Match:")
##                print("\t" + str(undisclosedLab))
##                print("\t" + str(disclosedLab))
##                print("\t" + str(undisclosedNASIS))
##                print("\t" + str(disclosedNASIS))
##                print("\t" + str(test))
##                bCountFailed = True
##
##            if undisclosedLab == 0 and disclosedLab == 0 and undisclosedNASIS == 0 and disclosedNASIS == 0:
##                print(f"    {coordinates} Returned empty:")
##
##            print(f"    {undisclosedLab},{disclosedLab},{undisclosedNASIS},{disclosedNASIS},{test},{bCountFailed}")
##
##            return [undisclosedLab,disclosedLab,undisclosedNASIS,disclosedNASIS,test,bCountFailed]
            return peiidList

        except:
            errorMsg()
            return [0,0,0]

    try:
        Starttest = tic()

        latNorth = 49
        latSouth = 24
        longWest = -125
        longEast = -65
        degreeSize = 5

        # list of coordinates for the 5x5 degree blocks covering the US
        USdegreeblocks = []

        # Create list of coordinates for 5x5 degree blocks for US
        for lat in range(latSouth,latNorth,degreeSize):
            for long in range(longWest,longEast,degreeSize):
                USdegreeblocks.append([lat,lat+degreeSize,long,long+degreeSize])

        # List of coordinates for 4 boxes around the US for the NW hemisphere
        #NW_hemisphere = [[0,90,-179.5,longWest],[0,latSouth,longWest,-0.1],[latSouth,90,longEast,-0.1],[latNorth,90,longWest,longEast]]
        NW_hemisphere = [[0,90,-180,longWest],[0,latSouth,longWest,0],[latSouth,90,longEast,0],[latNorth,90,longWest,longEast]]

        # Lat1, Lat2, Long1, Long2 -- S,N,W,E -- NE, SW, ,SE hemishpere
        # This represents the master list of coordinates to send to NASIS report
        #worldQuadrant = [[0.0,90.0,0.5,179.5],[-90.0,0.0,-179.5,-0.5],[-90.0,0.0,0.5,179.5]]
        worldQuadrant = [[0,90,0,180],[-90,0,-180,0],[-90,0,0,180]]

        # Add NW Hemisphere box coordinates to worldQuadrant list
        for coordLst in NW_hemisphere:
            worldQuadrant.append(coordLst)

        # Add US degree block coordinates to worldQuadrant list
        for coordLst in USdegreeblocks:
            worldQuadrant.append(coordLst)

##        i=0
##        for coord in worldQuadrant:
##            i+=1
##            Left = coord[2]
##            Right = coord[3]
##            Top = coord[1]
##            Bottom = coord[0]
##            outName = f"{Bottom}_{Top}_{Left}_{Right}"
##            outFC = f"N:\\flex\\NCSS_Pedons\\NASIS_Pedons\\Web_Feature_Service\\degreeBlocks\\quad_{outName}.shp"
##            origin_coord = f"{Left} {Bottom}"
##            y_axis_coord = f"{Left} {Bottom + 10}"
##            cell_width = abs(Left - Right)
##            cell_height = abs(Top - Bottom)
##            rows = 0
##            columns = 0
##            corner_coord = f"{Right} {Top}"
##            template = f"{Left} {Bottom} {Right} {Top}"
##            arcpy.CreateFishnet_management(outFC,origin_coord,y_axis_coord,cell_width,cell_height,rows,columns,corner_coord,'NO_LABELS',template,"POLYGON")

        undisclosedLabRecs = 0
        disclosedLabRecs = 0
        undisclosedNASISrecs = 0
        disclosedNASISrecs = 0
        TOTAL = 0

        peIIDlist = list()
        outFCs = list()

        # Gather global metrics w/out using US degree blocks.
        for coordLst in worldQuadrant:
            coordStr = f"&Lat1={coordLst[0]}&Lat2={coordLst[1]}&Long1={coordLst[2]}&Long2={coordLst[3]}"

            Left = coordLst[2]
            Right = coordLst[3]
            Top = coordLst[1]
            Bottom = coordLst[0]
            outName = f"{Bottom}_{Top}_{Left}_{Right}"
            outFC = f"N:\\flex\\NCSS_Pedons\\NASIS_Pedons\\Web_Feature_Service\\degreeBlocks\\quad_{outName}.shp"
            origin_coord = f"{Left} {Bottom}"
            y_axis_coord = f"{Left} {Bottom + 10}"
            cell_width = abs(Left - Right)
            cell_height = abs(Top - Bottom)
            rows = 0
            columns = 0
            corner_coord = f"{Right} {Top}"
            template = f"{Left} {Bottom} {Right} {Top}"
            arcpy.CreateFishnet_management(outFC,origin_coord,y_axis_coord,cell_width,cell_height,rows,columns,corner_coord,'NO_LABELS',template,"POLYGON")

            arcpy.AddField_management(outFC,"coord_str","TEXT","#","#",90,"Coordinate String")
            arcpy.AddField_management(outFC,"block_name","TEXT","#","#",50,"block name")
            arcpy.AddField_management(outFC,"num_pedons","LONG","#","#","#","Number of Pedons")
            arcpy.AddField_management(outFC,"duplic_ids","LONG","#","#","#","Number of duplicates")

            print(f"Running report on {coordStr}")
            pedonCounts = runWebMetricReport(coordStr)
            duplicateIDS = len(pedonCounts) - len(list(set(pedonCounts)))

            arcpy.CalculateField_management(outFC,"coord_str",r'"' + coordStr + r'"',"PYTHON3")
            arcpy.CalculateField_management(outFC,"block_name",r'"' + outName + r'"',"PYTHON3")
            arcpy.CalculateField_management(outFC,"num_pedons",len(pedonCounts),"PYTHON3")
            arcpy.CalculateField_management(outFC,"duplic_ids",duplicateIDS,"PYTHON3")
            outFCs.append(outFC)

            for id in pedonCounts:
                peIIDlist.append(id)

##            undisclosedLabRecs+=pedonCounts[0]
##            disclosedLabRecs+=pedonCounts[1]
##            undisclosedNASISrecs+=pedonCounts[2]
##            disclosedNASISrecs+=pedonCounts[3]
##
##            TOTAL+=pedonCounts[4]
##            if pedonCounts[5]:
##                exit()

        print("Merging Block_grids")
        arcpy.Merge_management(outFCs,f"N:\\flex\\NCSS_Pedons\\NASIS_Pedons\\Web_Feature_Service\\degreeBlocks\\All_Blocks.shp")

        print(toc(Starttest))
        #return [undisclosedLabRecs,disclosedLabRecs,undisclosedNASISrecs,disclosedNASISrecs,TOTAL]
        return peIIDlist

    except:
        errorMsg()
        return False

## ================================================================================================================
def getDictionaryOfAllPedonIDs():
    # Description
    # This function will send a URL request to the 'Web Pedon PEIID List All of NASIS' NASIS
    # report to obtain a list of ALL pedons in NASIS.  Pedons include regular
    # NASIS pedons and LAB pedons.  Each record in the report will contain the following values:
    # START 1204126, 1204127, 1204128 STOP"""

    try:
        AddMsgAndPrint("\nRequesting a list of ALL pedonIDs from NASIS")
        arcpy.SetProgressorLabel("Requesting a list of ALL pedonIDs from NASIS")

        #URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT' + coordinates
        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_PEDON_PEIID_LIST_ALL_OF_NASIS'

        # Open a network object using the URL with the search string already concatenated
        startTime = tic()
        #AddMsgAndPrint("\tNetwork Request Time: " + toc(startTime))

        """ --------------------------------------  Try connecting to NASIS to read the report ------------------------"""
        try:
            theReport = urllib.request.urlopen(URL).readlines()
        except:
            try:
                AddMsgAndPrint("\t2nd attempt at requesting data")
                theReport = urllib.request.urlopen(URL).readlines()

            except:
                try:
                    AddMsgAndPrint("\t3rd attempt at requesting data")
                    theReport = urllib.request.urlopen(URL).readlines()

                except URLError as e:
                    AddMsgAndPrint('URL Error' + str(e),2)
                    return False

                except HTTPError as e:
                    AddMsgAndPrint('HTTP Error' + str(e),2)
                    return False

                except socket.timeout as e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tServer Timeout Error", 2)
                    return False

                except socket.error as e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                    return False

        """ --------------------------------------  Read the NASIS report ------------------------------------"""
        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

        arcpy.SetProgressor("step", "Reading NASIS Report: 'WEB_PEDON_PEIID_LIST_ALL_OF_NASIS'", 0, len(theReport), 1)

        # iterate through the report until a valid record is found
        for theValue in theReport:

            # convert from bytes to string and remove white spaces
            theValue = theValue.decode('utf-8').strip()

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue == "STOP":  # written as part of the report; end of lines
                    break

                # Found a valid record
                if not theValue == None:

                    # All of the peodonIDs will be contained in 1 line
                    pedonDict = {val.strip():None for val in theValue.split(",")}

                else:
                    continue

            else:
                if theValue.startswith('<div id="ReportData">START'):
                    bValidRecord = True

            arcpy.SetProgressorPosition()

        #Resets the progressor back to its initial state
        arcpy.ResetProgressor()

        if len(pedonDict) == 0:
            AddMsgAndPrint("\tThere were no pedons returned from this report",2)
            return False

        else:
            return pedonDict

    except:
        errorMsg()
        return False


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy, socket, time, urllib, multiprocessing, requests
from arcpy import env
from sys import getsizeof, stderr
from itertools import chain
from collections import deque

from urllib.error import HTTPError, URLError
from urllib.request import Request

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

if __name__ == '__main__':

    try:

        inputFeatures = r'E:\Pedons\Temp\smallArea.shp'
        DBname = 'smallTest'
        outputFolder = r'E:\Pedons\Temp'
        sqliteFormat = False
        allPedons = True

        boxCountIDs = getNASISbreakdownCounts()
        boxCountIdsSet = list(set(boxCountIDs))

        boxCountIDsDuplicateNum = len(boxCountIDs) - len(boxCountIdsSet)

        print(f"WEB_EXPORT_PEDON_BOX_COUNT Report returned {len(boxCountIDs)} pedons")
        print(f"WEB_EXPORT_PEDON_BOX_COUNT Report Number of Duplicate IDs: {boxCountIDsDuplicateNum}")

        # User has chosen to donwload all pedons
        if allPedons:
            pedonDict = getDictionaryOfAllPedonIDs()
            totalPedons = len(pedonDict)

        allNASISidList = list(pedonDict.keys())
        allNASISidSet = list(set(allNASISidList))
        allNASISidDuplicateNum = len(allNASISidList) - len(allNASISidSet)

        print(f"\WEB_PEDON_PEIID_LIST_ALL_OF_NASIS Report returned {totalPedons} pedons")
        print(f"\WEB_PEDON_PEIID_LIST_ALL_OF_NASIS Report Number of Duplicate IDS: {allNASISidDuplicateNum}")

        onlyInBoxReport = list()
        onlyInPEIIDreport = list()

        for id in boxCountIDs:
            if not id in allNASISidList:
                onlyInBoxReport.append(id)

        for id in allNASISidList:
            if not id in boxCountIDs:
                onlyInPEIIDreport.append(id)

        print(f"There are {len(onlyInBoxReport)} IDs that only occur in WEB_EXPORT_PEDON_BOX_COUNT Report")
        print(f"There are {len(onlyInPEIIDreport)} IDs that only occur in WEB_PEDON_PEIID_LIST_ALL_OF_NASIS Report Report")


    except:
        errorMsg()
