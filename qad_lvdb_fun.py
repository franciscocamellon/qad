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
    print("lvdbAngle: ",lvdbAngle," - ",type(lvdbAngle))
    if entity.whatIs() == "ENTITY":
        canvasCRS = QgsProject.instance().crs().authid()
        destCRS = QgsCoordinateReferenceSystem(canvasCRS)
        pointGeom = entity.getGeometry(destCRS)
        fusePoint = pointGeom.asMultiPoint()
        lvdbAngleRad = math.radians(90-int(lvdbAngle))
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

def createReferencePoints(entity, lvdbAngle):
    refPointsList = list()
    point = getPointFromEntity(entity)
    middleRefPoint = drawRefOutConductor(entity, lvdbAngle)
    refPointsList.append(point)
    refPointsList.append(middleRefPoint)

    leftRefAngle = 450-(lvdbAngle + 120)
    leftRefAngleRad = math.radians(leftRefAngle)
    rightRefAngle = 450-(lvdbAngle + 240)
    rightRefAngleRad = math.radians(rightRefAngle)
    lista = [
        [2.5*(math.cos(leftRefAngleRad)), 2.5*(math.sin(leftRefAngleRad))],
        [2.5*(math.cos(rightRefAngleRad)), 2.5*(math.sin(rightRefAngleRad))]
    ]

    for i in range(len(lista)):
        refPoint = QgsPointXY(point.x()+lista[i][0], point.y()+lista[i][1])
        refPointsList.append(refPoint)
    return refPointsList

def createLinesFromPoints(firstPoint, lastPoint):
    # refLineGeom = QgsGeometry.fromPolylineXY([firstPoint, lastPoint])
    refLineGeom = [firstPoint, lastPoint]
    return refLineGeom



# ===============================================================================
# drawOutConductor
# ===============================================================================
def drawOutConductor(entity, fusesToDraw, lvdbAngle):
    """
    Docstring
    """
    outConductor = list()
    outPoint = getPointFromEntity(entity)
    # lvdbAngleRad = math.radians(getReversedLvdbAngle(lvdbAngle))

    firstPoint = drawRefOutConductor(entity, lvdbAngle)
    outConductor.append(firstPoint)

    fromLeft = (fusesToDraw - 1) // 2
    print(fromLeft)
    fromRight = (fusesToDraw - 1) - fromLeft
    print(fromRight)
    # refAngle = getArcCossinus()
    refPointsList = createReferencePoints(entity, lvdbAngle)
    lefLine = createLinesFromPoints(refPointsList[1], refPointsList[2])
    print(lefLine)
    rigthLine = createLinesFromPoints(refPointsList[1],refPointsList[3])
    print(rigthLine)
    pointsFromLeft = createPoints(fromLeft, lefLine, False)
    pointsFromRight = createPoints(fromRight, rigthLine, False)
    # for fuse in range(fromLeft):  # recebe uma line e um range fromleft
    #     lvdbAngleRad += refAngle
    #     newPoint = QgsPointXY(outPoint.x()+1.5*(math.cos(lvdbAngleRad)),
    #                         outPoint.y()+1.5*(math.sin(lvdbAngleRad)))
        # outConductor.append([outPoint, newPoint])
    outConductor.extend(pointsFromLeft)
    outConductor.extend(pointsFromRight)

    # lvdbAngleRad = math.radians(getReversedLvdbAngle(lvdbAngle))

    # for fuse in range(fromRight): # recebe a outra line e o outro range from right
    #     lvdbAngleRad -= refAngle
    #     newPoint = QgsPointXY(outPoint.x()+1.5*(math.cos(lvdbAngleRad)),
    #                         outPoint.y()+1.5*(math.sin(lvdbAngleRad)))
    #     outConductor.append([outPoint, newPoint])
    pairList = list()
    for point in outConductor:
        pairList.append([outPoint, point])
    print(pairList)
    return pairList


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
    newPoint = QgsPointXY(outPoint.x()+1.25*(math.cos(lvdbAngleRad)),
                            outPoint.y()+1.25*(math.sin(lvdbAngleRad)))
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

    # lineGeom = refLine.geometry()
    # generator['segStart'] = pairs(lineGeom.asPolyline())[0]
    generator['segStart'] = pairs(refLine)[0]
    # generator['segEnd'] = pairs(lineGeom.asPolyline())[1]
    generator['segEnd'] = pairs(refLine)[1]
    # for points in generator.items():
    lineStart = QgsPointXY(generator['segStart'])
    lineEnd = QgsPointXY(generator['segEnd'])
    pointM = vectorDifference(lineEnd, lineStart)
    cosA, cosB = directionCosines(pointM)
    length = vectorLength(lineEnd, lineStart)

    for i in range(1, lineRange + 1):
        m = i * interval
        if clockwise:
            newPoint = QgsPointXY(lineStart.x()  + (m * cosA), lineStart.y() + (m*cosB))
        else:
            newPoint = QgsPointXY(lineStart.x()  - (m * cosA), lineStart.y() - (m*cosB))
        pointList.append(newPoint)
    return pointList



