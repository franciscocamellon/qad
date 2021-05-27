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
# drawReferenceLines
# ===============================================================================
def drawReferenceLines(entity, lvdbAngle):
    """
    Docstring
    """
    refLinesList = list()
    p = getPointFromEntity(entity)

    firstRefAngle = 450-(lvdbAngle + 120)
    firstRefAngleRad = math.radians(firstRefAngle)
    lastRefAngle = 450-(lvdbAngle + 240)
    lastRefAngleRad = math.radians(lastRefAngle)
    lvdbAngleRad = math.radians(450 - lvdbAngle)
    lista = [
        [2.5*(math.cos(firstRefAngleRad)), 2.5*(math.sin(firstRefAngleRad))],
        [2.5*(math.cos(lastRefAngleRad)), 2.5*(math.sin(lastRefAngleRad))],
        [2.5*(math.cos(lvdbAngleRad)), 2.5*(math.sin(lvdbAngleRad))]
    ]

    for i in range(len(lista)):
        newPoint = QgsPointXY(p.x()+lista[i][0], p.y()+lista[i][1])
        refLinesList.append([p, newPoint])

    refLinesList.append([refLinesList[0][1], refLinesList[1][1]])
    
    return refLinesList

def drawTriangleIntersector():


    return None

def createLines(entity, lvdbAngle):
    # listOfLines = [[p1,p2],[p2,p3]]
    listOfLines = drawReferenceLines(entity, lvdbAngle)
    triangleLines = [listOfLines[0][0], listOfLines[1][1]]

    return None


# ===============================================================================
# drawOutConductor
# ===============================================================================
def drawOutConductor(entity, fusesToDraw, lvdbAngle):
    """
    Docstring
    """
    outConductor = list()
    outPoint = getPointFromEntity(entity)
    lvdbAngleRad = math.radians(getReversedLvdbAngle(lvdbAngle))

    firstPoint = drawRefOutConductor(entity, lvdbAngle)
    outConductor.append([outPoint, firstPoint])

    fromLeft = (fusesToDraw - 1) // 2
    fromRight = (fusesToDraw - 1) - fromLeft
    
    refAngle = getArcCossinus()

    for fuse in range(fromLeft):
        lvdbAngleRad += refAngle
        newPoint = QgsPointXY(outPoint.x()+1.5*(math.cos(lvdbAngleRad)),
                            outPoint.y()+1.5*(math.sin(lvdbAngleRad)))
        outConductor.append([outPoint, newPoint])

    lvdbAngleRad = math.radians(getReversedLvdbAngle(lvdbAngle))

    for fuse in range(fromRight):
        lvdbAngleRad -= refAngle
        newPoint = QgsPointXY(outPoint.x()+1.5*(math.cos(lvdbAngleRad)),
                            outPoint.y()+1.5*(math.sin(lvdbAngleRad)))
        outConductor.append([outPoint, newPoint])

    return outConductor

# ===============================================================================
# getPointFromEntity
# ===============================================================================
def getPointFromEntity(entity):
    if entity.whatIs() == "ENTITY":
        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        outPoint = pointGeom.asMultiPoint()[0]
    return outPoint

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
# drawRefOutConductor
# ===============================================================================
def drawRefOutConductor(entity, lvdbAngle):
    lvdbAngleRad = math.radians(getReversedLvdbAngle(lvdbAngle))
    outPoint = getPointFromEntity(entity)
    newPoint = QgsPointXY(outPoint.x()+1.5*(math.cos(lvdbAngleRad)),
                            outPoint.y()+1.5*(math.sin(lvdbAngleRad)))
    return newPoint

# ===============================================================================
# getArcCossinus
# ===============================================================================
def getArcCossinus():
    xy = xz = 1.5
    yz = 0.3
    dividend = math.pow(xy, 2) + math.pow(xz, 2) - math.pow(yz, 2)
    divider = 2*xy*xz
    cossinus = dividend/divider
    arcCoss = math.acos(cossinus)
    return arcCoss

# ===============================================================================
# getCartesianAngle
# ===============================================================================
def getCartesianAngle(lvdbAngle):
    if lvdbAngle < 90:
        cartesianAngle = 90 - lvdbAngle
    elif lvdbAngle > 90 and lvdbAngle < 180:
        cartesianAngle = 180 - lvdbAngle
    elif lvdbAngle > 180 and lvdbAngle < 270:
        cartesianAngle = 270 - lvdbAngle
    else:
        cartesianAngle = 360 - lvdbAngle
    return cartesianAngle

# ===============================================================================
# getPointFromCartesianQuadrant
# ===============================================================================

def getPointFromCartesianQuadrant(lvdbAngleRad, point):
    lvdbDegreeAngle = math.degrees(lvdbAngleRad)
    print('lvdbDegreeAngle: ',lvdbDegreeAngle)
    if lvdbDegreeAngle < 90:
        newPoint = QgsPointXY(point.x()-1.5*(math.cos(lvdbAngleRad)),
                              point.y()-1.5*(math.sin(lvdbAngleRad)))
        print('newpoint 90: ', newPoint)
    elif lvdbDegreeAngle > 90 and lvdbDegreeAngle < 180:
        newPoint = QgsPointXY(point.x()+1.5*(math.cos(lvdbAngleRad)),
                              point.y()-1.5*(math.sin(lvdbAngleRad)))
        print('newpoint 180: ', newPoint)
    elif lvdbDegreeAngle > 180 and lvdbDegreeAngle < 270:
        newPoint = QgsPointXY(point.x()+1.5*(math.cos(lvdbAngleRad)),
                              point.y()+1.5*(math.sin(lvdbAngleRad)))
        print('newpoint 270: ', newPoint)
    else:
        newPoint = QgsPointXY(point.x()-1.5*(math.cos(lvdbAngleRad)),
                              point.y()+1.5*(math.sin(lvdbAngleRad)))
        print('newpoint 360: ', newPoint)
    return newPoint






    