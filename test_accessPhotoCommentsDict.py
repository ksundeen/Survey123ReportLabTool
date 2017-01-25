from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Flowable, SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether, ListFlowable, ListItem, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import CMYKColor
from PIL import Image as pil_Image

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

# surveyname = always will be the main feature class table name 'SafetyObservationSurvey'
# Looping through eachobserver...
# with questions where the parenttable = is the question if the good picture/comment taken, so parenttable = 'apparelGoodPic_repeat'
# maybe add survey global id?
def getPhoto(surveyglobalid, surveyname, parenttable, photoDictionary, baseReportFolder, observerName):
    """
    Returns the photo location stored in a dictionary.
    :param surveyglobalid: the gdb's global id recorded for the particulat survey
    :param surveyname: the main feature class of the gdb survey
    :param parenttable: related tables within the survey gdb (for the repeats for example)
    :param photoDictionary: dictionary in format: {rowid: [Editor, parenttable, photofilename, SHAPE (or) comments]}
            ...was built using photoCommentsDict[parentrow[2]] = [parentrow[4], parenttable, filename, parentrow[1]]
    :param baseReportFolder: folder where Report and Pictures will be accessed
    :param observerName: the user name
    :return:
    """
    # Check if rowid field value is in the photoCommentsDict keys, then access the photoname & commentvalue in photoCommentsDict
    for key, vals in photoDictionary.iteritems():
        # If dictionary's key (rowid) = the surveyglobalid AND username = our iterating observer name AND dictionary's parentable == parentable (what we listed for the good comments question), then we grab the photoname from the dictionary
        if key == surveyglobalid and vals[0] == observerName and vals[1] == parenttable:
            print("Found & added photo for key ({0}) by observer ({1}) in parenttable ({2})".format(key, observerName, parenttable))
            # grab rowid (globalid) & get place pic & comment below pic
            photoname = vals[2]  # should access photoCommentsDict{rowid}: photoname

            # Checks if the parentrow comment is empty (in related tables) & checks that the the dict item is NOT from the parent table's surveyname feature class (this is the point feature class, which doesn't have any comments in it for good pictures)
            # If SHAPE or comments field in dictionary == None or NOT equal to SurveyName tablename, then record the commentvalue as 'No Comment'
            if vals[3] is None and vals[1] != surveyname:
                commentvalue = 'No comment'
            elif vals[3] is not None and vals[1] != surveyname:
                commentvalue = vals[0]
            elif vals[1] == surveyname:
                sitegps = vals[3]  # Grabs xy coord of site location, will be creating a google image from this lat/long.
                x_long = str(sitegps[0])
                y_lat = str(sitegps[1])
                # example google link: 'http://www.google.com/maps/place/49.46800006494457,17.11514008755796/@49.46800006494457,17.11514008755796,17'
                sitegps_hyperlink = 'http://www.google.com/maps/place/' + y_lat + ',' + x_long +  '/@' + y_lat + ',' + x_long + '/' + ',17z/data=!3m1!1e3'

            else:
                print("Something didn't work with the comments value")

            photofolder = baseReportFolder + "SurveyReport_" + observerName.split("_mnpower")[0] + "/Photos/"
            photolocation = photofolder + photoname
            #pholder = open(photolocation, "rb")  # holder for image, if only placing a non-hyperlinked image

            # Access image's width & height to use as parameters when placing in PDF
            with pil_Image.open(photolocation) as myimage:
                imageWidth, imageHeight = myimage.size

            if vals[1] == surveyname:
                myHyperlinkedImage = HyperlinkedImage(photolocation, hyperlink=photolocation, width=imageWidth*0.25, height=imageHeight*0.25)
                SiteHyperlink = HyperlinkedImage('siteimage.png', hyperlink=sitegps_hyperlink, width=1*inch, height=1*inch)
                return (myHyperlinkedImage, SiteHyperlink)
            else:
                myHyperlinkedImage = HyperlinkedImage(photolocation, hyperlink=photolocation, width=imageWidth*0.25, height=imageHeight*0.25)
                return (myHyperlinkedImage, commentvalue)

        else: print("Looped through key: {0} for observer ({1}) in parenttable ({2}); ".format(key, observerName, parenttable))

############################################################

# Think of what I'm iterating through for eachobserver
# Try to use photo folder path as relative (instead of absolute)
# Brandon mentioned to make this as an absolute path to user's share folder.
observersList = ['derdman_mnpower']

photoCommentsDict ={
'{D410117B-D3CC-4398-965F-772453F1BBE9}':[u'derdman_mnpower', 'SafetyObservationSurvey', '47_31_sitephoto-20160906-190055.jpg', (-94.32440481199995, 45.829640734000066)],

'{7FBB7A9C-A20D-4F6C-88B1-7C77BBBD55CF}': [u'derdman_mnpower', u'toolsequipmentGoodPic_repeat', '2_2_toolsequipmentGoodPic-20160816-150311.jpg', u'Using good body position away from the Load         '],

'{C81A433D-D7F2-4DD0-8CE6-2EF2DCA5527A}': [u'derdman_mnpower', 'SafetyObservationSurvey', '30_20_sitephoto-20160809-173616.jpg', (-95.14981859399995, 46.81943922800008)],

'{47C8B9B4-9958-476D-9503-90C1F07322BE}': [u'rdewey_mnpower', u'apparelGoodPic_repeat', '2_2_apparelGoodPic-20160831-201446.jpg', None],

'{7147EB76-5CB0-4A14-8973-E31B06CA806A}': [u'derdman_mnpower', u'apparelGoodPic_repeat', '1_1_apparelGoodPic-20160626-001752.jpg', u'Good use of grounds good use of body harness          ']}

# Folder & File Paths
surveyname = 'SafetyObservationSurvey'
parenttables_list = [surveyname]
downloaddatafolder = 'C:/code/trunk/Projects_Python/Survey123ReportTool/DownloadedData/'
extractpath = 'C:/code/trunk/Projects_Python/Survey123ReportTool/DownloadedData/' + surveyname # Location of our download data folder
surveygdb = extractpath + '/' + surveyname + '_test_09142016.gdb'
surveyfeatureclass = surveygdb + '/' + surveyname # Feature class containing survey responses
surveyReportAndPhotosfolder = extractpath + '/ReportAndPhotos/'

for observer in observersList:

    # Create PDF
    doc = SimpleDocTemplate(
        "myHyperlinkedPics.pdf",
        pagesize=letter,
        rightMargin=60, leftMargin=60,
        topMargin=60, bottomMargin=80)

    Story = []
    styleSheet = getSampleStyleSheet()

    logo = "IamZeroInjury.png"
    im = Image(logo, 1 * inch, 1 * inch)

    Story.append(KeepTogether(im))

    myphoto = getPhoto(surveyname=surveyname, parenttable=surveyname, photoDictionary=photoCommentsDict,baseReportFolder=surveyReportAndPhotosfolder, observerName=observer)
    Story.append(KeepTogether(myphoto[0])) # should show site photo hyperlinked to photolocation
    Story.append(KeepTogether(myphoto[1]))  # should show map icon hyperlinked to google maps locations

    #Story.append(KeepTogether(Paragraph(commentvalue, styles["Normal"]))) # if the parenttable ==  a repeat table, the commentvalue would be available the same way through myphoto[1] from the returned tuple

    # Story.append(KeepTogether(HyperlinkedImage(hyperlink=logo, Image=logo, 1*inch, 1*inch, 1*inch, 1*inch)))

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

    Story.append(PageBreak())

    doc.build(Story)

    print "PDF and photos exported on server\n"