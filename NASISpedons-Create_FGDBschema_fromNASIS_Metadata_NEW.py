#-------------------------------------------------------------------------------
# Name:        NASISpedons_Create_Pedon_Metadata_Tables
#
# Author:      Adolfo.Diaz
# Created:     3/02/2022

# This script will recreate the NASIS Pedon FGDB after a NASIS database model has
# been made.  schema using the following NASIS URL
# Report: Web-NREPO-Style-Metadata-Pedon-Main
#
# 1. Four Tables will be recreated within the Metadata_Tables.gdb:
#   A. Pedon Metadata Domain
#   B. PedonMetadataRelationships
#   C. PedonMetadataTableColDesc
#   D. PedonMetadataTableUniqueConstraints
#
# 2. Do NOT Delete the tables above.  The script will automatically delete ALL
#    Rows after data from Web-NREPO-Style-Metadata-Pedon-Main report has been
#    organized into a diectionary.
#
# 3. The report will return Table-Field-Records for the 4 tables above.  However,
#    There is no metadata to recreate these individual 4 tables in the Metadata_Tables.gdb
#    so if you delete them then you will have to ask Jason to generate a report
#    for each individual table in html format in order to copy into Excel and export
#    to a FGDB to get the default datatypes.
#
# 4. The report has 3 parameters:
#   A. nasisDBmodel: 'NASIS 7.4.1'
#   B. metadataName = r'NASIS 7.4.1'
#   C. domainName = r'Current NASIS/SSURGO Domains'
#
# 5. Before you rerun this script, make sure to run the report in a browwser using
#    the paramaeters, such as new database model version.
#
# 6. After the 4 pedon tables have been updated, a new FGDB will be craeted in the script's
#    location named with the new nasisDBmodel.
#
# 7. Individual tables will be created using the the table and column information from the
#    PedonMetadataTableColDesc table.  Tables that start with dom* or nasis* will be ignored
#    i.e. domaindetail, domaingroup, domainhist, domainmaster, nasisgroup, nasisgroupmember, nasissite
#
# 8. Relatiionships are created using the PedonMetadataRelationships Table
#
# 9. Field Indices are created using the PedonMetadataTableUniqueConstraints
#
# Example of Web-NREPO-Style-Metadata-Pedon-Main Report of NASIS 7.4.1 schema
# https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=Web-NREPO-Style-Metadata-Pedon-Main&system_name=NASIS%207.4.1&metadata_name=NASIS%207.4.1&domain_name=Current%20NASIS/SSURGO%20Domains


# - No data will be provided fo
#-------------------------------------------------------------------------------

# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

from urllib.error import HTTPError, URLError
from urllib.request import Request

arcpy.env.parallelProcessingFactor = "100%"

# --------------------------------------------------------------- SCRIPT PARAMATERS
# NASIS Web-NREPO-Style-Metadata-Pedon-Main URL Report parameters
nasisDBmodel = r'NASIS 7.4.1'
metadataName = r'NASIS 7.4.1'
domainName = r'Current NASIS/SSURGO Domains'
pedonMetadataURL = f"https://nasis.sc.egov.usda.gov/NasisReportsWebSite/limsreport.aspx?report_name=Web-NREPO-Style-Metadata-Pedon-Main&system_name={urllib.parse.quote(nasisDBmodel)}&metadata_name={urllib.parse.quote(metadataName)}&domain_name={urllib.parse.quote(domainName)}"

newSchemaFGDBroot = f"{os.path.dirname(sys.argv[0])}"
metadataTblFGDB = f"{newSchemaFGDBroot}\\Metadata_Tables.gdb"    # Metadata_Tables FGDB
newSchemaFGDBname = f"NASISPedonsTemplate_{nasisDBmodel.replace(' ','_').replace('.','_')}.gdb"
nasisTblsWithSubReports = f"{newSchemaFGDBroot}\\Tables_in_WEB_AnalysisPC_MAIN_URL_EXPORT_Report.txt"

tblColFldsDesc = f"{metadataTblFGDB}\\PedonMetadataTableColDesc"  # official NASIS table for table/column metadata
tblColRels = f"{metadataTblFGDB}\\PedonMetadataRelationships"
tblConstraints = f"{metadataTblFGDB}\\PedonMetadataTableUniqueConstraints"

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


# ------------------------------------------------------------------ POPULATE PEDON METADATA TABLES
arcpy.env.workspace = metadataTblFGDB
pedonMetadataTables = arcpy.ListTables('PedonMetadata*')

# Delete all of the rows from the pedon metadata tables
# i.e. PedonMetadataTableColDesc, PedonMetadataRelationships,
#      PedonMetadataTableUniqueConstraints, PedonMetadataDomain
print("\nDeleting old records for the following tables:")
for tbl in pedonMetadataTables:

    tblPath = f"{metadataTblFGDB}\\{tbl}"
    if arcpy.Exists(tblPath):
        print(f"\t{tbl}")
        arcpy.DeleteRows_management(tblPath)

# Insert new metadata values into appropriate tables.  Should be 4 tables.
print("\nInserting new records for the following tables:")
for tbl,recs in tableColumnsDict.items():
    print(f"\t{tbl}")

    tblPath = f"{metadataTblFGDB}\\{tbl}"
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
coldisplaysz = 12      # Field Length if associated with Domain choice list
attfldsiz = 15         # Field Length
attprec = 16           # Field Precision
domnm = 22             # Field Domain
aggregation = 23       # Determines whether a field needs to be disaggregated into 3 individual fields _l, _r, _h

tblFlds = [f.name for f in arcpy.ListFields(tblColFldsDesc)]

# List of all unique table physical names
tableList = list(set([row[0] for row in arcpy.da.SearchCursor(tblColFldsDesc, tblFlds[2])]))
tableList.sort()

# Create Table Alias dict that will be reference throughout
tblAliasDict = dict()
for tblPhyName in tableList:
    # tabphynm = 'pediagfeatures'
    expression = f"{arcpy.AddFieldDelimiters(tblColFldsDesc, tblFlds[tabphynm])} = \'{tblPhyName}\'"
    tblAlias = [row[0] for row in arcpy.da.SearchCursor(tblColFldsDesc,[tblFlds[1]],where_clause=expression)][0]
    tblAliasDict[tblPhyName] = tblAlias

# Create new Pedon FGDB
print(f"\nCreating New Pedon FGDB Template: {newSchemaFGDBname}")
arcpy.CreateFileGDB_management(newSchemaFGDBroot, newSchemaFGDBname)
newSchemaFGDBpath = f"{newSchemaFGDBroot}\\{newSchemaFGDBname}"

# Data type conversions between SQL and ESRI
sqlDataTypeConverstion = {'Boolean':'SHORT',
                          'Bit':'SHORT',
                          'Binary':'BLOB',
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

# Open the text file that contains all tables from the WEB_AnalysisPC_MAIN_URL_EXPORT
# that have subReports associated with them.  Tables not in the list will be ignored.
functionalTables = list()
with open(nasisTblsWithSubReports) as f:
    for line in f:
        functionalTables.append(line.strip('\n'))

for tbl in tableList:

    # Skip Domain and NASIS tables
    if tbl.startswith('dom') or tbl.startswith('nasis'):
        #print(f"Not Creating the following table: {tbl}")
        continue

    # Skip table if it doesn't have a subreport associated with it in NASIS
    if not tbl in functionalTables:
        #print(f"Not Creating the following table: {tbl}")
        continue

    tblAlias = tblAliasDict[tbl]

    # Create Feature class from pedon table
    if tbl == 'pedon':
        print(f"\n\tCreating Feature Class: {tbl} - ({tblAlias})")
        # Create the GCS WGS84 spatial reference and datum name using the factory code
        spatialRef = arcpy.SpatialReference(4326)
        arcpy.CreateFeatureclass_management(newSchemaFGDBpath, "pedon", "POINT", "#", "DISABLED", "DISABLED", spatialRef, out_alias=tblAlias)

    # Create Empty table
    else:
        print(f"\n\tTable Name: {tbl} ({tblAlias})")
        arcpy.CreateTable_management(newSchemaFGDBpath,tbl,out_alias=tblAlias)

    newTable = f"{newSchemaFGDBpath}\\{tbl}"

    # Order by the field sequence field
    expression = f"{arcpy.AddFieldDelimiters(tblColFldsDesc, tblFlds[tabphynm])} = \'{tbl}\'"
    sqlCluase = (None,f"ORDER BY {tblFlds[coldefseq]} ASC")

    print(f"\n\t\t{'Field Name' : <35}{'Alias' : <45}{'Type' : <10}")
    print(f"\t\t{85*'='}")
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

            # This is strictly for fields that have a domain associated with them
            # and the metadata describes them as integers instead of text
            if row[cholabtxt] == 'Choice':
                fieldType = 'TEXT'
                fieldLength = row[coldisplaysz] + 10

            # Create 3 fields representing _l, _r, _h if aggregation code is 2
            if row[aggregation] == 2:
                aggDict = {'_l':'_Low','_r':'_RV','_h':'_High'}
                for k,v in aggDict.items():
                    arcpy.AddField_management(newTable,fieldName + k,fieldType,'',field_alias=fieldAlias+v,field_is_nullable=fieldAllowNulls)
                    print(f"\t\t{fieldName + k: <35}{fieldAlias + v: <45}{fieldType : <10}")
            else:
                arcpy.AddField_management(newTable,fieldName,fieldType,field_length=fieldLength,field_alias=fieldAlias,field_is_nullable=fieldAllowNulls)
                print(f"\t\t{fieldName : <35}{fieldAlias : <45}{fieldType : <10}")

# --------------------------------------------------------------- CREATE FGDB PEDON TABLE RELATIONSHIPS

arcpy.env.workspace = newSchemaFGDBpath
newSchemaTables = arcpy.ListTables('*')
newSchemaTables.append('pedon')
newSchemaTables.sort()

tblColRelsFlds = [f.name for f in arcpy.ListFields(tblColRels)]

originTbl = 1        # tablephysicalname
originPKey = 2       # indexcolumnnames
relationship = 3     # relationshiporienation
destinTbl = 4        # tablephysicalname2
originFKey = 5       # indexcolumnames2

# Select only Parent:Child relationships and sort by
parentChldExp = f"{arcpy.AddFieldDelimiters(tblColRels, tblColRelsFlds[relationship])} = \'Parent:Child\'"
sqlCluase = (None,f"ORDER BY {tblColRelsFlds[originTbl]} ASC")
relList = [(row[1],row[2],row[4],row[5]) for row in arcpy.da.SearchCursor(tblColRels,'*',where_clause=parentChldExp,sql_clause=sqlCluase)]

print(f"\nCreating Relationship Classes")
print(f"\n\t{'Origin Table' : <25}{'Destination Table' : <30}{'Relationship Type' : <20}{'Relationship Name' : <60}")
print(f"\t{130*'='}")

# ('area', 'areaiid', 'areatext', 'areaiidref')
for rel in relList:

    # Skip tables that have more than 1 primary keys
    if len(rel[1].split(',')) > 1:
        continue

    origin_table = rel[0]
    destination_table = rel[2]
    outRelClass = f"z{origin_table.capitalize()}_{destination_table.capitalize()}"
    reltype = "SIMPLE"

    # forward label: > Area Table
    #expression = f"{arcpy.AddFieldDelimiters(tblColFldsDesc, tblFlds[tabphynm])} = \'{destination_table}\'"
    #tblAlias = [row[0] for row in arcpy.da.SearchCursor(tblColFldsDesc,[tblFlds[tablab]],where_clause=expression)][0]
    tblAlias = tblAliasDict[destination_table]
    forward_label = f"> {tblAlias} Table"

    # backward label: < Area Table
    #expression = f"{arcpy.AddFieldDelimiters(tblColFldsDesc, tblFlds[tabphynm])} = \'{origin_table}\'"
    #tblAlias = [row[0] for row in arcpy.da.SearchCursor(tblColFldsDesc,[tblFlds[tablab]],where_clause=expression)][0]
    tblAlias = tblAliasDict[origin_table]
    backward_label = f"< {tblAlias} Table"

    message_direction = "NONE"
    cardinality = "ONE_TO_MANY"
    attributed = 'NONE'
    origin_primaryKey = rel[1]
    origin_foreignKey = rel[3]

    origin_tablePath = f"{newSchemaFGDBpath}\\{origin_table}"
    destination_tablePath = f"{newSchemaFGDBpath}\\{destination_table}"

    if arcpy.Exists(origin_tablePath) and arcpy.Exists(destination_tablePath):
        arcpy.CreateRelationshipClass_management(origin_table,
                                                 destination_table,
                                                 outRelClass,
                                                 reltype,
                                                 forward_label,
                                                 backward_label,
                                                 message_direction,
                                                 cardinality,
                                                 attributed,
                                                 origin_primaryKey,
                                                 origin_foreignKey)

        print(f"\t{origin_table : <25}{'--> ' + destination_table: <30}{'--> ' + cardinality : <20}{'--> ' + outRelClass : <60}")
##    else:
##        print(f"{origin_table} or {destination_table} DOES NOT EXIST")

# --------------------------------------------------------------- CREATE FGDB PEDON FIELD INDEXES
# Field index includes OBJECTID
tabphynm = 1
indxName = 3
indxFld = 4

indexTblFlds = [f.name for f in arcpy.ListFields(tblConstraints)]

# Order by the field sequence field
pkIndexExp = f"{arcpy.AddFieldDelimiters(tblConstraints, indexTblFlds[indxName])} LIKE \'PK_%\'"
IndexSqlCluase = (None,f"ORDER BY {indexTblFlds[tabphynm]} ASC")

print(f"\nCreating Attribute Indexes")
print(f"\n\t{'Table' : <30}{'Index Field' : <30}{'Index Name' : <30}")
print(f"\t{90*'='}")

with arcpy.da.SearchCursor(tblConstraints,indexTblFlds,where_clause=pkIndexExp,sql_clause=IndexSqlCluase) as cursor:
    for row in cursor:

        table = row[tabphynm]
        tablePath = f"{newSchemaFGDBpath}\\{table}"

        if arcpy.Exists(tablePath):
            indexField = row[indxFld]

            if indexField in [f.name for f in arcpy.ListFields(tablePath,indexField)]:
                indexName = row[indxName]
                arcpy.AddIndex_management(tablePath,indexField,indexName)
                print(f"\t{table: <30}{indexField: <30}{indexName : <30}")








