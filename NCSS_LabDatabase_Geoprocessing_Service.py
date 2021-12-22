#-------------------------------------------------------------------------------
# Name: NCSS_LabDatabase_Geoprocessing_Service.py
# Purpose:
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@usda.gov
# phone: 608.662.4422 ext. 216
#
# Author: Jerry.Monhaupt
# e-mail: jerry.monhaput@usda.gov
#
# Created:     9/16/2021

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
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

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

# =========================================== Main Body ==========================================
# Import modules
import sys, re, os, traceback, arcpy, time, sqlite3
from arcpy import env

if __name__ == '__main__':

    try:
        startTime = tic()

        DBpath = r'E:\Temp\10.203.23.72, 26022.sde'
        #DBpath = r'E:\Pedons\NCSS_Characterization_Database\NewSchema\NCSS_Characterization_Database_newSchema_20200114.gdb'
        outFolder = r'E:\Pedons\KSSL_for_NASIS_Morphological'
        outName = r'KSSL_Test_2'

        textFilePath = outFolder + os.sep + "KSSL_Geoprocessing_Service_logFile.txt"

        env.workspace = DBpath
        labDataTables = arcpy.ListTables("*.lab_*")  #lab_webmap is not captured here
        labDataTables.append('sdmONLINE.dbo.lab_webmap')

        outFGDB = f"{outFolder}\{outName}.gdb"
        outGPKG = f"{outFolder}\{outName}.gpkg"
        outSQLite = f"{outFolder}\{outName}.sqlite"

##        # Create File Geodatabase
##        if not arcpy.Exists(outFGDB):
##            arcpy.CreateFileGDB_management(outFolder,outName)
##
##        # Create Geopackage 1.3
##        if not arcpy.Exists(outGPKG):
##            arcpy.CreateSQLiteDatabase_management(outGPKG,'GEOPACKAGE_1.2')
##
##        # Create SQLite with SpatiaLite geometry type
##        if not arcpy.Exists(outSQLite):
##            arcpy.CreateSQLiteDatabase_management(outSQLite,'SpatiaLite')
##
##        AddMsgAndPrint(f"There are {len(labDataTables)} Lab data tables to import from the sdmONLINE database")
##        AddMsgAndPrint("Importing Tables")
##        recordDict = dict()
##
##        for labTable in labDataTables:
##
##            outTableName = labTable.lstrip('sdmONLINE.dbo')    # left strip 'sdmONLINE.dbo' (name violation)
##            fgdbTablePath = os.path.join(outFGDB,outTableName) # absolute path of new FGDB table
##            gpkgTablePath = os.path.join(outGPKG,outTableName) # absolute path of new Geopackate table
##            sqlLTablePath = os.path.join(outSQLite,outTableName) # absolute path of new Geopackate table
##
##            # convert the combine_nasis_ncss into a point feature layer
##            if labTable.find('combine_nasis') > -1:
##
##                # combine_nasis_ncss -> XY Event layer -> feature class
##                spatialRef = arcpy.SpatialReference(4326)
##                combineNasisTemp = "in_memory\combineNASIS_NCSS_Temp"
##                arcpy.management.MakeXYEventLayer(labTable, "longitude_decimal_degrees", "latitude_decimal_degrees", combineNasisTemp, spatialRef)
##                arcpy.management.CopyFeatures(combineNasisTemp, fgdbTablePath)
##                arcpy.management.CopyFeatures(combineNasisTemp, gpkgTablePath)
##                arcpy.management.CopyFeatures(combineNasisTemp, sqlLTablePath)
##                arcpy.Delete_management(combineNasisTemp)
##
##            # labTable is a regular table
##            else:
##                # copy labTable from sdmONLINE to FGDB
##                arcpy.CopyRows_management(labTable,fgdbTablePath)
##
##                # copy rows from FGDB table to Geopackage
##                arcpy.CopyRows_management(fgdbTablePath,gpkgTablePath)
##
##                # copy rows from FGDB table to SQLite DB
##                arcpy.CopyRows_management(fgdbTablePath,sqlLTablePath)
##
##            recFGDBcount = arcpy.GetCount_management(fgdbTablePath)[0]
##            recPPKGcount = arcpy.GetCount_management(gpkgTablePath)[0]
##            #recSQLLcount = arcpy.GetCount_management(sqlLTablePath)[0]
##
##            theTabLength = (60 - len(outTableName)) * " "
##            AddMsgAndPrint("\t--> " + outTableName + theTabLength + " Records Added: " + splitThousands(recFGDBcount))
##            recordDict[outTableName] = recFGDBcount
##
##        # relationship Dictionary schema
##        # Relationship Name: [origin table, destination table, primary key, foreign key]
##        relateDict = {
##            "xLabCombineNasisNcss_LabPedon":                      ["lab_combine_nasis_ncss","lab_pedon","pedon_key","pedon_key","UNIQUE"],
##            "xLabCalculationsIncludingEstimates_LabPreparation":  ["lab_calculations_including_estimates_and_default_values","lab_preparation","prep_code","prep_code","NON_UNIQUE"],
##            "xLabChemicalProperties_LabPreparation":              ["lab_chemical_properties","lab_preparation","prep_code","prep_code","NON_UNIQUE"],
##            "xLabMethodCode_LabAnalyte":                          ["lab_method_code","lab_analyte","procedure_key","analyte_key","UNIQUE"],
##            "xLabMethodCode_LabAnalysisProcedure":                ["lab_method_code","lab_analysis_procedure","procedure_key","procedure_key","UNIQUE"],
##            "xLabLayer_LabCalculationsIncludingEstimates":        ["lab_layer","lab_calculations_including_estimates_and_default_values","labsampnum","labsampnum","UNIQUE"],
##            "xLabLayer_LabChemicalProperties":                    ["lab_layer","lab_chemical_properties","labsampnum","labsampnum","UNIQUE"],
##            "xLabLayer_LabMajorAndTraceElementsAndOxides":        ["lab_layer","lab_major_and_trace_elements_and_oxides","labsampnum","labsampnum","UNIQUE"],
##            "xLabLayer_LabMineralogyGlassCount":                  ["lab_layer","lab_mineralogy_glass_count","labsampnum","labsampnum","UNIQUE"],
##            "xLabLayer_LabPhysicalProperties":                    ["lab_layer","lab_physical_properties","labsampnum","labsampnum","UNIQUE"],
##            "xLabLayer_LabXrayAndThermal":                        ["lab_layer","lab_xray_and_thermal","labsampnum","labsampnum","UNIQUE"],
##            "xLabLayer_LabRosettaKey":                            ["lab_layer","lab_rosetta_key","layer_key","layer_key","UNIQUE"],
##            "xLabMajorAndTraceElementsAndOxides_LabPreperation":  ["lab_major_and_trace_elements_and_oxides","lab_preparation","prep_code","prep_code","NON_UNIQUE"],
##            "xLabPedon_LabWebMap":                                ["lab_pedon","lab_webmap","pedon_key","pedon_key","UNIQUE"],
##            "xLabPedon_LabSite":                                  ["lab_pedon","lab_site","site_key","site_key","UNIQUE"],
##            "xLabPhysicalProperties_LabPreparation":              ["lab_physical_properties","lab_preparation","prep_code","prep_code","NON_UNIQUE"],
##            "xLabPreparation_LabMineralogyGlassCount":            ["lab_preparation","lab_mineralogy_glass_count","prep_code","prep_code","NON_UNIQUE"],
##            "xLabPreparation_LabXrayAndThermal":                  ["lab_preparation","lab_xray_and_thermal","prep_code","prep_code","NON_UNIQUE"]
##            }
##
##        # -------------------------------------------------------- Add attribute index to primary and foreign keys in FGDB
##        env.workspace = outFGDB
##        AddMsgAndPrint(f"\nCreating Attribute Indices:")
##        for relate in relateDict:
##
##            # Attribute Index Parameter
##            origTable = relateDict[relate][0]
##            destTable = relateDict[relate][1]
##            pKey = relateDict[relate][2]
##            fKey = relateDict[relate][3]
##            uniqueParam = relateDict[relate][4]
##
##            # Look for indexes present for primary and foreign keys
##            origTblIndex = [f.name for f in arcpy.ListIndexes(origTable)]
##            destTblIndex = [f.name for f in arcpy.ListIndexes(destTable)]
##
##            # Add FGDB Index for primary key if not present
##            keyIndex = f"IDX_{origTable}_{pKey}"
##            if not keyIndex in origTblIndex:
##                arcpy.AddIndex_management(origTable,pKey,keyIndex,uniqueParam,"NON_ASCENDING")
##                AddMsgAndPrint(f"\tFGDB - {origTable} - {pKey}")
##
##            # Add FGDB Index for foregin key if not present
##            keyIndex = f"IDX_{destTable}_{fKey}"
##            if not keyIndex in destTblIndex:
##                arcpy.AddIndex_management(destTable,fKey,keyIndex,uniqueParam,"NON_ASCENDING")
##                AddMsgAndPrint(f"\tFGDB - {destTable} - {fKey}")
##
##        AddMsgAndPrint("\n")
##        # -------------------------------------------------------- Add attribute index to primary and foreign keys in GPKG and SQLITE
##        for DBproduct in (outGPKG,outSQLite):
##            sqliteConnection = sqlite3.connect(DBproduct)
##            sqliteCursor = sqliteConnection.cursor()
##            existingIndices = []
##
##            for relate in relateDict:
##
##                # Attribute Index Parameter
##                origTable = relateDict[relate][0]
##                destTable = relateDict[relate][1]
##                pKey = relateDict[relate][2]
##                fKey = relateDict[relate][3]
##                uniqueParam = relateDict[relate][4]
##
##                #createIndex = (f"CREATE{' UNIQUE' if uniqueParam == 'UNIQUE' else ''} INDEX IF NOT EXISTS {keyIndex} ON {tbl} ({key})")
##                for tbl in (origTable,destTable):
##
##                    key = pKey if tbl == origTable else fKey
##                    keyIndex = f"IDX_{tbl}_{pKey}"
##
##                    if not keyIndex in existingIndices:
##                        createIndex = (f"CREATE INDEX IF NOT EXISTS {keyIndex} ON {tbl} ({key})")
##                        sqliteCursor.execute(createIndex)
##                        existingIndices.append(keyIndex)
##                        AddMsgAndPrint(f"\t{'SQLITE' if DBproduct.endswith('.sqlite') else 'GPKG'} - {tbl} - {key}")
##
##            sqliteConnection.close()
##        AddMsgAndPrint("\n")
##
##        # -------------------------------------------------------- Add relationships to FGDB
##        for relate in relateDict:
##
##            # Relationship Parameters
##            relateName = relate
##            origTable = relateDict[relate][0]
##            destTable = relateDict[relate][1]
##            pKey = relateDict[relate][2]
##            fKey = relateDict[relate][3]
##            forwardLabel = f"> {destTable}"
##            backwardLabel = f"< {origTable}"
##
##            try:
##                arcpy.CreateRelationshipClass_management(origTable,destTable,relateName,"SIMPLE",forwardLabel,backwardLabel,"NONE","ONE_TO_MANY","NONE",pKey,fKey)
##                AddMsgAndPrint(f"Created Relationship Class between {origTable} - {destTable}")
##            except:
##                errorMsg()

        # Adjust Column Names
        env.workspace = outFGDB
        FGDBdataTables = arcpy.ListTables("lab_*")
        FGDBdataTables.append(arcpy.ListFeatureClasses("lab_*")[0])

        sqliteConnection = sqlite3.connect(outSQLite)
        sqliteCursor = sqliteConnection.cursor()

        gpkgConnection = sqlite3.connect(outGPKG)
        gpkgCursor = gpkgConnection.cursor()

        for tbl in FGDBdataTables:

            # FGDB Table Fields
            gdbFlds = [f.name for f in arcpy.ListFields(f"{outFGDB}\{tbl}")]

            # SQLITE Table Fields
            sqliteCursor = sqliteConnection.execute(f"select * from {tbl}")
            sqlFlds = [description[0] for description in sqliteCursor.description]

            # GPKG Table Fields
            gpkgCursor = gpkgConnection.execute(f"select * from {tbl}")
            gpkgFlds = [description[0] for description in gpkgCursor.description]

            for fldName in gdbFlds:
                sqliteFld = sqlFlds[gdbFlds.index(fldName)]
                try:
                    if not fldName == sqliteFld:
                        sqliteCursor.execute(f"ALTER TABLE {tbl} RENAME COLUMN {sqliteFld} TO {fldName}")
                        AddMsgAndPrint(f"Renamed SQLite - {tbl} - {sqliteFld}")

                    gpkgFld = gpkgFlds[gdbFlds.index(fldName)]
                    if not fldName == gpkgFld:
                        gpkgCursor.execute(f"ALTER TABLE {tbl} RENAME COLUMN {gpkgFld} TO {fldName}")
                        AddMsgAndPrint(f"Renamed GPKG - {tbl} - {gpkgFld}")
                except:
                    pass

        sqliteConnection.close()
        gpkgConnection.close()

        stopTime = toc(startTime)
        AddMsgAndPrint(f"Total Processing Time: {stopTime}")

    except:
        errorMsg()


















