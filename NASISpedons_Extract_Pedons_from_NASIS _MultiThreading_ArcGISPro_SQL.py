#-------------------------------------------------------------------------------
# Name:  NASISpedons_Extract_Pedons_from_NASIS_Multithreading_ArcGISPro_SQL.py
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Author: Jason.Nemecek
# e-mail: jason.nemecek@wi.usda.gov
# phone: 608.662.4422 ext. 190
#
# Created:     7/04/2016
# Last Modified: 7/12/2021
# Copyright:   (c) Adolfo.Diaz 2016

# https://alexwlchan.net/2019/10/adventures-with-concurrent-futures/

# ==========================================================================================
# Updated  4/29/2021 - Adolfo Diaz
# Major rewrite to introduce parallel tasking using concurrent.futures python
# module.  Using this module I was able t

# ==========================================================================================
# Updated  5/26/2021 - Adolfo Diaz
# - Changed the format in which failed pedon ids are written to the error log
#   file.  Before the pedon IDs were logged as a continous list seperated by commas.
#   Now, the pedon IDs are logged with a carriage return
# - Added capability to have the Pedons automatically added to the ArcGIS Pro Session
#   if the pedon fc has valid pedons.

# ==========================================================================================
# Updated  6/16/2021 - Adolfo Diaz
# - Added functionality to output an SQLite Database Format

# ==========================================================================================
# Updated  7/12/2021 - Adolfo Diaz
# - Added field within pedon layer to store pedon description hyperlink report

# ==========================================================================================
# Updated  2/8/2022 - Adolfo Diaz
# - Addressed a bug associated with unprojected feature in the getBoundingCoordinates function

# ==========================================================================================
# Updated  3/14/2022 - Adolfo Diaz
""" Address the following changes due to NASIS database model changes
"""
#-------------------------------------------------------------------------------


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
            AddMsgAndPrint(".\n\n")
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

## ================================================================================================================
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
##            outFC = f"N:\\flex\\NCSS_Pedons\\NASIS_Pedons\\Web_Feature_Service\\degreeBlocks\\quad_{Left}_{Right}_{Top}_{Bottom}.shp"
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

        # Gather global metrics w/out using US degree blocks.
        for coordLst in worldQuadrant:
            coordStr = f"&Lat1={coordLst[0]}&Lat2={coordLst[1]}&Long1={coordLst[2]}&Long2={coordLst[3]}"
            print(f"Running report on {coordStr}")
            pedonCounts = runWebMetricReport(coordStr)

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

##        # Create an Executor to manage all tasks.  Using the with statement creates a context
##        # manager, which ensures any stray threads or processes get cleaned up properly when done.
##        with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
##
##            # use a set comprehension to start all tasks.  This creates a future object
##            future_to_url = {executor.submit(openURL, url): url for url in URLlist}
##
##            # yield future objects as they are done.
##            for future in as_completed(future_to_url):
##                #futureResults.append(future.result())
##                organizeFutureInstanceIntoPedonDict(future.result())
##                arcpy.SetProgressorPosition()

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
        AddMsgAndPrint(".\nRequesting a list of ALL pedonIDs from NASIS")
        arcpy.SetProgressorLabel("Requesting a list of ALL pedonIDs from NASIS")

        #URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT' + coordinates
        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_PEDON_PEIID_LIST_ALL_OF_NASIS'

        # Open a network object using the URL with the search string already concatenated
        startTime = tic()
        #AddMsgAndPrint(".\tNetwork Request Time: " + toc(startTime))

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
                    AddMsgAndPrint(".\n\t" + URL)
                    AddMsgAndPrint(".\tServer Timeout Error", 2)
                    return False

                except socket.error as e:
                    AddMsgAndPrint(".\n\t" + URL)
                    AddMsgAndPrint(".\tNASIS Reports Website connection failure", 2)
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
            AddMsgAndPrint(".\tThere were no pedons returned from this report",2)
            return False

        else:
            return pedonDict

    except:
        errorMsg()
        return False


## ================================================================================================================
def getBoundingCoordinates(feature):
    """ This function will return WGS coordinates in Lat-Long format that will be passed over to
        the 'WEB_EXPORT_PEDON_BOX_COUNT' report.  The coordinates are generated by creating
        a minimum bounding box around the input features.  The box is then converted to vertices
        and the SW Ycoord, NE Ycoord, SW Xcoord and NE Ycoord are return in that order.
        Geo-Processing Environments are set to WGS84 in order to return coords in Lat/Long."""

    try:

        """ Determine if features are a subset of selected polygons OR the entire dataset
            is being used.  This was necessary b/c the output Coordinate System
            environmental variable was not being honored if a selected set is being used.
            Export selected set to a temporary feature class otherwise continue"""

        arcpy.SetProgressorLabel("Calculating bounding coordinates of input features")

        featurePath = arcpy.Describe(feature).catalogPath

        totalPolys = int(arcpy.GetCount_management(featurePath).getOutput(0))
        selectedPolys = int(arcpy.GetCount_management(feature).getOutput(0))
        bExport = False

        if selectedPolys < totalPolys:
            envelopeFeature = arcpy.CreateScratchName("envelopeFeature",data_type="FeatureClass", workspace="in_memory")
            arcpy.CopyFeatures_management(feature,envelopeFeature)
            AddMsgAndPrint(".\nCalculating bounding coordinates for " + splitThousands(selectedPolys) + " feature(s)")
            bExport = True

        else:
            envelopeFeature = feature
            AddMsgAndPrint(".\nCalculating bounding coordinates of input features")

        """ Set Projection and Geographic Transformation environments in order
            to post process everything in WGS84.  This will force all coordinates
            to be in Lat/Long"""

        inputSR = arcpy.Describe(feature).spatialReference                # Get Spatial Reference of input features

        if inputSR.name == 'Unknown':
            AddMsgAndPrint(".\n\tInput layer needs a spatial reference defined to determine bounding envelope",2)
            return False, False, False, False

        # Get Datum name of input features
        inputDatum = inputSR.GCS.datumName

        if inputDatum == "D_North_American_1983":
            arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983"
        elif inputDatum == "D_North_American_1927":
            arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1927"
        elif inputDatum == "D_NAD_1983_2011":
            arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983_2011"
        elif inputDatum == "D_WGS_1984":
            arcpy.env.geographicTransformations = ""
        else:
            AddMsgAndPrint(".\n\tGeo Transformation of Datum could not be set",2)
            AddMsgAndPrint(".\tTry Projecting input layer to WGS 1984 Coordinate System",2)
            return False, False, False, False

        # Factory code for WGS84 Coordinate System
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

        """ ------------ Create Minimum Bounding Envelope of features ------------"""
        envelope = arcpy.CreateScratchName("envelope",data_type="FeatureClass",workspace="in_memory")
        envelopePts = arcpy.CreateScratchName("envelopePts",data_type="FeatureClass",workspace="in_memory")

        # create minimum bounding geometry enclosing all features
        arcpy.MinimumBoundingGeometry_management(envelopeFeature,envelope,"ENVELOPE","ALL","#","MBG_FIELDS")

        if int(arcpy.GetCount_management(envelope).getOutput(0)) < 1:
            AddMsgAndPrint(".\n\tFailed to create minimum bounding area. \n\tArea of interest is potentially too small",2)
            return False

        arcpy.FeatureVerticesToPoints_management(envelope, envelopePts, "ALL")

        """ ------------ Get X and Y coordinates from envelope ------------"""
        coordList = []
        with arcpy.da.SearchCursor(envelopePts,['SHAPE@XY']) as cursor:
            for row in cursor:
                if abs(row[0][0]) > 0 and abs(row[0][1]) > 0:

                    # Don't add duplicate coords; Last coord will also be the starting coord
                    if not row[0] in coordList:
                        coordList.append(row[0])

        # Reset output Coord Sys Environment
        arcpy.env.outputCoordinateSystem = ""

        # Delete temp spatial files
        for tempFile in [envelope,envelopePts]:
            if arcpy.Exists(tempFile):
                arcpy.Delete_management(tempFile)

        if bExport:
            arcpy.Delete_management(envelopeFeature)

        if len(coordList) == 4:
            AddMsgAndPrint(".\tBounding Box Coordinates:")
            AddMsgAndPrint(".\t\tSouth Latitude: " + str(coordList[0][1]))
            AddMsgAndPrint(".\t\tNorth Latitude: " + str(coordList[2][1]))
            AddMsgAndPrint(".\t\tEast Longitude: " + str(coordList[0][0]))
            AddMsgAndPrint(".\t\tWest Longitude: " + str(coordList[2][0]))
            return coordList[0][1],coordList[2][1],coordList[0][0],coordList[2][0]

        else:
            AddMsgAndPrint(".\.tCould not get Latitude-Longitude coordinates from bounding area",2)
            return False

    except:

        for tempFile in [envelope,envelopePts]:
            if arcpy.Exists(tempFile):
                arcpy.Delete_management(tempFile)

        errorMsg()
        return False

## ================================================================================================================
def getNASISpedonCountbyBox(coordinates):
    """ This function will send the bounding coordinates to the 'Web Pedon Number SUM' NASIS report
        and return the number of pedons within the bounding coordinates.  Pedons include regular
        NASIS pedons and LAB pedons. Example of URL sent to the NASIS report would be:

        https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_ANALYSIS_PC_PEDON_NUMBER_SUM&Lat1=43.6425577303&Lat2=43.9828939095&Long1=-89.5997555233&Long2=-89.167551308

        # peiid: siteID,Labnum,X,Y
        # {'122647': ('84IA0130011', '85P0558', '-92.3241653', '42.3116684'), '883407': ('2014IA013003', None, '-92.1096600', '42.5332000')}
        """

    try:
        AddMsgAndPrint(".\nDetermining if there are any pedons within the bounding coordinates")
        arcpy.SetProgressorLabel("Determining if there are any pedons within the bounding coordinates")

        # Open a network object using the URL with the search string already concatenated
        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_ANALYSIS_PC_PEDON_NUMBER_SUM' + coordinates

        """ --------------------------------------  Try connecting to NASIS to read the report ------------------------"""
        try:
            theReport = urllib.request.urlopen(URL).readlines()
        except:
            try:
                AddMsgAndPrint(".\t2nd attempt at requesting data")
                theReport = urllib.request.urlopen(URL).read().decode('utf-8')
            except:
                try:
                    AddMsgAndPrint(".\t3rd attempt at requesting data")
                    theReport = urllib.request.urlopen(URL).read().decode('utf-8')

                except URLError as e:
                    AddMsgAndPrint('URL Error' + str(e),2)
                    return False

                except HTTPError as e:
                    AddMsgAndPrint('HTTP Error' + str(e),2)
                    return False

                except socket.timeout as e:
                    AddMsgAndPrint(".\n\t" + URL)
                    AddMsgAndPrint(".\tServer Timeout Error", 2)
                    return False

                except socket.error as e:
                    AddMsgAndPrint(".\n\t" + URL)
                    AddMsgAndPrint(".\tNASIS Reports Website connection failure (Socket Error)", 2)
                    return False

                except:
                    errorMsg()
                    return Falsethe

        """ --------------------------------------  Read the NASIS report ---------------------------------"""
        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

        # iterate through the report until a valid record is found
        for theValue in theReport:

            # convert from bytes to string and remove white spaces
            theValue = theValue.decode('utf-8').strip()

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue == "STOP":  # written as part of the report; end of lines
                    break

                else:
                    try:
                        return int(theValue)
                    except:
                        continue

            else:
                if theValue.startswith('<div id="ReportData">START'):
                    bValidRecord = True

    except:
        errorMsg()
        return False

## ================================================================================================================
def getNASISpedonIDsByBox(coordinates):
    """ This function will send the bounding coordinates to the 'Web Export Pedon Box' NASIS report
        and return a list of pedons within the bounding coordinates.  Pedons include regular
        NASIS pedons and LAB pedons.  Each record in the report will contain the following values:

            Row_Number,upedonid,peiid,pedlabsampnum,Longstddecimaldegrees,latstddecimaldegrees,Undisclosed Pedon
            24|S1994MN161001|102861|94P0697|-93.5380936|44.0612717|'Y'

        A dictionary will be returned containing something similar:
        {'102857': ('S1954MN161113A', '40A1694', '-93.6499481', '43.8647194','Y'),
        '102858': ('S1954MN161113B', '40A1695', '-93.6455002', '43.8899956','N')}
        theURL = r'    #getPedonIDURL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&Lat1=44.070820&Lat2=44.596950&Long1=-91.166274&Long2=-90.311911'

        returns a pedonDictionary"""

    try:
        AddMsgAndPrint(".\nRequesting a list of pedonIDs from NASIS using the above bounding coordinates")
        arcpy.SetProgressorLabel("Requesting a list of pedons from NASIS")

        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT' + coordinates

        # Open a network object using the URL with the search string already concatenated
        startTime = tic()
        #AddMsgAndPrint(".\tNetwork Request Time: " + toc(startTime))

        pedonDictionary = dict()

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
                    AddMsgAndPrint(".\n\t" + URL)
                    AddMsgAndPrint(".\tServer Timeout Error", 2)
                    return False

                except socket.error as e:
                    AddMsgAndPrint(".\n\t" + URL)
                    AddMsgAndPrint(".\tNASIS Reports Website connection failure", 2)
                    return False

        """ --------------------------------------  Read the NASIS report ------------------------------------"""
        totalPedonCnt = 0
        labPedonCnt = 0
        undisclosed = 0
        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

        arcpy.SetProgressor("step", "Reading NASIS Report: 'WEB_EXPORT_PEDON_BOX_COUNT'", 0, len(theReport), 1)

        # iterate through the report until a valid record is found
        for theValue in theReport:

            # convert from bytes to string and remove white spaces
            theValue = theValue.decode('utf-8').strip()

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue == "STOP":  # written as part of the report; end of lines
                    break

                # Found a valid project record i.e. -- SDJR - MLRA 103 - Kingston silty clay loam, 1 to 3 percent slopes|400036
                else:
                    theRec = theValue.split("|")

                    if len(theRec) != 7:
                        AddMsgAndPrint(".\tNASIS Report: Web Export Pedon Box is not returning the correct amount of values per record",2)
                        return False

                    # Undisclosed Record; Reject this record
                    if theRec[6] == "Y":
                        undisclosed+=1
                        totalPedonCnt += 1
                        continue

                    rowNumber = theRec[0]
                    userPedonID = theRec[1]
                    pedonID = theRec[2]
                    longDD = theRec[4]
                    latDD = theRec[5]

                    # Lab sample or not
                    if theRec[3] == 'Null' or theRec[3] == '':
                        labSampleNum = None
                    else:
                        labSampleNum = theRec[3]
                        labPedonCnt += 1

                    if not pedonID in pedonDictionary:
                        pedonDictionary[pedonID] = (userPedonID,labSampleNum,longDD,latDD)
                        totalPedonCnt += 1

            else:
                if theValue.startswith('<div id="ReportData">START'):
                    bValidRecord = True

            arcpy.SetProgressorPosition()

        #Resets the progressor back to its initial state
        arcpy.ResetProgressor()

        if len(pedonDictionary) == 0:
            AddMsgAndPrint(".\tThere were no pedons found in this area; Try using a larger extent",1)
            return False

        else:
            #AddMsgAndPrint(".\tThere are a total of " + splitThousands(totalPedonCnt) + " pedons found in this area:")
            AddMsgAndPrint(".\tThere are " + splitThousands(totalPedonCnt) + " within this layer:")
            AddMsgAndPrint(".\t\tLAB Pedons: " + splitThousands(labPedonCnt))
            AddMsgAndPrint(".\t\tUndisclosed: " + splitThousands(undisclosed))
            AddMsgAndPrint(".\t\tNASIS Pedons: " + splitThousands((totalPedonCnt - labPedonCnt) - undisclosed))

            return pedonDictionary

    except:
        errorMsg()
        return False

## ================================================================================================================
def filterPedonsByFeature(feature):
    # Description:
    # This function will temporarily plot out the pedons in order to determine which pedons fall completely
    # within the user's AOI.  Once determined, the extra pedons will be removed from the pedonDict so that
    # extra pedons are not downloaded.

    # Parameters
    # feature -  input area of interest that will be used to intersect agains temporarily plotted NASIS points.
    #            This will only be used as a reference.
    # The pedonDict will be altered but not necessary to be passed in.

    # Returns
    # This function returns an integer that reflects the number of pedons that are completely within the feature
    # AOI.  False will be returned if an error occurs within this function OR if there are NO pedons within the
    # feature AOI.
    # Although the function will update the pedonDict to reflect only the peodonIDs that are within the feature AOI.
    # it is not returned since it is directly updated from main.

    try:
        AddMsgAndPrint(".\nSelecting pedons that intersect with " + arcpy.Describe(feature).Name + " Layer")
        arcpy.SetProgressorLabel("Selecting pedons that intersect with " + arcpy.Describe(feature).Name + " Layer")

        # Set everything to WGS84
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

        # Make a copy of the user-input features - this is just in case there is a selected set
        aoiFeature = arcpy.CreateScratchName("aoiFeature",data_type="FeatureClass", workspace="in_memory")
        arcpy.CopyFeatures_management(feature,aoiFeature)

        # Create a temp point feature class to digitize ALL of the pedons within the bounding box first
        tempPoints = arcpy.CreateScratchName("tempPoints",data_type="FeatureClass", workspace="in_memory")

        # Factory code for WGS84 Coordinate System
        spatial_reference = arcpy.SpatialReference(4326)
        arcpy.CreateFeatureclass_management("in_memory", os.path.basename(tempPoints), "POINT", "#", "DISABLED", "DISABLED", spatial_reference)

        peiidFld = "peiid"
        arcpy.AddField_management(tempPoints,peiidFld,"LONG")

        # Initiate the insert cursor object using the peiid and XY values
        cursor = arcpy.da.InsertCursor(tempPoints,[peiidFld,'SHAPE@XY'])

        for pedon in pedonDict:
            xValue = float(pedonDict[pedon][2])
            yValue = float(pedonDict[pedon][3])
            newRow = [pedon,(xValue,yValue)]
            cursor.insertRow(newRow)
        del cursor

        arcpy.SetProgressorLabel("Selecting pedons that intersect with " + arcpy.Describe(feature).Name + " Layer")  # Some odd reason 'tempPointsPRJ' stays frozen in the progress bar.

        # Select all of the pedons within the user's AOI
        tempPointsLYR = arcpy.CreateScratchName("tempPointsLYR",data_type="FeatureClass", workspace="in_memory")
        arcpy.MakeFeatureLayer_management(tempPoints,tempPointsLYR)

        #AddMsgAndPrint(".\tThere are " + str(int(arcpy.GetCount_management("tempPoints_LYR").getOutput(0))) + " pedons in the layer",2)
        arcpy.SelectLayerByLocation_management(tempPointsLYR,"INTERSECT",aoiFeature, "","NEW_SELECTION")
        pedonsWithinAOI = int(arcpy.GetCount_management(tempPointsLYR).getOutput(0))

        # There are pedons within the user's AOI
        if pedonsWithinAOI > 0:
            AddMsgAndPrint(".\tThere are " + splitThousands(pedonsWithinAOI) + " pedons within this layer")

            # Make a copy of the user-input features - this is just in case there is a selected set
            selectedPedons = arcpy.CreateScratchName("selectedPedons",data_type="FeatureClass", workspace="in_memory")
            arcpy.CopyFeatures_management(tempPointsLYR,selectedPedons)

            # Create a new list of pedonIDs from the selected set; pedonIDs are converted to strings in order
            # to compare against the pedonDict()
            selectedPedonsList = [str(row[0]) for row in arcpy.da.SearchCursor(selectedPedons, (peiidFld))]

            # Make a copy of pedonDict b/c it cannot change during iteration (next step)
            pedonDictCopy = pedonDict.copy()

            # delete any pedon from the original pedonDict that is not in the selected set.
            labPedonCnt = 0
            for pedon in pedonDictCopy:
                if pedon not in selectedPedonsList:
                    del pedonDict[pedon]
                else:
                    if not pedonDict[pedon][1] is None:
                        labPedonCnt+=1

            AddMsgAndPrint(".\t\tLAB Pedons: " + splitThousands(labPedonCnt))
            AddMsgAndPrint(".\t\tNASIS Pedons: " + splitThousands(pedonsWithinAOI - labPedonCnt))

            for layer in (aoiFeature,tempPoints,tempPointsLYR,selectedPedons):
                if arcpy.Exists(layer):
                    arcpy.Delete_management(layer)

            del pedonDictCopy,selectedPedons,selectedPedonsList

            # Return integer reflecting number of pedons within feature AOI
            return pedonsWithinAOI

        else:
            AddMsgAndPrint(".\tThere are NO pedons that are completely within your AOI. EXITING! \n",2)
            return False

    except:
        errorMsg()
        return False

## ================================================================================================================
def createPedonDB():
    """This Function will create a new File Geodatabase using a pre-established XML workspace
       schema.  All Tables will be empty and should correspond to that of the access database.
       Relationships will also be pre-established.
       Return false if XML workspace document is missing OR an existing FGDB with the user-defined
       name already exists and cannot be deleted OR an unhandled error is encountered.
       Return the path to the new Pedon File Geodatabase if everything executes correctly."""

    try:
        if sqliteFormat:
            AddMsgAndPrint(".\nCreating New Pedon SQLite Database")
            arcpy.SetProgressorLabel("Creating New Pedon SQLite Database")
        else:
            AddMsgAndPrint(".\nCreating New Pedon File Geodatabase")
            arcpy.SetProgressorLabel("Creating New Pedon File Geodatabase")

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "NASISpedons_XMLWorkspace.xml"

        if sqliteFormat:
            localPedonDB = os.path.dirname(sys.argv[0]) + os.sep + "NASISPedonsSQLiteTemplate.sqlite"
            ext = ".sqlite"
        else:
            localPedonDB = os.path.dirname(sys.argv[0]) + os.sep + "NASISPedonsFGDBTemplate.gdb"
            ext = ".gdb"

        # Return false if pedon fGDB template is not found
        if not arcpy.Exists(localPedonDB):
            AddMsgAndPrint(".\t" + os.path.basename(localPedonDB) + " template was not found!",2)
            return False

        newPedonDB = os.path.join(outputFolder,DBname + ext)

        if arcpy.Exists(newPedonDB):
            try:
                arcpy.Delete_management(newPedonDB)
                AddMsgAndPrint(".\t" + os.path.basename(newPedonDB) + " already exists. Deleting and re-creating FGDB\n",1)
            except:
                AddMsgAndPrint(".\t" + os.path.basename(newPedonDB) + " already exists. Failed to delete\n",2)
                return False

        # copy template over to new location
        AddMsgAndPrint(".\tCreating " + DBname + ext + " with NCSS Pedon Schema 7.4.1")
        arcpy.Copy_management(localPedonDB,newPedonDB)

        """ ------------------------------ Code to use XML Workspace -------------------------------------------"""
##        # Return false if xml file is not found
##        if not arcpy.Exists(pedonXML):
##            AddMsgAndPrint(".\t" + os.path.basename(pedonXML) + " Workspace document was not found!",2)
##            return False
##
##        # Create empty temp File Geodatabae
##        arcpy.CreateFileGDB_management(outputFolder,os.path.splitext(os.path.basename(newPedonFGDB))[0])
##
##        # set the pedon schema on the newly created temp Pedon FGDB
##        AddMsgAndPrint(".\tImporting NCSS Pedon Schema 7.3 into " + DBname + ".gdb")
##        arcpy.ImportXMLWorkspaceDocument_management(newPedonFGDB, pedonXML, "DATA", "DEFAULTS")

        #arcpy.UncompressFileGeodatabaseData_management(newPedonFGDB)
        AddMsgAndPrint(".\tSuccessfully created: " + os.path.basename(newPedonDB))

        return newPedonDB

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (createDB)", 2)
        errorMsg()
        return False

## ===============================================================================================================
def createReferenceObjects(pedonDBloc):
    # Description
    # This function will create the following 2 unique dictionaries that will be used throughout the script:
    # - pedonGDBtablesList: contains every table in the newly created pedonDB above as a key.
    #                       Individual records of tables will be added as list of values to the table keys.
    #                       This dictionary will be populated using the results from the
    #                       the WEB_AnalysisPC_MAIN_URL_EXPORT NASIS report
    #                       i.e. {'area': [],'areatype': [],'basalareatreescounted': []}
    # - tableInfoDict:      Dictionary containing physical name from MDSTATTABS table as the key.
    #                       Each key has an associated list consisting of alias name, number of fields in the
    #                       physical table and the position index of the same table within the pedonGDBList.
    #
    #                       i.e. {croptreedetails:['Crop Tree Details',48,34]}
    #                       The number of fields is used to double check that the values from
    #                       the web report are correct.  This was added b/c there were text fields that were
    #                       getting disconnected in the report and being read as 2 lines -- Jason couldn't
    #                       address this issue in NASIS.
    #                       The position index is needed b/c once the pedonGDBList begins to be populated a
    #                       table cannot be looked up.

    # Paramaters
    # pedonDBloc - Catalog path of the pedon File Geodatabase that was create to store pedon data.
    #                This FGDB must contain the Metadata Table which will be used to retrieve alias names
    #                and physical table names

    # Returns
    # This function returns 2 dictionaries (Description above).  If anything goes wrong the function will
    # return False,False and the script will eventually exit.

    try:
        arcpy.SetProgressorLabel("Gathering Table and Field Information")

        # Open Metadata table containing information for other pedon tables
        theMDTable = pedonDBloc + os.sep + prefix + "MetadataTable"
        arcpy.env.workspace = pedonDBloc

        # Establishes a cursor for searching through field rows. A search cursor can be used to retrieve rows.
        # This method will return an enumeration object that will, in turn, hand out row objects
        if not arcpy.Exists(theMDTable):
            AddMsgAndPrint(theMDTable + " doesn't Exist",2)
            return False,False

        tableList = arcpy.ListTables("*")
        tableList.append(prefix + "pedon")

        # "Tablelabel" Table is misspelled....huh?
        #nameOfFields = ["TablePhysicalName","TableLabel"]
        nameOfFields = ["tabphynm","tablab"]

        # Initiate 3 Dictionaries
        tableInfoDict = dict()
        #tblAliasesDict = dict()
        emptyPedonGDBtablesDict = dict()

        with arcpy.da.SearchCursor(theMDTable,nameOfFields) as cursor:

            for row in cursor:

                physicalName = prefix + row[0]  # Physical name of table
                aliasName = row[1]     # Alias name of table

                if physicalName.find(prefix + 'Metadata') > -1: continue

                if physicalName in tableList:

                    uniqueFields = arcpy.Describe(os.path.join(pedonDBloc,physicalName)).fields
                    numOfValidFlds = 0

                    for field in uniqueFields:
                        if not field.type.lower() in ("oid","geometry","fid","shape"):
                            numOfValidFlds +=1

                    # Add 2 more fields to the pedon table for X,Y
                    if physicalName == prefix + 'pedon':
                        numOfValidFlds += 2

                    # i.e. {phtexture:'Pedon Horizon Texture',phtexture}; will create a one-to-many dictionary
                    # As long as the physical name doesn't exist in dict() add physical name
                    # as Key and alias as Value.
                    if not physicalName in tableInfoDict:
                        tableInfoDict[physicalName] = [aliasName,numOfValidFlds]
                        emptyPedonGDBtablesDict[physicalName] = []

                    del uniqueFields;numOfValidFlds

        del theMDTable,tableList,nameOfFields
        arcpy.SetProgressorLabel("")

        return emptyPedonGDBtablesDict,tableInfoDict

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False, False

    except:
        AddMsgAndPrint("Unhandled exception (GetTableAliases)", 2)
        errorMsg()
        return False, False

## ===============================================================================================================
def parsePedonsIntoLists():
    """ This function will parse pedons into manageable chunks that will be sent to the 2nd URL report.
        There is an inherent URL character limit of 2,083.  The report URL is 123 characters long which leaves 1,960 characters
        available. I arbitrarily chose to have a max URL of 1,860 characters long to avoid problems.  Most pedonIDs are about
        6 characters.  This would mean an average max request of 265 pedons at a time.

        This function returns a list of pedon lists"""
        #1860 = 265

    try:
        arcpy.SetProgressorLabel("Determining the number of requests to send the server")

        # Total Count
        i = 1
        listOfPedonStrings = list()  # List containing pedonIDstring lists; individual lists are comprised of about 265 pedons
        pedonIDstr = ""              # concatenated string of pedonIDs

        for pedonID in pedonDict:

            # End of pedon dictionary has been reached
            if i == len(pedonDict):
                pedonIDstr = pedonIDstr + str(pedonID)
                listOfPedonStrings.append(pedonIDstr)

            # End of pedon list NOT reached
            else:
                # Max URL length reached - retrieve pedon data and start over
                if len(pedonIDstr) > 1866:
                    pedonIDstr = pedonIDstr + str(pedonID)
                    listOfPedonStrings.append(pedonIDstr)

                    ## reset the pedon ID string to empty
                    pedonIDstr = ""
                    i+=1

                # concatenate pedonID to string and continue
                else:
                    pedonIDstr = pedonIDstr + str(pedonID) + ",";i+=1

        numOfPedonStrings = len(listOfPedonStrings)  # Number of unique requests that will be sent

        if not numOfPedonStrings:
            AddMsgAndPrint(".\n\t Something Happened here.....WTF!",2)
            exit()

        else:
            return listOfPedonStrings,numOfPedonStrings

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        exit()

## ================================================================================================================
def organizeFutureInstanceIntoPedonDict(futureObject):
    # Description:
    # This function will take in a "future" object representing the execution of the
    # ThreadPoolExecutor callable.  In this case, the future object represents
    # the content of pedon Horizon information for a list of pedon IDs.  The content
    # will be organized it into a dictionary (pedonDBDict) whose schema follows
    # NASIS 7.3 pedon schema.

    # Parameters
    # future object - Encapsulates the asynchronous execution of a callable.
    # Future instances are created by Executor.submit()

    # Returns
    # True if the data was organized correctly
    # False if the object was empty or there was an error.

    # To view a sample output report go to:
    # https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=14542

    try:
        theReport = futureObject

        # There was an obvious error in opening the URL in the openURL function
        if theReport == None:
            return None

        invalidTable = 0    # represents tables that don't correspond with the GDB
        invalidRecord = 0   # represents records that were not added
        validRecord = 0

        bHeader = False         # indicator that record represents fields
        currentTable = ""       # The table found in the report
        numOfFields = ""        # The number of fields a specific table should contain
        partialValue = ""       # variable containing part of a value that is not complete
        originalValue = ""      # variable containing the original incomplete value
        bPartialValue = False   # flag indicating if value is incomplete; append next record

        """ ------------------- Begin Adding data from URL into a dictionary of lists ---------------"""
        for theValue in theReport:

            # convert from bytes to string and remove white spaces
            theValue = theValue.decode('utf-8').strip()

            # represents the start of valid table; Typically Line #19
            if theValue.find('@begin') > -1:
                theTable = prefix + theValue[theValue.find('@') + 7:]  ## Isolate the table
                numOfFields = tableFldDict[theTable][1]

                # Check if the table name exists in the list of dictionaries
                # if so, set the currentTable variable and bHeader
                if theTable in pedonDBtablesDict:
                    currentTable = theTable
                    bHeader = True  ## Next line will be the header

                else:
                    AddMsgAndPrint(".\t" + theTable + " Does not exist in the FGDB schema!  Figure this out Jason Nemecek!",2)
                    invalidTable += 1

            # end of the previous table has been reached; reset currentTable
            elif theValue.find('@end') > -1:
                currentTable = ""
                bHeader = False

            # represents header line; skip this line
            elif bHeader:
                bHeader = False

            # this is a valid record that should be collected
            elif not bHeader and currentTable:
                numOfValues = len(theValue.split('|'))

                # Add the record to its designated list within the dictionary
                # Do not remove the double quotes b/c doing so converts the object
                # to a list which increases its object size.  Remove quotes before
                # inserting into table

                # this should represent the 2nd half of a valid value
                if bPartialValue:
                    partialValue += theValue  # append this record to the previous record

                    # This value completed the previous value
                    if len(partialValue.split('|')) == numOfFields:
                        pedonDBtablesDict[currentTable].append(partialValue)
                        validRecord += 1
                        bPartialValue = False
                        partialValue,originalValue = "",""

                    # appending this value still falls short of number of possible fields
                    # add another record; this would be the 3rd record appended and may
                    # exceed number of values.
                    elif len(partialValue.split('|')) < numOfFields:
                        arcpy.SetProgressorPosition()
                        continue

                    # appending this value exceeded the number of possible fields
                    else:
                        AddMsgAndPrint(".\t\tIncorrectly formatted Record Found in " + currentTable + " table:",2)
                        AddMsgAndPrint(".\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(len(partialValue.split('|'))),2)
                        AddMsgAndPrint(".\t\t\tOriginal Record: " + originalValue,2)
                        AddMsgAndPrint(".\t\t\tAppended Record: " + partialValue,2)
                        invalidRecord += 1
                        bPartialValue = False
                        partialValue,originalValue = ""

                # number of values do not equal the number of fields in the corresponding tables
                elif numOfValues != numOfFields:

                    # number of values exceed the number of fields; Big Error
                    if numOfValues > numOfFields:
                        AddMsgAndPrint(".\n\t\tIncorrectly formatted Record Found in " + currentTable + " table:",2)
                        AddMsgAndPrint(".\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(numOfValues),2)
                        AddMsgAndPrint(".\t\t\tRecord: " + theValue,2)
                        invalidRecord += 1

                    # number of values falls short of the number of correct fields
                    else:
                        partialValue,originalValue = theValue,theValue
                        bPartialValue = True

                else:
                    pedonDBtablesDict[currentTable].append(theValue)
                    validRecord += 1
                    bPartialValue = False
                    partialValue = ""

            elif theValue.find("ERROR") > -1:
                AddMsgAndPrint(".\n\t\t" + theValue[theValue.find("ERROR"):],2)
                return False

            else:
                invalidRecord += 1

        if not validRecord:
            AddMsgAndPrint(".\t\tThere were no valid records captured from NASIS request",2)
            return False

        # Report any invalid tables found in report; This should take care of itself as Jason perfects the report.
        if invalidTable and invalidRecord:
            AddMsgAndPrint(".\t\tThere were " + splitThousands(invalidTable) + " invalid table(s) included in the report with " + splitThousands(invalidRecord) + " invalid record(s)",1)

        # Report any invalid records found in report; There are 27 html lines reserved for headers and footers
        if invalidRecord > 28:
            AddMsgAndPrint(".\t\tThere were " + splitThousands(invalidRecord) + " invalid record(s) not captured",1)

        return True

    except:
        errorMsg()
        return False

## ================================================================================================================
def importPedonData(tableInfoDict,verbose=False):
    """ This function will purge the contents from the pedonDBtablesDict dictionary which contains all of the pedon
        data into the pedon FGDB.  Depending on the number of pedons in the user's AOI, this function will be
        used multiple times.  The pedonDBtablesDict dictionary could possilbly allocate all of the computer's
        memory so a fail-safe was built in to make sure a memory exception error wasn't encountered.  This
        function is invoked when approximately 40,000 pedons have been retrieved from the server and stored in \
        memory."""

    try:
        if verbose: AddMsgAndPrint(".\nImporting Pedon Data into FGDB")
        arcpy.SetProgressorLabel("Importing Pedon Data into FGDB")

        # use the tableInfoDict so that tables are imported in alphabetical order
        tblKeys = tableInfoDict.keys()
        maxCharTable = max([len(table) for table in tblKeys]) + 1
        maxCharAlias = max([len(value[1][0]) for value in tableInfoDict.items()])

        headerName = f"\n\t{'Table Physical Name' : <30}{'Table Alias Name' : <55}{'# of Records' : <20}"
        if verbose: AddMsgAndPrint(headerName)
        if verbose: AddMsgAndPrint(".\t" + len(headerName) * "=")

        tblKeys = dict(sorted(tableFldDict.items(), key=lambda item: item[0]))

        """ ---------------------------------------------------"""
        arcpy.SetProgressor("step","Importing Pedon Data into FGDB table: ",0,len(tblKeys),1)
        for table in tblKeys:

            arcpy.SetProgressorLabel("Importing Pedon Data into FGDB: " + table)
            arcpy.SetProgressorPosition()

            # Skip any Metadata files
            if table.find(prefix + 'Metadata') > -1: continue

            # Capture the alias name of the table
            aliasName = tableInfoDict[table][0]

            # Strictly for standardizing reporting
            firstTab = (maxCharTable - len(table)) * " "

            # check if list contains records to be added
            if len(pedonDBtablesDict[table]):

                numOfRowsAdded = 0
                GDBtable = pedonDB + os.sep + table # FGDB Pyhsical table path

                """ -------------------------------- Collect field information -----------------------"""
                ''' For the current table, get the field length if the field is a string.  I do this b/c
                the actual value may exceed the field length and error out as has happened in SSURGO.  If
                the value does exceed the field length then the value will be truncated to the max length
                of the field '''

                # Put all the field names in a list
                fieldList = arcpy.Describe(GDBtable).fields
                nameOfFields = []
                fldLengths = []

                for field in fieldList:

                    # Skip Object ID field Shape field (only for site)
                    if not field.type.lower() in ("oid","geometry"):
                        nameOfFields.append(field.name)

                        if field.type.lower() == "string":
                            fldLengths.append(field.length)
                        else:
                            fldLengths.append(0)

                # Add a new field at the end called 'labsampleIndicator' to indicate whether
                # record is a LAB pedon. Addd XY token to list
                if table == prefix + 'pedon':

                    # Pedon feature class will have X,Y geometry added; Add XY token to list
                    nameOfFields.append('SHAPE@XY')
                    fldLengths.append(0)  # X coord
                    fldLengths.append(0)  # Y coord

                """ -------------------------------- Insert Rows ------------------------------------------
                    Iterate through every value from a specific table in the pedonDBtablesDict dictary
                    and add it to the appropriate FGDB table  Truncate the value if it exceeds the
                    max number of characters.  Set the value to 'None' if it is an empty string."""

                # Initiate the insert cursor object using all of the fields
                cursor = arcpy.da.InsertCursor(GDBtable,nameOfFields)
                recNum = 0

                # '"S1962WI025001","43","15","9","North","89","7","56","West",,"Dane County, Wisconsin. 100 yards south of road."'
                for rec in pedonDBtablesDict[table]:

                    newRow = list()  # list containing the values that will populate a new row
                    fldNo = 0        # list position to reference the field lengths in order to compare

                    for value in rec.replace('"','').split('|'):

                        value = value.strip()
                        fldLen = fldLengths[fldNo]

                        if value == '' or value == 'NULL':   ## Empty String
                            value = None

                        elif fldLen > 0:  ## record is a string, truncate it
                            value = value[0:fldLen]

                        else:             ## record is a number, keep it
                            value = value

                        newRow.append(value)
                        fldNo += 1

                        del value, fldLen

                    # Add XY coordinates to the pedon point feature class.
                    if table == prefix + 'pedon':
                        try:
                            xValue = float(newRow[-1])  # Long
                            yValue = float(newRow[-2])  # Lat
                        except:
                            xValue = 0.00
                            yValue = 90.0

                        # remove the X,Y coords from the newRow list b/c X,Y
                        # fields don't exist in the pedon Table
                        newRow = newRow[:-2]

                        newRow.append((xValue,yValue))
                        del xValue,yValue

                    try:
                        cursor.insertRow(newRow)
                        numOfRowsAdded += 1;recNum += 1

                    except arcpy.ExecuteError:
                        AddMsgAndPrint(".\n\tError in :" + table + " table: Field No: " + str(fldNo) + " : " + str(rec),2)
                        AddMsgAndPrint(".\n\t" + arcpy.GetMessages(2),2)
                        break
                    except:
                        AddMsgAndPrint(".\n\tError in: " + table + " table")
                        AddMsgAndPrint(".\tNumber of Fields in GDB: " + str(len(nameOfFields)))
                        AddMsgAndPrint(".\tNumber of fields in report: " + str(len([rec.split('|')][0])))
                        errorMsg()
                        break

                    del newRow,fldNo

                # Report the # of records added to the table
##                if bAliasName:
                if verbose:AddMsgAndPrint(f".\t{table : <30}{aliasName: <55}{'Records Added: ' + splitThousands(numOfRowsAdded) : <20}")

                del numOfRowsAdded,GDBtable,fieldList,nameOfFields,fldLengths,cursor

            # Table had no records; still print it out
            else:
                if verbose:
                    AddMsgAndPrint(f".\t{table : <30}{aliasName: <55}{'Records Added: 0' : <20}")


        #Resets the progressor back to its initial state
        arcpy.ResetProgressor()

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        errorMsg()
        return False

## ================================================================================================================
def getObjectSize(obj, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}
    """

    try:
        # lamda function to iterate through a dictionary
        dict_handler = lambda d: chain.from_iterable(d.items())

    #     Use the following lines if you want to determine the size for ANY object
    ##    all_handlers = {tuple: iter,
    ##                    list: iter,
    ##                    deque: iter,
    ##                    dict: dict_handler,
    ##                    set: iter,
    ##                    frozenset: iter,
    ##                   }

        # Limit the focus to just dictionaries since that is the only thing I will pass
        all_handlers = {dict: dict_handler}

        all_handlers.update(handlers)     # user handlers take precedence
        seen = set()                      # unique list of Object's memory ID
        default_size = getsizeof(0)       # estimate sizeof object without __sizeof__; a dict will always be 140 bytes

        def sizeof(obj):

            if id(obj) in seen:       # do not double count the same object's memory ID
                return 0

            seen.add(id(obj))
            s = getsizeof(obj, default_size)

            if verbose:
                print(s, type(obj), repr(obj))

            # iterate through all itemized objects (tuple,list) 'all_handlers' including their content
            for typ, handler in all_handlers.items():

                # check if the object is associated with the type at hand.  i.e. if the current
                # type is dict then check if the object 'o' is a dict. ({'a': 1, 'c': 3, 'b': 2, 'e': 'a string of chars', 'd': [4, 5, 6, 7]})
                # if True, go thru and add the bytes for each eleement
                if isinstance(obj, typ):
                    s += sum(map(sizeof, handler(obj)))   # Iterates through this function
                    break

            return s

        byteSize = sizeof(obj)

        if byteSize < 1024:
            return splitThousands(byteSize) + " bytes"
        elif byteSize > 1023 and byteSize < 1048576:
            return splitThousands(round((byteSize / 1024.0),1)) + " KB"
        elif byteSize > 1048575 and byteSize < 1073741824:
            return splitThousands(round((byteSize / (1024*1024.0)),1)) + " MB"
        elif byteSize > 1073741823:
            return splitThousands(round(byteSize / (1024*1024*1024.0),1)) + " GB"

    except:
        errorMsg()
        pass

## ===================================================================================
def openURL(url):
    # Description
    # This function will open a URL, read the lines and send back the response.
    # It is used within the ThreadPoolExecutor to send multiple NASIS server
    # requests.  The primary URL passed to this function from this script will be:
    # https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=14542
    # This function also replaces the 'getPedonHorizon' function that not only opened
    # the URL but also organized the contents into a dictionary that followed the NASIS schema.
    # The function of organizing the URL content is now handled by the 'organizeFutureInstance' function

    # Parameters
    # url - the url that connection will be establised to and whose contents will be returned.
    # 1 global variable will be updated within this function.

    # Returns
    # This function returns the contents of a URL.  However, within this script, the openURL
    # function is being called within the ThreadPoolExecutor asynchronous callables which returns
    # a "future" object representing the execution of the callable.

    try:

        # isolate the pedonIDs from the URL - strictly for formatting
        thisPedonString = url.split('=')[2]
        numOfPedonsInThisString = len(thisPedonString.split(','))

        # Update Global variables
        global i

        """ Strictly for formatting print message """
        if numOfPedonStrings > 1:
            AddMsgAndPrint(".\tRequest " + splitThousands(i) + " of " + splitThousands(numOfPedonStrings) + " for " + str(numOfPedonsInThisString) + " pedons")
            arcpy.SetProgressorLabel("Request " + splitThousands(i) + " of " + splitThousands(numOfPedonStrings) + " for " + str(numOfPedonsInThisString) + " pedons")
        else:
            AddMsgAndPrint("Retrieving pedon data from NASIS for " + str(numOfPedonsInThisString) + " pedons.")
            arcpy.SetProgressorLabel("Retrieving pedon data from NASIS for " + str(numOfPedonsInThisString) + " pedons.")

        # update request number
        if not i == len(URLlist):
            i+=1  # request number

        response = urllib.request.urlopen(url)
        arcpy.SetProgressorLabel("")

        if response.code == 200:
            return response.readlines()
        else:
            AddMsgAndPrint(".\nFailed to open URL: " + str(url),2)
            return None

    except URLError as e:
        AddMsgAndPrint('URL Error' + str(e),2)
        return None

    except HTTPError as e:
        AddMsgAndPrint('HTTP Error' + str(e),2)
        return None

    except socket.timeout as e:
        AddMsgAndPrint("Server Timeout Error", 2)
        return None

    except socket.error as e:
        AddMsgAndPrint("NASIS Reports Website connection failure", 2)
        return None

    except errorMsg():
        return None

## ===================================================================================
def addPedonReportHyperlink(pedonFC):
    # Description:
    # This function will add a field called 'pedondescriptionreport' to the pedon layer to
    # to store a hyperlink to the pedon description report for every user pedon ID.

    # Parameters
    # path to the 'pedon' layer within the output database

    # Returns
    # True if the data was organized correctly
    # False if the object was empty or there was an error.

    # 2 similar reports to choose from
    #pedonDescLink = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=Pedon%20Description%20html%20(userpedid)&pedon_id='
    #pedonDescLink = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=Pedon_Site_Description_usepedonid&pedon_id='

    try:
        arcpy.SetProgressorLabel("Adding Pedon Description Hyperlink to Pedon layer")

        # New field that will be added to PedonFC
        fieldName = "pedondescriptionreport"
        arcpy.AddField_management(pedonFC, fieldName,'TEXT',field_length=215, field_alias="Pedon Description Report", field_is_nullable="NULLABLE")

        expression = "createPedonDescLink(!upedonid!)"

        codeblock = """
def createPedonDescLink(pedonID):

    pedonDescLink = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=Pedon_Site_Description_usepedonid&pedon_id=' + pedonID
    #hyperLinkName = pedonID + r' Pedon Description Report'
    hyperLinkName = r'Pedon Description Report'
    arcGISProHyperLink = r'<a href="' + pedonDescLink + r'" target="_top">' + hyperLinkName + r'</a>'

    return arcGISProHyperLink"""

        # Execute CalculateField
        arcpy.CalculateField_management(pedonFC, fieldName, expression, "PYTHON3",codeblock)
        return True

    except:
        errorMsg()
        return False

#===================================================================================================================================
""" ----------------------------------------My Notes -------------------------------------------------"""

""" --------------- Column Headers
Column order
1.	Row_Number2,
2.	upedonid,
3.	peiid,
4.	pedlabsampnum,
5.	longstddecimaldegrees ,
6.	latstddecimaldegrees
                    ----------------------"""

""" 1st Report """
# If user choses to download all Pedons then the 1st report is to get a list of ALL NASIS pedonIDs:
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_PEDON_PEIID_LIST_ALL_OF_NASIS'

# If the user choses to download pedons by AOI then the 1st report is to get a count of pedons within a bounding box
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_ANALYSIS_PC_PEDON_NUMBER_SUM&lat1=43&lat2=45&long1=-90&long2=-88

""" 2nd Report """
# Used to get a list of peiids based on bounding box coordinates; This peiid list will passed over to the 3rd report
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&lat1=43&lat2=45&long1=-90&long2=-88

""" 3rd Report """
# This report will return all NASIS pedon related information that will be parsed into a FGDB.

# Original Report URL
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=TEST_sub_pedon_pc_6.1_phorizon&pedonid_list=

# Updated Report URL
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=

# Sample URL with pedonIDs:
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=36186,59976,60464,60465,101219,102867,106105,106106
#===================================================================================================================================


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

        try:
            # This set of parameters corresponds to the 'Extract Pedons from NASIS by AOI' tool
            inputFeatures = arcpy.GetParameter(0)
            DBname = arcpy.GetParameter(1)
            outputFolder = arcpy.GetParameterAsText(2)
            sqliteFormat = arcpy.GetParameter(3)
            allPedons = arcpy.GetParameter(4)

        except:
            # This set of parameters corresponds to the 'Extract All Pedons from NASIS' tool
            DBname = arcpy.GetParameter(0)
            outputFolder = arcpy.GetParameterAsText(1)
            sqliteFormat = arcpy.GetParameter(2)
            allPedons = arcpy.GetParameter(3)

##        inputFeatures = r'E:\SSURGO\WI025\spatial\'
##        DBname = 'PedonTest'
##        outputFolder = r'E:\Temp\scratch'
##        sqliteFormat = False
##        allPedons = False

        if sqliteFormat == True:
            prefix = "main."
        else:
            prefix = ""

        arcpy.env.parallelProcessingFactor = "100%"
        arcpy.env.overwriteOutput = True

        textFilePath = outputFolder + os.sep + DBname + "_logFile.txt"
        startTime = tic()

        # User has chosen to donwload all pedons
        if allPedons:
            pedonDict = getDictionaryOfAllPedonIDs()
            totalPedons = len(pedonDict)
            exit()
            #pedonDict = dict(d.items()[len(d)/2:])

            AddMsgAndPrint(".\nProcessing " + str(splitThousands(totalPedons)) + " pedons")

            if not pedonDict:
                AddMsgAndPrint(".\nFailed to obtain a list of ALL NASIS Pedon IDs",2)
                exit()

        # User has chosen to pedons by AOI
        else:

            # Get Bounding box coordinates of AOI
            # Lat1 = 43.8480050;Lat2 = 44.1962;Long1 = -93.7678808;Long2 = -93.40649;
            Lat1,Lat2,Long1,Long2 = getBoundingCoordinates(inputFeatures)

            if not Lat1:
                AddMsgAndPrint(".\nFailed to acquire Lat/Long coordinates to pass over; Try a new input feature",2)
                exit()

            coordStr = "&Lat1=" + str(Lat1) + "&Lat2=" + str(Lat2) + "&Long1=" + str(Long1) + "&Long2=" + str(Long2)

            # Get a number of PedonIDs that are within the bounding box from NASIS
            # Exit if pedon count is 0
            # Uses the 'WEB_ANALYSIS_PC_PEDON_NUMBER_SUM' NASIS report
            areaPedonCount = getNASISpedonCountbyBox(coordStr)

            if areaPedonCount:
                AddMsgAndPrint(".\tThere are " + splitThousands(areaPedonCount) + " pedons within the bounding coordinates")
            else:
                AddMsgAndPrint(".\nThere are no records found within the area of interest.  Try using a larger area",2)
                exit()

            # Get a list of PedonIDs that are within the bounding box from NASIS
            # Uses the 'WEB_EXPORT_PEDON_BOX_COUNT' NASIS report
            # {peiid: (siteID,Labnum,X,Y)} -- {'122647': ('84IA0130011', '85P0558', '-92.3241653', '42.3116684')
            pedonDict = getNASISpedonIDsByBox(coordStr)

            # populate the pedonDict with the pedons that fall within the bounding coordinates of the AOI
            if not pedonDict:
                AddMsgAndPrint(".\n\tFailed to get a list of pedonIDs from NASIS \n",2)
                exit()

            # Filter pedons by those that fall completely within the AOI; This will update the pedonDict
            totalPedons = filterPedonsByFeature(inputFeatures)

            if not totalPedons:
                AddMsgAndPrint(".\n\tFailed to filter list of Pedons by Area of Interest. EXITING! \n",2)
                exit()

            """ ------------------------------------------------------Create New File Geodatabaes and get Table Aliases for printing -------------------------------------------------------------------
                Create a new FGDB using a pre-established XML workspace schema.  All tables will be empty
                and relationships established.  A dictionary of empty lists will be created as a placeholder
                for the values from the XML report.  The name and quantity of lists will be the same as the FGDB"""

        # Create a FGDB or sqlite database
        pedonDB = createPedonDB()
        arcpy.env.workspace = pedonDB

        if not pedonDB:
            AddMsgAndPrint(".\nFailed to Initiate Empty Pedon Database.  Error in createPedonDB() function. Exiting!",2)
            exit()

        # Create 2 Dictionaries that will be used throughout this script
        pedonDBtablesDict,tableFldDict = createReferenceObjects(pedonDB)

        if not tableFldDict:
            AddMsgAndPrint(".\nCould not retrieve alias names from " + prefix + "\'MetadataTable\'",1)
            exit()

        """ ------------------------------------------ Get Site, Pedon, and Pedon Horizon information from NASIS -------------------------------------------------------------------------
        ----------------------------------------------- Uses the 'WEB_AnalysisPC_MAIN_URL_EXPORT' NASIS report ---------------------------------------------------------------------------
        In order to request pedon information, the pedonIDs need to be split up into manageable
        lists of about 265 pedons due to URL limitations.  Submit these individual lists of pedon
        to the server """

        # Parse pedonIDs into lists containing about 265 pedons
        listOfPedonStrings,numOfPedonStrings = parsePedonsIntoLists()

        if numOfPedonStrings > 1:
            AddMsgAndPrint(".\nDue to URL limitations there will be " + splitThousands(len(listOfPedonStrings))+ " seperate requests to NASIS:",1)
        else:
            AddMsgAndPrint(".\n")

        i = 1   # represents the request number; only used for ArcMap formatting

        multiThreadStartTime = tic()
        URLlist = list()              # List of unique URLs of pedonIDs
        futureResults = []            # List of html results from opening URLs

        # Iterate through a list of pedons strings to create a list of URLs by concatenating the URL
        # base with the pedon strings.
        for pedonString in listOfPedonStrings:
            URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=' + pedonString
            URLlist.append(URL)

        arcpy.SetProgressor("step", "Sending Pedon Requests", 0, len(URLlist), 1)

        # Create an Executor to manage all tasks.  Using the with statement creates a context
        # manager, which ensures any stray threads or processes get cleaned up properly when done.
        with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:

            # use a set comprehension to start all tasks.  This creates a future object
            future_to_url = {executor.submit(openURL, url): url for url in URLlist}

            # yield future objects as they are done.
            for future in as_completed(future_to_url):
                #futureResults.append(future.result())
                organizeFutureInstanceIntoPedonDict(future.result())
                arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()

##        with ProcessPoolExecutor() as executor:
##            for result in futureResults:
##                organizeFutureInstanceIntoPedonDict(result)


# The next 10 lines were used to test the ProcessPoolExecutor with arcpy.da.editor
# The test was successful but it was way too slow.
##        edit = arcpy.da.Editor(pedonDB)
##        pedonDBtables = pedonDBtablesDict.keys()  # A list of pedonDB tables extracted from tblAliases dict
##        pedonDBtables.sort()                       # Sort the list so that tables are alphabetical order
##
##        maxCharTable = max([len(table) for table in pedonDBtables]) + 1
##        maxCharAlias = max([len(value[1]) for value in tblAliases.items()])
##
##        with ProcessPoolExecutor() as executor:
##            for table in pedonDBtables:
##                importPedonDataByTable(table)

        # Import Pedon Information into Pedon FGDB
        if len(pedonDBtablesDict[prefix + 'pedon']):
            if not importPedonData(tableFldDict,verbose=(True if i==numOfPedonStrings else False)):
                exit()

        # Pedon FGDB path
        pedonDBfc = os.path.join(pedonDB,prefix + 'pedon')

        # Add Hyperlink to Pedon Description Report
        if addPedonReportHyperlink(pedonDBfc):
            AddMsgAndPrint(".\nSuccessfully added Pedon Description Report Hyperlink")
        else:
            AddMsgAndPrint(".\nPedon Description Report Hyperlink Could not be added",2)

        """ ------------------------------------ Report Summary of results -----------------------------------"""
        pedonCount = int(arcpy.GetCount_management(pedonDBfc).getOutput(0))

        # Text file that will be created with pedonIDs that did not get collected
        errorFile = outputFolder + os.sep + os.path.basename(pedonDB).split('.')[0] + "_error.txt"

        if os.path.exists(errorFile):
            os.remove(errorFile)

        if totalPedons == pedonCount:
            AddMsgAndPrint(".\n\nSuccessfully downloaded " + splitThousands(totalPedons) + " pedons from NASIS")

        else:
            difference = totalPedons - pedonCount
            AddMsgAndPrint(".\nDownloaded " + splitThousands(pedonCount) + " from NASIS",2)
            AddMsgAndPrint(".\tFailed to download " + splitThousands(difference) + " pedons from NASIS:",2)

            FGDBpedons = [str(row[0]) for row in arcpy.da.SearchCursor(pedonDBfc,'peiid')]
            missingPedons = list(set(pedonDict.keys()) - set(FGDBpedons))

            # Log pedons that did not download successfully into a text file
            f = open(errorFile,'a+')
            i=1
            for miaPedon in missingPedons:
                if i != len(missingPedons):
                    f.write(miaPedon + "\n")
                else:
                    f.write(miaPedon)
                i+=1
            f.close()

            if difference < 20:
                AddMsgAndPrint(".")
                AddMsgAndPrint(".\t\t" + str(missingPedons))

            AddMsgAndPrint(".\n\tThe Missing Pedons have been written to " + errorFile + " files",2)

        """ ---------------------------Add Pedon Feature Class to ArcGIS Pro Session if available ------------------"""
        try:
            if arcpy.GetCount_management(pedonDBfc).inputCount > 0:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                aprxMap = aprx.listMaps()[0]
                aprxMap.addDataFromPath(pedonDBfc)
                AddMsgAndPrint(".\nAdded the pedon feature class to your ArcMap Session")
        except:
            pass

##        FinishTime = toc(startTime)
##        AddMsgAndPrint("Total Time = " + str(FinishTime))
##        AddMsgAndPrint(".\n")
##        AddMsgAndPrint("Dictionary Size: " + str(getObjectSize(pedonDBtablesDict)))

    except:
        FinishTime = toc(startTime)
        AddMsgAndPrint("Total Time = " + str(FinishTime))
        #AddMsgAndPrint("Size of pedonDBtablesDict  = " + str(objSize) )
        errorMsg()
