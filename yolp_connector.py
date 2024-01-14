# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Y!maptool(Yahoo! JAPAN YOLP Web API)
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

from .networkaccessmanager import NetworkAccessManager
import sys, os, json

from PyQt5.QtWidgets import QMessageBox

CLIENT_ID = 'dj00aiZpPXJ4aUFEUFVIUnVPUCZzPWNvbnN1bWVyc2VjcmV0Jng9NDE-'

NAM = NetworkAccessManager()

class YolpConnectorException(Exception):
    pass

class YolpConnector():
    zip_code_search_url = 'https://map.yahooapis.jp/search/zip/V1/zipCodeSearch?appid={client_id}&query={zip_code}&output=json'
    get_altitude_url = 'https://map.yahooapis.jp/alt/V1/getAltitude?appid={client_id}&coordinates={lon},{lat}&output=json'

    def zip_code_search(self, zip_code):
        try: 
            url = self.zip_code_search_url.format(**{'client_id': CLIENT_ID, 'zip_code': zip_code.decode('utf8')})
            result = NAM.request(url, blocking=True)[1].decode('utf8')
            if not result:
                return
            result = json.loads(result)
            if result['ResultInfo']['Count'] == 0:
                return
            return [(rec['Name'] + ' ' + rec['Property']['PostalName'], (rec['Geometry']['Coordinates'].split(','))) for rec in result['Feature']]
        except Exception as e:
            raise YolpConnectorException(str(e))


    def get_altitude(self, lon, lat):
        try: 
            url = self.get_altitude_url.format(**{'client_id': CLIENT_ID, 'lon': lon, 'lat': lat})
            result = NAM.request(url, blocking=True)[1].decode('utf8')
            if not result:
                return
            result = json.loads(result)
            if result['ResultInfo']['Count'] == 0:
                return
            return result['Feature'][0]['Property']['Altitude']
        except Exception as e:
            raise YolpConnectorException(str(e))
