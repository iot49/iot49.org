# ssl via urpc

from urpc import import_

wrap_socket = import_('ssl').wrap_socket
