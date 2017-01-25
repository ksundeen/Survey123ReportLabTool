import traceback
import arcpy
import reportlab
import os
import time
import glob
import textwrap
import shutil

# Modules for
import zipfile
import os
import string
import sys
import glob
import json
import urllib, urllib2
from urllib2 import urlopen
import requests
import csv
import datetime
from datetime import timedelta
import shutil

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Flowable, SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether, ListFlowable, ListItem, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import CMYKColor, PCMYKColor
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.textlabels import Label

from PIL import Image as pil_Image

#safetyobservationgdb = r'\\p\files1\mxd\bkeinath\AGOLandServerProjects\Safety Observation Survey\SafetyObservation.gdb' #Location of the downloaded safety observation geodatabase
""" Structure of download folders:
[survey name]
[survey name]\[survey name].gdb
[survey name]\[survey name].gdb\[survey name]           # feature class
[survey name]\[survey name].gdb\[survey name]__ATTACH   # attachments gdb table (only for the Site Photo)
[survey name]\[survey name].gdb\[survey name]__ATTACH   # attachments gdb table (only for the Site Photo)
[survey name]\ReportAndPhotos                           # folder  created in each username's share folder to store the PDF report
[survey name]\ReportAndPhotos\Photos
"""

# Folder & File Paths
surveyname = 'SafetyObservationSurvey'
# http://svn.mnpower.com/svn/its_deo/trunk
downloaddatafolder = 'C:/code/trunk/Projects_Python/Survey123ReportTool/DownloadedData/'
extractpath = 'C:/code/trunk/Projects_Python/Survey123ReportTool/DownloadedData/' + surveyname # Location of our download data folder
surveygdb = extractpath + '/' + surveyname + '_test_09142016.gdb'
surveyfeatureclass = surveygdb + '/' + surveyname # Feature class containing survey responses
surveyReportAndPhotosfolder = extractpath + '/ReportAndPhotos/'

archivefolder = extractpath + 'Archive' # Location of archived data folder


attachmenttables_list =[surveyname+"__ATTACH"]
parenttables_list = [surveyname]  # add surveyname back in to run for the main feature class

arcpy.env.workspace = surveygdb
tables = arcpy.ListTables()
for table in tables:
    if "__ATTACH" in table:
        attachmenttables_list.append(table)
    else:
        parenttables_list.append(table)

print(attachmenttables_list)
print(parenttables_list)


# attachmenttable_list = [
#     'SafetyObservationSurvey__ATTACH',
#     'bodyPositionGoodPic_repeat__ATTACH',
#     'movingObjectsGoodPic_repeat__ATTACH',
#     'lockouttagoutGoodPic_repeat__ATTACH',
#     'permitsGoodPic_repeat__ATTACH',
#     'apparelGoodPic_repeat__ATTACH',
#     'housekeepingGoodPic_repeat__ATTACH',
#     'toolsequipmentGoodPic_repeat__ATTACH',
#     'trafficControlGoodPic_repeat__ATTACH'
# ]

# Functions/Classes

class FooterCanvas(canvas.Canvas):
    """
    Class adds a canvas class to draw the footer of a line and page numbers.
    """
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_canvas(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_canvas(self, page_count):
        page = "Page %s of %s" % (self._pageNumber, page_count)
        x = 128
        self.saveState()

        # Use these to insert a line above the page #s at bottom of pg
        #self.setStrokeColorRGB(0, 0, 0)
        #self.setLineWidth(0.5)
        #self.line(66, 78, letter[0] - 66, 78)

        self.setFont('Helvetica', 10)
        self.drawString(letter[0]-x, 65, page)
        self.restoreState()

class ConditionalSpacer(Spacer):
    """
    Class creates a conditional spacer that can overun on pages.
    http://stackoverflow.com/questions/35494584/reportlab-layouterror-flowable-spacer-too-large
    """
    def wrap(self, availWidth, availHeight):
        height = min(self.height, availHeight-1e-8)
        return (availWidth, height)


class HyperlinkedImage(Image, object):
    """Image with a hyperlink, adopted from http://stackoverflow.com/a/26294527/304209.
    Class based on Dennis Golomazov's answer: http://stackoverflow.com/questions/19596300/reportlab-image-link/39134216#39134216
    Create object with Image=image location; hyperlink=<the hyperlink>
    """

    def __init__(self, filename, hyperlink=None, width=None, height=None, kind='direct',
                 mask='auto', lazy=1, hAlign='CENTER'):
        """The only variable added to __init__() is hyperlink.

        It defaults to None for the if statement used later.
        """
        super(HyperlinkedImage, self).__init__(filename, width, height, kind, mask, lazy, hAlign=hAlign)
        self.hyperlink = hyperlink

    def drawOn(self, canvas, x, y, _sW=0):
        if self.hyperlink:  # If a hyperlink is given, create a canvas.linkURL()
            # This is basically adjusting the x coordinate according to the alignment
            # given to the flowable (RIGHT, LEFT, CENTER)
            x1 = self._hAlignAdjust(x, _sW)
            y1 = y
            x2 = x1 + self._width
            y2 = y1 + self._height
            canvas.linkURL(url=self.hyperlink, rect=(x1, y1, x2, y2), thickness=0, relative=1)
        super(HyperlinkedImage, self).drawOn(canvas, x, y, _sW)

##################################################

class MCLine(Flowable):
    """
    Line flowable --- draws a line in a flowable
    http://two.pairlist.net/pipermail/reportlab-users/2005-February/003695.html
    """

    # ----------------------------------------------------------------------
    def __init__(self, width, height=0):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    # ----------------------------------------------------------------------
    def __repr__(self):
        return "Line(w=%s)" % self.width

    # ----------------------------------------------------------------------
    def draw(self):
        """
        draw the line
        """
        self.canv.line(0, self.height, self.width, self.height)

###################################################

def addPageNumber(canvas, doc):
   """
   Add the page number
   """
   page_num = canvas.getPageNumber()
   text = "{0}".format(page_num)
   canvas.drawRightString(8*inch, 8*inch, text)

###################################################

def addBadCommentBullets(yesnofieldnum, titletext):
    """
    :param titletext: (string) Text before row value such as "Title: "
    :param rownum: (integer) Index number of field row to reference the titletext's row value
    :return:
    """
    if row[yesnofieldnum] == 'nooption':
        ptext = titletext + "<i>" + str(row[yesnofieldnum+2]) + "</i>"
        Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

        # Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))
        my_bullets = ListFlowable([
            ListItem(Paragraph(ptext, styles['Normal']),
                     leftIndent=35, value='circle',
                     bulletColor=CMYKColor(0.81, 0.45, 0.53, 0.23)
                     )
        ],
            bulletType='bullet',
            start='circle',
            leftIndent=10
        )
        Story.append(my_bullets)

###################################################

def addHeaderTitle(titletext):
    ptext = "<font color=DimGray size=16><b>" + titletext + "</b></font>" # pick colors: http://www.w3schools.com/colors/colors_hex.asp
    Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

###################################################

def addSubHeaderTitle(titletext):
    ptext = "<font color=RoyalBlue size=13><u><i><b>" + titletext + "</b></i></u></font>" # pick colors: http://www.w3schools.com/colors/colors_hex.asp
    Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

###################################################

def addSmallText(titletext):
    ptext = "<font color=DimGray size=9><i>" + titletext + "</i></font>"
    Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

###################################################

def addBoldNormalParagraphText(titletext):
    """
    :param titletext: (string) Text before row value such as "Title: "
    :param rownum: (integer) Index number of field row to reference the titletext's row value
    :return:
    """
    ptext = "<b>" + titletext + "</b>"
    Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

###################################################

def addNormalParagraphText(titletext, rownum):
    """
    :param titletext: (string) Text before row value such as "Title: "
    :param rownum: (integer) Index number of field row to reference the titletext's row value
    :return:
    """
    if row[rownum] == 'yesoption' or str(row[rownum]) == 'yes':
        ptext = "<b>" + titletext + "</b><i>Yes</i>"
    elif row[rownum] == 'nooption' or str(row[rownum]) == 'no':
        ptext = "<b>" + titletext + "</b><i>No</i>"
    elif row[rownum] is None:
        ptext = "<b>" + titletext + "</b><i>-</i>"
    else: ptext = "<b>" + titletext + "</b><i>" + str(row[rownum]) + "</i>"
    Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

###################################################

def getAnswerOrChangeNoToDash(rownum):
    """
    :param rownum: (integer) the field index value of attribute table where the field value will originate. For example, 1 would be for row index 1 in field attribute table.
    :return: returns the dash "-" if the string value of the index is no or nooption.
    """
    if row[rownum] is not None:
        return str(row[rownum])
    elif row[rownum] is None:
        return "-"

###################################################

def create_bar_graph(headerList, dataTable, outputgraphname, graphformat):
    """
    :param headerList: list of header fields for the dataTable
    :param dataTable: list of data values
    :param outputgraphname: output filename of exported graph
    :param graphformat: output graph file format, can be 'svg', 'pdf', 'png, 'jpg', 'eps', 'ps'
    Creates a bar graph in a PDF. Code from http://www.blog.pythonlibrary.org/2016/02/18/reportlab-how-to-add-charts-graphs/
    """
    # d = Drawing(280, 250)
    d = Drawing(600, 300)  # (x, y) for how large the image/output format will be
    bar = VerticalBarChart()
    bar.x = 40  # coordinate where x-axis is drawn
    bar.y = 45  # coordinate where y-axis is drawn
    # data = [[1, 2, 3, None, None, None, 5],
    #         [10, 5, 2, 6, 8, 3, 5],
    #         [5, 7, 2, 8, 8, 2, 5],
    #         [2, 10, 2, 1, 8, 9, 5],
    #         ]
    bar.data = dataTable

    bar.categoryAxis.categoryNames = headerList

    # bar.bars[0].fillColor = PCMYKColor(75, 0, 100, 20, alpha=85) # this would be for another set row of data to add color to
    # bar.bars.fillColor = PCMYKColor(70, 64, 0, 0, alpha=85)  # base color for 1st data row; bright green
    # bar.bars.fillColor = PCMYKColor(0,0,0,0, alpha=85)  # base color for 1st data row; teal light green
    bar.bars[0].fillColor = PCMYKColor(28,1,30,16)
    bar.width = 500
    bar.height = 200
    bar.barLabels.fontName = 'Helvetica'
    bar.barLabels.fontSize = 12
    bar.barLabels.nudge = 7
    bar.barLabels.dy = 3
    bar.barLabelFormat = '%d'
    bar.valueAxis.labels.fontName = 'Helvetica'  # y-axis
    bar.valueAxis.labels.fontSize = 12
    bar.categoryAxis.labels.fontName = 'Helvetica'  # x-axis
    bar.categoryAxis.labels.fontSize = 14
    bar.categoryAxis.visibleTicks = 1
    bar.categoryAxis.labels.angle = 45
    bar.categoryAxis.labels.dy = -15  # adjusts month labels down
    bar.categoryAxis.labels.dx = -5  # adjusts month labels over

    d.add(bar, '')

    # Output image will be re-written on every call
    d.save(formats=[graphformat], outDir='.', fnRoot = outputgraphname)

###################################################

def checkDates(dateToCheck, startMonth, endMonth, startDay=1, endDay=1, startYear=2016, endYear=2016):
    if (dateToCheck >= datetime.datetime(startYear, startMonth, startDay) and dateToCheck < datetime.datetime(endYear, endMonth, endDay)):
        return 1

###################################################

# Function to archive a directory
# copy archiveData function from archive_test.py
# def archiveData(basefolder_to_be_archived, subfolder_to_be_archived, archived_folder_path, gdbpath_to_copy, copiedgdbname, subfolder_to_copy, copiedsubfoldername):

###################################################

def IfNotExistCreaterFolder(folder_source):
    """
    :param folder_source: folder name being checked for whether it exists, if it doesn't then a folder is created.
    :return:
    """
    if not os.path.exists(folder_source):
        os.makedirs(folder_source)
        return "\nCreated " + folder_source

###################################################

# Recursively copies source folder to destination folder; http://pythoncentral.io/how-to-recursively-copy-a-directory-folder-in-python/
def copyOrCreateDirectoryToShare(srcCopyFolder, destBaseFolder, destCopyFolder):
    """
    :param srcCopyFolder: (string) Source folder to be copied.
    :param desBaseFolder: (string) Destination base folder. Should be one level up from destCopyFolder.
    :param destCopyFolder: (string) Destination copy folder to be copied within the destBaseFolder.
    :return:
    """
    try:
        # modify to allow to overwrite existing data...
        #archivefolder(destBaseFolder)
        if not os.path.exists(destBaseFolder):
            os.makedirs(destBaseFolder)
            print("\nCreated {0} and {1}".format(destBaseFolder, destCopyFolder))
            shutil.copytree(srcCopyFolder, destCopyFolder)

        elif os.path.exists(destBaseFolder) and not os.path.exists(destCopyFolder):
            shutil.copytree(srcCopyFolder, destCopyFolder)
            print("\nCreated {0} and {1}".format(destBaseFolder, destCopyFolder))

        # If dest folder already exists, overwrite files within
        elif os.path.exists(destBaseFolder) and os.path.exists(destCopyFolder):
            # for each file in dest folder, copy or overwrite
            for src_dir, dirs, files in os.walk(srcCopyFolder):
                dst_dir = src_dir.replace(srcCopyFolder, destCopyFolder) # creates destination folder path
                for file_ in files:
                    src_file = os.path.join(src_dir, file_)
                    dst_file = os.path.join(dst_dir, file_)
                    # if os.path.exists(dst_file):
                    #     os.remove(dst_file)
                    shutil.copy(src_file, dst_dir)

        print("Copied reports & pictures over into {0}".format(destBaseFolder))

    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)
    except IOError as e:
        print('Directory/file does not exist: %s' % e)
    except WindowsError as e:
        print('Access is denied to folder: %s' % e)

###################################################

def createHyperlinkedSitePhotoObject(surveyglobalid, surveyname, photoDictionary, baseReportFolder, observerName):
    """
    Returns the photo location and X,Y tuple of GPS location for site photo in main feature class stored in a dictionary.
    :param surveyglobalid: the gdb's global id recorded for the particular survey
    :param surveyname: the main feature class of the gdb survey
    :param photoDictionary: dictionary in format: {rowid: [[Editor, parenttable, photofilename, SHAPE], [Editor, parenttable, photofilename, SHAPE (or) comments]...etc.]}, with the value being a list of lists to allow for all the pictures associated with each survey}
            ...was built using photoCommentsDict[parentrow[2]] = [[[parentrow[4], parenttable, filename, parentrow[1]],[parentrow[4], parenttable, filename, parentrow[1]]]
    :param baseReportFolder: folder where Report and Pictures will be accessed; this can be an absolute or relative file path.
    :param observerName: the user name
    :return:
    """
    # Check if rowid field value is in the photoCommentsDict keys, then access the photoname & commentvalue in photoCommentsDict
    for key, vals in photoDictionary.iteritems():
        # If dictionary's key (rowid) = the surveyglobalid AND username = our iterating observer name AND dictionary's parentable == parentable (what we listed for the good comments question), then we grab the photoname from the dictionary
        if key == surveyglobalid:
            # Iterate through value list for each key (globalid)
            for listvalue in vals:
                # Checking within each list of values within value list for photoCommentsDict's key for observer & parenttable name (needed to check for each question in survey based on table).
                if listvalue[0] == observerName and listvalue[1] == surveyname:
                    # print("Found & added photo for key ({0}) by observer ({1}) in parenttable ({2})".format(key, observerName, surveyname))

                    # If listvalue[2] (the site photoname) is None, (bascially no site photo taken), then still create a hyperlinked site photo pic.
                    if listvalue[2] is None:
                        if listvalue[1] == surveyname:
                            sitegps = listvalue[3]  # Grabs xy coord of site location, will be creating a google image from this lat/long.
                            x_long = str(sitegps[0])
                            y_lat = str(sitegps[1])
                            # example google link: 'http://www.google.com/maps/place/49.46800006494457,17.11514008755796/@49.46800006494457,17.11514008755796,17'
                            sitegps_hyperlink = 'http://www.google.com/maps/place/' + y_lat + ',' + x_long + '/@' + y_lat + ',' + x_long + '/' + ',17z/data=!3m1!1e3'

                        else:
                            print("Something didn't work with the GPS location")

                        if listvalue[1] == surveyname:
                            siteHyperlink = HyperlinkedImage('siteimage.png', hyperlink=sitegps_hyperlink,
                                                             width=1 * inch, height=1 * inch)
                            return (None, siteHyperlink)

                    # If listvalue[2] (the site photoname) is filled in, (site photo was taken), then create hyperlinked site photo and hyperlinked GPS location photo
                    else:
                        photoname = listvalue[2]  # should access photoCommentsDict{rowid}: photoname
                        # Checks if the parentrow comment is empty (in related tables) & checks that the the dict item is NOT from the parent table's surveyname feature class (this is the point feature class, which doesn't have any comments in it for good pictures)
                        # If SHAPE or comments field in dictionary == None or NOT equal to SurveyName tablename, then record the commentvalue as 'No Comment'

                        if listvalue[1] == surveyname:
                            sitegps = listvalue[3]  # Grabs xy coord of site location, will be creating a google image from this lat/long.
                            x_long = str(sitegps[0])
                            y_lat = str(sitegps[1])
                            # example google link: 'http://www.google.com/maps/place/49.46800006494457,17.11514008755796/@49.46800006494457,17.11514008755796,17'
                            sitegps_hyperlink = 'http://www.google.com/maps/place/' + y_lat + ',' + x_long +  '/@' + y_lat + ',' + x_long + '/' + ',17z/data=!3m1!1e3'

                        else:
                            print("Something didn't work with the GPS location")

                        photofolder = baseReportFolder + "SurveyReport_" + observerName.split("_mnpower")[0] + "/Photos/"
                        photolocation = photofolder + photoname
                        #pholder = open(photolocation, "rb")  # holder for image, if only placing a non-hyperlinked image

                        # Access image's width & height to use as parameters when placing in PDF
                        with pil_Image.open(photolocation) as myimage:
                            imageWidth, imageHeight = myimage.size

                        if listvalue[1] == surveyname:
                            myHyperlinkedImage = HyperlinkedImage(photolocation, hyperlink=photolocation, width=imageWidth*0.25, height=imageHeight*0.25)
                            siteHyperlink = HyperlinkedImage('siteimage.png', hyperlink=sitegps_hyperlink, width=1*inch, height=1*inch)
                            return (myHyperlinkedImage, siteHyperlink)

                else: print("Didn't find key: {0} for observer ({1}) in parenttable ({2}) in photoCommentsDict".format(key, observerName, surveyname))

###################################################

##==For Share PDF==##
def createShareHyperlinkedSitePhotoObject(surveyglobalid, surveyname, photoDictionary, observerName):
    """
    Returns the photo location and X,Y tuple of GPS location for site photo in main feature class stored in a dictionary. The hyperlink points to the sharedrive filepath for the picture.
    :param surveyglobalid: the gdb's global id recorded for the particular survey
    :param surveyname: the main feature class of the gdb survey
    :param photoDictionary: dictionary in format: {rowid: [[Editor, parenttable, photofilename, SHAPE], [Editor, parenttable, photofilename, SHAPE (or) comments]...etc.]}, with the value being a list of lists to allow for all the pictures associated with each survey}
            ...was built using photoCommentsDict[parentrow[2]] = [[[parentrow[4], parenttable, filename, parentrow[1]],[parentrow[4], parenttable, filename, parentrow[1]]]
    :param observerName: the user name
    :return:
    """
    # Check if rowid field value is in the photoCommentsDict keys, then access the photoname & commentvalue in photoCommentsDict
    for key, vals in photoDictionary.iteritems():
        # If dictionary's key (rowid) = the surveyglobalid AND username = our iterating observer name AND dictionary's parentable == parentable (what we listed for the good comments question), then we grab the photoname from the dictionary
        if key == surveyglobalid:
            # Iterate through value list for each key (globalid)
            for listvalue in vals:
                # Checking within each list of values within value list for photoCommentsDict's key for observer & parenttable name (needed to check for each question in survey based on table).
                if listvalue[0] == observerName and listvalue[1] == surveyname:
                    # print("Found & added photo for key ({0}) by observer ({1}) in parenttable ({2})".format(key, observerName, surveyname))

                    # If listvalue[2] (the site photoname) is None, (bascially no site photo taken), then still create a hyperlinked site photo pic.
                    if listvalue[2] is None:
                        if listvalue[1] == surveyname:
                            sitegps = listvalue[
                                3]  # Grabs xy coord of site location, will be creating a google image from this lat/long.
                            x_long = str(sitegps[0])
                            y_lat = str(sitegps[1])
                            # example google link: 'http://www.google.com/maps/place/49.46800006494457,17.11514008755796/@49.46800006494457,17.11514008755796,17'
                            sitegps_hyperlink = 'http://www.google.com/maps/place/' + y_lat + ',' + x_long + '/@' + y_lat + ',' + x_long + '/' + ',17z/data=!3m1!1e3'

                        else:
                            print("Something didn't work with the GPS location")

                        if listvalue[1] == surveyname:
                            siteHyperlink = HyperlinkedImage('siteimage.png', hyperlink=sitegps_hyperlink,
                                                             width=1 * inch, height=1 * inch)
                            return (None, siteHyperlink)

                    # If listvalue[2] (the site photoname) is filled in, (site photo was taken), then create hyperlinked site photo and hyperlinked GPS location photo
                    else:
                        photoname = listvalue[2]  # should access photoCommentsDict{rowid}: photoname
                        # Checks if the parentrow comment is empty (in related tables) & checks that the the dict item is NOT from the parent table's surveyname feature class (this is the point feature class, which doesn't have any comments in it for good pictures)
                        # If SHAPE or comments field in dictionary == None or NOT equal to SurveyName tablename, then record the commentvalue as 'No Comment'

                        if listvalue[1] == surveyname:
                            sitegps = listvalue[
                                3]  # Grabs xy coord of site location, will be creating a google image from this lat/long.
                            x_long = str(sitegps[0])
                            y_lat = str(sitegps[1])
                            # example google link: 'http://www.google.com/maps/place/49.46800006494457,17.11514008755796/@49.46800006494457,17.11514008755796,17'
                            sitegps_hyperlink = 'http://www.google.com/maps/place/' + y_lat + ',' + x_long + '/@' + y_lat + ',' + x_long + '/' + ',17z/data=!3m1!1e3'

                        else:
                            print("Something didn't work with the GPS location")

                        ##===============================================================================##
                        ##============ New code for changing filepath to share folder====================##
                        shareFolderPhotoFolder = "//users/~" + observerName.split("_mnpower")[0] + "$/share/" + surveyname + "/CurrentSurveyReport_" + observerName.split("_mnpower")[0] + "/Photos/"
                        ##===============================================================================##

                        photolocation = shareFolderPhotoFolder + photoname
                        # pholder = open(photolocation, "rb")  # holder for image, if only placing a non-hyperlinked image

                        # Access image's width & height to use as parameters when placing in PDF
                        with pil_Image.open(photolocation) as myimage:
                            imageWidth, imageHeight = myimage.size

                        if listvalue[1] == surveyname:
                            myHyperlinkedImage = HyperlinkedImage(photolocation, hyperlink=photolocation,
                                                                  width=imageWidth * 0.25,
                                                                  height=imageHeight * 0.25)
                            siteHyperlink = HyperlinkedImage('siteimage.png', hyperlink=sitegps_hyperlink,
                                                             width=1 * inch, height=1 * inch)
                            return (myHyperlinkedImage, siteHyperlink)

                else:
                    print("Didn't find matching globalid {0} for ({1}) in parenttable ({2})".format(
                        key, observerName, surveyname))

                ###################################################

###################################################

def createGoodHyperlinkPhotoCommentObject(surveyglobalid, parenttable, photoDictionary, baseReportFolder, observerName):
    """
    Returns hyperlinked good comments photo and/or comments from the photoCommentsDict dictionary.
    :param surveyglobalid: the gdb's global id recorded for the particular survey
    :param parenttable: related tables within the survey gdb (for the repeats for example)
    :param photoDictionary: dictionary in format: {rowid: [[Editor, parenttable, photofilename, SHAPE], [Editor, parenttable, photofilename, SHAPE (or) comments]...etc.]}, with the value being a list of lists to allow for all the pictures associated with each survey}
            ...was built using photoCommentsDict[parentrow[2]] = [[[parentrow[4], parenttable, filename, parentrow[1]],[parentrow[4], parenttable, filename, parentrow[1]]]
    :param baseReportFolder: folder where Report and Pictures will be accessed; this can be an absolute or relative file path.
    :param observerName: the user name
    :return:
    """
    # Check if rowid field value is in the photoCommentsDict keys, then access the photoname & commentvalue in photoCommentsDict
    for key, vals in photoDictionary.iteritems():
        print("photoComments key: {0}".format(key))
        # print key, vals
        # If dictionary's key (rowid) = the surveyglobalid AND username = our iterating observer name AND dictionary's parentable == parentable (what we listed for the good comments question), then we grab the photoname from the dictionary
        if key == surveyglobalid:
            print("Found photoComments key: {0}".format(key))
            # Iterate through value list for each key (globalid)
            for listvalue in vals:
                print("Iterating through photoCommentDic listvalue: {0}".format(listvalue))
                # Checking within each list of values within value list for photoCommentsDict's key for observer & parenttable name (needed to check for each question in survey based on table).
                if listvalue[0] == observerName and listvalue[1] == parenttable:
                    print("Found & added photo for key ({0}) by observer ({1}) in parenttable ({2})".format(key, observerName, parenttable))

                    # If listvalue[2] (the site photoname) is None, (bascially no site photo taken), then still create a hyperlinked site photo pic.
                    if listvalue[2] is None:
                        if listvalue[3] is None:
                            commentvalue = 'No comment'
                        elif listvalue[3] != None:
                            commentvalue = listvalue[3]  # comments in this index if there are any
                        else:
                            print("Something didn't work with the comments value")
                            commentvalue = "Something didn't work with the comments value"

                        return (None, commentvalue)

                    # If listvalue[2] (there is a site photo), then create hyperlinked site photo and hyperlinked GPS location photo
                    else:
                        photoname = listvalue[2]  # should access photoCommentsDict{rowid}: photoname
                        # Checks if the parentrow comment is empty (in related tables) & checks that the the dict item is NOT from the parent table's surveyname feature class (this is the point feature class, which doesn't have any comments in it for good pictures)
                        # If SHAPE or comments field in dictionary == None or NOT equal to SurveyName tablename, then record the commentvalue as 'No Comment'
                        if str(listvalue[3]) == 'None':
                            commentvalue = 'No comment'
                        elif str(listvalue[3]) != 'None':
                            commentvalue = listvalue[3]  # comments in this index if there are any
                        else:
                            print("Something didn't work with the comments value")
                            commentvalue = "Something didn't work with the comments value"

                        photofolder = baseReportFolder + "SurveyReport_" + observerName.split("_mnpower")[
                            0] + "/Photos/"
                        photolocation = photofolder + photoname
                        # pholder = open(photolocation, "rb")  # holder for image, if only placing a non-hyperlinked image

                        # Access image's width & height to use as parameters when placing in PDF
                        with pil_Image.open(photolocation) as myimage:
                            imageWidth, imageHeight = myimage.size
                        myHyperlinkedImage = HyperlinkedImage(photolocation, hyperlink=photolocation,
                                                              width=imageWidth * 0.25, height=imageHeight * 0.25)
                        return (myHyperlinkedImage, commentvalue)

                else: print("Didn't find photoCommentDic listvalue: {0}".format(listvalue))
        else: print("Didn't find photoComments key: {0} for ({1}) in parenttable ({2})".format(key, observerName, parenttable))

###################################################

##==For Share PDF==##
def createShareGoodHyperlinkPhotoCommentObject(surveyglobalid, parenttable, photoDictionary, observerName):
    """
    Returns hyperlinked good comments photo and/or comments from the photoCommentsDict dictionary. The hyperlink points to the sharedrive filepath for the picture.
    :param surveyglobalid: the gdb's global id recorded for the particular survey
    :param parenttable: related tables within the survey gdb (for the repeats for example)
    :param photoDictionary: dictionary in format: {rowid: [[Editor, parenttable, photofilename, SHAPE], [Editor, parenttable, photofilename, SHAPE (or) comments]...etc.]}, with the value being a list of lists to allow for all the pictures associated with each survey}
            ...was built using photoCommentsDict[parentrow[2]] = [[[parentrow[4], parenttable, filename, parentrow[1]],[parentrow[4], parenttable, filename, parentrow[1]]]
    :param observerName: the user name
    :return:
    """
    # Check if rowid field value is in the photoCommentsDict keys, then access the photoname & commentvalue in photoCommentsDict
    for key, vals in photoDictionary.iteritems():
        # If dictionary's key (rowid) = the surveyglobalid AND username = our iterating observer name AND dictionary's parentable == parentable (what we listed for the good comments question), then we grab the photoname from the dictionary
        if key == surveyglobalid:
            print("Found photoComments key: {0}".format(key))
            # Iterate through value list for each key (globalid)
            for listvalue in vals:
                # Checking within each list of values within value list for photoCommentsDict's key for observer & parenttable name (needed to check for each question in survey based on table).
                if listvalue[0] == observerName and listvalue[1] == parenttable:

                    # If listvalue[2] (the site photoname) is None, (bascially no site photo taken), then still create a hyperlinked site photo pic.
                    if listvalue[2] is None:
                        if listvalue[3] is None:
                            commentvalue = 'No comment'
                        elif listvalue[3] != None:
                            commentvalue = listvalue[3]  # comments in this index if there are any
                        else:
                            print("Something didn't work with the comments value")
                            commentvalue = "Something didn't work with the comments value"

                        return (None, commentvalue)

                    # If listvalue[2] (there is a site photo), then create hyperlinked site photo and hyperlinked GPS location photo
                    else:
                        photoname = listvalue[2]  # should access photoCommentsDict{rowid}: photoname
                        # Checks if the parentrow comment is empty (in related tables) & checks that the the dict item is NOT from the parent table's surveyname feature class (this is the point feature class, which doesn't have any comments in it for good pictures)
                        # If SHAPE or comments field in dictionary == None or NOT equal to SurveyName tablename, then record the commentvalue as 'No Comment'
                        if str(listvalue[3]) == 'None':
                            commentvalue = 'No comment'
                        elif str(listvalue[3]) != 'None':
                            commentvalue = listvalue[3]  # comments in this index if there are any
                        else:
                            print("Something didn't work with the comments value")
                            commentvalue = "Something didn't work with the comments value"

##===============================================================================##
##============ New code for changing filepath to share folder====================##
                        shareFolderPhotos = "//users/~" + observerName.split("_mnpower")[0] + "$/share/" + surveyname + "/CurrentSurveyReport_" + observerName.split("_mnpower")[0] + "/Photos/"
##===============================================================================##

                        photolocation = shareFolderPhotos + photoname
                        # Access image's width & height to use as parameters when placing in PDF
                        with pil_Image.open(photolocation) as myimage:
                            imageWidth, imageHeight = myimage.size
                        myHyperlinkedImage = HyperlinkedImage(photolocation, hyperlink=photolocation,
                                                              width=imageWidth * 0.25, height=imageHeight * 0.25)
                        return (myHyperlinkedImage, commentvalue)

                else: print("Didn't find photoCommentDic listvalue: {0}".format(listvalue))
        else: print("Didn't find matching globalid {0} for ({1}) in parenttable ({2})".format(key, observerName, parenttable))

###################################################

def addSitePhotoAndGPSPic(photoObject):
    """
    :param photoObject: HyperlinkedPhoto object as a tuple of a hyperlinked photo [0] and a hyperlinked photo pointing to a Google Maps location of the GPS coordinates
        photoObject[0] is an image class object
        photoObject[1] is an image class object
    :return:
    """
    # Sets text to be drawn centered
    styles = getSampleStyleSheet()
    style_center = styles["Normal"]
    style_center.alignment = TA_CENTER
    if photoObject is None:
        addSmallText('(no photo taken)')  # This isn't working...not sure why not. It should print this on the PDF when there's no site photo uploaded
    else:
        # No photo object
        if photoObject is None:
            addSmallText('(no photo taken)')

        else:
            # No photo, but has GPS locations
            if (photoObject[0] is None) and (photoObject[1] is not None):
                Story.append(spacer)
                addSmallText('(no photo taken)')
                Story.append(spacer)
                Story.append(KeepTogether(photoObject[1]))
                Story.append(KeepTogether(Paragraph("Click on Globe to open a Google Maps location of your site.", style_center)))
                Story.append(spacer)
                # print("Added photo GPS location")

            # Has photo, but not comments/GPS locations
            elif (photoObject[0] is not None) and (photoObject[1] is None):
                Story.append(spacer)
                Story.append(KeepTogether(photoObject[0]))
                # print("Appended hyperlinked site photo")
                Story.append(spacer)
                addSmallText('(no GPS points taken)')

            # Has both photo and comments/GPS locations
            elif (photoObject[0] is not None) and (photoObject[1] is not None):
                Story.append(spacer)
                Story.append(KeepTogether(photoObject[0]))
                # print("Appended hyperlinked photo")
                Story.append(spacer)
                Story.append(KeepTogether(photoObject[1]))
                Story.append(KeepTogether(Paragraph("Click on Globe to open a Google Maps location of your site.", style_center)))
                # print("Added hyperlinked GPS location photo ")

            else:
                print("Something went wrong with adding photo & comments/GPS locations to PDF")

###################################################

def addPhotoAndComment(photoObject):
    """
    :param photoObject: HyperlinkedPhoto object as a tuple of a hyperlinked photo [0] and its comment [1]
        photoObject[0] is an image class object
        photoObject[1] is a text string
    :return:
    """
    # Sets text to be drawn centered
    styles = getSampleStyleSheet()
    style_center = styles["Normal"]
    style_center.alignment = TA_CENTER
    style_left = styles["Normal"]
    style_left.alignment = TA_LEFT

    # No photo object
    if photoObject is None:
        addSmallText('(no photo taken)')

    # Photo Object is not None
    else:
        # No photo, but has comments/GPS locations
        if (photoObject[0] is None) and (photoObject[1] is not None):
            Story.append(spacer)
            addSmallText('(no photo taken)')
            Story.append(KeepTogether(Paragraph("<b>-Good Behavior Comments: </b><i>" + photoObject[1] + "</i>", style_center)))
            # print("Added photo comments")

        # Has photo, but not comments/GPS locations
        elif (photoObject[0] is not None) and (photoObject[1] is None):
            Story.append(spacer)
            Story.append(KeepTogether(photoObject[0]))
            # print("Appended hyperlinked photo")
            Story.append(spacer)
            addSmallText('<i>(no comments added)</i>')

        # Has both photo and comments/GPS locations
        elif (photoObject[0] is not None) and (photoObject[1] is not None):
            Story.append(spacer)
            Story.append(KeepTogether(photoObject[0]))
            # print("Appended hyperlinked photo")
            Story.append(spacer)
            Story.append(KeepTogether(Paragraph("<b>-Good Behavior Comments: </b><i>" + photoObject[1] + "</i>", style_center)))
            # print("Added photo comments")

        else:
            print("Something went wrong with adding photo & comments to PDF")

###################################################

def addGoodBadPhotoCommentsToPDF(pdf_parentable, pdf_parentable_goodbad_rownum, subheadertitle, subheader_smalltext):
    """
    :param pdf_parentable: Geodatabase table name where good behavior comments are located
    :param pdf_parentable_goodbad_rownum: field index value (integer) where survey answers are held for question of whether a good or bad behavior was observed.
    :param pdf_parentable_good_rownum:
    :param pdf_parentable_bad_rownum:
    :param subheadertitle:
    :param subheader_smalltext:
    :return:
    """
    # print("{0} answered? {1}".format(subheadertitle, row[pdf_parentable_goodbad_rownum]))
    if str(row[pdf_parentable_goodbad_rownum]) == "yes" or str(row[pdf_parentable_goodbad_rownum]) == "yesoption":
        addSubHeaderTitle(subheadertitle)
        addSmallText(subheader_smalltext)
        Story.append(spacer)

        # Add in Positive Comments & Photo
        if str(row[pdf_parentable_goodbad_rownum+1]) == "yes" or str(row[pdf_parentable_goodbad_rownum+1]) == "yesoption":
            addNormalParagraphText("<b>-Were Good Behaviors Observed? </b> ", pdf_parentable_goodbad_rownum)
            # Checking in photoCommentDict for comments & photos
            for k in photoCommentsDict.iterkeys():
                if k == row[1]:  # row[1] is globalid
                    # print("Found surveyid in photoCommentDict for: {0}".format(k))
                    myphoto = createGoodHyperlinkPhotoCommentObject(surveyglobalid=str(row[1]),
                                                              parenttable=pdf_parentable,
                                                              photoDictionary=photoCommentsDict,
                                                              baseReportFolder=surveyReportAndPhotosfolder,
                                                              observerName=eachobserver)
                    addPhotoAndComment(myphoto)
                    del myphoto

            Story.append(spacer)

        # Add in Questionable Comments
        if str(row[pdf_parentable_goodbad_rownum+2]) == "yes" or str(row[pdf_parentable_goodbad_rownum+2]) == "yesoption":
            addNormalParagraphText("<b>-Were Questionable Behaviors Observed? </b> ", row[pdf_parentable_goodbad_rownum+2])
            addNormalParagraphText("<b>-Questionable Behavior Comments: </b>", pdf_parentable_goodbad_rownum+3)

        Story.append(spacer)

###################################################

##==For Share PDF==##
def addShareGoodBadPhotoCommentsToPDF(pdf_parentable, pdf_parentable_goodbad_rownum, subheadertitle, subheader_smalltext, observerUserName):
    """
    Function returns good or bad photo comments associated with a photo. The hyperlink points to the sharedrive filepath for the picture.
    :param pdf_parentable: Geodatabase table name where good behavior comments are located
    :param pdf_parentable_goodbad_rownum: field index value (integer) where survey answers are held for question of whether a good or bad behavior was observed.
    :param pdf_parentable_good_rownum:
    :param pdf_parentable_bad_rownum:
    :param subheadertitle:
    :param subheader_smalltext:
    :param observerUserName: the string name of the user to iterate through; I used a different name than eachobserver since this variable is also used in 2 other related functions & I didn't want to get confused with observer name variables. The variable "observerName" is already used in the function "createShareGoodHyperlinkPhotoCommentObject" below.
    :return:
    """
    if str(row[pdf_parentable_goodbad_rownum]) == "yes" or str(row[pdf_parentable_goodbad_rownum]) == "yesoption":
        addSubHeaderTitle(subheadertitle)
        addSmallText(subheader_smalltext)
        Story.append(spacer)

        # Add in Positive Comments & Photo
        if str(row[pdf_parentable_goodbad_rownum+1]) == "yes" or str(row[pdf_parentable_goodbad_rownum+1]) == "yesoption":
            addNormalParagraphText("<b>-Were Good Behaviors Observed? </b> ", pdf_parentable_goodbad_rownum)
            # Checking in photoCommentDict for comments & photos
            for k in photoCommentsDict.iterkeys():
                if k == row[1]:  # row[1] is globalid
                    myphoto = createShareGoodHyperlinkPhotoCommentObject(surveyglobalid=str(row[1]),
                                                              parenttable=pdf_parentable,
                                                              photoDictionary=photoCommentsDict,
                                                              observerName=observerUserName)
                    addPhotoAndComment(myphoto)
                    del myphoto

            Story.append(spacer)

        # Add in Questionable Comments
        if str(row[pdf_parentable_goodbad_rownum+2]) == "yes" or str(row[pdf_parentable_goodbad_rownum+2]) == "yesoption":
            addNormalParagraphText("<b>-Were Questionable Behaviors Observed? </b> ", row[pdf_parentable_goodbad_rownum+2])
            addNormalParagraphText("<b>-Questionable Behavior Comments: </b>", pdf_parentable_goodbad_rownum+3)

###################################################

def deleteFolderAndData(folder_source):
    """
    Deletes folder and all data contained in folder path
    :param folder_source: (string) Path of folder directory to be deleted. All data contained in folder will also be deleted.
    :return:
    """
    try:
        if os.path.exists(folder_source):
            shutil.rmtree(folder_source)
        elif not os.path.exists(folder_source):
            print(folder_source + " wasn't removed because it doesn't exist")
    except:
        print(folder_source + " wasn't removed. Something else when wrong.")

###################################################

def sendRequest(url, data):
    """
    # Connects to ArcGIS Online to download file gdb
    :param url: url for AGOL account
    :param data: not sure...
    :return:
    """
    result = urllib2.urlopen(url, data).read()
    jres = json.loads(result)
    return jres

###################################################

def getToken(username, password):
    data = {'username': username,
            'password': password,
            'referer': 'https://www.arcgis.com',
            'expiration': '1440',
            'f': 'json'}
    url = 'https://arcgis.com/sharing/rest/generateToken'
    jres = sendRequest(url, urllib.urlencode(data))
    print jres
    return jres['token']

"""======= Archiving Functions...======="""
###################################################
# # Archive data for past 3 months, copying the survey folder data (with ReportAndPhoto folder & file gdb) into the archive folder)
# archiveData(basefolder_to_be_archived=extractpath,
#             subfolder_to_be_archived=surveyReportAndPhotosfolder,
#             archived_folder_path=archivefolder,
#             gdbpath_to_copy=surveygdb,
#             copiedgdbname=surveyname + '.gdb',
#             subfolder_to_copy=surveyReportAndPhotosfolder,
#             copiedsubfoldername='ReportAndPhotos')


# token = getToken('ALLETEPublic', '$3rv1c361$')  # need to add this user to the survey app group; should be a non-enterprise user account
# replicaparams = urllib.urlencode({
#     "token": token,
#     "f": "json",
#     "replicaName": "testreplica",
#     "layers": "0",
#     "geometryType": "esriGeometryPoint",
#     "returnAttachments": "true",
#     "returnAttachmentsDataByUrl": "true",
#     "transportType": "esriTransportTypeEmbedded",
#     "async": "false",
#     "syncModel": "none",
#     "dataFormat": "filegdb"})
# print replicaparams

# Creates file structure for newly downloaded survey data from ArcGIS Online
IfNotExistCreaterFolder(downloaddatafolder) # Folder for all surveys downloaded from AGOL
IfNotExistCreaterFolder(extractpath) # Create extract Survey folder if it doesn't exist
IfNotExistCreaterFolder(surveyReportAndPhotosfolder) # Creates ReportAndPhotos folder if doesn't exist

"""======Code to create replicas...======="""
####
#
# # Clean out folder in survey *.gdb
# if arcpy.Exists(surveygdb):
#     print "Deleting GDB files"
#     arcpy.Delete_management(surveygdb)
#     for file in glob.glob(extractpath + '\\*zip'):
#         os.remove(file)
#
#
# """ For Storm Damage Audit survey, there are 3 feature services published into AGOL that we'll need to download:
# poles_v5 = "http://services.arcgis.com/ehV0YC56b0w2eenG/arcgis/rest/services/StormAssessment_Demo_Poles_v5/FeatureServer/createReplica"
# fieldlayers = "http://services.arcgis.com/ehV0YC56b0w2eenG/arcgis/rest/services/StormAssessment_Demo_FieldLayers_v2/FeatureServer/createReplica"
# databaselayers = "http://services.arcgis.com/ehV0YC56b0w2eenG/arcgis/rest/services/StormAssessment_Demo_DatabaseFeatures/FeatureServer/createReplica"
# url_list = [poles_v5, fieldlayers, databaselayers]
# """
#
# # Service URL
# # Add "/createReplica" to get the exported GDB
# url_list = [http://services.arcgis.com/ehV0YC56b0w2eenG/arcgis/rest/services/service_432d853ca5434f8c8fc2e9aaba75ed1a/FeatureServer/createReplica]
#
# for replicaqueryURL in url_list:
#
#     # Use request method on the urllib2 library
#     replicareq = sendRequest(replicaqueryURL,
#                              replicaparams)  # forces POST request (deleteFeatures can only be done with a POST request)
#
#     # Obtains just the URL portion of the response and handles the redirect
#     r = requests.get(replicareq['responseUrl'], allow_redirects=True, verify=False)
#
#     # Creating spot for the downloaded .zip and writing the resource to it
#     with open(extractpath + "\\" + "replicaGDB.zip", "wb") as f:  # HERE
#         for chunk in r.iter_content():
#             f.write(chunk)
#
#     # Look for just zip files in extractpath folder.  Should always only be one
#     # because the program deletes the folder contents when it is done
#     # but still seems like a good catch
#     for file in glob.glob(extractpath + '\\*.zip'):
#         print file
#         zf = zipfile.ZipFile(file)
#         zf.extractall(extractpath)
#         zf.close()
#     for gdb in glob.glob(extractpath + '\\*.gdb'):
#         os.rename(gdb, surveygdb)
#
#     result = arcpy.GetCount_management(surveyfeatureclass)
#     featurecount = int(result.getOutput(0))
#     if featurecount > 0:
#         print "Features greater than 0"


# Exclude fields that end in "_repeat_count", "Creator", "EditDate", "Editor" (these aren't needed for survey report)

# Gather all fields in survey feature class to get index # to reference
fullfieldlist = arcpy.ListFields(surveyfeatureclass)
fieldlist = []

for field in fullfieldlist:
    # Check if field is in exlude list, if so, exclude from final list
    excludelist = ["Creator", "SHAPE", "_repeat_count"]
    if (field.name not in excludelist) and (excludelist[2] not in field.name):
        fieldlist.append(field.name)

#for each in fullfieldlist: print each.name
for field in fieldlist:
    # prints index of field to reference in code
    print('fieldlist = {0}: {1}'.format(fieldlist.index(field), field))

# Dictionary to hold all observers who recorded a survey during previous month as well as
# associated global ids of the surveys
observersDict = {}

#Loop through [survey name].gdb\featureclass to populate observers dictionary with observer name and global ids.
# This area also creates folders to contain pdfs and photos created in later steps
with arcpy.da.SearchCursor(surveyfeatureclass, ["Creator", "rowid", "objectid", "date", "supervisor_name", "supervisor_other"]) as scur:
    for row in scur:
        # Create observer report and photos folder for each observer
        observerreportfolder = surveyReportAndPhotosfolder + "SurveyReport_" + row[0].split("_mnpower")[0]
        IfNotExistCreaterFolder(observerreportfolder)
        observerphotofolder = observerreportfolder + "/Photos"
        IfNotExistCreaterFolder(observerphotofolder)

        # Logic to access actual names of users who took survey including 'Other' if their name wasn't listed
        if row[4] == 'Other':
            actualObserver = row[0] + '-' + row[5]
        else: actualObserver = row[0] + '-' + row[4]

        # Insert key:value pairs of {'rowid': ['Creator', 'objectid', 'date', 'supervisor_name', 'supervisor_other']} into observersDict dictionary
        observersDict[row[1]] = [row[0], row[2], row[3], row[4], row[5], actualObserver]  # date will be used to summarize how many each observer did per month

    del row, scur  # delete from memory

#Create actual *.jpg photos from attachment table
# see help: http://support.esri.com/technical-article/000011912 on "Batch export attachments from a feature class"

#============================================================================================#
#========================Exporting Pictures & Creating PhotoDictionary=======================#
photoCommentsDict = {}

# Looping through all attachment tables with pictures in the "attachmenttables_list" list of attachment tables
# Link picture comments in the "attachmenttables" list of tables
for parenttable in parenttables_list:
    attachmenttable =  parenttable + '__ATTACH'
    # Checks if the parenttable name is also within the attachmenttable name
    # Only runs if pictures are attached. Otherwise moves on to attach comments into photoCommentsDictionary
    print parenttable
    print attachmenttable

    # name filepaths for both parenttable & picturetable
    attachmenttable_path = surveygdb + '/' + attachmenttable
    parenttable_path = surveygdb + '/' + parenttable

    # Lists fields in commentable or main Survey feature class (has points) (they are slightly different in each table)
    if parenttable == surveyname:
        parenttable_FieldListStrings = ['objectid', 'SHAPE', 'rowid', 'EditDate', 'Editor', 'supervisor_name', 'supervisor_other']
    else:
        parenttable_FieldListStrings = [field.name for field in arcpy.ListFields(parenttable_path)]
    print('ParentTable Fields: {0}'.format(parenttable_FieldListStrings))
# ParentTable Fields: [u'objectid', u'bodyPositioningGoodComment', u'parentrowid', u'CreationDate', u'Creator', u'EditDate', u'Editor'
    # Creates search cursor for parenttables

    with arcpy.da.SearchCursor(parenttable_path, parenttable_FieldListStrings) as parentSCUR:
        # Iterates through parenttable by row
        for parentrow in parentSCUR:
            # Creates search cursor for attachmenttables
            with arcpy.da.SearchCursor(attachmenttable_path, ['DATA', 'ATT_NAME', 'ATTACHMENTID', 'REL_OBJECTID']) as picSCUR:
                # Iterates through attachmenttable while iterating through each row in parenttable
                for picrow in picSCUR:
                    observerphotofolder_fromdict = surveyReportAndPhotosfolder + "SurveyReport_" + observersDict[parentSCUR[2]][0].split("_mnpower")[0] + "/Photos/"
                    # Find in parenttable where Objectid == REL_OBJECTID
                    if parentrow[0] == picrow[3]:
                        print('\nfound the related record & pic')

                        attachment = picrow[0]  # 'DATA'
                        filenum = str(picrow[3]) + '_' + str(picrow[2])  # 'REL_OBJECTID' + 'ATTACHMENTID'
                        filename = filenum + '_' + str(picrow[1])  # <tablename> + 'ATT_NAME'
                        #print(filename)

                        ## parentrow[4] is 'Creator'
                        picRowListValue = [parentrow[4], parenttable, filename, parentrow[1]]
                        # Checks if parentrow[2] (the rowid) is already a key in photoComments Dict, if not, then add it.
                        if parentrow[2] in photoCommentsDict:
                            photoCommentsDict[parentrow[2]].append(picRowListValue)
                        else:
                            photoCommentsDict[parentrow[2]] = [picRowListValue]  # Creates a list of a list as 1st value for key
                        # Build Dictionary to reference picture texts & hyperlink in PDF report later. & build

                        open(observerphotofolder_fromdict + filename, 'wb').write(attachment.tobytes())
                        del picrow, filenum, filename, attachment

                    # check if picrow[0] is not in list, then add new dictionary item to photoDict of just the comments from parenttable
                    # else: print("Didn't find related index (for a positive pic or comment) in {0}".format(parentrow))


    del parentrow, parentSCUR, picSCUR # delete from memory just to be safe with code below...

    # Checking for good behvaior comments that don't have pictures & add to photoCommentsDict
    pictable_id_list = []

    # Creates search cursor for attachmenttables
    with arcpy.da.SearchCursor(attachmenttable_path, ['DATA', 'ATT_NAME', 'ATTACHMENTID', 'REL_OBJECTID']) as picSCUR:
        # Iterates through attachmenttable while iterating through each row in parenttable
        for picrow in picSCUR:
            pictable_id_list.append(picrow[3])

    # Iterate through parenttable to check if object is NOT in related ATTACHMENTS table; if not, then add the comment to photoCommentsDict
    with arcpy.da.SearchCursor(parenttable_path, parenttable_FieldListStrings) as parentSCUR:
        # Iterates through parenttable by row
        for parentrow in parentSCUR:
            if parentrow[0] not in pictable_id_list:
                # Append comment to photoCommentsDict; parentrow[4] = creator
                # ParentTable Fields: [u'objectid', u'bodyPositioningGoodComment', u'parentrowid', u'CreationDate', u'Creator', u'EditDate', u'Editor']
                # Creating dictionary's value with a placeholder of "None" value for where there would otherwise be a photo.
                picRowListValue = [parentrow[4], parenttable, None, parentrow[1]]
                # Checks if parentrow[2] (the rowid) is already a key in photoComments Dict, if not, then add it.
                if parentrow[2] in photoCommentsDict:
                    photoCommentsDict[parentrow[2]].append(picRowListValue)
                else:
                    photoCommentsDict[parentrow[2]] = [picRowListValue]  # Creates a list of a list as 1st value for key
                    # Build Dictionary to reference picture texts & hyperlink in PDF report later. & build


del parenttable, parentSCUR, picSCUR  # delete from memory

#========================Exporting Pictures & Creating photoCommentsDict=======================#
#============================================================================================#
print("\nphotoCommentsDict: \n")
for k,v in photoCommentsDict.iteritems(): print("{0}: {1}".format(k,v))
del k,v  # delete from memory

uniqueobservers = set(val[0] for val in observersDict.values())

# uniqueobservers = set(val[0] for val in observersDict.values())
print("\nuniqueobservers: \n")
print uniqueobservers
# for key, vals in photoCommentsDict.iteritems():
#     print('key={0}, vals={1}'.format(key,vals))

#========================Building Dictionary of Summary of Surveys===========================#
# Get summary of # survey each observer completed
# Add to numObserverSurveyDict by observer & number of surveys they completed per month & total completed
# in format: {observer: [totalsurveys, _01surveys, _02surveys, _03surveys, _04surveys, _05surveys, _06surveys, _07surveys, _08surveys, _09surveys, _10surveys, _11surveys, _12surveys]}
numObserverSurveysDict = {}

# Add num surveys of 0 as default for each observer into dictionary
for key, vals in observersDict.iteritems():
    # set default values for new observer all to 0
    surveytotalsDict = {'totalsurveys': 0, '_01surveys': 0, '_02surveys': 0, '_03surveys': 0, '_04surveys': 0,
                        '_05surveys': 0, '_06surveys': 0, '_07surveys': 0, '_08surveys': 0, '_09surveys': 0,
                        '_10surveys': 0, '_11surveys': 0, '_12surveys': 0}

    numObserverSurveysDict[vals[0]] = surveytotalsDict

del key, vals  # delete from memory

for observer, surveyvariables in numObserverSurveysDict.iteritems():
    #print observer, surveyvariables
    # If observer's already a key in the numObserverSurveyDict, then add 1 to totalsurvey variable
    # observersDict in format: {'rowid': ['Creator', 'objectid', 'date']}
    for vals in observersDict.itervalues():
        #print vals
        if vals[0] == observer:
            # Iterate through numObserverSurveysDict vals
            myKey = numObserverSurveysDict[observer]

            # Populate the surveytotalsDict values with totals from the counts of surveys
            myKey['totalsurveys'] +=1

            # Check by date of surveys in observersDict
            # observersDict in format of: {'rowid': ['Creator', 'objectid', 'date']}
            # If survey date is (> 01/01/2016 and < 02/01/2016):

            if checkDates(dateToCheck=vals[2], startMonth=1, endMonth=2) == 1: myKey['_01surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=2, endMonth=3) == 1: myKey['_02surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=3, endMonth=4) == 1: myKey['_03surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=4, endMonth=5) == 1: myKey['_04surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=5, endMonth=6) == 1: myKey['_05surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=6, endMonth=7) == 1: myKey['_06surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=7, endMonth=8) == 1: myKey['_07surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=8, endMonth=9) == 1: myKey['_08surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=9, endMonth=10) == 1: myKey['_09surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=10, endMonth=11) == 1: myKey['_10surveys'] +=1
            if checkDates(dateToCheck=vals[2], startMonth=11, endMonth=12) == 1: myKey['_11surveys'] +=1
            if checkDates(dateToCheck=vals[2], startYear=2016, startMonth=12, endYear=2017, endMonth=1) == 1: myKey['_12surveys'] +=1

del observer, surveyvariables  # delete from memory

print("\nnumObserverSurveysDict: \n")
for k, v in numObserverSurveysDict.iteritems(): print("{0}: {1}".format(k,v))
del k, v  # delete from memory

##==========================================================================##
##========================Building Local PDF Report=========================##
##==========================================================================##
#uniqueobservers = ['ksundeen_mnpower'] # for testing
uniqueobservers = ['rdewey_mnpower']  # for testing
for eachobserver in uniqueobservers: # for running with all observer list

#def createPDF(): see http://matthiaseisen.com/pp/patterns/p0150/ for how to return all the story append items
    # PDF Generation code.  May make sense as a function
    doc = SimpleDocTemplate(
        surveyReportAndPhotosfolder + "SurveyReport_" + eachobserver.split("_mnpower")[0] + "/Report_" + eachobserver.split("_mnpower")[0] + ".pdf",
        pagesize=letter,
        rightMargin=60, leftMargin=60,
        topMargin=60, bottomMargin=80)

    spacer = ConditionalSpacer(0, 0.1 * inch)
    line500 = MCLine(500)  # Header line
    line250 = MCLine(250)  # Subheader line.

    wherequery = "Editor = '" + eachobserver + "'"
    # print('\nwherequery = ' + wherequery)
    # fieldlist = full list of main parenttable of survey. See "survey_fields.py"
    with arcpy.da.SearchCursor(surveyfeatureclass, fieldlist, wherequery) as scur:
        myKey = numObserverSurveysDict[eachobserver]
        Story = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        addSmallText('Survey data current as of: {0}'.format(time.strftime("%m/%d/%Y")))
        Story.append(spacer)

#================Add Summary Graph================#
        monthheaders = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']

        surveytabledata = [[myKey['_01surveys'], myKey['_02surveys'], myKey['_03surveys'], myKey['_04surveys'],
                            myKey['_05surveys'], myKey['_06surveys'], myKey['_07surveys'], myKey['_08surveys'],
                            myKey['_09surveys'], myKey['_10surveys'], myKey['_11surveys'], myKey['_12surveys']]]

        surveygraph = create_bar_graph(headerList=monthheaders, dataTable=surveytabledata,
                                       outputgraphname='surveyscompleted', graphformat='png')
        addHeaderTitle("SURVEYS COMPLETED:")
        Story.append(spacer)
        Story.append(line500)
        Story.append(spacer)
        graphpic = Image('surveyscompleted.png', 5*inch, 2*inch)
        Story.append(spacer)
        Story.append(KeepTogether(graphpic))

#===============Iterate through feature classes, tables, & dictionaries to add text to PDF========#
        # write the document to disk
        # Searches within all fields listed in main parent survey feature class. See "survey_fields.py"
        # row[1] == globalid or rowid or parentrowid
        for row in scur:
            Story.append(spacer)
            logo = "IamZeroInjury.png"
            im = Image(logo, 0.75*inch, 0.75*inch)
            Story.append(spacer)
            Story.append(KeepTogether(im))
            Story.append(spacer)

#===========DETAILS==========#
            addHeaderTitle("DETAILS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)

            # Esri username
            ptext = "<b>-Logged-in Username: </b>" + str(row[53]).split("_mnpower")[0]
            Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

            # Actual Observer name
            ptext = "<b>-Observer: </b>" + str(row[6]).split("_mnpower")[0]
            Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

            # Other user if entered
            addNormalParagraphText("-Other Observer: ", 7)

#===========Add Survey date================#
            # addNormalParagraphText("Date: ", 2)
            # Add in formatted time of survey
            formatted_time = datetime.datetime.strptime(str(row[2]).rsplit(None, 2)[0], '%Y-%m-%d').date()
            ptext = "<b>-Survey Date: </b>{0}".format(formatted_time)
            Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

            addNormalParagraphText("-Observer's Region of Work: ", 3)
            addNormalParagraphText("-Observer's Other Region of Work: ", 5)
            addNormalParagraphText("-Lead Line Worker's Region of Work: ", 8)
            addNormalParagraphText("-Lead Line Worker's Other Region of Work: ", 10)
            addNormalParagraphText("-Lead Line Worker: ", 11)
            addNormalParagraphText("-Other Line Worker: ", 12)

            Story.append(spacer)
            # SITE LOCATION
            addHeaderTitle("SITE LOCATION")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)

#===========Add site photo=============#
            # Checks if each survey as a site photo. If not, prints out no photo found for survey
            # check that row[1] (rowid) == photoCommentsDict key
            for k in photoCommentsDict.iterkeys():
                if k == row[1]: # row[1] is survey globalid
                    # print("Found surveyid in photoCommentDict for: {0}".format(k))
                    sitephoto = createHyperlinkedSitePhotoObject(surveyglobalid=str(row[1]),
                                       surveyname=surveyname,
                                       photoDictionary=photoCommentsDict,
                                       baseReportFolder=surveyReportAndPhotosfolder, # change this to relative file path
                                       observerName=eachobserver)
                    addSitePhotoAndGPSPic(sitephoto)
                    del sitephoto
            Story.append(spacer)

#===========TAILGATE=============#
            addHeaderTitle("TAILGATE")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)
            addNormalParagraphText("-Was Tailgate Signed? ", 13)
            addNormalParagraphText("-Reason why tailgate wasn't signed: ", 13)
            Story.append(spacer)
            Story.append(spacer)

#===========360 WALK-AROUND==========#
            addHeaderTitle("360 WALK-AROUND")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)
            addNormalParagraphText("-Was a 360 walk-around observed? ", 15)
            Story.append(spacer)
            Story.append(spacer)

#===========OBSERVING BEHAVIORS============#
            addHeaderTitle("OBSERVING BEHAVIORS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)

#===========Body Position/Protecting Behaviors===========#
            addGoodBadPhotoCommentsToPDF(pdf_parentable='bodyPositionGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=16,
                                         subheadertitle="Body Position/Protecting Behaviors",
                                         subheader_smalltext="*Positioning/protecting body parts, i.e. bending at the knees while lifting, avoiding line of fire (wire coming off a reel), using personal protective equipment, ergonomics, equipment guards, and barricaded off work area.")

#============Moving/Lifting Objects/Proper Body Alignment=============#
            addGoodBadPhotoCommentsToPDF(pdf_parentable='movingObjectsGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=20,
                                         subheadertitle="Moving/Lifting Objects/Proper Body Alignment",
                                         subheader_smalltext="*Body mechanics while lifting, pushing/pulling, i.e. loading poles, rolling up wire, plowing cable.")

#===========Complying with Lockout/Tagout Procedures================#
            addGoodBadPhotoCommentsToPDF(pdf_parentable='lockouttagoutGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=24,
                                         subheadertitle="Complying with Lockout/Tagout Procedures",
                                         subheader_smalltext="*Following safe & proper procedures for lockout/tagout & clearances, i.e. make sure all equipment being worked on is tagged out properly on non-auto feature used, when appropriate.")

#============Complying with Permits==================#
            addGoodBadPhotoCommentsToPDF(pdf_parentable='permitsGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=28,
                                         subheadertitle="Complying with Permits",
                                         subheader_smalltext="*Obtaining & complying with permits, i.e. traffic control, confined space entry, & digger line/one call locates.")

#===========Safe Apparel Requirements==============#
            addGoodBadPhotoCommentsToPDF(pdf_parentable='apparelGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=32,
                                         subheadertitle="Safe Apparel Requirements",
                                         subheader_smalltext="*Practicing safe & proper procedures with: hair, clothes, jewelry, & personnel protective equipment, i.e. hard hats, safety glasses, FR clothing, work gloves, safety boots, traffic vests, & fall protection.")

#============Housekeeping===============#
            addGoodBadPhotoCommentsToPDF(pdf_parentable='housekeepingGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=36,
                                         subheadertitle="Housekeeping",
                                         subheader_smalltext="*Practicing safe & proper housekeeping procedures, i.e. material secured on trucks & warehouses free & clear of tripping & fire hazards.")

#===========Tools/Equipment=================#
            addGoodBadPhotoCommentsToPDF(pdf_parentable='toolsequipmentGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=40,
                                         subheadertitle="Tools/Equipment",
                                         subheader_smalltext="*Practicing safe & proper procedures with tools & equipment, i.e. condition & proper use of tool guards, proper use of ladders, & logs & forms properly filled out & kept up-to-date.")

#===========Traffic Control=================#
            addGoodBadPhotoCommentsToPDF(pdf_parentable='trafficControlGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=44,
                                         subheadertitle="Traffic Control",
                                         subheader_smalltext="*Traffic Control should be appropriate for the work location/job site.")

#===========OE TOOLS==============#
            Story.append(spacer)
            addHeaderTitle("OE TOOLS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)

            # Checking if OE Tools field value is empty, if not then split answers using oe_dict
            if row[48] is None:
                addNormalParagraphText("-OE Tools Used: ", 48)
            else:
                ptext = "<b>-OE Tools Used:</b><i> " + str(row[48]) + "</i>"

                oe_dict = {
                    'prejobbreifing': 'Pre-Job Briefing',
                    'postjobreview': 'Post-Job Review',
                    'twominuterule': '2-Minute Rule',
                    'stopworkauthority': 'Stop Work Authority',
                    'concurrentverification': 'Concurrent Verification',
                    'independentverification': 'Independent Verification',
                    'flagging': 'Flagging',
                    'stopwhenunsure': 'Stop When Unsure',
                    'starcheck': 'Self (STAR) Check',
                    'peercheck': 'Peer Check',
                    'procedureadherence': 'Procedure Adherence',
                    'threewaycommunication': '3-Way Communication',
                    ',': ', '
                }

                for k, v in oe_dict.iteritems():
                    # replace text strings with dictionary value
                    new_text = string.replace(ptext, k, v, 12)
                    ptext = new_text

                textlist = textwrap.wrap(new_text, width=200)
                for t in textlist:
                    Story.append(KeepTogether(Paragraph(t, styles["Normal"])))
                Story.append(spacer)
                Story.append(spacer)

#===========CHALLENGES & CONCERNS============#
            addHeaderTitle("CHALLENGES & CONCERNS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)
            addNormalParagraphText("-Struggles: ", 49)
            Story.append(spacer)
            Story.append(spacer)

#===========FINAL COMMENTS==============#
            addHeaderTitle("FINAL COMMENTS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)
            addNormalParagraphText("-Final Comments: ", 50)

# ===========Add final PDF page break==============#
            Story.append(PageBreak())

            # doc.build(Story) # Use doc.build to troubleshoot if the multiBuild function below throws an error
            #print(Story)
            # this printed story line shows that my username is actually being returned, when the picture & comment should be returned....

#==================Builds Final PDF for each user=================#
        try:
            # doc.build(Story, onFirstPage=addPageNumber, onLaterPages=addPageNumber)
            doc.multiBuild(Story, canvasmaker=FooterCanvas)
            # doc.multiBuild(Story, canvasmaker=FooterCanvas, onFirstPage=addPageNumber, onLaterPages=addPageNumber)
            print "PDF and photos exported on server\n"
        except Exception:
            print(traceback.format_exc())
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not convert data to an integer.")
        except AttributeError:
            print("There was a NoneType somewhere: {0}".format(sys.exc_info()[0]))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise


##==========================================================================##
##=============Copying Local PDFs & Photos to Share Drive===================##
##==========================================================================##

# ==================Copy user-folders to their share folders==================
## \\users\~[username]$\share\SafetyObservationSurvey
## Change when using full list of observers
uniqueobservers = ['rdewey_mnpower']  # for testing
for eachobserver in uniqueobservers:
    srcCopyFolder = surveyReportAndPhotosfolder + "/SurveyReport_" + eachobserver.split("_mnpower")[0]
    destCopyFolder = "//users/~" + eachobserver.split("_mnpower")[0] + "$/share/" + surveyname + "/CurrentSurveyReport_" + eachobserver.split("_mnpower")[0]
    destBaseFolder = os.path.dirname(destCopyFolder)  # Looks one folder up from the destCopyFolder location (SafetyObservationSurvey folder)
    copyOrCreateDirectoryToShare(srcCopyFolder, destBaseFolder, destCopyFolder)

    # Checks if the locally-hyperlinked Report is on the share drive; if so, it removes PDF from share drive
    localHyperlinkedPDF = "//users/~" + eachobserver.split("_mnpower")[0] + "$/share/" + surveyname + "/CurrentSurveyReport_" + eachobserver.split("_mnpower")[0] + "/Report_" + eachobserver.split("_mnpower")[0] + ".pdf"
    if os.path.exists(localHyperlinkedPDF):
        os.remove(localHyperlinkedPDF)

del eachobserver # clear memory to reuse eachobserver variable

##==========================================================================##
##=====================Building Share Drive PDF Report======================##
##==========================================================================##
uniqueobservers = ['rdewey_mnpower'] # for testing
for eachobserver in uniqueobservers: # for running with all observer list
    shareFolder = "//users/~" + eachobserver.split("_mnpower")[0] + "$/share/" + surveyname + "/CurrentSurveyReport_" + eachobserver.split("_mnpower")[0]

    doc = SimpleDocTemplate(shareFolder + "/ShareReport_" + eachobserver.split("_mnpower")[0] + ".pdf",
        pagesize=letter,
        rightMargin=60, leftMargin=60,
        topMargin=60, bottomMargin=80)

    spacer = ConditionalSpacer(0, 0.1 * inch)
    line500 = MCLine(500)  # Header line
    line250 = MCLine(250)  # Subheader line.

    wherequery = "Editor = '" + eachobserver + "'"
    # fieldlist = full list of main parenttable of survey. See "survey_fields.py"
    with arcpy.da.SearchCursor(surveyfeatureclass, fieldlist, wherequery) as scur:
        myKey = numObserverSurveysDict[eachobserver]
        Story = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        addSmallText('Survey data current as of: {0}'.format(time.strftime("%m/%d/%Y")))
        Story.append(spacer)

#================Add Summary Graph================#
        monthheaders = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']

        surveytabledata = [[myKey['_01surveys'], myKey['_02surveys'], myKey['_03surveys'], myKey['_04surveys'],
                            myKey['_05surveys'], myKey['_06surveys'], myKey['_07surveys'], myKey['_08surveys'],
                            myKey['_09surveys'], myKey['_10surveys'], myKey['_11surveys'], myKey['_12surveys']]]

        surveygraph = create_bar_graph(headerList=monthheaders, dataTable=surveytabledata,
                                       outputgraphname='surveyscompleted', graphformat='png')
        addHeaderTitle("SURVEYS COMPLETED:")
        Story.append(spacer)
        Story.append(line500)
        Story.append(spacer)
        graphpic = Image('surveyscompleted.png', 5*inch, 2*inch)
        Story.append(spacer)
        Story.append(KeepTogether(graphpic))

#===============Iterate through feature classes, tables, & dictionaries to add text to PDF========#
        # write the document to disk
        # Searches within all fields listed in main parent survey feature class. See "survey_fields.py"
        # row[1] == globalid or rowid or parentrowid
        for row in scur:
            Story.append(spacer)
            logo = "IamZeroInjury.png"
            im = Image(logo, 0.75*inch, 0.75*inch)
            Story.append(spacer)
            Story.append(KeepTogether(im))
            Story.append(spacer)

#===========DETAILS==========#
            addHeaderTitle("DETAILS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)

            # Esri username
            ptext = "<b>-Logged-in Username: </b>" + str(row[53]).split("_mnpower")[0]
            Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

            # Actual Observer name
            ptext = "<b>-Observer: </b>" + str(row[6]).split("_mnpower")[0]
            Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

            # Other user if entered
            ptext = "<b>-Other Observer: </b>" + str(row[7]).split("_mnpower")[0]
            Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

#===========Add Survey date================#
            # addNormalParagraphText("Date: ", 2)
            # Add in formatted time of survey
            formatted_time = datetime.datetime.strptime(str(row[2]).rsplit(None, 2)[0], '%Y-%m-%d').date()
            ptext = "<b>-Survey Date: </b>{0}".format(formatted_time)
            Story.append(KeepTogether(Paragraph(ptext, styles["Normal"])))

            addNormalParagraphText("-Observer's Region of Work: ", 3)
            addNormalParagraphText("-Observer's Other Region of Work: ", 5)
            addNormalParagraphText("-Lead Line Worker's Region of Work: ", 8)
            addNormalParagraphText("-Lead Line Worker's Other Region of Work: ", 10)
            addNormalParagraphText("-Lead Line Worker: ", 11)
            addNormalParagraphText("-Other Line Worker: ", 12)

            Story.append(spacer)
            # SITE LOCATION
            addHeaderTitle("SITE LOCATION")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)

#===========Add site photo=============#
            # Checks if each survey as a site photo. If not, prints out no photo found for survey
            # check that row[1] (rowid) == photoCommentsDict key
            for k in photoCommentsDict.iterkeys():
                if k == row[1]: # row[1] is survey globalid
                    # print("Found surveyid in photoCommentDict for: {0}".format(k))
                    sitephoto = createShareHyperlinkedSitePhotoObject(surveyglobalid=str(row[1]),
                                       surveyname=surveyname,
                                       photoDictionary=photoCommentsDict,
                                       observerName=eachobserver)
                    addSitePhotoAndGPSPic(sitephoto)
                    del sitephoto
            Story.append(spacer)

#===========TAILGATE=============#
            addHeaderTitle("TAILGATE")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)
            addNormalParagraphText("-Was Tailgate Signed? ", 13)
            addNormalParagraphText("-Reason why tailgate wasn't signed: ", 13)
            Story.append(spacer)
            Story.append(spacer)

#===========360 WALK-AROUND==========#
            addHeaderTitle("360 WALK-AROUND")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)
            addNormalParagraphText("-Was a 360 walk-around observed? ", 15)
            Story.append(spacer)
            Story.append(spacer)

#===========OBSERVING BEHAVIORS============#
            addHeaderTitle("OBSERVING BEHAVIORS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)

#===========Body Position/Protecting Behaviors===========#
            addShareGoodBadPhotoCommentsToPDF(pdf_parentable='bodyPositionGoodPic_repeat',
                                            pdf_parentable_goodbad_rownum=16,
                                            subheadertitle="Body Position/Protecting Behaviors",
                                            subheader_smalltext="*Positioning/protecting body parts, i.e. bending at the knees while lifting, avoiding line of fire (wire coming off a reel), using personal protective equipment, ergonomics, equipment guards, and barricaded off work area.",
                                              observerUserName=eachobserver)

#============Moving/Lifting Objects/Proper Body Alignment=============#
            addShareGoodBadPhotoCommentsToPDF(pdf_parentable='movingObjectsGoodPic_repeat',
                                            pdf_parentable_goodbad_rownum=20,
                                            subheadertitle="Moving/Lifting Objects/Proper Body Alignment",
                                            subheader_smalltext="*Body mechanics while lifting, pushing/pulling, i.e. loading poles, rolling up wire, plowing cable.",
                                              observerUserName=eachobserver)

#===========Complying with Lockout/Tagout Procedures================#
            addShareGoodBadPhotoCommentsToPDF(pdf_parentable='lockouttagoutGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=24,
                                         subheadertitle="Complying with Lockout/Tagout Procedures",
                                         subheader_smalltext="*Following safe & proper procedures for lockout/tagout & clearances, i.e. make sure all equipment being worked on is tagged out properly on non-auto feature used, when appropriate.",
                                              observerUserName=eachobserver)

#============Complying with Permits==================#
            addShareGoodBadPhotoCommentsToPDF(pdf_parentable='permitsGoodPic_repeat',pdf_parentable_goodbad_rownum=28,subheadertitle="Complying with Permits",subheader_smalltext="*Obtaining & complying with permits, i.e. traffic control, confined space entry, & digger line/one call locates.",observerUserName=eachobserver)

#===========Safe Apparel Requirements==============#
            addShareGoodBadPhotoCommentsToPDF(pdf_parentable='apparelGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=32,
                                         subheadertitle="Safe Apparel Requirements",
                                         subheader_smalltext="*Practicing safe & proper procedures with: hair, clothes, jewelry, & personnel protective equipment, i.e. hard hats, safety glasses, FR clothing, work gloves, safety boots, traffic vests, & fall protection.",
                                              observerUserName=eachobserver)

#============Housekeeping===============#
            addShareGoodBadPhotoCommentsToPDF(pdf_parentable='housekeepingGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=36,
                                         subheadertitle="Housekeeping",
                                         subheader_smalltext="*Practicing safe & proper housekeeping procedures, i.e. material secured on trucks & warehouses free & clear of tripping & fire hazards.",
                                              observerUserName=eachobserver)

#===========Tools/Equipment=================#
            addShareGoodBadPhotoCommentsToPDF(pdf_parentable='toolsequipmentGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=40,
                                         subheadertitle="Tools/Equipment",
                                         subheader_smalltext="*Practicing safe & proper procedures with tools & equipment, i.e. condition & proper use of tool guards, proper use of ladders, & logs & forms properly filled out & kept up-to-date.",
                                              observerUserName=eachobserver)

#===========Traffic Control=================#
            addShareGoodBadPhotoCommentsToPDF(pdf_parentable='trafficControlGoodPic_repeat',
                                         pdf_parentable_goodbad_rownum=44,
                                         subheadertitle="Traffic Control",
                                         subheader_smalltext="*Traffic Control should be appropriate for the work location/job site.",
                                              observerUserName=eachobserver)

#===========OE TOOLS==============#
            Story.append(spacer)
            addHeaderTitle("OE TOOLS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)

            # Checking if OE Tools field value is empty, if not then split answers using oe_dict
            if row[48] is None:
                addNormalParagraphText("-OE Tools Used: ", 48)
            else:
                ptext = "<b>-OE Tools Used:</b><i> " + str(row[48]) + "</i>"

                oe_dict = {
                    'prejobbreifing': 'Pre-Job Briefing',
                    'postjobreview': 'Post-Job Review',
                    'twominuterule': '2-Minute Rule',
                    'stopworkauthority': 'Stop Work Authority',
                    'concurrentverification': 'Concurrent Verification',
                    'independentverification': 'Independent Verification',
                    'flagging': 'Flagging',
                    'stopwhenunsure': 'Stop When Unsure',
                    'starcheck': 'Self (STAR) Check',
                    'peercheck': 'Peer Check',
                    'procedureadherence': 'Procedure Adherence',
                    'threewaycommunication': '3-Way Communication',
                    ',': ', '
                }

                for k, v in oe_dict.iteritems():
                    # replace text strings with dictionary value
                    new_text = string.replace(ptext, k, v, 12)
                    ptext = new_text

                textlist = textwrap.wrap(new_text, width=200)
                for t in textlist:
                    Story.append(KeepTogether(Paragraph(t, styles["Normal"])))
                Story.append(spacer)
                Story.append(spacer)

#===========CHALLENGES & CONCERNS============#
            addHeaderTitle("CHALLENGES & CONCERNS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)
            addNormalParagraphText("-Struggles: ", 49)
            Story.append(spacer)
            Story.append(spacer)

#===========FINAL COMMENTS==============#
            addHeaderTitle("FINAL COMMENTS")
            Story.append(spacer)
            Story.append(line500)
            Story.append(spacer)
            addNormalParagraphText("-Final Comments: ", 50)

# ===========Add final PDF page break==============#
            Story.append(PageBreak())

            # doc.build(Story) # Use doc.build to troubleshoot if the multiBuild function below throws an error
            #print(Story)
            # this printed story line shows that my username is actually being returned, when the picture & comment should be returned....

#==================Builds Final PDF for each user=================#
        try:
            # doc.build(Story, onFirstPage=addPageNumber, onLaterPages=addPageNumber)
            doc.multiBuild(Story, canvasmaker=FooterCanvas)
            # doc.multiBuild(Story, canvasmaker=FooterCanvas, onFirstPage=addPageNumber, onLaterPages=addPageNumber)
            print "PDF and photos exported on server\n"
        except Exception:
            print(traceback.format_exc())
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not convert data to an integer.")
        except AttributeError:
            print("There was a NoneType somewhere: {0}".format(sys.exc_info()[0]))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise