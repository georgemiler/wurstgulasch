import sys
sys.path.append("/srv/http/wurstgulasch")

from wurstgulasch import create_app 
application = create_app("/srv/http/wurstgulasch/wurstgulasch.cfg")
