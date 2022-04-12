#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     05/04/2022
# Copyright:   (c) Adolfo.Diaz 2022
# Licence:     <your licence>

#-------------------------------------------------------------------------------

# Import modules
import sys, string, os, traceback, urllib, re, arcpy
from arcpy import env

newSchemaFGDBroot = f"{os.path.dirname(sys.argv[0])}"
metadataTblFGDB = f"{newSchemaFGDBroot}\\Metadata_Tables.gdb"    # Metadata_Tables FGDB
tblColFldsDesc = f"{metadataTblFGDB}\\PedonMetadataTableColDesc"
tblColRels = f"{metadataTblFGDB}\\PedonMetadataRelationships"
nasisTblsWithSubReports = f"{newSchemaFGDBroot}\\Tables_in_WEB_AnalysisPC_MAIN_URL_EXPORT_Report.txt"

arcpy.env.workspace = metadataTblFGDB

# ----------------------------------------------- Configuration for Table Fields
pedonMetadataTables = arcpy.ListTables('PedonMetadataTableColDesc')

# The following represents the position of fields from the 'PedonMetadataTableColDesc' table
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
uomsym = 21            # Unit of measurement symbol
domnm = 22             # Field Domain
aggregation = 23       # Determines whether a field needs to be disaggregated into 3 individual fields _l, _r, _h

tblFlds = [f.name for f in arcpy.ListFields(tblColFldsDesc)]

# List of all unique table physical names
tableList = list(set([row[0] for row in arcpy.da.SearchCursor(tblColFldsDesc, tblFlds[2])]))
tableList.sort()

# Open the text file that contains all tables from the WEB_AnalysisPC_MAIN_URL_EXPORT
# that have subReports associated with them.  Tables not in the list will be ignored.
functionalTables = list()
with open(nasisTblsWithSubReports) as f:
    for line in f:
        functionalTables.append(line.strip('\n'))

# ----------------------------------------------- Configuration for Relationships
tblColRelsFlds = [f.name for f in arcpy.ListFields(tblColRels)]

originTbl = 1        # tablephysicalname
originPKey = 2       # indexcolumnnames
relationship = 3     # relationshiporienation
destinTbl = 4        # tablephysicalname2
originFKey = 5       # indexcolumnames2

for table in tableList:

    aliasExpression = f"{arcpy.AddFieldDelimiters(tblColRels, tblFlds[2])} = \'{table}\'"
    tableAlias = [row[0] for row in arcpy.da.SearchCursor(tblColFldsDesc, tblFlds[1], where_clause=aliasExpression)][0]

    #if table in functionalTables:continue

    #if not table == 'area':continue

    print("=" * 100)
    print(f"NASIS Pedon Report for: {table} ---- {tableAlias}\n")

    # Order by the field sequence field
    expression = f"{arcpy.AddFieldDelimiters(tblColFldsDesc, tblFlds[tabphynm])} = \'{table}\'"
    sqlCluase = (None,f"ORDER BY {tblFlds[coldefseq]} ASC")

    # Field Physical Name, Field Alias, Field Type, Field Domain
    fields = [tblFlds[attphynm],tblFlds[collab],tblFlds[cholabtxt],tblFlds[domnm]]

    tableFields = [(row[0],row[1],row[2],row[3]) for row in arcpy.da.SearchCursor(tblColFldsDesc,fields,where_clause=expression,sql_clause=sqlCluase)]

    FIELDstatement = ""
    firstFieldNameList = ""
    secondFieldNameList = ""

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ START REPORT
    print("ACCEPT pedonid_list.")
    print("EXEC SQL SELECT\n")

    # ------------------ Print list of fields
    i=1
    for fldPair in tableFields:

        # Line will end in a comma
        ending = r'' if i == len(tableFields) else r','

        # Field is a Lineage field or Record ID; introduce /1
        if fldPair[1] in ('Lineage','Rec ID','Record Last Updated By'):
            print(f"{table}.{fldPair[0]}/1 AS {fldPair[0]}{ending}")

        # Field has a domain associated.
        elif not fldPair[3] == None:
            print(f"CODELABEL ({fldPair[0]}) AS {fldPair[0]}{ending}")

        # Print normal
        else:
            print(f"{table}.{fldPair[0]} AS {fldPair[0]}{ending}")

        if not i==1:
            FIELDstatement += f"FIELD{'.' if i == len(tableFields) else ','}\n"

        trailReturn = '\n' if not i == len(tableFields) else ''
        firstFieldNameList += f"'{fldPair[0]}'{'.' if i == len(tableFields) else ','}{trailReturn}"
        secondFieldNameList += f"{fldPair[0]}{'.' if i == len(tableFields) else ','}{trailReturn}"

        i+=1

    # ------------------ Print Relationship Join Statements (Needs to be verified by Jason)
    # originTbl,originPKey,destinTbl,originFKey
    pcFields = [tblColRelsFlds[originTbl],tblColRelsFlds[originPKey],tblColRelsFlds[destinTbl],tblColRelsFlds[originFKey]]

    iCnt = 1
    originTable = table
    joinStatementList = list()

    while originTable != 'pedon':

        # Select Parent:Child relationship -- relationshiporientation = 'Parent:Child' AND tablephysicalname2 = 'vegplot'"
        parentChldExp = f"{arcpy.AddFieldDelimiters(tblColRels, tblColRelsFlds[relationship])} = \'Parent:Child\' AND {arcpy.AddFieldDelimiters(tblColRels, tblColRelsFlds[destinTbl])} = \'{originTable}\'"

        try:
            parentResults = [(row[0],row[1],row[2],row[3]) for row in arcpy.da.SearchCursor(tblColRels,pcFields,where_clause=parentChldExp)]

            # Sometimes there are more than 1 parent:child results; ignore nasisgroup and nasissite relationship.
            # This should help out with vegplot object tables.
            if len(parentResults) > 1:
                nasisRel = True
                for results in parentResults:
                    if results[0].find('nasis') == -1:
                        parentResults = parentResults[parentResults.index(results)]
                        nasisRel = False
                        break
                if nasisRel:
                    parentResults = parentResults[0]

            else:
                parentResults = parentResults[0]

        except:
            #print("No relationships were returned: {parentChldExp}")
            originTable = 'pedon'
            joinStatementList.insert(0,f"RELATIONSHIP TO PEDON TABLE COULD NOT BE ESTABLISHED")
            break

        originTable = parentResults[0]

        if parentResults[0] == 'siteobs':
            joinStatementList.insert(0,"INNER JOIN siteobs ON siteobs.siteiidref=site.siteiid")
            joinStatementList.insert(1,"INNER JOIN pedon ON pedon.siteobsiidref=siteobs.siteobsiid AND peiid IN ($pedonid_list)")
            originTable = 'pedon'
            break

        if iCnt==1:
            if originTable == 'pedon':
                joinStatementList.append(f"INNER JOIN {table} ON {table}.{parentResults[3]}={parentResults[0]}.{parentResults[1]} AND peiid IN ($pedonid_list);.\n")
            else:
                joinStatementList.append(f"INNER JOIN {table} ON {table}.{parentResults[3]}={parentResults[0]}.{parentResults[1]};.\n")
            iCnt+=1
            continue

        if originTable == 'pedon':
            joinStatementList.insert(0,f"INNER JOIN {parentResults[2]} ON {parentResults[2]}.peiidref=pedon.peiid AND peiid IN ($pedonid_list)")
        else:
            joinStatementList.insert(0,f"INNER JOIN {parentResults[2]} ON {parentResults[2]}.{parentResults[3]}={parentResults[0]}.{parentResults[1]}")


    print("\nFROM pedon")
    for statement in joinStatementList:
        print(statement)

    print(f"TEMPLATE {table} WIDTH UNLIMITED SEPARATOR\"|\"")
    print("AT LEFT FIELD SEPARATOR  \"\",")
    print(FIELDstatement)

    print("SECTION WHEN AT START")
    print("HEADING")
    print(f"AT LEFT \"@begin {table}\".")
    print("END SECTION.\n")

    print("SECTION HEADING")
    print(f"USING {table}")
    print(firstFieldNameList)

    print("\nDATA")
    print(f"USING {table}")
    print(secondFieldNameList)
    print("END SECTION.\n")

    print("SECTION WHEN NO DATA")
    print("DATA")
    print(f"AT LEFT \"@begin {table}\".")
    print(f"USING {table}")
    print(firstFieldNameList)
    print(f"AT LEFT \"@end\".")
    print("END SECTION.\n")

    print("SECTION WHEN AT END DATA")
    print(f"AT LEFT \"@end\".")
    print("END SECTION.\n")





