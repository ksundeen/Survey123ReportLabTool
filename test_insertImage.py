from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Flowable, SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether, ListFlowable, ListItem, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# doc = SimpleDocTemplate(
#     "myHyperlinkedPics.pdf",
#     pagesize=letter,
#     rightMargin=60, leftMargin=60,
#     topMargin=60, bottomMargin=80)
#
# Story = []
# styleSheet = getSampleStyleSheet()
#
logo = "IamZeroInjury.png"
im = Image(logo, 1 * inch, 1 * inch)

mycanvas = Canvas('myPicPDF.pdf', pagesize=letter)
mycanvas.drawImage(logo, 1, 1, mask='auto')
mycanvas.linkAbsolute()
mycanvas.showPage()
mycanvas.save()


#
# Story.append(KeepTogether(im))
#
# myHyperlinkedImage = HyperlinkedImage(logo, hyperlink=logo)
# # myHyperlinkedImage.hyperlink = logo
# Story.append(KeepTogether(myHyperlinkedImage))
# # Story.append(KeepTogether(HyperlinkedImage(hyperlink=logo, Image=logo, 1*inch, 1*inch, 1*inch, 1*inch)))
#
# styles = getSampleStyleSheet()
# styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
#
# # Add hyperlink of photo in PDF to photo in Photo directory
# # Story.append(KeepTogether(HyperlinkedImage(pholder, 1*inch, 1*inch, 1*inch, 1*inch)))
#
# # Story.linkURL('http://google.com', (inch, inch, 1 * inch, 1 * inch), relative=1)
#
# Story.append(PageBreak())
#
# doc.build(Story)

print "PDF and photos exported on server\n"