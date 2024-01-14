# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Y!maptool(Yahoo! JAPAN YOLP Web API)
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

import sys, os


# Import the PyQt and QGIS libraries
try:
    from qgis.core import *
    from qgis.gui import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5 import uic
    QT_VERSION=5
    os.environ['QT_API'] = 'pyqt5'
    from urllib.request import URLError
except:
    from PyQt4.QtCore import *
    from PyQt4.QtCore import QSettings as QgsSettings
    from PyQt4.QtGui import *
    from PyQt4 import uic
    QT_VERSION=4
    from urllib2 import URLError

# Import the code for the dialog
from .zip_code_search_dialog import ZipCodeSearchDialog
from .target_select_dialog import TargetSelectDialog

from .yolp_connector import *


class Ymaptool:

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.layerid = ''
        self.layer = None
        try:
            self.registry = QgsMapLayerRegistry.instance()
        except:
            self.registry = QgsProject.instance()


#    def log_message(self, msg):
#        QgsMessageLog.logMessage(msg, 'Y!maptool')


    def initGui(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))

        self.zip_code_search_action = QAction(QIcon(os.path.join(current_directory, "img", "ZipCodeSearch.gif")), \
        u'郵便番号検索', self.iface.mainWindow())
        self.zip_code_search_action.triggered.connect(self.zip_code_search)

        self.click_point_altitude_action = QAction(QIcon(os.path.join(current_directory, "img", "ClickPointAltitude.gif")), \
        u'クリック地点標高', self.iface.mainWindow())
        self.click_point_altitude_action.triggered.connect(self.click_point_altitude)
        
        self.menu = QMenu(QCoreApplication.translate('Y!maptool', u'Y!maptool（Yahoo!JAPAN YOLP Web API）'))
        self.menu.addActions([self.zip_code_search_action, self.click_point_altitude_action])
        self.iface.pluginMenu().addMenu(self.menu)
        self.iface.addToolBarIcon(self.zip_code_search_action)
        self.iface.addToolBarIcon(self.click_point_altitude_action)

        self.previous_map_tool = self.iface.mapCanvas().mapTool()


    def unload(self):
        self.iface.removePluginMenu('Y!maptool', self.zip_code_search_action)
        if self.previous_map_tool:
            self.iface.mapCanvas().setMapTool(self.previous_map_tool)


    def zip_code_search(self):
        if self.previous_map_tool:
            self.iface.mapCanvas().setMapTool(self.previous_map_tool)

        yolp_connector = YolpConnector()
        
        gasdlg = ZipCodeSearchDialog()
        gasdlg.show()
        result = gasdlg.exec_()

        if result == 1 :
            try:
                results = yolp_connector.zip_code_search(unicode(gasdlg.zip_code.text()).encode('utf-8'))
            except Exception as e:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('Y!maptool', u"郵便番号検索 エラー"), QCoreApplication.translate('Y!maptool', u"Yahoo!JAPAN YOLP Web APIでエラーが発生しました。:<br><strong>%s</strong>" % e))
                return

            if not results:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('Y!maptool', u"郵便番号検索 結果なし"), QCoreApplication.translate('Y!maptool', u"Yahoo!JAPAN YOLP Web APIから検索結果を得られませんでした。: <strong>%s</strong>." % gasdlg.zip_code.text()))
                return

            locations = {}
            for location, point in results:
                locations[location] = point

            locations = dict(sorted(locations.items()))
        
            tsdlg = TargetSelectDialog()
            tsdlg.selectComboBox.addItems(locations.keys())
            tsdlg.show()
            results = tsdlg.exec_()

            if results == 1 :
                point = locations[unicode(tsdlg.selectComboBox.currentText())]
                self.locate(point)

            return


    def locate(self, point):

        self.set_canvas_center_lon_lat(point[0], point[1])

        # if scale:
        #     self.canvas.zoomScale(scale)

        self.canvas.refresh()


    def set_canvas_center_lon_lat(self, lon, lat):

        point = QgsPoint(float(lon), float(lat))

        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326') # WGS 84 / UTM zone 33N
        transformer = QgsCoordinateTransform(crs_wgs84, map_crs, QgsProject.instance())

        point = transformer.transform(QgsPointXY(point)) 

        self.canvas.setCenter(point)


    def click_point_altitude(self):
        sb = self.iface.mainWindow().statusBar()
        sb.showMessage(u"標高を調べたい場所をクリックしてください。")
        ct = ClickPointAltitudeTool(self.iface, self.iface.mapCanvas());
        self.previous_map_tool = self.iface.mapCanvas().mapTool()
        self.iface.mapCanvas().setMapTool(ct)


class ClickPointAltitudeTool(QgsMapTool):

    def __init__(self, iface, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface


    def canvasPressEvent(self, event):

        x = event.pos().x()
        y = event.pos().y()
        pres_pt = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)

        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326') # WGS 84 / UTM zone 33N
        transformer = QgsCoordinateTransform(map_crs, crs_wgs84, QgsProject.instance())

        point = transformer.transform(QgsPointXY(pres_pt)) 

        yolp_connector = YolpConnector()

        try:
            result = yolp_connector.get_altitude(point[0], point[1])

            if not result:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('Y!maptool', "クリック地点標高 結果なし"), unicode(QCoreApplication.translate('Y!maptool', u"Yahoo!JAPAN YOLP Web APIから検索結果を得られませんでした。: <strong>%s</strong>." % 'lon:' + str(point[0]) + ' lat:' + str(point[1]))))
                return
            else:
                QMessageBox.information(None, u"標高", str(result) + ' m')
                
        except Exception as e:
            QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('Y!maptool', "クリック地点標高 エラー"), unicode(QCoreApplication.translate('Y!maptool',  u"Yahoo!JAPAN YOLP Web APIでエラーが発生しました。:<br><strong>%s</strong>" % e)))
        return


if __name__ == "__main__":
    pass
