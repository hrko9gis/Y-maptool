# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Y!maptool(Yahoo! JAPAN YOLP Web API)
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

def classFactory(iface):
    from .y_maptool import Ymaptool
    return Ymaptool(iface)


