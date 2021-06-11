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
from .cmd.qad_generic_cmd import QadCommandClass as gen_cmd

# ===============================================================================
# drawLvFuses
# ===============================================================================


def drawInConductor(entity, lvdbAngle):
    fuseLine = list()
    fusePoint = None
    pointGeom = QgsGeometry.fromPointXY(entity)

    canvasCRS = QgsProject.instance().crs().authid()
    destCRS = QgsCoordinateReferenceSystem(canvasCRS)

    lvdbAngleRad = math.radians(90-int(lvdbAngle))
    lista = [1.5*(math.cos(lvdbAngleRad)), 1.5*(math.sin(lvdbAngleRad))]

    if pointGeom.type() == QgsWkbTypes.PointGeometry:
        fusePoint = entity
    elif entity == QgsMultiPoint:
        fusePoint = entity[0]
    else:
        if entity.whatIs == "ENTITY":
            pointGeom = entity.getGeometry(destCRS)
            fusePoint = pointGeom.asMultiPoint()[0]

    newPoint = QgsPointXY(fusePoint[0].x()+lista[0], fusePoint[0].y()+lista[1])
    fuseLine.append([fusePoint[0], newPoint])

    return fuseLine

# ===============================================================================
# drawReferenceLines
# ===============================================================================


def drawReferenceLines(point, lvdbAngle):
    """
    Docstring
    """
    refLinesList = list()

    firstRefAngle = 450-(lvdbAngle + 120)
    firstRefAngleRad = math.radians(firstRefAngle)
    lastRefAngle = 450-(lvdbAngle + 240)
    lastRefAngleRad = math.radians(lastRefAngle)
    lvdbAngleRad = math.radians(450 - lvdbAngle)
    cossinusList = [
        [2.5*(math.cos(firstRefAngleRad)), 2.5*(math.sin(firstRefAngleRad))],
        [2.5*(math.cos(lastRefAngleRad)), 2.5*(math.sin(lastRefAngleRad))],
        [2.5*(math.cos(lvdbAngleRad)), 2.5*(math.sin(lvdbAngleRad))]
    ]

    entityPoint = returnPointFromEntityOrQGSPoint(point)

    for i in range(len(cossinusList)):
        newPoint = QgsPointXY(
            entityPoint.x() + cossinusList[i][0], entityPoint.y() + cossinusList[i][1])
        refLinesList.append([entityPoint, newPoint])

    refLinesList.append([refLinesList[0][1], refLinesList[1][1]])

    return refLinesList


def createReferencePoints(outPoint, lvdbAngle):
    refPointsList = list()
    middleRefPoint = drawRefOutConductor(outPoint, lvdbAngle)
    refPointsList.append(outPoint)
    refPointsList.append(middleRefPoint)

    leftRefAngle = 450-(lvdbAngle + 120)
    leftRefAngleRad = math.radians(leftRefAngle)
    rightRefAngle = 450-(lvdbAngle + 240)
    rightRefAngleRad = math.radians(rightRefAngle)
    cossinusList = [
        [2.5*(math.cos(leftRefAngleRad)), 2.5*(math.sin(leftRefAngleRad))],
        [2.5*(math.cos(rightRefAngleRad)), 2.5*(math.sin(rightRefAngleRad))]
    ]

    entityPoint = returnPointFromEntityOrQGSPoint(outPoint)

    for i in range(len(cossinusList)):
        refPoint = QgsPointXY(
            entityPoint.x() + cossinusList[i][0], entityPoint.y() + cossinusList[i][1])
        refPointsList.append(refPoint)
    return refPointsList


def createLinesFromPoints(firstPoint, lastPoint):
    refLineGeom = [firstPoint, lastPoint]
    return refLineGeom


# ===============================================================================
# drawOutConductor
# ===============================================================================
def drawOutConductor(outPoint, fusesToDraw, lvdbAngle):
    """
    Docstring
    """
    outConductor = list()

    firstPoint = drawRefOutConductor(outPoint, lvdbAngle)
    outConductor.append(firstPoint)

    fromLeft = (fusesToDraw - 1) // 2
    fromRight = (fusesToDraw - 1) - fromLeft

    refPointsList = createReferencePoints(outPoint, lvdbAngle)
    leftLine = createLinesFromPoints(refPointsList[1], refPointsList[2])

    rigthLine = createLinesFromPoints(refPointsList[1], refPointsList[3])

    pointsFromLeft = createPoints(fromLeft, leftLine, False)
    pointsFromRight = createPoints(fromRight, rigthLine, False)
    outConductor.extend(pointsFromLeft)
    outConductor.extend(pointsFromRight)

    pairList = list()
    for point in outConductor:
        pairList.append([outPoint, point])
    return pairList


# ===============================================================================
# getPointFromEntity
# ===============================================================================
def getPointFromEntity(entity):
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


def drawRefOutConductor(outPoint, lvdbAngle):
    lvdbAngleRad = math.radians(getReversedLvdbAngle(lvdbAngle))

    entityPoint = returnPointFromEntityOrQGSPoint(outPoint)

    newPoint = QgsPointXY(entityPoint.x()+1.25*(math.cos(lvdbAngleRad)),
                          entityPoint.y()+1.25*(math.sin(lvdbAngleRad)))

    return newPoint


def returnPointFromEntityOrQGSPoint(entityPoint):
    if type(entityPoint) == QgsPointXY:
        newPoint = QgsPointXY(entityPoint)
    elif entityPoint.whatIs() == "ENTITY":
        qgsPoint = getPointFromEntity(entityPoint)
        newPoint = QgsPointXY(qgsPoint)
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


def vectorMagnitude(point):
    magnitude = math.sqrt(point.x()**2 + point.y()**2)
    return magnitude


def vectorDifference(firstPoint, lastPoint):
    xDiff = firstPoint.x() - lastPoint.x()
    yDiff = firstPoint.y() - lastPoint.y()
    differencePoint = QgsPointXY(xDiff, yDiff)
    return differencePoint


def vectorLength(firstPoint, lastPoint):
    length = math.sqrt(lastPoint.sqrDist(firstPoint))
    return length


def directionCosines(point):
    cosA = point.x()/vectorMagnitude(point)
    cosB = point.y()/vectorMagnitude(point)
    return cosA, cosB


def pairs(pointList):
    for i in range(1, len(pointList)):
        return pointList[i-1], pointList[i]


def createPoints(lineRange, refLine, clockwise=True):
    interval = 0.3
    pointList = list()
    generator = dict()

    generator['segStart'] = pairs(refLine)[0]
    generator['segEnd'] = pairs(refLine)[1]
    lineStart = QgsPointXY(generator['segStart'])
    lineEnd = QgsPointXY(generator['segEnd'])
    pointM = vectorDifference(lineEnd, lineStart)
    cosA, cosB = directionCosines(pointM)
    length = vectorLength(lineEnd, lineStart)

    for i in range(1, lineRange + 1):
        m = i * interval
        if clockwise:
            newPoint = QgsPointXY(
                lineStart.x() + (m * cosA), lineStart.y() + (m*cosB))
        else:
            newPoint = QgsPointXY(
                lineStart.x() - (m * cosA), lineStart.y() - (m*cosB))
        pointList.append(newPoint)
    return pointList
