#-------------------------------------------------------------------------------
# Name:  NASISpedons_Extract_Pedons_from_NASIS
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
# Last Modified: 5/18/2017
# Copyright:   (c) Adolfo.Diaz 2016

#-------------------------------------------------------------------------------

## ===================================================================================
class ExitError(Exception):
    pass

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print msg

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
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

### ===================================================================================
def setScratchWorkspace():
    """ This function will set the scratchWorkspace for the interim of the execution
        of this tool.  The scratchWorkspace is used to set the scratchGDB which is
        where all of the temporary files will be written to.  The path of the user-defined
        scratchWorkspace will be compared to existing paths from the user's system
        variables.  If there is any overlap in directories the scratchWorkspace will
        be set to C:\TEMP, assuming C:\ is the system drive.  If all else fails then
        the packageWorkspace Environment will be set as the scratchWorkspace. This
        function returns the scratchGDB environment which is set upon setting the scratchWorkspace"""

    try:
        AddMsgAndPrint("\nSetting Scratch Workspace")
        scratchWK = arcpy.env.scratchWorkspace

        # -----------------------------------------------
        # Scratch Workspace is defined by user or default is set
        if scratchWK is not None:

            # dictionary of system environmental variables
            envVariables = os.environ

            # get the root system drive
            if envVariables.has_key('SYSTEMDRIVE'):
                sysDrive = envVariables['SYSTEMDRIVE']
            else:
                sysDrive = None

            varsToSearch = ['ESRI_OS_DATADIR_LOCAL_DONOTUSE','ESRI_OS_DIR_DONOTUSE','ESRI_OS_DATADIR_MYDOCUMENTS_DONOTUSE',
                            'ESRI_OS_DATADIR_ROAMING_DONOTUSE','TEMP','LOCALAPPDATA','PROGRAMW6432','COMMONPROGRAMFILES','APPDATA',
                            'USERPROFILE','PUBLIC','SYSTEMROOT','PROGRAMFILES','COMMONPROGRAMFILES(X86)','ALLUSERSPROFILE']

            """ This is a printout of my system environmmental variables - Windows 7
            -----------------------------------------------------------------------------------------
            ESRI_OS_DATADIR_LOCAL_DONOTUSE C:\Users\adolfo.diaz\AppData\Local\
            ESRI_OS_DIR_DONOTUSE C:\Users\ADOLFO~1.DIA\AppData\Local\Temp\6\arc3765\
            ESRI_OS_DATADIR_MYDOCUMENTS_DONOTUSE C:\Users\adolfo.diaz\Documents\
            ESRI_OS_DATADIR_COMMON_DONOTUSE C:\ProgramData\
            ESRI_OS_DATADIR_ROAMING_DONOTUSE C:\Users\adolfo.diaz\AppData\Roaming\
            TEMP C:\Users\ADOLFO~1.DIA\AppData\Local\Temp\6\arc3765\
            LOCALAPPDATA C:\Users\adolfo.diaz\AppData\Local
            PROGRAMW6432 C:\Program Files
            COMMONPROGRAMFILES :  C:\Program Files (x86)\Common Files
            APPDATA C:\Users\adolfo.diaz\AppData\Roaming
            USERPROFILE C:\Users\adolfo.diaz
            PUBLIC C:\Users\Public
            SYSTEMROOT :  C:\Windows
            PROGRAMFILES :  C:\Program Files (x86)
            COMMONPROGRAMFILES(X86) :  C:\Program Files (x86)\Common Files
            ALLUSERSPROFILE :  C:\ProgramData
            ------------------------------------------------------------------------------------------"""

            bSetTempWorkSpace = False

            """ Iterate through each Environmental variable; If the variable is within the 'varsToSearch' list
                list above then check their value against the user-set scratch workspace.  If they have anything
                in common then switch the workspace to something local  """
            for var in envVariables:

                if not var in varsToSearch:
                    continue

                # make a list from the scratch and environmental paths
                varValueList = (envVariables[var].lower()).split(os.sep)          # ['C:', 'Users', 'adolfo.diaz', 'AppData', 'Local']
                scratchWSList = (scratchWK.lower()).split(os.sep)                 # [u'C:', u'Users', u'adolfo.diaz', u'Documents', u'ArcGIS', u'Default.gdb', u'']

                # remove any blanks items from lists
                if '' in varValueList: varValueList.remove('')
                if '' in scratchWSList: scratchWSList.remove('')

                # First element is the drive letter; remove it if they are
                # the same otherwise review the next variable.
                if varValueList[0] == scratchWSList[0]:
                    scratchWSList.remove(scratchWSList[0])
                    varValueList.remove(varValueList[0])

                # obtain a similarity ratio between the 2 lists above
                #sM = SequenceMatcher(None,varValueList,scratchWSList)

                # Compare the values of 2 lists; order is significant
                common = [i for i, j in zip(varValueList, scratchWSList) if i == j]

                if len(common) > 0:
                    bSetTempWorkSpace = True
                    break

            # The current scratch workspace shares 1 or more directory paths with the
            # system env variables.  Create a temp folder at root
            if bSetTempWorkSpace:
                AddMsgAndPrint("\tCurrent Workspace: " + scratchWK,0)

                if sysDrive:
                    tempFolder = sysDrive + os.sep + "TEMP"

                    if not os.path.exists(tempFolder):
                        os.makedirs(tempFolder,mode=777)

                    arcpy.env.scratchWorkspace = tempFolder
                    AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                else:
                    packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                    if arcpy.env[packageWS[0]]:
                        arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                        AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)
                    else:
                        AddMsgAndPrint("\tCould not set any scratch workspace",2)
                        return False

            # user-set workspace does not violate system paths; Check for read/write
            # permissions; if write permissions are denied then set workspace to TEMP folder
            else:
                arcpy.env.scratchWorkspace = scratchWK

                if arcpy.env.scratchGDB == None:
                    AddMsgAndPrint("\tCurrent scratch workspace: " + scratchWK + " is READ only!",0)

                    if sysDrive:
                        tempFolder = sysDrive + os.sep + "TEMP"

                        if not os.path.exists(tempFolder):
                            os.makedirs(tempFolder,mode=777)

                        arcpy.env.scratchWorkspace = tempFolder
                        AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                    else:
                        packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                        if arcpy.env[packageWS[0]]:
                            arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                            AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                        else:
                            AddMsgAndPrint("\tCould not set any scratch workspace",2)
                            return False

                else:
                    AddMsgAndPrint("\tUser-defined scratch workspace is set to: "  + arcpy.env.scratchGDB,0)

        # No workspace set (Very odd that it would go in here unless running directly from python)
        else:
            AddMsgAndPrint("\tNo user-defined scratch workspace ",0)
            sysDrive = os.environ['SYSTEMDRIVE']

            if sysDrive:
                tempFolder = sysDrive + os.sep + "TEMP"

                if not os.path.exists(tempFolder):
                    os.makedirs(tempFolder,mode=777)

                arcpy.env.scratchWorkspace = tempFolder
                AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

            else:
                packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                if arcpy.env[packageWS[0]]:
                    arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                    AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)

                else:
                    return False

        arcpy.Compact_management(arcpy.env.scratchGDB)
        return arcpy.env.scratchGDB

    except:

        # All Failed; set workspace to packageWorkspace environment
        try:
            packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
            if arcpy.env[packageWS[0]]:
                arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                arcpy.Compact_management(arcpy.env.scratchGDB)
                return arcpy.env.scratchGDB
            else:
                AddMsgAndPrint("\tCould not set scratchWorkspace. Not even to default!",2)
                return False
        except:
            errorMsg()
            return False

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
            envelopeFeature = arcpy.CreateScratchName("envelopeFeature",data_type="FeatureClass", workspace=scratchWS)
            arcpy.CopyFeatures_management(feature,envelopeFeature)
            AddMsgAndPrint("\nCalculating bounding coordinates for " + splitThousands(selectedPolys) + " feature(s)",0)
            bExport = True

        else:
            envelopeFeature = feature
            AddMsgAndPrint("\nCalculating bounding coordinates of input features",0)

        """ Set Projection and Geographic Transformation environments in order
            to post process everything in WGS84.  This will force all coordinates
            to be in Lat/Long"""

        inputSR = arcpy.Describe(feature).spatialReference                # Get Spatial Reference of input features
        inputDatum = inputSR.GCS.datumName                                # Get Datum name of input features

        if inputSR == "Unkown":
            AddMsgAndPrint("\n\tInput layer needs a spatial reference defined to determine bounding envelope",2)
            return False

        if inputDatum == "D_North_American_1983":
            arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983"
        elif inputDatum == "D_North_American_1927":
            arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1927"
        elif inputDatum == "D_NAD_1983_2011":
            arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983_2011"
        elif inputDatum == "D_WGS_1984":
            arcpy.env.geographicTransformations = ""
        else:
            AddMsgAndPrint("\n\tGeo Transformation of Datum could not be set",2)
            AddMsgAndPrint("\tTry Projecting input layer to WGS 1984 Coordinate System",2)
            return False, False, False, False

        # Factory code for WGS84 Coordinate System
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

        """ ------------ Create Minimum Bounding Envelope of features ------------"""
        envelope = arcpy.CreateScratchName("envelope",data_type="FeatureClass",workspace=scratchWS)
        envelopePts = arcpy.CreateScratchName("envelopePts",data_type="FeatureClass",workspace=scratchWS)

        # create minimum bounding geometry enclosing all features
        arcpy.MinimumBoundingGeometry_management(envelopeFeature,envelope,"ENVELOPE","ALL","#","MBG_FIELDS")

        if int(arcpy.GetCount_management(envelope).getOutput(0)) < 1:
            AddMsgAndPrint("\n\tFailed to create minimum bounding area. \n\tArea of interest is potentially too small",2)
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
            AddMsgAndPrint("\tBounding Box Coordinates:")
            AddMsgAndPrint("\t\tSouth Latitude: " + str(coordList[0][1]))
            AddMsgAndPrint("\t\tNorth Latitude: " + str(coordList[2][1]))
            AddMsgAndPrint("\t\tEast Longitude: " + str(coordList[0][0]))
            AddMsgAndPrint("\t\tWest Longitude: " + str(coordList[2][0]))
            return coordList[0][1],coordList[2][1],coordList[0][0],coordList[2][0]

        else:
            AddMsgAndPrint("\tCould not get Latitude-Longitude coordinates from bounding area",2)
            return False

    except:

        for tempFile in [envelope,envelopePts]:
            if arcpy.Exists(tempFile):
                arcpy.Delete_management(tempFile)

        errorMsg()
        return False

## ================================================================================================================
def getWebPedonNumberSum(coordinates):
    """ This function will send the bounding coordinates to the 'Web Pedon Number SUM' NASIS report
        and return the number of pedons within the bounding coordinates.  Pedons include regular
        NASIS pedons and LAB pedons. Example of URL sent to the NASIS report would be:

        https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_ANALYSIS_PC_PEDON_NUMBER_SUM&Lat1=43.6425577303&Lat2=43.9828939095&Long1=-89.5997555233&Long2=-89.167551308"""

    try:
        AddMsgAndPrint("\nDetermining if there are any pedons within the bounding coordinates")
        arcpy.SetProgressorLabel("Determining if there are any pedons within the bounding coordinates")

        # Open a network object using the URL with the search string already concatenated
        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_ANALYSIS_PC_PEDON_NUMBER_SUM' + coordinates

        """ --------------------------------------  Try connecting to NASIS to read the report ------------------------"""
        try:
            theReport = urlopen(URL).readlines()
        except:
            try:
                AddMsgAndPrint("\t2nd attempt at requesting data")
                theReport = urlopen(URL).readlines()
            except:
                try:
                    AddMsgAndPrint("\t3rd attempt at requesting data")
                    theReport = urlopen(URL).readlines()

                except URLError, e:
                    if hasattr(e, 'reason'):
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\tURL Error: " + str(e.reason), 2)

                    elif hasattr(e, 'code'):
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\t" + e.msg + " (errorcode " + str(e.code) + ")", 2)

                    return False

                except socket.timeout, e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tServer Timeout Error", 2)
                    return False

                except socket.error, e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure (Socket Error)", 2)
                    return False

                except httplib.BadStatusLine:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure (Bad Status Line)", 2)
                    return False

                except:
                    errorMsg()
                    return False

        """ --------------------------------------  Read the NASIS report ---------------------------------"""
        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

        # iterate through the report until a valid record is found
        for theValue in theReport:

            theValue = theValue.strip() # removes whitespace characters

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
def getWebExportPedon(coordinates):
    """ This function will send the bounding coordinates to the 'Web Export Pedon Box' NASIS report
        and return a list of pedons within the bounding coordinates.  Pedons include regular
        NASIS pedons and LAB pedons.  Each record in the report will contain the following values:

            Row_Number,upedonid,peiid,pedlabsampnum,Longstddecimaldegrees,latstddecimaldegrees,Undisclosed Pedon
            24|S1994MN161001|102861|94P0697|-93.5380936|44.0612717|'Y'

        A dictionary will be returned containing something similar:
        {'102857': ('S1954MN161113A', '40A1694', '-93.6499481', '43.8647194','Y'),
        '102858': ('S1954MN161113B', '40A1695', '-93.6455002', '43.8899956','N')}
        theURL = r'    #getPedonIDURL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&Lat1=44.070820&Lat2=44.596950&Long1=-91.166274&Long2=-90.311911'"""

    try:
        AddMsgAndPrint("\nRequesting a list of pedonIDs from NASIS using the above bounding coordinates")
        arcpy.SetProgressorLabel("Requesting a list of pedons from NASIS")

        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT' + coordinates

        # Open a network object using the URL with the search string already concatenated
        startTime = tic()
        #AddMsgAndPrint("\tNetwork Request Time: " + toc(startTime))

        """ --------------------------------------  Try connecting to NASIS to read the report ------------------------"""
        try:
            theReport = urlopen(URL).readlines()
        except:
            try:
                AddMsgAndPrint("\t2nd attempt at requesting data")
                theReport = urlopen(URL).readlines()

            except:
                try:
                    AddMsgAndPrint("\t3rd attempt at requesting data")
                    theReport = urlopen(URL).readlines()

                except URLError, e:
                    if hasattr(e, 'reason'):
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\tURL Error: " + str(e.reason), 2)

                    elif hasattr(e, 'code'):
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\t" + e.msg + " (errorcode " + str(e.code) + ")", 2)

                    return False

                except socket.timeout, e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tServer Timeout Error", 2)
                    return False

                except socket.error, e:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                    return False

                except httplib.BadStatusLine:
                    AddMsgAndPrint("\n\t" + URL)
                    AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                    return False

        """ --------------------------------------  Read the NASIS report ------------------------------------"""
        totalPedonCnt = 0
        labPedonCnt = 0
        undisclosed = 0
        bValidRecord = False # boolean that marks the starting point of the mapunits listed in the project

        arcpy.SetProgressor("step", "Reading NASIS Report: 'WEB_EXPORT_PEDON_BOX_COUNT'", 0, len(theReport), 1)

        # iterate through the report until a valid record is found
        for theValue in theReport:

            theValue = theValue.strip() # removes whitespace characters

            # Iterating through the lines in the report
            if bValidRecord:
                if theValue == "STOP":  # written as part of the report; end of lines
                    break

                # Found a valid project record i.e. -- SDJR - MLRA 103 - Kingston silty clay loam, 1 to 3 percent slopes|400036
                else:
                    theRec = theValue.split("|")

                    if len(theRec) != 7:
                        AddMsgAndPrint("\tNASIS Report: Web Export Pedon Box is not returning the correct amount of values per record",2)
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

                    if not pedonDict.has_key(pedonID):
                        pedonDict[pedonID] = (userPedonID,labSampleNum,longDD,latDD)
                        totalPedonCnt += 1

            else:
                if theValue.startswith('<div id="ReportData">START'):
                    bValidRecord = True

            arcpy.SetProgressorPosition()

        #Resets the progressor back to its initial state
        arcpy.ResetProgressor()

        if len(pedonDict) == 0:
            AddMsgAndPrint("\tThere were no pedons found in this area; Try using a larger extent",1)
            return False

        else:
            #AddMsgAndPrint("\tThere are a total of " + splitThousands(totalPedonCnt) + " pedons found in this area:")
            AddMsgAndPrint("\tThere are " + splitThousands(totalPedonCnt) + " within this layer:")
            AddMsgAndPrint("\t\tLAB Pedons: " + splitThousands(labPedonCnt))
            AddMsgAndPrint("\t\tUndisclosed: " + splitThousands(undisclosed))
            AddMsgAndPrint("\t\tNASIS Pedons: " + splitThousands((totalPedonCnt - labPedonCnt) - undisclosed))

            return True

    except:
        errorMsg()
        return False

## ================================================================================================================
def filterPedonsByFeature(feature):
    """ This function will temporarily plot out the pedons in order to determine which pedons fall completely
        within the user's AOI.  Once determined, the extra pedons will be removed from the pedonDict"""

    try:
        AddMsgAndPrint("\nSelecting pedons that intersect with " + arcpy.Describe(feature).Name + " Layer",0)
        arcpy.SetProgressorLabel("Selecting pedons that intersect with " + arcpy.Describe(feature).Name + " Layer")

        #arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

        # Make a copy of the user-input features - this is just in case there is a selected set
        aoiFeature = arcpy.CreateScratchName("aoiFeature",data_type="FeatureClass", workspace=scratchWS)
        arcpy.CopyFeatures_management(feature,aoiFeature)

        # Create a temp point feature class to digitize ALL of the pedons within the bounding box first
        tempPoints = arcpy.CreateScratchName("tempPoints",data_type="FeatureClass", workspace=scratchWS)

        # Factory code for WGS84 Coordinate System
        spatial_reference = arcpy.SpatialReference(4326)
        #spatial_reference = arcpy.Describe(feature).spatialReference
        arcpy.CreateFeatureclass_management(scratchWS, os.path.basename(tempPoints), "POINT", "#", "DISABLED", "DISABLED", spatial_reference)

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

        tempPointsPRJ = arcpy.CreateScratchName("tempPointsPRJ",data_type="FeatureClass", workspace=scratchWS)
        arcpy.Project_management(tempPoints,tempPointsPRJ,arcpy.Describe(feature).spatialReference)
        arcpy.SetProgressorLabel("Selecting pedons that intersect with " + arcpy.Describe(feature).Name + " Layer")  # Some odd reason 'tempPointsPRJ' stays frozen in the progress bar.

        # Select all of the pedons within the user's AOI
        tempPointsLYR = arcpy.CreateScratchName("tempPointsLYR",data_type="FeatureClass", workspace=scratchWS)
        arcpy.MakeFeatureLayer_management(tempPointsPRJ,tempPointsLYR)

        #AddMsgAndPrint("\tThere are " + str(int(arcpy.GetCount_management("tempPoints_LYR").getOutput(0))) + " pedons in the layer",2)
        arcpy.SelectLayerByLocation_management(tempPointsLYR,"INTERSECT",aoiFeature, "","NEW_SELECTION")

        pedonsWithinAOI = int(arcpy.GetCount_management(tempPointsLYR).getOutput(0))

        # There are pedons within the user's AOI
        if pedonsWithinAOI > 0:
            AddMsgAndPrint("\tThere are " + splitThousands(pedonsWithinAOI) + " pedons within this layer",0)

            # Make a copy of the user-input features - this is just in case there is a selected set
            selectedPedons = arcpy.CreateScratchName("selectedPedons",data_type="FeatureClass", workspace=scratchWS)
            arcpy.CopyFeatures_management(tempPointsLYR,selectedPedons)

            # Create a new list of pedonIDs from the selected set; pedonIDs are converted to strings in order
            # to compare against the pedonDict()
            selectedPedonsList = [str(row[0]) for row in arcpy.da.SearchCursor(selectedPedons, (peiidFld))]

            # Make a copy of pedonDict b/c it cannot change during iteration
            pedonDictCopy = pedonDict.copy()

            # delete any pedon from the original pedonDict that is not in the selected set.
            labPedonCnt = 0
            for pedon in pedonDictCopy:
                if pedon not in selectedPedonsList:
                    del pedonDict[pedon]
                else:
                    if not pedonDict[pedon][1] is None:
                        labPedonCnt+=1

            AddMsgAndPrint("\t\tLAB Pedons: " + splitThousands(labPedonCnt))
            AddMsgAndPrint("\t\tNASIS Pedons: " + splitThousands(pedonsWithinAOI - labPedonCnt))

            for layer in (aoiFeature,tempPoints,tempPointsPRJ,tempPointsLYR,selectedPedons):
                if arcpy.Exists(layer):
                    arcpy.Delete_management(layer)

            del pedonDictCopy,selectedPedons,selectedPedonsList

            return pedonsWithinAOI

        else:
            AddMsgAndPrint("\tThere are NO pedons that are completely within your AOI. EXITING! \n",2)
            exit()

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (filterPedonsByFeature). EXITING!", 2)
        errorMsg()
        return False

## ================================================================================================================
def createPedonFGDB():
    """This Function will create a new File Geodatabase using a pre-established XML workspace
       schema.  All Tables will be empty and should correspond to that of the access database.
       Relationships will also be pre-established.
       Return false if XML workspace document is missing OR an existing FGDB with the user-defined
       name already exists and cannot be deleted OR an unhandled error is encountered.
       Return the path to the new Pedon File Geodatabase if everything executes correctly."""

    try:
        AddMsgAndPrint("\nCreating New Pedon File Geodatabase",0)
        arcpy.SetProgressorLabel("Creating New Pedon File Geodatabase")

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "NASISpedons_XMLWorkspace.xml"
        localPedonGDB = os.path.dirname(sys.argv[0]) + os.sep + "NasisPedonsTemplate.gdb"

        # Return false if pedon fGDB template is not found
        if not arcpy.Exists(localPedonGDB):
            AddMsgAndPrint("\t" + os.path.basename(localPedonGDB) + " FGDB template was not found!",2)
            return False

        newPedonFGDB = os.path.join(outputFolder,GDBname + ".gdb")

        if arcpy.Exists(newPedonFGDB):
            try:
                arcpy.Delete_management(newPedonFGDB)
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Deleting and re-creating FGDB\n",1)
            except:
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Failed to delete\n",2)
                return False

        # copy template over to new location
        AddMsgAndPrint("\tCreating " + GDBname + ".gdb with NCSS Pedon Schema 7.3")
        arcpy.Copy_management(localPedonGDB,newPedonFGDB)

        """ ------------------------------ Code to use XML Workspace -------------------------------------------"""
##        # Return false if xml file is not found
##        if not arcpy.Exists(pedonXML):
##            AddMsgAndPrint("\t" + os.path.basename(pedonXML) + " Workspace document was not found!",2)
##            return False
##
##        # Create empty temp File Geodatabae
##        arcpy.CreateFileGDB_management(outputFolder,os.path.splitext(os.path.basename(newPedonFGDB))[0])
##
##        # set the pedon schema on the newly created temp Pedon FGDB
##        AddMsgAndPrint("\tImporting NCSS Pedon Schema 7.3 into " + GDBname + ".gdb")
##        arcpy.ImportXMLWorkspaceDocument_management(newPedonFGDB, pedonXML, "DATA", "DEFAULTS")

        arcpy.UncompressFileGeodatabaseData_management(newPedonFGDB)
        arcpy.RefreshCatalog(outputFolder)
        AddMsgAndPrint("\tSuccessfully created: " + GDBname + ".gdb")

        return newPedonFGDB

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        return False

## ===============================================================================================================
def getTableAliases(pedonFGDBloc):
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores physical names (key) and aliases (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}
    # Fieldnames are Physical Name = AliasName,IEfilename

    try:

        arcpy.SetProgressorLabel("Gathering Table and Field aliases")

        # Open Metadata table containing information for other pedon tables
        theMDTable = pedonFGDBloc + os.sep + "MetadataTable"
        arcpy.env.workspace = pedonFGDBloc

        # Establishes a cursor for searching through field rows. A search cursor can be used to retrieve rows.
        # This method will return an enumeration object that will, in turn, hand out row objects
        if not arcpy.Exists(theMDTable):
            return False

        tableList = arcpy.ListTables("*")
        tableList.append("pedon")

        nameOfFields = ["TablePhysicalName","TableLabel"]

        for table in tableList:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            expression = arcpy.AddFieldDelimiters(theMDTable,"TablePhysicalName") + " = '" + table + "'"
            with arcpy.da.SearchCursor(theMDTable,nameOfFields, where_clause = expression) as cursor:

                for row in cursor:
                    # read each table record and assign 'TablePhysicalName' and 'TableLabel' to 2 variables
                    physicalName = row[0]
                    aliasName = row[1]

                    # i.e. {phtexture:'Pedon Horizon Texture',phtexture}; will create a one-to-many dictionary
                    # As long as the physical name doesn't exist in dict() add physical name
                    # as Key and alias as Value.
                    if not tblAliases.has_key(physicalName):
                        tblAliases[physicalName] = aliasName

                    del physicalName,aliasName

        del theMDTable,tableList,nameOfFields

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (GetTableAliases)", 2)
        errorMsg()
        return False

## ===============================================================================================================
def createEmptyDictOfTables():
    # Create a new dictionary called pedonGDBtablesDict that will contain every table in the newly created
    # pedonFGDB above as a key.  Individual records of tables will be added as values to the table keys.
    # These values will be in the form of lists.  This dictionary will be populated using the results of
    # the WEB_AnalysisPC_MAIN_URL_EXPORT NASIS report.  Much faster than opening and closing cursors every
    # a request is made to nasis.  URL report contents will be parsed out to this dictionary.
    # {'area': [],'areatype': [],'basalareatreescounted': [],'beltdata': [],'belttransectsummary': []........}

    try:

        arcpy.env.workspace = pedonFGDB
        tables = arcpy.ListTables()
        tables.append(arcpy.ListFeatureClasses('pedon','Point')[0])  ## pedon is a feature class and gets excluded by the ListTables function

        # Create dictionary where keys will be tables and values will be later populated
        # {'area': [],'areatype': [],'basalareatreescounted': [],'beltdata': [],'belttransectsummary': []........}
        pedonGDBtablesDict = dict()

        for table in tables:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue
            pedonGDBtablesDict[str(table)] = []

        del tables
        return pedonGDBtablesDict

    except:
        AddMsgAndPrint("\nUnhandled exception (GetTableAliases)\n", 2)
        errorMsg()
        exit()

## ===============================================================================================================
def createTableFieldLookuup():
    # This function will create a dictionary that will contain table:number of fields in order
    # to double check that the values from the web report are correct. This was added b/c there
    # were text fields that were getting disconnected in the report and being read as 2 lines
    # and Jason couldn't address this issue in NASIS.  This also serves as a QC against values
    # have an incorrect number of values relative to the available fields.  This has been a problem
    # with values having a pipe (|) which causes a problem with splitting values.

    try:

        arcpy.env.workspace = pedonFGDB

        tableInfoDict = dict()    # contains all valid tables and the number of fields that it contains i.e. petext:11
        validTables = arcpy.ListTables("*")
        validTables.append('pedon')

        for table in validTables:

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            uniqueFields = arcpy.Describe(os.path.join(pedonFGDB,table)).fields
            numOfValidFlds = 0

            for field in uniqueFields:
                if not field.type.lower() in ("oid","geometry","FID"):
                    numOfValidFlds +=1

            # Add 2 more fields to the pedon table for X,Y
            if table == 'pedon':
                numOfValidFlds += 2

            tableInfoDict[table] = numOfValidFlds
            del uniqueFields;numOfValidFlds

        return tableInfoDict

    except:
        AddMsgAndPrint("\nUnhandled exception (createTableFieldLookup)\n", 2)
        errorMsg()
        exit()


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
        pedonIDstr = ""

        for pedonID in pedonDict:

            # End of pedon list has been reached
            if i == len(pedonDict):
                pedonIDstr = pedonIDstr + str(pedonID)
                listOfPedonStrings.append(pedonIDstr)

            # End of pedon list NOT reached
            else:
                # Max URL length reached - retrieve pedon data and start over
                if len(pedonIDstr) > 1860:
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
            AddMsgAndPrint("\n\t Something Happened here.....WTF!",2)
            exit()

        else:
            return listOfPedonStrings,numOfPedonStrings

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        exit()

## ================================================================================================================
def getPedonHorizon(pedonList):

    # To view a sample output report go to:
    # https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=14542

    try:

        if numOfPedonStrings > 1:
            tab = "\t\t"
        else:
            tab = "\t"

        """----------------------------------- Open a network object --------------------------------"""
        ''' Open a network object using the URL with the search string already concatenated.
            As soon as the url is opened it needs to be read otherwise there will be a socket
            error raised.  Experienced this when the url was being opened before the above
            dictionary was created.  Bizarre'''

        URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=' + pedonList

        requestStartTime = tic()

        try:
            theReport = urlopen(URL).readlines()
        except:
            try:
                AddMsgAndPrint(tab + "2nd attempt at requesting data - 15 second pause")
                time.sleep(15)
                theReport = urlopen(URL).readlines()
            except:
                try:
                    AddMsgAndPrint(tab + "3rd attempt at requesting data - 30 second pause")
                    time.sleep(30)
                    theReport = urlopen(URL).readlines()
                except:
                    errorMsg()
                    return False

        #AddMsgAndPrint(tab + "Network Request Time: " + toc(requestStartTime))

        invalidTable = 0    # represents tables that don't correspond with the GDB
        invalidRecord = 0  # represents records that were not added
        validRecord = 0

        bHeader = False         # flag indicating if value is html junk
        currentTable = ""       # The table found in the report
        numOfFields = ""        # The number of fields a specific table should contain
        partialValue = ""       # variable containing part of a value that is not complete
        originalValue = ""      # variable containing the original incomplete value
        bPartialValue = False   # flag indicating if value is incomplete; append next record

        """ ------------------- Begin Adding data from URL into a dictionary of lists ---------------"""
        # iterate through the lines in the report
        arcpy.SetProgressor("step", "Reading NASIS Report: 'WEB_AnalysisPC_MAIN_URL_EXPORT'", 0, len(theReport),1)

        #memoryStartTime = tic()
        for theValue in theReport:

            theValue = theValue.strip() # remove whitespace characters

            # represents the start of valid table
            if theValue.find('@begin') > -1:
                theTable = theValue[theValue.find('@') + 7:]  ## Isolate the table
                numOfFields = tableFldDict[theTable]

                # Check if the table name exists in the list of dictionaries
                # if so, set the currentTable variable and bHeader
                if pedonGDBtablesDict.has_key(theTable):
                    currentTable = theTable
                    bHeader = True  ## Next line will be the header

                else:
                    AddMsgAndPrint("\t" + theTable + " Does not exist in the FGDB schema!  Figure this out Jason Nemecek!",2)
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
                        pedonGDBtablesDict[currentTable].append(partialValue)
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
                        AddMsgAndPrint("\t\tIncorrectly formatted Record Found in " + currentTable + " table:",2)
                        AddMsgAndPrint("\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(len(partialValue.split('|'))),2)
                        AddMsgAndPrint("\t\t\tOriginal Record: " + originalValue,2)
                        AddMsgAndPrint("\t\t\tAppended Record: " + partialValue,2)
                        invalidRecord += 1
                        bPartialValue = False
                        partialValue,originalValue = ""

                # number of values do not equal the number of fields in the corresponding tables
                elif numOfValues != numOfFields:

                    # number of values exceed the number of fields; Big Error
                    if numOfValues > numOfFields:
                        AddMsgAndPrint("\n\t\tIncorrectly formatted Record Found in " + currentTable + " table:",2)
                        AddMsgAndPrint("\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(numOfValues),2)
                        AddMsgAndPrint("\t\t\tRecord: " + theValue,2)
                        invalidRecord += 1

                    # number of values falls short of the number of correct fields
                    else:
                        partialValue,originalValue = theValue,theValue
                        bPartialValue = True

                else:
                    pedonGDBtablesDict[currentTable].append(theValue)
                    validRecord += 1
                    bPartialValue = False
                    partialValue = ""

            elif theValue.find("ERROR") > -1:
                AddMsgAndPrint("\n\t\t" + theValue[theValue.find("ERROR"):],2)
                return False

            else:
                invalidRecord += 1

            arcpy.SetProgressorPosition()

        #Resets the progressor back to its initial state
        arcpy.ResetProgressor()

        #AddMsgAndPrint(tab + "Storing Data into Memory: " + toc(memoryStartTime))

        if not validRecord:
            AddMsgAndPrint("\t\tThere were no valid records captured from NASIS request",2)
            return False

        # Report any invalid tables found in report; This should take care of itself as Jason perfects the report.
        if invalidTable and invalidRecord:
            AddMsgAndPrint("\t\tThere were " + splitThousands(invalidTable) + " invalid table(s) included in the report with " + splitThousands(invalidRecord) + " invalid record(s)",1)

        # Report any invalid records found in report; There are 27 html lines reserved for headers and footers
        if invalidRecord > 28:
            AddMsgAndPrint("\t\tThere were " + splitThousands(invalidRecord) + " invalid record(s) not captured",1)

        return True

    except URLError, e:
        if hasattr(e, 'reason'):
            AddMsgAndPrint(tab + "URL Error: " + str(e.reason), 2)

        elif hasattr(e, 'code'):
            AddMsgAndPrint(tab + e.msg + " (errorcode " + str(e.code) + ")", 2)

        return False

    except socket.timeout, e:
        AddMsgAndPrint(tab + "Server Timeout Error", 2)
        return False

    except socket.error, e:
        AddMsgAndPrint(tab + "NASIS Reports Website connection failure", 2)
        return False

    except httplib.BadStatusLine:
        AddMsgAndPrint(tab + "NASIS Reports Website connection failure", 2)
        return False

    except:
        errorMsg()
        return False

## ================================================================================================================
def importPedonData(tblAliases,verbose=False):
    """ This function will purge the contents from the pedonGDBtablesDict dictionary which contains all of the pedon
        data into the pedon FGDB.  Depending on the number of pedons in the user's AOI, this function will be
        used multiple times.  The pedonGDBtablesDict dictionary could possilbly allocate all of the computer's
        memory so a fail-save was built in to make sure a memory exception error wasn't encountered.  This
        function is invoked when approximately 40,000 pedons have been retrieved from the server and stored in \
        memory."""

    try:
        if verbose: AddMsgAndPrint("\nImporting Pedon Data into FGDB")
        arcpy.SetProgressorLabel("Importing Pedon Data into FGDB")

        # use the tblAliases so that tables are imported in alphabetical order
        if bAliasName:
            tblKeys = tblAliases.keys()
            maxCharTable = max([len(table) for table in tblKeys]) + 1
            maxCharAlias = max([len(value[1]) for value in tblAliases.items()])

            firstTab = (maxCharTable - len("Table Physical Name")) * " "
            headerName = "\n\tTable Physical Name" + firstTab + "Table Alias Name"
            if verbose: AddMsgAndPrint(headerName,0)
            if verbose: AddMsgAndPrint("\t" + len(headerName) * "=",0)

        else:
            maxCharTable = max([len(table) for table in tblKeys]) + 1
            tblKeys = pedonGDBtablesDict.keys()

        tblKeys.sort()

        """ ---------------------------------------------------"""
        arcpy.SetProgressor("step","Importing Pedon Data into FGDB table: ",0,len(tblKeys),1)
        for table in tblKeys:

            arcpy.SetProgressorLabel("Importing Pedon Data into FGDB: " + table)
            arcpy.SetProgressorPosition()

            # Skip any Metadata files
            if table.find('Metadata') > -1: continue

            # Capture the alias name of the table
            if bAliasName:
                aliasName = tblAliases[table]

            # Strictly for standardizing reporting
            firstTab = (maxCharTable - len(table)) * " "

            # check if list contains records to be added
            if len(pedonGDBtablesDict[table]):

                numOfRowsAdded = 0
                GDBtable = pedonFGDB + os.sep + table # FGDB Pyhsical table path

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
                if table == 'pedon':

##                    labField = 'labsampleIndicator'
##                    arcpy.AddField_management(GDBtable,'labsampleIndicator','TEXT','#','#',3,'Lab Sample Indicator','#','#','#')
##                    nameOfFields.append(labField)

                    # Pedon feature class will have X,Y geometry added; Add XY token to list
                    nameOfFields.append('SHAPE@XY')
                    fldLengths.append(0)  # X coord
                    fldLengths.append(0)  # Y coord

##                    peiidFld = [f.name for f in arcpy.ListFields(table,'peiid')][0]
##                    peiidIndex = nameOfFields.index(peiidFld)


                """ -------------------------------- Insert Rows ------------------------------------------
                    Iterate through every value from a specific table in the pedonGDBtablesDict dictary
                    and add it to the appropriate FGDB table  Truncate the value if it exceeds the
                    max number of characters.  Set the value to 'None' if it is an empty string."""

                # Initiate the insert cursor object using all of the fields
                cursor = arcpy.da.InsertCursor(GDBtable,nameOfFields)
                recNum = 0

                # '"S1962WI025001","43","15","9","North","89","7","56","West",,"Dane County, Wisconsin. 100 yards south of road."'
                for rec in pedonGDBtablesDict[table]:

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
                    if table == 'pedon':
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
                        AddMsgAndPrint("\n\tError in :" + table + " table: Field No: " + str(fldNo) + " : " + str(rec),2)
                        AddMsgAndPrint("\n\t" + arcpy.GetMessages(2),2)
                        break
                    except:
                        AddMsgAndPrint("\n\tError in: " + table + " table")
                        print "\n\t" + str(rec)
                        print "\n\tRecord Number: " + str(recNum)
                        AddMsgAndPrint("\tNumber of Fields in GDB: " + str(len(nameOfFields)))
                        AddMsgAndPrint("\tNumber of fields in report: " + str(len([rec.split('|')][0])))
                        errorMsg()
                        break

                    del newRow,fldNo

                # Report the # of records added to the table
                if bAliasName:
                    secondTab = (maxCharAlias - len(aliasName)) * " "
                    if verbose: AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: " + splitThousands(numOfRowsAdded),1)
                else:
                    if verbose: AddMsgAndPrint("\t" + table + firstTab + " Records Added: " + splitThousands(numOfRowsAdded),1)

                del numOfRowsAdded,GDBtable,fieldList,nameOfFields,fldLengths,cursor

            # Table had no records; still print it out
            else:
                if bAliasName:
                    secondTab = (maxCharAlias - len(aliasName)) * " "
                    if verbose: AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: 0",1)
                else:
                    if verbose: AddMsgAndPrint("\t" + table + firstTab + " Records Added: 0",1)

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
# Used to get a number of pedons that are within a bounding box
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_ANALYSIS_PC_PEDON_NUMBER_SUM&lat1=43&lat2=45&long1=-90&long2=-88

""" 2nd Report """
# Used to get a list of peiid which will be passed over to the 2nd report0
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_EXPORT_PEDON_BOX_COUNT&lat1=43&lat2=45&long1=-90&long2=-88

""" 3rd Report """
# This report will contain pedon information to be parsed into a FGDB.

# Raw URL
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=TEST_sub_pedon_pc_6.1_phorizon&pedonid_list=    OLD one
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=    NEW one

# Sample complete URL with pedonIDs:
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_AnalysisPC_MAIN_URL_EXPORT&pedonid_list=36186,59976,60464,60465,101219,102867,106105,106106
#===================================================================================================================================


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy, socket, httplib, time
from arcpy import env
from urllib2 import urlopen, URLError, HTTPError
from sys import getsizeof, stderr
from itertools import chain
from collections import deque

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

if __name__ == '__main__':

    try:

        inputFeatures = arcpy.GetParameter(0)
        GDBname = arcpy.GetParameter(1)
        outputFolder = arcpy.GetParameterAsText(2)

##        inputFeatures = r'E:\SSURGO\WI025\spatial\soilsa_a_wi025.shp'
##        GDBname = 'Dane_Original'
##        outputFolder = r'E:\Pedons\Temp'

        """ ------------------------------------------------------------------------ Set Scratch Workspace -------------------------------------------------------------------------------------"""
        scratchWS = setScratchWorkspace()
        arcpy.env.scratchWorkspace = scratchWS

        if not scratchWS:
            AddMsgAndPrint("\n Failed to scratch workspace; Try setting it manually",2)
            exit()

        """ ---------------------------------------------------------------------- Get Bounding box coordinates -----------------------------------------------------------------------------------"""
        #Lat1 = 43.8480050291613;Lat2 = 44.196269661256736;Long1 = -93.76788085724957;Long2 = -93.40649833646484;
        Lat1,Lat2,Long1,Long2 = getBoundingCoordinates(inputFeatures)

        if not Lat1:
            AddMsgAndPrint("\nFailed to acquire Lat/Long coordinates to pass over; Try a new input feature",2)
            exit()

        coordStr = "&Lat1=" + str(Lat1) + "&Lat2=" + str(Lat2) + "&Long1=" + str(Long1) + "&Long2=" + str(Long2)

        """ ----------------------------------------------- Get a number of PedonIDs that are within the bounding box from NASIS ------------------------------------------------------------------
            ---------------------------------------------------- Uses the 'WEB_ANALYSIS_PC_PEDON_NUMBER_SUM' NASIS report --------------------------------------------------------------------------"""
        areaPedonCount = getWebPedonNumberSum(coordStr)

        if areaPedonCount:
            AddMsgAndPrint("\tThere are " + splitThousands(areaPedonCount) + " pedons within the bounding coordinates",0)
        else:
            AddMsgAndPrint("\nThere are no records found within the area of interest.  Try using a larger area",2)
            exit()

        """ -------------------------------------------------- Get a list of PedonIDs that are within the bounding box from NASIS -----------------------------------------------------------------
            ---------------------------------------------------- Uses the 'WEB_EXPORT_PEDON_BOX_COUNT' NASIS report --------------------------------------------------------------------------"""

        # peiid: siteID,Labnum,X,Y
        #{'122647': ('84IA0130011', '85P0558', '-92.3241653', '42.3116684'), '883407': ('2014IA013003', None, '-92.1096600', '42.5332000')}
        pedonDict = dict()

        if not getWebExportPedon(coordStr):
            AddMsgAndPrint("\n\tFailed to get a list of pedonIDs from NASIS \n",2)
            exit()

        """ -------------------------------------------------- Filter pedons by those that fall completely within the user-input feature ---------------------------------------------------------"""
        totalPedons = filterPedonsByFeature(inputFeatures)

        if not totalPedons:
            AddMsgAndPrint("\n\tFailed to filter list of Pedons by Area of Interest. EXITING! \n",2)
            exit()

        """ ------------------------------------------------------Create New File Geodatabaes and get Table Aliases for printing -------------------------------------------------------------------
            Create a new FGDB using a pre-established XML workspace schema.  All tables will be empty
            and relationships established.  A dictionary of empty lists will be created as a placeholder
            for the values from the XML report.  The name and quantity of lists will be the same as the FGDB"""

        pedonFGDB = createPedonFGDB()
        arcpy.env.workspace = pedonFGDB

        if not pedonFGDB:
            AddMsgAndPrint("\nFailed to Initiate Empty Pedon File Geodatabase.  Error in createPedonFGDB() function. Exiting!",2)
            exit()

        # Acquire Table and Field Aliases.  This is only used for printing purposes
        tblAliases = dict()
        bAliasName = True

        if not getTableAliases(pedonFGDB):
            AddMsgAndPrint("\nCould not retrieve alias names from \'MetadataTable\'",1)
            bAliasName = False

        """ ------------------------------------------------------Create dictionary with all of the NASIS 7.3 tables  -------------------------------------------------------------------
            Create a new dictionary called pedonGDBtablesDict that will contain every table in the newly created
            pedonFGDB above as a key.  Individual records of tables will be added as values to the table keys.
            These values will be in the form of lists.  This dictionary will be populated using the results of
            the WEB_AnalysisPC_MAIN_URL_EXPORT NASIS report.  Much faster than opening and closing cursors."""

        pedonGDBtablesDict = createEmptyDictOfTables()

        """ --------------------------------------------------- Create a dictionary of number of fields per table -----------------------------------------------------------------------
            Create a dictionary that will contain table:number of fields in order
            to double check that the values from the web report are correct
            this was added b/c there were text fields that were getting disconnected in the report
            and being read as 2 lines -- Jason couldn't address this issue in NASIS """

        tableFldDict = createTableFieldLookuup()

        """ ------------------------------------------ Get Site, Pedon, and Pedon Horizon information from NASIS -------------------------------------------------------------------------
        ----------------------------------------------- Uses the 'WEB_AnalysisPC_MAIN_URL_EXPORT' NASIS report ---------------------------------------------------------------------------
        In order to request pedon information, the pedonIDs need to be split up into manageable
        lists of about 265 pedons due to URL limitations.  Submit these individual lists of pedon
        to the server """

        # Parse pedonIDs into lists containing about 265 pedons
        listOfPedonStrings,numOfPedonStrings = parsePedonsIntoLists()

        if numOfPedonStrings > 1:
            AddMsgAndPrint("\nDue to URL limitations there will be " + str(len(listOfPedonStrings))+ " seperate requests to NASIS:",1)
        else:
            AddMsgAndPrint("\n")

        i = 1                                         # represents the request number
        j = 0                                         # number of Pedons that are in memory;gets reset once dumped into FGDB
        k = 0                                         # number of total pedons that have been requested thus far

        badStrings = list()                           # lists containing lists of pedons that failed

        """ --------- iterate through groups of pedonIDs to retrieve their data"""
        requestTime = tic()
        for pedonString in listOfPedonStrings:

            numOfPedonsInPedonString = len(pedonString.split(','))
            j+=numOfPedonsInPedonString
            k+=numOfPedonsInPedonString

            """ Strictly for formatting print message """
            if numOfPedonStrings > 1:
                AddMsgAndPrint("\tRequest " + splitThousands(i) + " of " + splitThousands(numOfPedonStrings) + " for " + str(len(pedonString.split(','))) + " pedons",0)
                arcpy.SetProgressorLabel("Request " + splitThousands(i) + " of " + splitThousands(numOfPedonStrings) + " for " + str(len(pedonString.split(','))) + " pedons")
            else:
                AddMsgAndPrint("Retrieving pedon data from NASIS for " + str(len(pedonString.split(','))) + " pedons.",0)
                arcpy.SetProgressorLabel("Retrieving pedon data from NASIS for " + str(len(pedonString.split(','))) + " pedons.")

            """ Submit string of pedons to server """
            if not getPedonHorizon(pedonString):
                AddMsgAndPrint("\n\tFailed to receive pedon horizon info from NASIS",2)
                badStrings += pedonString
                k-=numOfPedonsInPedonString

            #AddMsgAndPrint("\t\tCurrent Size of pedonGDBtablesDict dictionary: " + getObjectSize(pedonGDBtablesDict, verbose=False),0)

            """ Import pedons from memory to the FGDB after about 40000 pedons have been requested to avoid Memory Errors"""
            if j > 40000  or i == numOfPedonStrings:

                # Only print if number of pedons exceed 40,000
                if not i == numOfPedonStrings:
                    AddMsgAndPrint("\n\tUnloading pedon data into FGDB to avoid memory issues. Current size: " + str(getObjectSize(pedonGDBtablesDict, verbose=False)) + " -- Number of Pedons: " + splitThousands(j) ,1)

                # Import Pedon Information into Pedon FGDB
                if len(pedonGDBtablesDict['pedon']):
                    AddMsgAndPrint("---------------- Request and organize info in dict: " + toc(requestTime))
                    populateFGDBTime = tic()
                    if not importPedonData(tblAliases,verbose=(True if i==numOfPedonStrings else False)):
                        exit()
                    AddMsgAndPrint("---------------- populate Pedon FGDB: " + toc(populateFGDBTime))

                    del pedonGDBtablesDict

                    # recreate pedonGDBtablesDict dictionary only if the requests are not done
                    if not i == numOfPedonStrings:
                        pedonGDBtablesDict = createEmptyDictOfTables()
                        j=0

            i+=1

        """ ------------------------------------ Report Summary of results -----------------------------------"""
        pedonTable = os.path.join(pedonFGDB,'pedon')
        pedonCount = int(arcpy.GetCount_management(pedonTable).getOutput(0))

        # Text file that will be created with pedonIDs that did not get collected
        errorFile = outputFolder + os.sep + os.path.basename(pedonFGDB).split('.')[0] + "_error.txt"

        if totalPedons == pedonCount:
            AddMsgAndPrint("\n\nSuccessfully downloaded " + splitThousands(totalPedons) + " pedons from NASIS",0)
        else:
            difference = totalPedons - pedonCount
            AddMsgAndPrint("\n\nDownloaded " + splitThousands(pedonCount) + " from NASIS",2)
            AddMsgAndPrint("\tFailed to download " + splitThousands(difference) + " pedons from NASIS:",2)

            downloadedPedons = [str(row[0]) for row in arcpy.da.SearchCursor(pedonTable,'peiid')]
            missingPedons = str(list(set(pedonList) - set(downloadedPedons))).replace('[','').replace(']','').replace('\'','')

            f = open(errorFile,'a+')
            if os.stat(errorFile).st_size == 0:
                f.write(str(missingPedons))
            else:
                f.write("," + str(missingPedons))
            f.close()

            if difference < 20:
                AddMsgAndPrint("\t\t" + missingPedons)

            AddMsgAndPrint("\n\tThe Missing Pedons have been written to " + errorFile + " files",2)

        """ ---------------------------Add Pedon Feature Class to ArcMap Session if available ------------------"""
        try:
            mxd = arcpy.mapping.MapDocument("CURRENT")
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            lyr = os.path.join(pedonFGDB,'pedon')
            newLayer = arcpy.mapping.Layer(lyr)
            arcpy.mapping.AddLayer(df, newLayer, "TOP")
            AddMsgAndPrint("\nAdded the pedon feature class to your ArcMap Session",0)
        except:
            pass

        AddMsgAndPrint("\n")

    except:
        errorMsg()
