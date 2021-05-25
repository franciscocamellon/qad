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
def drawInConductor(entity, lvdbAngle):
    fuseLine = list()

    if entity.whatIs() == "ENTITY":
        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        fusePoint = pointGeom.asMultiPoint()
        lvdbAngleRad = math.radians(90-lvdbAngle)
        lista = [1.5*(math.cos(lvdbAngleRad)), 1.5*(math.sin(lvdbAngleRad))]

        newPoint = QgsPointXY(fusePoint[0].x()+lista[0], fusePoint[0].y()+lista[1])
        fuseLine.append([fusePoint[0],newPoint])
    return fuseLine


# ===============================================================================
# drawConnector
# ===============================================================================
def drawOutConductor(entity, fusesToDraw):
    """
    Docstring
    """
    outConductor = list()
    intervalAngle = 120 / fusesToDraw
    refAngle = 450-155

    if entity.whatIs() == "ENTITY":
        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        outPoint = pointGeom.asMultiPoint()[0]
            
        for fuse in range(fusesToDraw):
            newPoint = QgsPointXY(outPoint.x()+1.5*(math.cos(math.radians(refAngle))), outPoint.y()+1.5*(math.sin(math.radians(refAngle))))
            outConductor.append([outPoint, newPoint])
            refAngle -= intervalAngle

        return outConductor


# def createRefAngleList(angle, point):
#     refAngleList = list()
#     bearingLvFuse = math.radians(angle)
#     bearingRefereceOne = math.radians(155)
#     bearingRefereceTwo = math.radians(275)
#     for quadrant in [90, 180, 270, 360]:
#         if angle == quadrant:

#     if angle > 0 and angle < 90:
#         angle1 = math.radians(90-angle)
#         angle2 = math.radians(90-155)
#         angle3 = math.radians(90-275)
#         newPoint = QgsPointXY(point.x()+(2.5*math.cos(angle1)),
#                               point.y()+(2.5*math.cos(bearingLvFuse)))
#         refPointOne = QgsPointXY(
#             point.x()+(2.5*math.cos(angle2)), point.y()+(2.5*math.cos(bearingRefereceOne)))
#         refPointTwo = QgsPointXY(
#             point.x()+(2.5*math.cos(angle3)), point.y()+(2.5*math.cos(bearingRefereceTwo)))
#     elif angle > 90 and angle < 180:
#         angle1 = math.radians(180-angle)
#         angle2 = math.radians(180-155)
#         angle3 = math.radians(180-275)
#     elif angle > 180 and angle < 270:
#         angle1 = math.radians(270-angle)
#         angle2 = math.radians(270-155)
#         angle3 = math.radians(270-275)
#     elif angle > 270 and angle < 360:
#         angle1 = math.radians(360-angle)
#         angle2 = math.radians(360-155)
#         angle3 = math.radians(360-275)


# ===============================================================================
# drawReferenceLines
# ===============================================================================
def drawReferenceLines(entity):
    """
    Docstring
    """
    line = QgsFeature()
    refLinesList = list()

    if entity.whatIs() == "ENTITY":
        selfi = QadPoint()

        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        f = pointGeom.asMultiPoint()
        p = QadPoint.set(selfi, f[0])

        angle1 = math.radians(180+(270-275))
        print(angle1)
        angle2 = math.radians(270+(180-155))
        print(angle2)
        angle3 = math.radians(90)
        lista = [
            [2.5*(math.cos(angle1)), 2.5*(math.sin(angle1))],
            [2.5*(math.cos(angle2)), 2.5*(math.sin(angle2))],
            [2.5*(math.cos(angle3)), 2.5*(math.sin(angle3))]
            ]

        for i in range(len(lista)):
            newPoint = QgsPointXY(p.x()+lista[i][0], p.y()+lista[i][1])
            refLinesList.append([p,newPoint])
            
        return refLinesList
