# requests via urpc

from urpc import import_

urequests = import_('urequests')

request = urequests.request
head    = urequests.head
get     = urequests.get
post    = urequests.post
put     = urequests.put
patch   = urequests.patch
delete  = urequests.delete
