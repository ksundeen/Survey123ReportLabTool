
import ago
import urllib2
import zipfile
import json


# ID of the feature service you want to export
featureService_ID = "f4a06f02b1dd4b1f8904ed0d4e8713bd"
# Output format  Shapefile | CSV | File Geodatabase
output_format = 'Shapefile'
# Local folder where the data will be downloaded (include slash at the end)
download_folder = "D:/Temp/"
# ArcGIS user credentials to authenicate against the portal
credentials = { 'userName' : 'XXXXX', 'passWord' : 'YYYYYY'}
# Address of your ArcGIS portal
portal_url = r"https://www.arcgis.com/"

download_file = download_folder + 'download.zip'


def downloadFile(url, filename, token):
    """
    Downloads a file from the given URL.
    :param url: URL from which to download the file
    :param filename: Name of file to store the download locally. Proper permissions are assumed.
    :param token: Token for the portal identity
    :return:
    """
    print ("...Downloading")
    req = urllib2.urlopen(url + "?token=" + token)
    CHUNK = 16 * 1024
    with open(filename, 'wb') as fp:
        while True:
            chunk = req.read(CHUNK)
            if not chunk: break
            fp.write(chunk)

def extractZIP(filename,folder):
    """
    Extracts the contents of the zip file into the specified folder.
    :param filename: The name of the ZIP archive to unpack. The file is assumed to exist.
    :param folder: The target folder to hold the content of the ZIP archive. Proper permissions are assumed.
    :return:
    """
    print ("...Extracting")
    zfile = zipfile.ZipFile(filename)
    zfile.extractall(folder)


print ("...Starting")
# initialize the portal helper class
# ago.py is part of the 10.3 python install
agol_helper = ago.AGOLHelper(portal_url)
print ("...Authenticating against your Portal ")
# login
agol_helper.login(credentials['userName'], credentials['passWord'])

# export url and parameters 
export_url = "{}/content/users/{}/export".format(agol_helper.secure_url, agol_helper.username)

export_parameters = {
    'token': agol_helper.token,
    'itemId': featureService_ID,
    'title': "Temp-" + str(int(round(time.time() * 1000))),
    'exportFormat': output_format,
    'f' :'json'
}
# launching async export request
export_data = agol_helper.url_request(export_url, export_parameters, request_type="POST")

if export_data is  None:
    print "ERROR: Can't find a feature service with id: " + featureService_ID
    print "TIP:   Navigate to the item details page of your feature service, and get the id from the URL"
else:
    print ("...Exporting data")
    # retrieve the itemId for the export
    exportItemId = export_data['exportItemId']
    # retrieve the jobId to watch the export progress
    jobId = export_data['jobId']
    status = "processing"

    items_url = "{}/content/users/{}/items/{}/status".format(agol_helper.secure_url,agol_helper.username, exportItemId)
    data_url = "{}/content/items/{}/data".format(agol_helper.secure_url, exportItemId)

    status_parameters = {
        'jobId' : jobId,
        'jobType' : 'export',
        'f' : 'json',
        'token' : agol_helper.token
    }

    while status == "processing":
        print ("...." + status)
        # checking export job status
        time.sleep(5)
        data = agol_helper.url_request(items_url, status_parameters)

        status = data['status']

    if status == "completed":
        print ("...." + status)
        # once the export has completed, download the file
        downloadFile(data_url, download_file, agol_helper.token)
        # deleting export results in the portal
        agol_helper.delete(item_id=export_data['exportItemId'])
        # uncompress the contents of the archive
        extractZIP(download_file, download_folder)


    else:
        raise Exception("!!! Export job failed. Status \"" + status + "\"")

    print ("Completed. Files available at: " + download_folder )
