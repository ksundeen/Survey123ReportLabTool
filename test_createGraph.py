from reportlab.lib.colors import PCMYKColor
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.textlabels import Label
from reportlab.platypus import Flowable, SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether, ListFlowable, ListItem, Table

def create_bar_graph(headerList, dataTable):
    """
    Creates a bar graph in a PDF. Code from http://www.blog.pythonlibrary.org/2016/02/18/reportlab-how-to-add-charts-graphs/
    """
    # d = Drawing(280, 250)
    d = Drawing(295, 180)  # (x, y) for how large the image/output format will be
    bar = VerticalBarChart()
    bar.x = 40  # coordinate where x-axis is drawn
    bar.y = 45  # coordinate where y-axis is drawn
    # data = [[1, 2, 3, None, None, None, 5],
    #         [10, 5, 2, 6, 8, 3, 5],
    #         [5, 7, 2, 8, 8, 2, 5],
    #         [2, 10, 2, 1, 8, 9, 5],
    #         ]
    bar.data = dataTable
    # bar.data = data
    # bar.categoryAxis.categoryNames = ['Year1', 'Year2', 'Year3',
    #                                   'Year4', 'Year5', 'Year6',
    #                                   'Year7']

    bar.categoryAxis.categoryNames = headerList

    bar.bars[0].fillColor = PCMYKColor(75, 0, 100, 20, alpha=85)
    bar.bars.fillColor = PCMYKColor(70, 64, 0, 0, alpha=85)  # base color for 1st data row
    bar.width = 230
    bar.height = 100
    bar.barLabels.fontName = 'Helvetica'
    bar.barLabels.fontSize = 6
    bar.barLabels.nudge = 7
    bar.barLabels.dy = 3
    bar.barLabelFormat = '%d'
    bar.valueAxis.labels.fontName = 'Helvetica'  # y-axis
    bar.valueAxis.labels.fontSize = 8
    bar.categoryAxis.labels.fontName = 'Helvetica'  # x-axis
    bar.categoryAxis.labels.fontSize = 8
    bar.categoryAxis.visibleTicks = 1
    bar.categoryAxis.labels.angle = 45
    bar.categoryAxis.labels.dy = -10  # adjusts month labels down
    bar.categoryAxis.labels.dx = -5  # adjusts month labels over

    d.add(bar, '')

    # Output image will be re-written on every call
    d.save(formats=['svg'], outDir='.', fnRoot='surveyscompleted')


#monthheaders = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
monthheaders = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
surveytabledata = [[0, 0, 0, 0, 1, 2, 5, 0, 1, 0, 0, 0]]
# Shows to rows with diff colors
# surveytabledata = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
#                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]

surveygraph = create_bar_graph(headerList=monthheaders, dataTable=surveytabledata)

#Story.append(surveygraph)