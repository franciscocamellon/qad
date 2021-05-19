# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 funzioni per offset
 
                              -------------------
        begin                : 2019-05-20
        copyright            : iiiii
        email                : hhhhh
        developers           : bbbbb aaaaa ggggg
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import *
from qgis.core import QgsPointXY
from qgis.gui import *
import qgis.utils

import math

from . import qad_utils
from .qad_geom_relations import *
from .qad_join_fun import selfJoinPolyline
from .qad_arc import QadArc


# ===============================================================================
# drawLvFuses
# ===============================================================================
def drawLvFuses(feature, angle, lvFuseNumber):
    """
    Docstring
    """

    return None


# ===============================================================================
# drawConnector
# ===============================================================================
def drawConnector(drawConnector=False):
    """
    Docstring
    """

    return None


# ===============================================================================
# drawReferenceLines
# ===============================================================================
def drawReferenceLines(selectedLvdbPoint):
    """
    Docstring
    """
    angle1 = math.radians(180+(270-275))
    angle2 = math.radians(270+(180-155))
    angle3 = math.radians(90-35)

    lista = [[math.cos(angle1), math.sin(angle1)],
             [math.cos(angle2), math.sin(angle2)],
             [math.cos(angle3), math.sin(angle3)]]

    geom = selectedLvdbPoint[0].geometry()
    point = geom.asMultiPoint()
    sing_point = point[0].x()

    for i in range(len(lista)):
    #point_40 = QgsPointXY(point.x()+cos, point.y()+sin)
        point_40 = QgsPointXY(point[0].x()+lista[i][0], point[0].y()+lista[i][1])
        print(point_40)
        line.setGeometry(QgsGeometry.fromPolylineXY([point[0],point_40]))

        #print(geom.asPoint().x())
        pr.addFeatures([line])
    lines.triggerRepaint()



    return None
