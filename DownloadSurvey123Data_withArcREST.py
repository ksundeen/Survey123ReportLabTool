# uses ArcREST module.
# see github site here: https://github.com/Esri/ArcREST
# see ArcREST documentation here: http://esri.github.io/ArcREST/index.html (original code here)

from arcrest.manageorg import Administration
from arcrest import AGOLTokenSecurityHandler
from arcrest.agol import FeatureService
from arcrest.common.filters import LayerDefinitionFilter

def download_features(fs_url,where_clause,out_path):
    '''downloads a hosted service features into a feature class'''
    username = 'ksundeen@mnpower.com'
    pwd = 'lilybug1'
    agol_securityHandler = AGOLTokenSecurityHandler(username, pwd,'http://mnpower.maps.arcgis.com/')
    agol_org_obj = Administration(securityHandler=agol_securityHandler,initialize=True)

    fs = FeatureService(url=fs_url,securityHandler=agol_securityHandler,initialize=True)

    ldf = LayerDefinitionFilter()
    ldf.addFilter(0, where=where_clause)

    queryResults = fs.query(layerDefsFilter=ldf,returnCountOnly=False,returnGeometry=True)
    result = queryResults[0].save(r'in_memory','SampleSurvey')
    arcpy.CopyFeatures_management(result,out_path)

download_features('78a3e4547f494d3a94a42fdc4afb0851', out_path=r"C:\code\trunk\Projects_Python\Survey123ReportTool\DownloadedData")
