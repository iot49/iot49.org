# ssl via urpc

POLLIN   =  1
POLLOUT  =  4
POLLERR  =  8
POLLHUP  = 16

from urpc import import_

def poll():
    poller = import_('select').poll()
    poller.ipoll = poller.poll
    return poller

select = import_('select').select
