# network via urpc

AP_IF                     = 1
AUTH_MAX                  = 8
AUTH_OPEN                 = 0
AUTH_WEP                  = 1
AUTH_WPA2_PSK             = 3
AUTH_WPA_PSK              = 2
AUTH_WPA_WPA2_PSK         = 4
MODE_11B                  = 1
MODE_11G                  = 2
MODE_11N                  = 4
PHY_IP101                 = 2
PHY_LAN8720               = 0
PHY_TLK110                = 1
STAT_ASSOC_FAIL           = 203
STAT_BEACON_TIMEOUT       = 200
STAT_CONNECTING           = 1001
STAT_GOT_IP               = 1010
STAT_HANDSHAKE_TIMEOUT    = 204
STAT_IDLE                 = 1000
STAT_NO_AP_FOUND          = 201
STAT_WRONG_PASSWORD       = 202
STA_IF                    = 0

from urpc import import_

WLAN = import_('network').WLAN
