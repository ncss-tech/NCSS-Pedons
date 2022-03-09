#-------------------------------------------------------------------------------
# Name:  NASISpedons_ExtractPedons_WFS.py
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Created:     1/10/2022
# Last Modified: 1/10/2022

# https://alexwlchan.net/2019/10/adventures-with-concurrent-futures/

# This tool is a modification of the NASISpedons_Extract_Pedons_from_NASIS _MultiThreading_ArcGISPro_SQL.py
# script.  It was modified\created for the purpose of mining all pedons from
# NASIS to update an existing Web Feature Service.  Only


## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print(msg)

##        try:
##            f = open(textFilePath,'a+')
##            f.write(msg + " \n")
##            f.close
##            del f
##        except:
##            pass

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
    try:
        return time.time()
    except:
        errorMsg()

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
def getDictionaryOfAllPedonIDs():
    # Description
    # This function will send a URL request to the 'Web Pedon PEIID List All of NASIS' NASIS
    # report to obtain a list of ALL pedons in NASIS.  Pedons include regular
    # NASIS pedons and LAB pedons.  Each record in the report will contain the following values:
    # START 1204126, 1204127, 1204128 STOP"""

    try:
        AddMsgAndPrint("Retrieving a list of ALL pedonIDs from NASIS")
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
def createPedonDB():
    """This Function will create a new File Geodatabase using a pre-established XML workspace
       schema.  All Tables will be empty and should correspond to that of the access database.
       Relationships will also be pre-established.
       Return false if XML workspace document is missing OR an existing FGDB with the user-defined
       name already exists and cannot be deleted OR an unhandled error is encountered.
       Return the path to the new Pedon File Geodatabase if everything executes correctly."""

    try:
        if sqliteFormat:
            AddMsgAndPrint("\nCreating New Pedon SQLite Database",0)
            arcpy.SetProgressorLabel("Creating New Pedon SQLite Database")
        else:
            AddMsgAndPrint("\nCreating New Pedon File Geodatabase",0)
            arcpy.SetProgressorLabel("Creating New Pedon File Geodatabase")

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "NASISpedons_XMLWorkspace.xml"

        if sqliteFormat:
            localPedonDB = os.path.dirname(sys.argv[0]) + os.sep + "NASISPedonsSQLiteTemplate.sqlite"
            ext = ".sqlite"
        else:
            localPedonDB = os.path.dirname(sys.argv[0]) + os.sep + "NASISPedonsFGDBTemplate_WFS.gdb"
            ext = ".gdb"

        # Return false if pedon fGDB template is not found
        if not arcpy.Exists(localPedonDB):
            AddMsgAndPrint("\t" + os.path.basename(localPedonDB) + ext + " template was not found!",2)
            return False

        newPedonDB = os.path.join(outputFolder,DBname + ext)

        if arcpy.Exists(newPedonDB):
            try:
                arcpy.Delete_management(newPedonDB)
                AddMsgAndPrint("\t" + os.path.basename(newPedonDB) + " already exists. Deleting and re-creating FGDB",1)
            except:
                AddMsgAndPrint("\t" + os.path.basename(newPedonDB) + " already exists. Failed to delete",2)
                return False

        # copy template over to new location
        # AddMsgAndPrint("\tCreating " + DBname + ext + " with NCSS Pedon Schema 7.3")
        arcpy.Copy_management(localPedonDB,newPedonDB)

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
##        AddMsgAndPrint("\tImporting NCSS Pedon Schema 7.3 into " + DBname + ".gdb")
##        arcpy.ImportXMLWorkspaceDocument_management(newPedonFGDB, pedonXML, "DATA", "DEFAULTS")

        #arcpy.UncompressFileGeodatabaseData_management(newPedonFGDB)
        AddMsgAndPrint("\tSuccessfully created: " + os.path.basename(newPedonDB))

        return newPedonDB

    except:
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
                        if not field.type.lower() in ("oid","geometry","FID"):
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
            AddMsgAndPrint("\n\t Something Happened here.....WTF!",2)
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

        bHeader = False         # flag indicating if value is html junk
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
                    pedonDBtablesDict[currentTable].append(theValue)
                    validRecord += 1
                    bPartialValue = False
                    partialValue = ""

            elif theValue.find("ERROR") > -1:
                AddMsgAndPrint("\n\t\t" + theValue[theValue.find("ERROR"):],2)
                return False

            else:
                invalidRecord += 1

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
        if verbose: AddMsgAndPrint("\nImporting Pedon Data into FGDB")
        arcpy.SetProgressorLabel("Importing Pedon Data into FGDB")

        # use the tableInfoDict so that tables are imported in alphabetical order
        tblKeys = tableInfoDict.keys()
        maxCharTable = max([len(table) for table in tblKeys]) + 1
        maxCharAlias = max([len(value[1][0]) for value in tableInfoDict.items()])

        firstTab = (maxCharTable - len("Table Physical Name")) * " "
        headerName = "\n\tTable Physical Name" + firstTab + "Table Alias Name"
        if verbose: AddMsgAndPrint(headerName,0)
        if verbose: AddMsgAndPrint("\t" + len(headerName) * "=",0)

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
                            #santaPedons+=1

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
                        AddMsgAndPrint("\tNumber of Fields in GDB: " + str(len(nameOfFields)))
                        AddMsgAndPrint("\tNumber of fields in report: " + str(len([rec.split('|')][0])))
                        errorMsg()
                        break

                    del newRow,fldNo

                # Report the # of records added to the table
##                if bAliasName:
                secondTab = (maxCharAlias - len(aliasName)) * " "
                if verbose: AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: " + splitThousands(numOfRowsAdded))
##                else:
##                    if verbose: AddMsgAndPrint("\t" + table + firstTab + " Records Added: " + splitThousands(numOfRowsAdded),1)

                del numOfRowsAdded,GDBtable,fieldList,nameOfFields,fldLengths,cursor

            # Table had no records; still print it out
            else:
                secondTab = (maxCharAlias - len(aliasName)) * " "
                if verbose: AddMsgAndPrint("\t" + table + firstTab + aliasName + secondTab + " Records Added: 0")

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
            #AddMsgAndPrint("\tRequest " + splitThousands(i) + " of " + splitThousands(numOfPedonStrings) + " for " + str(numOfPedonsInThisString) + " pedons")
            arcpy.SetProgressorLabel("Request " + splitThousands(i) + " of " + splitThousands(numOfPedonStrings) + " for " + str(numOfPedonsInThisString) + " pedons")
        else:
            #AddMsgAndPrint("Retrieving pedon data from NASIS for " + str(numOfPedonsInThisString) + " pedons.")
            arcpy.SetProgressorLabel("Retrieving pedon data from NASIS for " + str(numOfPedonsInThisString) + " pedons.")

        # update request number
        if not i == len(URLlist):
            i+=1  # request number

        response = urllib.request.urlopen(url)
        arcpy.SetProgressorLabel("")

        if response.code == 200:
            return response.readlines()
        else:
            AddMsgAndPrint("\nFailed to open URL: " + str(url),2)
            return None

    except URLError as e:
        AddMsgAndPrint('\tURL Error' + str(e),2)
        return None

    except HTTPError as e:
        AddMsgAndPrint('\tHTTP Error' + str(e),2)
        return None

    except socket.timeout as e:
        AddMsgAndPrint("\tServer Timeout Error", 2)
        return None

    except socket.error as e:
        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
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

## ===================================================================================
def overwritePedonLayer():

    try:
        AddMsgAndPrint("\nUpdating NASIS Pedon Web Feature Layer")
        overwriteStartTime = tic()

        # Set the path to the project
        prjFolder = r"N:\flex\NCSS_Pedons\NASIS_Pedons\Web_Feature_Service\NASIS_Pedons_WFS"
        aprxPath = f"{prjFolder}\\NASIS_Pedons_WFS.aprx"
        aprxMap = 'NASIS Pedon WFS Map'

        AGOL_sdName = r'NASIS_Pedons'                      # Name of service definition in AGOL w/out .sd
        sddraft = f"{prjFolder}\\NASIS_Pedon_WFS.sddraft"  # Output service definition draft file
        sd = f"{prjFolder}\\NASIS_Pedon_WFS_SD.sd"         # contains information to share a web layer

        if os.path.exists(sddraft):
            os.remove(sddraft)
        if os.path.exists(sd):
            os.remove(sd)

        # Set login credentials (user name is case sensitive, fyi)
        portal = r'https://nrcs.maps.arcgis.com'
        user = r'adolfo.diaz_nrcs'
        contrasena = base64.b64decode(b'd2FzaW1hbjIwMTA=')

        # Connect to NRCS AGOL Organizational account
        try:
            AddMsgAndPrint(f"\tConnecting to {portal}")
            gis = GIS(portal, user, contrasena)
            AddMsgAndPrint(f"\tSuccessfully logged in as: {gis.properties.user.username}")
        except:
            errorMsg()
            return False

        """ ------ Set up ArcGIS Pro session WFS paramaters --------"""
        aprx = arcpy.mp.ArcGISProject(aprxPath)
        maps = aprx.listMaps(aprxMap)[0]
        pedonLayer = maps.listLayers('NASIS Pedons')[0]

        arcpy.mp.CreateWebLayerSDDraft(pedonLayer, sddraft, AGOL_sdName, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS', True, True)
        AddMsgAndPrint(f"\tSuccessfully created Service Definition Draft file")
        arcpy.StageService_server(sddraft, sd)
        AddMsgAndPrint(f"\tSuccessfully staged Service Definition Draft file")


        """ ----- Update publication date and pedon count in Service Defintion Description ----"""
        # Get the serice definition that will be updated from AGOL
        # [<Item title:"NASIS Pedons" type:Service Definition owner:adolfo.diaz_nrcs>]
        NASISPedonSD = gis.content.search(query="title: NASIS Pedons", item_type="Service Definition")

        if len(NASISPedonSD):
            NASISPedonSDItem = NASISPedonSD[0]
            NASISPedonSDid = NASISPedonSDItem.id  # itemID of service definition '9b18c755acd6428d8d519fbb65765ee2'

        else:
            AddMsgAndPrint("\tCouldn't find service definition file for: \"NASIS Pedons\"")
            return False

##        # Open the metrics file and get the last pedon count and last date of publication
##        with open(metricsTextFile, 'r') as metFile:
##            last_line = metFile.readlines()[-1]
##
##        # ['February 09 2022', '11:19 AM', '54 minute(s): 25 second(s)', '763519', '0', '763519', 'Yes\n']
##        metrics = last_line.split(',')
##        lastPublishDate = metrics[0]
##        lastPedonCount = splitThousands(int(metrics[5]))
##
##        update1 = re.sub(lastPedonCount, splitThousands(totalPedons), NASISPedonSDdesc)
##        update2 = re.sub(lastPublishDate, date, update1)
##        descDict = dict()
##        descDict['description'] = update2

        # Update the pedon count and date of service definition description
        NASISPedonSDdesc = NASISPedonSDItem.description
        updateString = f"Currently, the NASIS Pedons feature layer contains {splitThousands(totalPedons)} pedons and was last updated {date} at {datetime.datetime.today().strftime(r'%I:%M %p')} CST."
        search1 = re.search(r'Currently, the NASIS',NASISPedonSDdesc)
        search2 = re.search(r'CST.',NASISPedonSDdesc)
        updatedDescription = NASISPedonSDdesc.replace(NASISPedonSDdesc[search1.start():search2.end()],updateString)
        #updatePedonCount = re.sub(r'(\d{3},\d{3})(?!\d)', splitThousands(totalPedons), NASISPedonSDdesc)

        descDict = dict()
        descDict['description'] = updatedDescription

        """ ----- Update the feature service -----"""
        updateItem = gis.content.get(NASISPedonSDid) # access an AGOL item using it's itemID
        updateItem.update(item_properties=descDict,data=sd)
        #updateItem.update(data=sd)
        fs = updateItem.publish(overwrite=True)

        overwriteEndTime = toc(overwriteStartTime)
        AddMsgAndPrint(f"Successfully updated {fs.title} Web Layer -- {overwriteEndTime}")

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
# Used to get a list of all pedonIDs in NASIS
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_PEDON_PEIID_LIST_ALL_OF_NASIS'

""" 2nd Report """
# Used to get pedon table information by pedonID list
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_Pedon_Web_Feature_Service


# Sample complete URL with pedonIDs:
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_Pedon_Web_Feature_Service&pedonid_list=36186,59976,60464,60465,101219,102867,106105,106106
#===================================================================================================================================


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy, socket, time, urllib, multiprocessing, requests, base64
from arcpy import env
from sys import getsizeof, stderr
from itertools import chain
from collections import deque
from datetime import date
from arcgis.gis import GIS

from urllib.error import HTTPError, URLError
from urllib.request import Request

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

if __name__ == '__main__':

    #test = getNASISbreakdownCounts()
    #exit()

    try:

        DBname = r'NASIS_Pedons_Interim'
        #outputFolder = r'N:\flex\NCSS_Pedons\NASIS_Pedons\Web_Feature_Service'
        outputFolder = r'E:\NCSS_Pedons\NASIS_Pedons_Metatdata_Update'
        FinalDB = f"{outputFolder}\\NASIS_Pedons_WFS_Final.gdb"
        sqliteFormat = False
        allPedons = True

        if sqliteFormat == True:
            prefix = "main."
        else:
            prefix = ""

        arcpy.env.parallelProcessingFactor = "100%"
        arcpy.env.overwriteOutput = True

        # Text file path
        textFilePath = outputFolder + os.sep + "NASIS_Pedon_WFS_logFile.txt"
        metricsTextFile = outputFolder + os.sep + "NASIS_Pedon_Metrics.txt"
        startTime = tic()

        # Formatting purposes - starts the logging
        AddMsgAndPrint("\n" + "=" * 90)
        now = datetime.datetime.today()
        date = now.strftime("%B %d %Y")
        hour = now.strftime("%I:%M %p")
        AddMsgAndPrint(f"{date} - {hour}")

        totalPedons = 773487
        overwritePedonLayer()
        exit()

        # User has chosen to donwload all pedons
        if allPedons:
            pedonDict = getDictionaryOfAllPedonIDs()
            totalPedons = len(pedonDict)
            #pedonDict = dict(d.items()[len(d)/2:])

            # --------------Just for testing; to limit number of pedons
##            tempDict = dict()
##            i = 0
##            for a in pedonDict.items():
##                tempDict[a[0]] = a[1]
##                i+=1
##                if i==2000:break
##            pedonDict = tempDict
##            totalPedons = len(pedonDict)
            # --------------End Testing

            AddMsgAndPrint("\nRequesting " + str(splitThousands(totalPedons)) + " pedons from NASIS")

            if not pedonDict:
                AddMsgAndPrint("\nFailed to obtain a list of ALL NASIS Pedon IDs",2)
                exit()

        # Create a FGDB or sqlite database
        pedonDB = createPedonDB()
        arcpy.env.workspace = pedonDB

        if not pedonDB:
            AddMsgAndPrint("\nFailed to Initiate Empty Pedon Database.  Error in createPedonDB() function. Exiting!",2)
            exit()

        # Create 2 Dictionaries that will be used throughout this script
        pedonDBtablesDict,tableFldDict = createReferenceObjects(pedonDB)

        if not tableFldDict:
            AddMsgAndPrint("\nCould not retrieve alias names from " + prefix + "\'MetadataTable\'",1)
            exit()

        """ ------------------------------------------ Get Site, Pedon, and Pedon Horizon information from NASIS -------------------------------------------------------------------------
        ----------------------------------------------- Uses the 'WEB_AnalysisPC_MAIN_URL_EXPORT' NASIS report ---------------------------------------------------------------------------
        In order to request pedon information, the pedonIDs need to be split up into manageable
        lists of about 265 pedons due to URL limitations.  Submit these individual lists of pedon
        to the server """

        # Parse pedonIDs into lists containing about 265 pedons
        listOfPedonStrings,numOfPedonStrings = parsePedonsIntoLists()

        if numOfPedonStrings > 1:
            AddMsgAndPrint("\nDue to URL limitations there will be " + splitThousands(len(listOfPedonStrings))+ " seperate requests to NASIS:",1)
        else:
            AddMsgAndPrint("\n")

        i = 1   # represents the request number; only used for ArcMap formatting

        multiThreadStartTime = tic()
        URLlist = list()              # List of unique URLs of pedonIDs
        futureResults = []            # List of html results from opening URLs

        # Iterate through a list of pedons strings to create a list of URLs by concatenating the URL
        # base with the pedon strings.
        for pedonString in listOfPedonStrings:
            URL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=WEB_Pedon_Web_Feature_Service&pedonid_list=' + pedonString
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

        santaPedons = 0

        # Import Pedon Information into Pedon FGDB
        if len(pedonDBtablesDict[prefix + 'pedon']):
            #if not importPedonData(tableFldDict,verbose=(True if i==numOfPedonStrings else False)):
            if not importPedonData(tableFldDict,verbose=False):
                exit()

        # Pedon FGDB path
        pedonDBfc = os.path.join(pedonDB,prefix + 'pedon')

        # Add Hyperlink to Pedon Description Report
        if addPedonReportHyperlink(pedonDBfc):
            AddMsgAndPrint("Successfully added Pedon Description Report Hyperlink")
        else:
            AddMsgAndPrint("Pedon Description Report Hyperlink Could not be added",2)

        """ ------------------------------------ Report Summary of results -----------------------------------"""
        pedonCount = int(arcpy.GetCount_management(pedonDBfc).getOutput(0))

        # Text file that will be created with pedonIDs that did not get collected
        errorFile = outputFolder + os.sep + os.path.basename(pedonDB).split('.')[0] + "_error.txt"

        if os.path.exists(errorFile):
            os.remove(errorFile)

        if totalPedons == pedonCount:
            AddMsgAndPrint("\nSuccessfully downloaded " + splitThousands(totalPedons) + " pedons from NASIS",0)

            # Copy pedon feature class to final DB
            if arcpy.Exists(FinalDB):
                finalPedonFC = f"{FinalDB}\\pedon"
                if arcpy.Exists(finalPedonFC):
                    arcpy.Delete_management(finalPedonFC)
                arcpy.CopyFeatures_management(pedonDBfc,finalPedonFC)
                AddMsgAndPrint("Successfully copied interim pedon FC to final FC")

        else:
            difference = totalPedons - pedonCount
            AddMsgAndPrint("\nDownloaded " + splitThousands(pedonCount) + " from NASIS",2)
            AddMsgAndPrint("\tFailed to download " + splitThousands(difference) + " pedons from NASIS:",2)

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

            AddMsgAndPrint("\n\tThe Missing Pedons have been written to " + errorFile + " files",2)

        # Delete Metadata Table
        if arcpy.Exists(os.path.join(pedonDB,'MetadataTable')):
            arcpy.Delete_management(os.path.join(pedonDB,'MetadataTable'))

        # If there were no missing pedons from the download process
        # proceed to updating the AGOL NASIS Pedon Web layer
        bUpdateWFS = False
        if totalPedons == pedonCount:

            bUpdateWFS = overwritePedonLayer()

            if not bUpdateWFS:
                # Attempt second time
                AddMsgAndPrint("\tAttempting 2nd attempt to update NAIS Pedon Hosted Feature layer")
                if not overwritePedonLayer():
                    AddMsgAndPrint("AGOL NASIS Pedon Web Feature Layer NOT updated due to errors in downloading process")

        else:
            AddMsgAndPrint("AGOL NASIS Pedon Web Feature Layer NOT updated due to errors in downloading process")

        # Stop the clock
        FinishTime = toc(startTime)
        AddMsgAndPrint("Total Time = " + str(FinishTime))

        #------------------ Update NASIS Metrics Log File
        m = open(metricsTextFile,'a+')
        m.write(f"{date},{hour},{FinishTime},{pedonCount},{len(missingPedons) if totalPedons != pedonCount else 0},{totalPedons},{'Yes' if bUpdateWFS else 'No'}")
        m.write("\n")
        m.close
        del m

    except:
        FinishTime = toc(startTime)
        AddMsgAndPrint("Total Time = " + str(FinishTime))
        errorMsg()
