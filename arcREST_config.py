# Found https://github.com/Esri/ArcREST to fetch AGOL folders

import arcrest
from arcresthelper import securityhandlerhelper

config = {'username': 'ksundeen@mnpower.com', 'password': 'lilybug1'}
token = securityhandlerhelper.securityhandlerhelper(config)
admin = arcrest.manageorg.Administration(securityHandler=token.securityhandler)
content = admin.content
userInfo = content.users.user()
print userInfo.folders


# Get item metadata:

# item = admin.content.getItem(itemId=itemId)
# item.title
# u'Streets'

