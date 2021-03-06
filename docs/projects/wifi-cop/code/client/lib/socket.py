# sockets via urpc

AF_INET              = 2
AF_INET6             = 10
IPPROTO_IP           = 0
IPPROTO_TCP          = 6
IPPROTO_UDP          = 17
IP_ADD_MEMBERSHIP    = 3
SOCK_DGRAM           = 2
SOCK_RAW             = 3
SOCK_STREAM          = 1
SOL_SOCKET           = 4095
SO_REUSEADDR         = 4

from urpc import import_

getaddrinfo = import_('socket').getaddrinfo
socket = import_('socket').socket
