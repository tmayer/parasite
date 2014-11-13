#!flask/bin/python

activate_this = '/var/www/paralleltext.info/data/flask/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/var/www/paralleltext.info/data')
sys.path.insert(0, '/var/www/paralleltext.info/data/flask')
sys.path.insert(0, '/var/www/paralleltext.info/data/parasite')

from parasite.views import app as application
