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

        newPoint = QgsPointXY(
            fusePoint[0].x()+lista[0], fusePoint[0].y()+lista[1])
        fuseLine.append([fusePoint[0], newPoint])
    return fuseLine


# ===============================================================================
# drawOutConductor
# ===============================================================================
def drawOutConductor(entity, fusesToDraw, lvdbAngle):
    """
    Docstring
    """
    outConductor = list()
    firstRefAngle = math.radians(450-(lvdbAngle + 120))
    intervalAngle = 120 / fusesToDraw
    refAngle = getArcCossinus()
    refPoint = drawRefOutConductor(entity, lvdbAngle)
    distBetweenPoints = 1.5*(getOffsetDistanceFromFuse())

    if entity.whatIs() == "ENTITY":
        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        outPoint = pointGeom.asMultiPoint()[0]

        for fuse in range(fusesToDraw):
            newPoint = QgsPointXY(outPoint.x()-1.5*math.cos(firstRefAngle),
                                  outPoint.y()+1.5*math.sin(firstRefAngle))
            firstRefAngle += refAngle
            outConductor.append([outPoint, newPoint])
            

        return outConductor
# ===============================================================================
# drawRefOutConductor
# ===============================================================================
def drawRefOutConductor(entity, lvdbAngle):
    outConductor = list()
    lvdbAngleRad = math.radians(getReversedLvdbAngle(lvdbAngle))
    # passar o ponto logo ao inves da entity
    if entity.whatIs() == "ENTITY":
        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        outPoint = pointGeom.asMultiPoint()[0]

        newPoint = QgsPointXY(outPoint.x()+1.5*(math.cos(lvdbAngleRad)),
                                outPoint.y()+1.5*(math.sin(lvdbAngleRad)))
        # outConductor.append([outPoint, newPoint])

        return newPoint

# ===============================================================================
# drawOutConductor
# ===============================================================================


def getOffsetDistanceFromFuse():
    distance = (0.3 * math.sqrt(2)) / 2
    return distance

# ===============================================================================
# getReversedLvdbAngle
# ===============================================================================


def getReversedLvdbAngle(lvdbAngle):
    cartesianAngle = 450 - lvdbAngle
    if cartesianAngle < 180:
        reverseLvdbAngle = cartesianAngle + 180
    elif cartesianAngle > 180:
        reverseLvdbAngle = cartesianAngle - 180
    return reverseLvdbAngle


# ===============================================================================
# drawReferenceLines
# ===============================================================================
def drawReferenceLines(entity, lvdbAngle):
    """
    Docstring
    """
    line = QgsFeature()
    refLinesList = list()
    reverseLvdbAngle = getReversedLvdbAngle(lvdbAngle)
    print('reverseLvdbAngle: ', reverseLvdbAngle)

    if entity.whatIs() == "ENTITY":
        selfi = QadPoint()

        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        f = pointGeom.asMultiPoint()
        p = QadPoint.set(selfi, f[0])

        firstRefAngle = 450-(lvdbAngle + 120)
        firstRefAngleRad = math.radians(firstRefAngle)
        lastRefAngle = 450-(lvdbAngle + 240)
        lastRefAngleRad = math.radians(lastRefAngle)
        lvdbAngleRad = math.radians(450 - lvdbAngle)
        lista = [
            [1.5*(math.cos(firstRefAngleRad)),
             1.5*(math.sin(firstRefAngleRad))],
            [1.5*(math.cos(lastRefAngleRad)), 1.5*(math.sin(lastRefAngleRad))],
            [2.5*(math.cos(lvdbAngleRad)), 2.5*(math.sin(lvdbAngleRad))]
        ]

        for i in range(len(lista)):
            newPoint = QgsPointXY(p.x()+lista[i][0], p.y()+lista[i][1])
            refLinesList.append([p, newPoint])

        return refLinesList

def getArcCossinus():
    xy = xz = 1.5
    yz = 0.3
    dividend = math.pow(xy, 2) + math.pow(xz, 2) - math.pow(yz, 2)
    divider = 2*xy*xz
    cossinus = dividend/divider
    arcCoss = math.acos(cossinus)
    return arcCoss