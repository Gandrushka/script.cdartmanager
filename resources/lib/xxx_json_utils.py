# -*- coding: utf-8 -*-
# xbmc-json utils

import traceback
import sys
import xbmc
import settings

if sys.version_info >= (2, 7):
    import json as simplejson
else:
    import simplejson


def get_json():
    return simplejson


def retrieve_json_dict(json_query, items='items', force_log=False):
    empty = []
    settings.log("[xxx_json_utils.py] - JSONRPC Query -\n%s" % json_query)
    response = xbmc.executeJSONRPC(json_query)
    if force_log:
        settings.log("[xxx_json_utils.py] - retrieve_json_dict - JSONRPC -\n%s" % response)
    if response.startswith("{"):
        response = eval(response)
        try:
            if response.has_key('result'):
                result = response['result']
                json_dict = result[items]
                return json_dict
            else:
                settings.log("[xxx_json_utils.py] - retrieve_json_dict - No response from XBMC", xbmc.LOGNOTICE)
                settings.log(response)
                return None
        except:
            traceback.print_exc()
            settings.log("[xxx_json_utils.py] - retrieve_json_dict - JSONRPC -\n%s" % response, xbmc.LOGNOTICE)
            settings.log("[xxx_json_utils.py] - retrieve_json_dict - Error trying to get json response", xbmc.LOGNOTICE)
            return empty
    else:
        return empty
