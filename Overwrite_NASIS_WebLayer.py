##################################################################################
#                                                                                 #
#  This script updates existing feature layers on AGOL by replacing the           #
#  associated service definition file with one newly generated from locally       #
#  hosted data.                                                                   #
#                                                                                 #
#  If this script is to run successfully, certain parameters must be met prior    #
#  to its execution. For complete documentation of the workflow, visit:           #
#  https://drive.google.com/open?id=1k6b3NOAo9TztbP1DHPB3J1UFNpGAA1Q8             #
#                                                                                 #
#  Rachel Schultz | rachel.schultz@tn.gov                                         #
#                                                                            	  #
###################################################################################

#-------------------------------------------------------------------------------
# Name:        Overwrite_NASISpedons_WebLayer.py
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     01/24/2022

#-------------------------------------------------------------------------------

# Import modules
import arcpy
import os, sys, base64
from arcgis.gis import GIS

if __name__ == '__main__':


    ############################ BEGIN ASSIGNING VARIABLES ############################

    # Set the path to the project
    prjFolder = r"N:\flex\NCSS_Pedons\NASIS_Pedons\Web_Feature_Service\NASIS_Pedons_WFS"
    aprxPath = f"{prjFolder}\\NASIS_Pedons_WFS.aprx"
    aprxMap = 'NASIS Pedon WFS Map'

    AGOL_sdName = r'NASIS_Pedons'                      # Name of service definition in AGOL w/out .sd
    sddraft = f"{prjFolder}\\NASIS_Pedon_WFS.sddraft"
    sd = f"{prjFolder}\\NASIS_Pedon_WFS_SD.sd"
    AGOL_folder = "NASIS Pedons"

    # Set login credentials (user name is case sensitive, fyi)
    portal = r'https://nrcs.maps.arcgis.com'
    user = r'adolfo.diaz_nrcs'
    contrasena = base64.b64decode(b'd2FzaW1hbjIwMTA=')

    # Set sharing settings
    shrOrg = True
    shrEveryone = False
    shrGroups = " "

    ############################# END ASSIGNING VARIABLES #############################
    # Connect to ArcGIS online
    print("Connecting to {}".format(portal))
    gis = GIS(portal, user, contrasena)
    print("Successfully logged in as: " + gis.properties.user.username + "\n")

    # Assign environment and project, and create empty dictionaries
    arcpy.env.overwriteOutput = True

    aprx = arcpy.mp.ArcGISProject(aprxPath)
    maps = aprx.listMaps(aprxMap)[0]
    pedonLayer = maps.listLayers('NASIS Pedons')[0]

    # Get the serice definition from AGOL
    # [<Item title:"NASIS Pedons" type:Service Definition owner:adolfo.diaz_nrcs>]
    NASISPedonSD = gis.content.search(query="title: NASIS Pedons", item_type="Service Definition")

    if not len(NASISPedonSD):


    updateItem = gis.content.get(sdID) # need to get service definition ID from AGOL

    arcpy.mp.CreateWebLayerSDDraft(pedonLayer, sddraft, AGOL_sdName, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS', True, True)
    arcpy.StageService_server(sddraft, sd)
    updateItem.update(data=sd)
    fs = updateItem.publish(overwrite=True)


    mapDict = {}
    servDict = {}

    # Populate map dictionary with map names and objects from earlier defined project
    for map in prj.listMaps():
    	mapDict[map.name]=map

    # Search for service definition files under the current user's account and populate
    # service definition dictionary with names and ID numbers
    sdItem = gis.content.search(query="owner: " + user + " AND type:Service Definition", max_items=100)
    for serv in sdItem:
    	if str(serv.name).endswith(".sd"):
    		servDict[str(serv.name)[:-3]]=serv.id

    # Iterate through maps in project and, if a matching service definition is found,
    # overwrite that service definition with the data in the local map
    for sdName, sdID in servDict.items():
    	for mapName, mapItem in mapDict.items():
    		if mapName == sdName:
    			updateItem = gis.content.get(sdID)
    			arcpy.mp.CreateWebLayerSDDraft(mapItem, sddraft, sdName, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS', True, True)
    			arcpy.StageService_server(sddraft, sd)
    			updateItem.update(data=sd)
    			print("Overwriting {}...".format(sdName))
    			fs = updateItem.publish(overwrite=True)
    			if shrOrg or shrEveryone or shrGroups:
    				print("Setting sharing options...")
    				fs.share(org=shrOrg, everyone=shrEveryone, groups=shrGroups)
    			print("Successfully updated {}.\n".format(fs.title))
