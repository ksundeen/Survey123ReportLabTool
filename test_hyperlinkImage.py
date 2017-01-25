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


#def createPDF()
doc = SimpleDocTemplate(
    "myHyperlinkedPics.pdf",
    pagesize=letter,
    rightMargin=60, leftMargin=60,
    topMargin=60, bottomMargin=80)

Story = []
styleSheet = getSampleStyleSheet()

logo = "test.png"
# Access image size: http://stackoverflow.com/questions/6444548/how-do-i-get-the-picture-size-with-pil
with pil_Image.open(logo) as myimage:
    imageWidth, imageHeight = myimage.size
print(myimage.size)

pholder = open(logo, "rb")

# myHyperlinkedImage = HyperlinkedImage(logo, hyperlink='http://www.google.com', width=imageWidth*0.1*inch, height=imageHeight*0.1*inch)

myHyperlinkedImage = HyperlinkedImage(logo, hyperlink='C:/code/trunk/Projects_Python/Survey123ReportTool/' + logo, width=imageWidth, height=imageHeight)

Story.append(KeepTogether(myHyperlinkedImage))

#Story.append(KeepTogether(HyperlinkedImage(hyperlink=logo, Image=logo, 1*inch, 1*inch, 1*inch, 1*inch)))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))





Story.append(PageBreak())

doc.build(Story)

print "PDF and photos exported on server\n"