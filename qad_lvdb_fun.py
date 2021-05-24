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
from qgis.gui import *
import qgis.utils

import math

from . import qad_utils
from .qad_geom_relations import *
from .qad_join_fun import selfJoinPolyline
from .qad_arc import QadArc
from .qad_point import QadPoint
from .qad_multi_geom import QadMultiPoint
from .qad_layer import *
from .cmd.qad_offset_cmd import QadOFFSETCommandClass as cmd


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
def drawReferenceLines(entity, angle):
    """
    Docstring
    """
    line = QgsFeature()

    if entity.whatIs() == "ENTITY":
        selfi = QadPoint()
        # selfii = cmd()
        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        f = pointGeom.asMultiPoint()
        p = QadPoint.set(selfi, f[0])
        print(p)

    # elif entity.whatIs() == "DIMENTITY":
        bearingLvFuse = math.radians(angle)
        bearingRefereceOne = math.radians(155)
        bearingRefereceTwo = math.radians(275)
        if angle > 0 and angle< 90:
            angle1 = math.radians(90-angle)
            angle2 = math.radians(90-155)
            angle3 = math.radians(90-275)
        elif angle > 90 and angle < 180:
            angle1 = math.radians(180-angle)
            angle2 = math.radians(180-155)
            angle3 = math.radians(180-275)
        elif angle > 180 and angle < 270:
            angle1 = math.radians(270-angle)
            angle2 = math.radians(270-155)
            angle3 = math.radians(270-275)
        elif angle > 270 and angle < 360:
            angle1 = math.radians(360-angle)
            angle2 = math.radians(360-155)
            angle3 = math.radians(360-275)

        newPoint = QgsPointXY(p.x()+(2.5*math.cos(angle1)), p.y()+(2.5*math.cos(bearingLvFuse)))
        refPointOne = QgsPointXY(p.x()+(2.5*math.cos(angle2)), p.y()+(2.5*math.cos(bearingRefereceOne)))
        refPointTwo = QgsPointXY(p.x()+(2.5*math.cos(angle3)), p.y()+(2.5*math.cos(bearingRefereceTwo)))
    
        
        
        
          
        
        return [[p, newPoint],[p, refPointOne],[p, refPointTwo]]
    

