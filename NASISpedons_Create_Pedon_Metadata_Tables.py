#-------------------------------------------------------------------------------
# Name:        NASISpedons_Create_Pedon_Metadata_Tables
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     3/02/2022

# This script will recreate the NASIS Pedon FGDB schema using the following NASIS URL
# Report: Web-NREPO-Style-Metadata-Pedon-Main


# - No data will be provided fo
#-------------------------------------------------------------------------------


# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

from urllib.error import HTTPError, URLError
from urllib.request import Request

# --------------------------------------------------------------- SCRIPT PARAMATERS
# NASIS Web-NREPO-Style-Metadata-Pedon-Main URL Report parameters
nasisDBmodel = r'NASIS 7.4.1'
metadataName = r'NASIS 7.4.1'
domainName = r'Current NASIS/SSURGO Domains'
pedonMetadataURL = r'https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=Web-NREPO-Style-Metadata-Pedon-Main&system_name=NASIS%207.4.1&metadata_name=NASIS%207.4.1&domain_name=Current%20NASIS/SSURGO%20Domains'

schemaGDB = r'E:\Temp\scratch\scratch.gdb'    # Make a copy of
newSchemaFGDBroot = r'E:\NCSS_Pedons\NASIS_Pedons_Metatdata_Update'
newSchemaFGDBname = f"NASISPedonsFGDBTemplate_{nasisDBmodel.replace(' ','_').replace('.','_')}.gdb"
tblColFldsDesc = f"{schemaGDB}\\PedonMetadataTableColDesc"  # official NASIS table for table/column metadata
tblColRels = f"{schemaGDB}\\PedonMetadataRelationships"



# --------------------------------------------------------------- ORGANIZE PEDON METADATA TABLE INFORMATION
print(f"Opening NASIS Pedon URL Report: Web-NREPO-Style-Metadata-Pedon-Main Report")
print(f"\tNASIS Database Model: {nasisDBmodel}")
print(f"\tNASIS Metadata Name: {metadataName}")
print(f"\tDomain Name: {domainName}")

bHeader = False
theTable = ""
tableColumnsDict = dict()

numOfFields = ""        # The number of fields a specific table should contain
partialValue = ""       # variable containing part of a value that is not complete
originalValue = ""      # variable containing the original incomplete value
bPartialValue = False   # flag indicating if value is incomplete; append next record

theReport = urllib.request.urlopen(pedonMetadataURL).readlines()

for theValue in theReport:

    # convert from bytes to string and remove white spaces
    theValue = theValue.decode('utf-8').strip()

    # skip blank lines
    if theValue == '' or theValue == None:
        continue

    # represents the start of valid table; Typically Line #19
    if theValue.find('@begin') > -1:
        theTable = theValue[theValue.find('@') + 7:]  ## Isolate table name i.e. PedonMetadataDomain
        print(f"\n\tCollecting Metadata Information for {theTable} table")
        bHeader = True  ## Next line will be the header

    # end of the previous table has been reached; reset currentTable
    elif theValue.find('@end') > -1:
        currentTable = ""
        bHeader = False

    # represents header line
    elif bHeader:
        fieldNames = theValue.split('|')   ## ['tablognm','tabphynm','tablab','tabhelp','logicaldatatype','physicaldatatype']
        bHeader = False                    ## Reset to look for another header
        numOfFields = len(fieldNames)
        print(f"\t\tTotal # of fields: {len(fieldNames)}")
        #print(f"\t\tField Names: {fieldNames}")

    # represents individual legitimate records
    elif not bHeader and theTable:

        numOfValues = len(theValue.split('|'))

        if numOfValues == 1 and bPartialValue == False and numOfFields > 1:
            lastRecord = tableColumnsDict[theTable][-1]
            lastItem = f"{lastRecord[-1]} {theValue}"
            lastRecord[-1] = lastItem
            del tableColumnsDict[theTable][-1]
            tableColumnsDict[theTable].append(lastRecord)
            continue

        # Add the record to its designated list within the dictionary
        # Do not remove the double quotes b/c doing so converts the object
        # to a list which increases its object size.  Remove quotes before
        # inserting into table

        # this should represent the 2nd half of a valid value
        if bPartialValue:
            partialValue += theValue  # append this record to the previous record

            # This value completed the previous value
            if len(partialValue.split('|')) == numOfFields:

                if not theTable in tableColumnsDict:
                    tableColumnsDict[theTable] = [partialValue.split('|')]
                else:
                    tableColumnsDict[theTable].append(partialValue.split('|'))

                bPartialValue = False
                partialValue = ""

            # appending this value still falls short of number oof possible fields
            # add another record; this would be the 3rd record appended and may
            # exceed number of values.
            elif len(partialValue.split('|')) < numOfFields:
                continue

            # appending this value exceeded the number of possible fields
            else:
                print("\t\tIncorrectly formatted Record Found in " + theTable + " table:")
                print("\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(len(partialValue.split('|'))))
                print("\t\t\tRecord: " + partialValue)
                bPartialValue = False
                partialValue = ""

        # number of values do not equal the number of fields in the corresponding tables
        elif numOfValues != numOfFields:

            # number of values exceed the number of fields; Big Error
            if numOfValues > numOfFields:
                print("\n\t\tIncorrectly formatted Record Found in " + theTable + " table:",2)
                print("\t\t\tRecord should have " + str(numOfFields) + " values but has " + str(numOfValues),2)
                print("\t\t\tRecord: " + theValue,2)

            # number of values falls short of the number of correct fields
            else:
                partialValue,originalValue = theValue,theValue
                bPartialValue = True

        else:
            if not theTable in tableColumnsDict:
                tableColumnsDict[theTable] = [theValue.split('|')]
            else:
                tableColumnsDict[theTable].append(theValue.split('|'))
            bPartialValue = False
            partialValue = ""


# --------------------------------------------------------------- POPULATE PEDON METADATA TABLES
arcpy.env.workspace = schemaGDB
pedonMetadataTables = arcpy.ListTables('PedonMetadata*')

# Delete all of the rows from the pedon metadata tables
# i.e. PedonMetadataTableColDesc, PedonMetadataRelationships,
#      PedonMetadataTableUniqueConstraints, PedonMetadataDomain
print("\nDeleting old records for the following tables:")
for tbl in pedonMetadataTables:

    tblPath = f"{schemaGDB}\\{tbl}"
    if arcpy.Exists(tblPath):
        print(f"\t{tbl}")
        arcpy.DeleteRows_management(tblPath)

# Insert new metadata values into appropriate tables.  Should be 4 tables.
print("\nInserting new records for the following tables:")
for tbl,recs in tableColumnsDict.items():
    print(f"\t{tbl}")

    tblPath = f"{schemaGDB}\\{tbl}"
    if not arcpy.Exists(tblPath):
        print(f"{tblPath} Does NOT exist!")
        continue

    tblFlds = [f.name for f in arcpy.ListFields(tblPath)][1:]
    cursor = arcpy.da.InsertCursor(tblPath, tblFlds)

    for rec in recs:
        updatedRec = [None if val == '' else val for val in rec]

        cursor.insertRow(updatedRec)
        del updatedRec

    del cursor

# --------------------------------------------------------------- CREATE FGDB PEDON TABLES USING NEW METADATA SCHEMA

tablab = 1             # Table Alias
tabphynm = 2           # Table Physical Name
tabhelptext = 4        # Table Description
coldefseq = 5          # Field Sequence
attphynm = 7           # Field Physical Name
collab = 8             # Field Alias
cholabtxt = 9          # Field Type
colnotnulbool = 11     # Field Allow NULLs
attfldsiz = 15         # Field Length
attprec = 16           # Field Precision
domnm = 22             # Field Domain
aggregation = 23       # Determines whether a field needs to be disaggregated into 3 individual fields _l, _r, _h

tblFlds = [f.name for f in arcpy.ListFields(tblColFldsDesc)]

# List of all unique table physical names
tableList = list(set([row[0] for row in arcpy.da.SearchCursor(tblColFldsDesc, tblFlds[2])]))
tableList.sort()

# Create new Pedon FGDB
print(f"\nCreating New Pedon FGDB Template: {newSchemaFGDBname}")
arcpy.CreateFileGDB_management(newSchemaFGDBroot, newSchemaFGDBname)
newSchemaFGDBpath = f"{newSchemaFGDBroot}\\{newSchemaFGDBname}"

sqlDataTypeConverstion = {'Boolean':'SHORT',
                          'Bit':'SHORT',
                          'Char':'TEXT',
                          'Choice':'SHORT',
                          'Date/Time':'DATE',
                          'Datetime':'DATE',
                          'File Reference':'TEXT',
                          'Float':'FLOAT',
                          'Hyperlink':'TEXT',
                          'Integer':'LONG',
                          'Int':'LONG',
                          'Smallint':'SHORT',
                          'String':'TEXT',
                          'Real':'FLOAT',
                          'Narrative Text':'TEXT',
                          'Varchar':'TEXT',
                          'Varchar(max)':'TEXT'}

for tbl in tableList:

    print(f"\n\tTable Name: {tbl} ({tblFlds[tablab]})")
    arcpy.CreateTable_management(newSchemaFGDBpath,tbl,out_alias=tblFlds[tablab])
    newTable = f"{newSchemaFGDBpath}\\{tbl}"

    # tabphynm = 'pediagfeatures'
    expression = f"{arcpy.AddFieldDelimiters(tblColFldsDesc, tblFlds[tabphynm])} = \'{tbl}\'"

    # Order by the field sequence field
    sqlCluase = (None,f"ORDER BY {tblFlds[coldefseq]} ASC")

    print(f"\n\t\t{'Field Name' : <30}{'Alias' : ^30}{'Type' : >10}")
    print(f"\t\t{75*'='}")
    with arcpy.da.SearchCursor(tblColFldsDesc,tblFlds,where_clause=expression,sql_clause=sqlCluase) as cursor:
        for row in cursor:

            fieldName = row[attphynm]
            fieldType = sqlDataTypeConverstion[row[cholabtxt]]
            fieldAlias = row[collab]

            if fieldType == 'TEXT':
                fieldLength = row[attfldsiz]
            else:
                fieldLength = ''

            if row[domnm] == '':
                fieldDomain = None
            else:
                fieldDomain = row[domnm]

            if row[colnotnulbool].lower() == 'yes':
                fieldAllowNulls = 'NON_NULLABLE'
            else:
                fieldAllowNulls = 'NULLABLE'

            # Create 3 fields representing _l, _r, _h if aggregation code is 2
            if row[aggregation] == 2:
                aggDict = {'_l':'_Low','_r':'_RV','_h':'_High'}
                for k,v in aggDict.items():
                    arcpy.AddField_management(newTable,fieldName + k,fieldType,'',field_alias=fieldAlias+v,field_is_nullable=fieldAllowNulls)
                    print(f"\t\t{fieldName : <30}{fieldAlias : ^30}{fieldType : >6}")
            else:
                arcpy.AddField_management(newTable,fieldName,fieldType,field_length=fieldLength,field_alias=fieldAlias,field_is_nullable=fieldAllowNulls)
                print(f"\t\t{fieldName : <30}{fieldAlias : ^30}{fieldType : >6}")






##    whereClause = f"""lower({metadtaFlds[fieldName].upper()}) IN ('{"','".join(flds)}')"""
##
##    # columnphysicalname,columnlabel,logicaldatatype,fieldsize, decimalprecision,notnull
##    searchFlds = [metadtaFlds[fieldName],metadtaFlds[fieldAlias],metadtaFlds[fieldType],metadtaFlds[fieldSize],
##                  metadtaFlds[fieldDecimalPrecsion],metadtaFlds[fieldNull]]
##
##    exit()

##    for fld in flds:
##        for row in arcpy.da.SearchCursor(tableColumnMetadata,searchFlds,where_clause=whereClause):




