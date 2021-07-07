#-------------------------------------------------------------------------------
# Name:        Extract_LDM_Pedons_from_SDA.py
# Purpose:     Download NCSS Lab Data Mart Pedons from Soil Data Access
#              Compliance process.

# Author: Adolfo.Diaz
#         GIS Specialist
#         National Soil Survey Center
#         USDA - NRCS
# e-mail: adolfo.diaz@usda.gov
# phone: 608.662.4422 ext. 216


# ==========================================================================================
# Updated  2/12/2021 - Adolfo Diaz
# - Hydric Classification Presence was added as an additional optional interpreation.
# - Added the simple soils geometry as a layer.
# - Added 'datetime' as a library to be imported; not sure why it was functioning
#   correclty without it.
# - replaced the reserved python keyword 'property' with soilProperty
# - slightly updated the metadata description

# ==========================================================================================
# Updated  4/7/2021 - Adolfo Diaz
# - Changed Hydric Rating interpretation from dominant condition to component frequency.
#   This uses Jason Nemecek's approach
# - Added URL to access Ecological Site Descriptions in EDIT database
# - Added SSURGO Metadata for spatial and tabular version to final output.

#-------------------------------------------------------------------------------



# ==============================================================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:

        print(msg)
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


# ==============================================================================================================================
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

# ==============================================================================================================================
def getSDATabularRequest(sqlQuery,layerPath):
    # Description
    # This function sends an SQL query to Soil Data Access and appends the results to a
    # layer.

    # Parameters
    # sqlQuery - A valid SDA SQL statement in ascii format
    # layerPath - Directory path to an existing spatial layer or table where the SDA results
    #             will be appended to.  The field names returned in the metadata portion
    #             of the JSON request will automatically be added to the layer

    # Returns
    # This function returns True if SDA results were successfully appended to the input
    # layer.  False otherwise.
    # Return Flase if an HTTP Error occurred such as a bad query, server timeout or no
    # response from server

    try:

        #uncomment next line to print interp query to console
        #arcpy.AddMessage(pQry.replace("&gt;", ">").replace("&lt;", "<"))

        # SDA url
        url = r'https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest'

        # Create request using JSON, return data as JSON
        request = {}
        request["format"] = "JSON+COLUMNNAME+METADATA"
        request["query"] = sqlQuery

        #json.dumps = serialize obj (request dictionary) to a JSON formatted str
        data = json.dumps(request)

        # Send request to SDA Tabular service using urllib library
        # because we are passing the "data" argument, this is a POST request, not a GET

        # ArcMap Request
        #req = urllib.Request(url, data)
        #response = urllib.urlopen(req)

        # ArcPro Request
        data = data.encode('ascii')
        response = urllib.request.urlopen(url,data)

        # read query results
        queryResults = response.read()

        # Convert the returned JSON string into a Python dictionary.
        qData = json.loads(queryResults)

        # if dictionary key "Table" is found
        if "Table" in qData:

            # extract 'Data' List from dictionary to create list of lists
            queryData = qData["Table"]

##            # remove the column names and column info lists from propRes list above
##            # Last element represents info for specific property
##            # [u'areasymbol', u'musym', u'muname', u'mukey', u'drainagecl']
##            # [u'ColumnOrdinal=0,ColumnSize=20,NumericPrecision=255,NumericScale=255,ProviderType=VarChar,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlString,DataTypeName=varchar',
##            columnNames = list()   # ['drainagecl']
##            columnInfo = list()
##            columnNames.append(propRes.pop(0)[-1])
##            columnInfo.append(propRes.pop(0)[-1])

            columnNames = queryData.pop(0)       # Isolate column names and remove from queryData
            columnInfo = queryData.pop(0)        # Isolate column info and remove from queryData
            mukeyIndex = columnNames.index('mukey') # list index of where 'mukey' is found
            propertyIndex = len(columnNames) -1     # list index of where property of interest is found; normally last place
            propertyFldName = columnNames[propertyIndex] # SSURGO field name of the property of interest

            # Add fields in columnNames to layerPath
            if not addSSURGOpropertyFld(layerPath, columnNames, columnInfo):
                return False

            # Get the expanded SSURGO field name of the property of interest
            fieldAlias = lookupSSURGOFieldName(propertyFldName,returnAlias=True)

            # Update the field alias if possible
            if fieldAlias:
                arcpy.AlterField_management(layerPath,propertyFldName,"#",fieldAlias)

            # rearrange queryData list into a dictionary of lists with the
            # mukey as key and tabular info as a list of values.  This will be used
            # in the UpdateCursor to lookup tabular info by MUKEY
            # '455428': [u'MN161','L110E','Lester-Ridgeton complex, 18 to 25 percent slopes','B']
            propertyDict = dict()

            for item in queryData:
                propertyDict[item[mukeyIndex]] = item

            # columnNames = [u'areasymbol', u'musym', u'muname', u'mukey', u'drainagecl']
            with arcpy.da.UpdateCursor(layerPath, columnNames) as cursor:
                for row in cursor:
                    mukey = row[mukeyIndex]

                    # lookup property info by MUKEY; Only update the property of interest
                    # No need to keep updating fields such as areasymbol, musym....etc
                    propertyVal = propertyDict[mukey][propertyIndex]
                    row[propertyIndex] = propertyVal

                    cursor.updateRow(row)

            return True

        else:
            AddMsgAndPrint("Failed to get tabular data (getSDATabularRequest)",2)
            return False

    except socket.timeout as e:
        AddMsgAndPrint('Soil Data Access timeout error',2)
        return False

    except socket.error as e:
        AddMsgAndPrint('Socket error: ' + str(e),2)
        return False

    except HTTPError as e:
        AddMsgAndPrint('HTTP Error' + str(e),2)
        return False

    except URLError as e:
        AddMsgAndPrint('URL Error' + str(e),2)
        return False

    except:
        errorMsg()
        return False


if __name__ == '__main__':

    try:

        import sys, os, time, urllib, json, traceback, socket, arcpy, datetime
        from arcpy import metadata as md

        from urllib.error import HTTPError, URLError
        from urllib.request import Request

        #sqlQuery = """SELECT * FROM lab_physical_properties;"""
        #sqlQuery = """SELECT COUNT labsampnum FROM lab_physical_properties;"""
        #sqlQuery = """SELECT TOP 10000 * FROM lab_physical_properties;"""
        #sqlQuery = """SELECT (labsampnum) FROM lab_physical_properties;"""
        #sqlQuery = """SELECT (labsampnum) FROM lab_physical_properties FOR JSON AUTO;"""


        sqlQuery = "~DeclareVarchar(@json,max)~\n"\
            ";WITH src (n) AS\n"\
            "(\n"\
            "    SELECT TOP 50 PERCENT *\n"\
            "    FROM lab_physical_properties sc1\n"\
            "    FOR JSON AUTO\n"\
            ")\n"\
            "SELECT @json = src.n\n"\
            "FROM src\n"\
            "SELECT @json, LEN(@json);"

##~DeclareVarchar(@json,max)~
##;WITH src (n) AS
##(
##    SELECT *
##    FROM lab_physical_properties sc1
##    FOR JSON AUTO
##)
##SELECT @json = src.n
##FROM src
##SELECT @json, LEN(@json);

        print(sqlQuery)

        # SDA url
        url = r'https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest'

        # Create request using JSON, return data as JSON
        request = {}
        #request["format"] = "JSON+COLUMNNAME+METADATA"
        request["format"] = "JSON"
        request["query"] = sqlQuery

        #json.dumps = serialize obj (request dictionary) to a JSON formatted str
        data = json.dumps(request)

        # Send request to SDA Tabular service using urllib library
        # because we are passing the "data" argument, this is a POST request, not a GET

        # ArcMap Request
        #req = urllib.Request(url, data)
        #response = urllib.urlopen(req)

        # ArcPro Request
        data = data.encode('ascii')
        response = urllib.request.urlopen(url,data)

        # read query results
        queryResults = response.read()

        # Convert the returned JSON string into a Python dictionary.
        qData = json.loads(queryResults)

    except HTTPError as e:
        content = e.read()
        print(content)

    except:
        errorMsg()





