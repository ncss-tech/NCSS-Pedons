#-------------------------------------------------------------------------------
# Name:        AGOL Pedons Download Pedons from AGOL
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     13/07/2021
# Copyright:   (c) Adolfo.Diaz 2021
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# ===================================================================================
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

# ===================================================================================
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

# ===================================================================================
def getPortalTokenInfo(portalURL):

    try:

        # Returns the URL of the active Portal
        # i.e. 'https://gis.sc.egov.usda.gov/portal/'
        activePortal = arcpy.GetActivePortalURL()

        # {'SSL_enabled': False, 'portal_version': 6.1, 'role': '', 'organization': '', 'organization_type': ''}
        #portalInfo = arcpy.GetPortalInfo(activePortal)

        # targeted portal is NOT set as default
        if activePortal != portalURL:

               # List of managed portals
               managedPortals = arcpy.ListPortalURLs()

               # portalURL is available in managed list
               if activePortal in managedPortals:
                   AddMsgAndPrint("\nYour Active portal is set to: " + activePortal,2)
                   AddMsgAndPrint("Set your active portal and sign into: " + portalURL,2)
                   return False

               # portalURL must first be added to list of managed portals
               else:
                    AddMsgAndPrint("\nYou must add " + portalURL + " to your list of managed portals",2)
                    AddMsgAndPrint("Open the Portals Tab to manage portal connections",2)
                    AddMsgAndPrint("For more information visit the following ArcGIS Pro documentation:",2)
                    AddMsgAndPrint("https://pro.arcgis.com/en/pro-app/help/projects/manage-portal-connections-from-arcgis-pro.htm",1)
                    return False

        # targeted Portal is correct; try to generate token
        else:

            # Get Token information
            tokenInfo = arcpy.GetSigninToken()

            # Not signed in.  Token results are empty
            if not tokenInfo:
                AddMsgAndPrint("\nYou are not signed into: " + portalURL,2)
                return False

            # Token generated successfully
            else:
                return tokenInfo

    except:
        errorMsg()
        return False

# ===================================================================================
def submitFSquery(url,INparams):
    """ This function will send a spatial query to a web feature service and convert
        the results into a python structure.  If the results from the service is an
        error due to an invalid token then a second attempt will be sent with using
        a newly generated arcgis token.  If the token is good but the request returned
        with an error a second attempt will be made.  The funciion takes in 2 parameters,
        the URL to the web service and a query string in URLencoded format.

        Error produced with invalid token
        {u'error': {u'code': 498, u'details': [], u'message': u'Invalid Token'}}

        The function returns requested data via a python dictionary"""
    try:

        INparams = INparams.encode('ascii')
        resp = urllib.request.urlopen(url,INparams)

        responseStatus = resp.getcode()
        responseMsg = resp.msg
        jsonString = resp.read()

        # json --> Python; dictionary containing 1 key with a list of lists
        results = json.loads(jsonString)

        # Check for expired token; Update if expired and try again
        if 'error' in results.keys():
           if results['error']['message'] == 'Invalid Token':
               AddMsgAndPrint("\tRegenerating ArcGIS Token Information")

               # Get new ArcPro Token
               newToken = arcpy.GetSigninToken()

               # Update the original portalToken
               global portalToken
               portalToken = newToken

               # convert encoded string into python structure and update token
               # by parsing the encoded query strting into list of (name, value pairs)
               # i.e [('f', 'json'),('token','U62uXB9Qcd1xjyX1)]
               # convert to dictionary and update the token in dictionary

               queryString = parseQueryString(params)

               requestDict = dict(queryString)
               requestDict.update(token=newToken['token'])

               newParams = urllibEncode(requestDict)

               if bArcGISPro:
                   newParams = newParams.encode('ascii')

               # update incoming parameters just in case a 2nd attempt is needed
               INparams = newParams

               # Python 3.6 - ArcPro
               if bArcGISPro:
                   resp = urllib.request.urlopen(url,newParams)  # A failure here will probably throw an HTTP exception
               else:
                   req = urllib2.Request(url,newParams)
                   resp = urllib2.urlopen(req)

               responseStatus = resp.getcode()
               responseMsg = resp.msg
               jsonString = resp.read()

               results = json.loads(jsonString)

        # Check results before returning them; Attempt a 2nd request if results are bad.
        if 'error' in results.keys() or len(results) == 0:
            time.sleep(5)

            if bArcGISPro:
                resp = urllib.request.urlopen(url,INparams)  # A failure here will probably throw an HTTP exception
            else:
                req = urllib2.Request(url,INparams)
                resp = urllib2.urlopen(req)

            responseStatus = resp.getcode()
            responseMsg = resp.msg
            jsonString = resp.read()

            results = json.loads(jsonString)

            if 'error' in results.keys() or len(results) == 0:
                AddMsgAndPrint("\t2nd Request Attempt Failed - Error Code: " + str(responseStatus) + " -- " + responseMsg + " -- " + str(results),2)
                return False
            else:
                return results

        else:
             return results

    except httpErrors as e:

        if int(e.code) >= 500:
           #AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Server side error. Probably exceed JSON imposed limit",2)
           #AddMsgAndPrint("t\t" + str(request))
           pass
        elif int(e.code) >= 400:
           #AddMsgAndPrint("\n\t\tHTTP ERROR: " + str(e.code) + " ----- Client side error. Check the following SDA Query for errors:",2)
           #AddMsgAndPrint("\t\t" + getGeometryQuery)
           pass
        else:
           AddMsgAndPrint('HTTP ERROR = ' + str(e.code),2)

    except:
        errorMsg()
        return False

# ===================================================================================
def createOutputFC(metadata,outputWS,shape="POLYGON"):
    """ This function will create an empty polygon feature class within the outputWS
        The feature class will be set to the same spatial reference as the Web Feature
        Service. All fields part of the WFS will also be added to the new feature class.
        A field dictionary containing the field names and their property will also be
        returned.  This fieldDict will be used to create the fields in the CLU fc and
        by the getCLUgeometry insertCursor.

        fieldDict ={field:(fieldType,fieldLength,alias)
        i.e {'clu_identifier': ('TEXT', 36, 'clu_identifier'),'clu_number': ('TEXT', 7, 'clu_number')}

        Return the field dictionary and new feature class including the path
        Return False if error ocurred."""

    try:
        # output FC will the 'CLU_' as a prefix along with AOI name
        newFC = outputWS + os.sep + "CLU_" + os.path.basename(AOI)

        AddMsgAndPrint("\nCreating New Feature Class: " + "CLU_" + os.path.basename(AOI))
        arcpy.SetProgressorLabel("Creating New Feature Class: " + "CLU_" + os.path.basename(AOI))

        # set the spatial Reference to same as WFS
        # Probably WGS_1984_Web_Mercator_Auxiliary_Sphere
        # {'spatialReference': {'latestWkid': 3857, 'wkid': 102100}
        spatialReferences = metadata['extent']['spatialReference']
        if 'latestWkid' in [sr for sr in spatialReferences.keys()]:
            sr = spatialReferences['latestWkid']
        else:
            sr = spatialReferences['wkid']

        outputCS = arcpy.SpatialReference(sr)

        # fields associated with feature service
        fsFields = metadata['fields']   # {u'alias':u'land_unit_id',u'domain': None, u'name': u'land_unit_id', u'nullable': True, u'editable': True, u'alias': u'LAND_UNIT_ID', u'length': 38, u'type': u'esriFieldTypeString'}
        fieldDict = dict()

        # lookup list for fields that are in DATE field; Date values need to be converted
        # from Unix Epoch format to mm/dd/yyyy format in order to populate a table
        dateFields = list()

        # cross-reference portal attribute description with ArcGIS attribute description
        fldTypeDict = {'esriFieldTypeString':'TEXT','esriFieldTypeDouble':'DOUBLE','esriFieldTypeSingle':'FLOAT',
                       'esriFieldTypeInteger':'LONG','esriFieldTypeSmallInteger':'SHORT','esriFieldTypeDate':'DATE',
                       'esriFieldTypeGUID':'GUID','esriFieldTypeGlobalID':'GUID'}

        # Collect field info to pass to new fc
        for fieldInfo in fsFields:

            # skip the OID field
            if fieldInfo['type'] == 'esriFieldTypeOID':
               continue

            fldType = fldTypeDict[fieldInfo['type']]
            fldAlias = fieldInfo['alias']
            fldName = fieldInfo['name']

            # skip the SHAPE_STArea__ and SHAPE_STLength__ fields
            if fldName.find("SHAPE_ST") > -1:
               continue

            if fldType == 'TEXT':
               fldLength = fieldInfo['length']
            elif fldType == 'DATE':
                 dateFields.append(fldName)
            else:
               fldLength = ""

            fieldDict[fldName] = (fldType,fldLength,fldAlias)

        # Delete newFC if it exists
        if arcpy.Exists(newFC):
           arcpy.Delete_management(newFC)
           AddMsgAndPrint("\t" + os.path.basename(newFC) + " exists.  Deleted")

        # Create empty polygon featureclass with coordinate system that matches AOI.
        arcpy.CreateFeatureclass_management(outputWS, os.path.basename(newFC), shape, "", "DISABLED", "DISABLED", outputCS)

        # Add fields from fieldDict to mimic WFS
        arcpy.SetProgressor("step", "Adding Fields to " + "CLU_" + os.path.basename(AOI),0,len(fieldDict),1)
        for field,params in fieldDict.items():
            try:
                fldLength = params[1]
                fldAlias = params[2]
            except:
                fldLength = 0
                pass

            arcpy.SetProgressorLabel("Adding Field: " + field)
            arcpy.AddField_management(newFC,field,params[0],"#","#",fldLength,fldAlias)
            arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()
        arcpy.SetProgressorLabel("")
        return fieldDict,newFC

    except:
        errorMsg()
        AddMsgAndPrint("\tFailed to create scratch " + newFC + " Feature Class",2)
        return False

# ===================================================================================
def createListOfJSONextents(inFC,RESTurl):
    """ This function will deconstruct the input FC into JSON format and determine if the
        clu count within this extent exceeds the max record limit of the WFS.  If the clu
        count exceeds the WFS limit then the incoming FC will continously be split
        until the CLU count is below WFS limit.  Each split will be an individual request
        to the WFS. Splits are done by using the subdivide polygon tool.

        The function will return a dictionary of JSON extents created from the individual
        splits of the original fc bounding box along with a CLU count for the request
        {'Min_BND': ['{"xmin":-90.1179,
                       "ymin":37.0066,
                       "xmax":-89.958,
                       "ymax":37.174,
                       "spatialReference":{"wkid":4326,"latestWkid":4326}}', 998]}

        Return False if jsonDict is empty"""

    try:
        # Dictionary containing JSON Extents to submit for geometry
        jsonDict = dict()

        # create JSON extent to send to REST URL to determine if
        # records requested exceed max allowable records.
        #jSONextent  = arcpy.da.Describe(inFC)['extent'].JSON

        # deconstructed AOI geometry in JSON
        jSONpolygon = [row[0] for row in arcpy.da.SearchCursor(inFC, ['SHAPE@JSON'])][0]

        params = urllibEncode({'f': 'json',
                               'geometry':jSONpolygon,
                               'geometryType':'esriGeometryPolygon',
                               'returnCountOnly':'true',
                               'token': portalToken['token']})

        # Get geometry count of incoming fc
        countQuery = submitFSquery(RESTurl,params)

        if not countQuery:
           AddMsgAndPrint("Failed to get estimate of CLU count",2)
           return False

        AddMsgAndPrint("\nThere are approximately " + splitThousands(countQuery['count']) + " CLUs within AOI")

        # if count is within max records allowed no need to proceed
        if countQuery['count'] <= maxRecordCount:
            jsonDict[os.path.basename(inFC)] = [jSONpolygon,countQuery['count']]

        # AOI bounding box will have to be continously split until polygons capture
        # CLU records below 1000 records.
        else:
            AddMsgAndPrint("Determining # of WFS requests")

            numOfAreas = int(countQuery['count'] / 800)  # How many times the input fc will be subdivided initially
            splitNum = 0                   # arbitrary number to keep track of unique files
            subDividedFCList = list()      # list containing recycled fcs to be split
            subDividedFCList.append(inFC)  # inFC will be the first one to be subdivided

            # iterate through each polygon in fc in list and d
            for fc in subDividedFCList:
                arcpy.SetProgressorLabel("Determining # of WFS requests. Current #: " + str(len(jsonDict)))

                # Subdivide fc into 2
                subdivision_fc = "in_memory" + os.sep + os.path.basename(arcpy.CreateScratchName("subdivision",data_type="FeatureClass",workspace=scratchWS))
                #subdivision_fc = r'O:\scratch\scratch.gdb\subdivision'

                if splitNum > 0:
                   numOfAreas = 2

                arcpy.SubdividePolygon_management(fc,subdivision_fc,"NUMBER_OF_EQUAL_PARTS",numOfAreas, "", "", "", "STACKED_BLOCKS")

                # first iteration will be the inFC and don't wnat to delete it
                if splitNum > 0:
                   arcpy.Delete_management(fc)

                # Add new fld to capture unique name used for each subdivided polygon which the
                # splitByAttributes tool will use.
                newOIDfld = "objectID_TEXT"
                expression = "assignUniqueNumber(!" + arcpy.Describe(subdivision_fc).OIDFieldName + "!)"
                randomNum = str(random.randint(1,9999999999))

                # code block doesn't like indentations
                codeBlock = """
def assignUniqueNumber(oid):
    return \"request_\" + str(""" + str(randomNum) + """) + str(oid)"""

                if not len(arcpy.ListFields(subdivision_fc,newOIDfld)) > 0:
                    arcpy.AddField_management(subdivision_fc,newOIDfld,"TEXT","#","#","30")

                arcpy.CalculateField_management(subdivision_fc,newOIDfld,expression,"PYTHON3",codeBlock)
                splitNum+=1

                # Create a fc for each subdivided polygon
                # split by attributes was faster by 2 secs than split_analysis
                arcpy.SplitByAttributes_analysis(subdivision_fc,scratchWS,[newOIDfld])
                arcpy.Delete_management(subdivision_fc)

                # Create a list of fcs that the split tool outputs
                arcpy.env.workspace = scratchWS
                #arcpy.env.workspace = "in_memory"
                #arcpy.env.workspace = r'O:\scratch\scratch.gdb'

                splitFCList = arcpy.ListFeatureClasses('request_' + randomNum + '*')

                # Assess each split FC to determine if it
                for splitFC in splitFCList:

                    splitFC = arcpy.da.Describe(splitFC)['catalogPath']
                    arcpy.SetProgressorLabel("Determining # of WFS requests. Current #: " + str(len(jsonDict)))

                    #splitExtent = arcpy.da.Describe(splitFC)['extent'].JSON
                    splitExtent = [row[0] for row in arcpy.da.SearchCursor(splitFC, ['SHAPE@JSON'])][0]

                    params = urllibEncode({'f': 'json',
                                           'geometry':splitExtent,
                                           'geometryType':'esriGeometryPolygon',
                                           'returnCountOnly':'true',
                                           'token': portalToken['token']})

                    # Send geometry count request
                    countQuery = submitFSquery(RESTurl,params)
                    print("H")

                    # request failed.....try once more
                    if not countQuery:
                        time.sleep(5)
                        countQuery = submitFSquery(RESTurl,params)

                        if not countQuery:
                           AddMsgAndPrint("\tFailed to get count request -- 3 attempts made -- Recycling request")
                           subDividedFCList.append(splitFC)
                           continue

                    # if count is within max records allowed add it dict
                    if countQuery['count'] <= maxRecordCount:
                        jsonDict[os.path.basename(splitFC)] = [splitExtent,countQuery['count']]

                        #arcpy.CopyFeatures_management(splitFC,scratchWS + os.sep + arcpy.da.Describe(splitFC)['baseName'])
                        arcpy.Delete_management(splitFC)

                    # recycle this fc back to be split into 2 polygons
                    else:
                        subDividedFCList.append(splitFC)

        if len(jsonDict) < 1:
            AddMsgAndPrint("\tCould not determine number of server requests.  Exiting",2)
            return False
        else:
            AddMsgAndPrint("\t" + splitThousands(len(jsonDict)) + " server requests are needed")
            return jsonDict

    except:
        errorMsg()
        return False


## ====================================== Main Body ==================================


# Import modules
import sys, string, os, traceback
import urllib, re, time, json

from urllib.request import Request, urlopen
from urllib.error import HTTPError as httpErrors
urllibEncode = urllib.parse.urlencode
parseQueryString = urllib.parse.parse_qsl

import arcpy
from arcpy import env
import random

if __name__ == '__main__':

    try:

        # Use most of the cores on the machine where ever possible
        arcpy.env.parallelProcessingFactor = "75%"

        """ ---------------------------------------------- ArcGIS Portal Information ---------------------------"""
        nrcsPortal = r'https://gis.sc.egov.usda.gov/portal/'
        nrcsAGOL = r'https://nrcs.maps.arcgis.com/'

        portalToken = getPortalTokenInfo(nrcsAGOL)
        #portalToken = {'token': '5PkSO0ZZcNVv7eEzXz8MTZBxgZbenP71uyMNnYXOefTqYs8rh0TJFGk7VKyxozK1vHOhKmpy2Z2M6mr-pngEbKjBxgIVeQmSnlfANwGXfEe5aOZjgQOU2UfLHEuGEIn1R0d0HshCP_LDtwn1-JPhbnsevrLY2a-LxTQ6D4QwCXanJECA7c8szW_zv30MxX6aordbhxHnugDD1pzCkPKRXkEoHR7r-dQxuaFSczD1jLFyDNB-7vdakAzhLc2xHPidLGt0PNileXzIecb2SA8PLQ..', 'referer': 'http://www.esri.com/AGO/8ED471D4-0B17-4ABC-BAB9-A9433506FD1C', 'expires': 1584646706}

        if not portalToken:
           AddMsgAndPrint("Could not generate Portal Token. Exiting!",2)
           exit()

        # URL for Feature Service Metadata (Service Definition) - AGOL Pedons
        pedonRESTurl_Metadata = """https://services.arcgis.com/SXbDpmb7xQkk44JV/arcgis/rest/services/service_771d431d949748178cd5852ee0b729a1/FeatureServer/1"""

        # Used for admin or feature service info; Send POST request
        params = urllibEncode({'f': 'json','token': portalToken['token']})

        # request info about the feature service
        pedonMetadata = submitFSquery(pedonRESTurl_Metadata,params)

    except:
        errorMsg()
