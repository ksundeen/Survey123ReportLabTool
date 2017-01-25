import arcpy
import reportlab
import os
import time
import glob
import textwrap
import shutil

# Modules for downloading Feature Service gdb
import zipfile
import sys
import json
import urllib, urllib2
from urllib2 import urlopen
import requests
import csv
import datetime
from datetime import timedelta

# Modules for PDF reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether, ListFlowable, ListItem, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import CMYKColor

#safetyobservationgdb = r'\\p\files1\mxd\bkeinath\AGOLandServerProjects\Safety Observation Survey\SafetyObservation.gdb' #Location of the downloaded safety observation geodatabase
""" Structure of download folders:
[survey name]
[survey name]\[survey name].gdb
[survey name]\[survey name].gdb\[survey name]           # feature class
[survey name]\[survey name].gdb\[survey name]__ATTACH   # attachments gdb table
[survey name]\ReportAndPhotos                           # folder  created in each username's share folder to store the PDF report
[survey name]\ReportAndPhotos\Photos
"""

# Variables
surveyname = 'SafetyObservationSurvey'
downloaddatafolder = r'C:\code\trunk\Projects_Python\Survey123ReportTool\DownloadedData'
extractpath = r'C:\code\trunk\Projects_Python\Survey123ReportTool\DownloadedData' + '\\' + surveyname # Location of our download data folder
surveygdb = extractpath + '\\' + surveyname + '.gdb'
surveyfeatureclass = surveygdb + '\\' + surveyname # Feature class containing survey responses
surveyReportAndPhotosfolder = extractpath + '\\ReportAndPhotos'
surveyattachmenttable = surveygdb + '\\' + surveyname + '__ATTACH'
archivefolder = extractpath + '\\Archive' # Location of archived data folder

# Functions

#########################################################
def IfNotExistCreaterFolder(folder_source):
    """
    :param folder_source: folder name being checked for whether it exists, if it doesn't then a folder is created.
    :return:
    """
    if not os.path.exists(folder_source):
        os.makedirs(folder_source)
        return "\nCreated " + folder_source

#########################################################

def archiveData(days_to_archive,
                basefolder_to_be_archived,
                subfolder_to_be_archived,
                archived_folder_path,
                subfolder1path_to_copy,
                copiedsubfolder1name,
                subfolder2path_to_copy,
                copiedsubfolder2name):
    """
    :param days_to_archive: (integer) Number of days to archive data. Days are converted to seconds.
    :param basefolder_to_be_archived: (string) Base folder (at the top) to be archived, then deleted, then re-created after final archiving is complete.
    :param subfolder_to_be_archived: (string) Subfolder within the base folder to also be archived, then deleted, then re-created after final archiving is complete.
    :param archived_folder_path: (string) Destination folder to where archived data from the basefolder & subfolder will be copied.
    :param subfolder1path_to_copy: (string) Subfolder 1 (for example, a file geodatabase) path to be copied within the basefolder.
    :param copiedsubfolder1name: (string) Name of the file subfolder 1 (file gdb) when copied over to the archive folder.
    :param subfolder2path_to_copy: (string) Subfolder 2 path to be copied within basefolder.
    :param copiedsubfolder2name: (string) Name of subfolder 2 to be copied within basefolder.
    :return:
    """

    currentdate = datetime.date.today()
    timeformat = "%H%M%S"
    currenttime = datetime.datetime.today()
    z = currenttime.strftime(timeformat)

    #Create folder structure if it doesn't exist; If does exist folder will be zipped up & placed in archive directory.     # Then the folders will be deleted and recreated.
    # Check if folders to be archived exist; if not, then make the basefolder, subdirectory folders, & archive folder.
    if not os.path.exists(archived_folder_path):
        os.mkdir(archived_folder_path)

    else:
        print 'Creating archive of survey & report data'
        zf = zipfile.ZipFile(archived_folder_path + "\\" + str(currentdate) + "_" + str(z) + '.zip', mode='w')
        for root, dirs, files in os.walk(subfolder1path_to_copy):
            for f in files:
                print f
                zf.write(subfolder1path_to_copy + "\\" + f, copiedsubfolder1name +"\\" + f, zipfile.ZIP_DEFLATED)

        # iteratively writes files within base folder to zipped archive location
        for root, dirs, files in os.walk(subfolder2path_to_copy):
            for r in files:
                zf.write(subfolder2path_to_copy + "\\" + r, copiedsubfolder2name + "\\" + r, zipfile.ZIP_DEFLATED)

        zf.close()
    print 'Zipped & closed archive'

    #Remove files in archive older than x days
    now = time.time() # returns time in seconds since epoch of 1/1/1970 as floating point number.
    print "Now time: {}".format(now)
    seconds_to_archive = days_to_archive * 60 * 60 * 24 # days_to_archive x 60sec/min x 60min/hour x 24hours/day
    for f in os.listdir(archived_folder_path):
     #if os.stat(archived_folder_path + "\\" + f).st_mtime < now - 1 * 86400:
        if os.stat(archived_folder_path + "\\" + f).st_mtime < now - seconds_to_archive: # seconds for 93 days

            # Delete old ReportAndPhotos folder & file gdb subfolders
            shutil.rmtree(subfolder1path_to_copy)
            shutil.rmtree(subfolder2path_to_copy)

            # Creates new survey folder & ReportAndPhotos in folder that was originally archived
            IfNotExistCreaterFolder(basefolder_to_be_archived)
            IfNotExistCreaterFolder(subfolder_to_be_archived)

            print "Placeholder: then delete the existing gdb here"
#########################################################


# Execute Code

# Archive data for past 3 months, copying the survey folder data (with ReportAndPhoto folder & file gdb) into the archive folder)
archiveData(days_to_archive=1,
            basefolder_to_be_archived=extractpath,
            subfolder_to_be_archived=surveyReportAndPhotosfolder,
            archived_folder_path=archivefolder,
            subfolder1path_to_copy=surveygdb,
            copiedsubfolder1name=surveyname + '.gdb',
            subfolder2path_to_copy=surveyReportAndPhotosfolder,
            copiedsubfolder2name='ReportAndPhotos')

# Creates file structure for newly downloaded survey data from ArcGIS Online
IfNotExistCreaterFolder(downloaddatafolder) # Folder for all surveys downloaded from AGOL
IfNotExistCreaterFolder(extractpath) # Create extract Survey folder if it doesn't exist
IfNotExistCreaterFolder(surveyReportAndPhotosfolder) # Creates ReportAndPhotos folder if doesn't exist

# uniqueobservers = ['ksundeen_mnpower']
# for eachobserver in uniqueobservers:
#     srcCopyFolder = surveyReportAndPhotosfolder + "\\SurveyReport_" + eachobserver.split("_mnpower")[0]
#     destCopyFolder = r"\\users\~" + eachobserver.split("_mnpower")[0] + "$\\share\\" + surveyname
#     destBaseFolder = os.path.dirname(destCopyFolder) # Looks one folder up from the destCopyFolder location
#     copyDirectory(srcCopyFolder, destBaseFolder, destCopyFolder)

