# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 classe per gestire il map tool in ambito del comando offset
 
                              -------------------
        begin                : 2013-10-04
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


from qgis.core import QgsMapLayer, QgsVectorLayer, QgsMessageLog, QgsProject, QgsFeature, QgsGeometry, QgsPointXY
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsMapToolEmitPoint, QgsMapCanvas, QgsMapTool
import qgis.utils
from qgis.PyQt.QtWidgets import (QHBoxLayout,
                                 QVBoxLayout,
                                 QMessageBox,
                                 QHeaderView,
                                 QWidget,
                                 QComboBox,
                                 QLineEdit)


from .. import qad_utils
from ..qad_variables import QadVariables
from ..qad_getpoint import QadGetPoint, QadGetPointDrawModeEnum, QadGetPointSelectionModeEnum
from ..qad_highlight import QadHighlight
from ..qad_rubberband import QadRubberBand
from ..qad_dim import QadDimStyles
from ..qad_msg import QadMsg
from ..qad_layer import getLayersByName
from ..qad_offset_fun import offsetPolyline
from ..qad_geom_relations import getQadGeomClosestPart


#===============================================================================
# Qad_lvdb_maptool_ModeEnum class.
#===============================================================================
class Qad_lvdb_maptool_ModeEnum():
   # si richiede il primo punto per calcolo offset 
   NONE_KNOWN_ASK_FOR_CREATE = 1     
   # noto il primo punto per calcolo offset si richiede il secondo punto
   ASK_FOR_LV_FUSE_NUMBER = 2    
   # nota la distanza di offset si richiede il punto per stabilire da che parte
   FUSE_NUMBER_KNOWN_ASK_FOR_LVDBFP_ANGLE = 3
   # si richiede il punto di passaggio per stabilire da che parte e a quale offset
   LVDBFP_ANGLE_KNOWN_ASK_FOR_DRAW_CONDUCTOR = 4

   DRAW_CONDUCTOR_KNOWN_ASK_FOR_FILLING_ATTRIBUTES = 5

#===============================================================================
# Qad_offset_maptool class
#===============================================================================
class Qad_lvdb_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
      # self.iface = self.plugIn.iface.mainWindow()
      # self.iface = qgis.utils.iface.mapCanvas()
      self.basePt = None
      self.cacheEntitySet = None
      self.x = float()
      self.y = float()
      self.__highlight = QadHighlight(self.canvas)
      # self.__rubberBand = QadRubberBand(self.canvas)

   def hidePointMapToolMarkers(self):
      QadGetPoint.hidePointMapToolMarkers(self)
      self.__highlight.hide()

   def showPointMapToolMarkers(self):
      QadGetPoint.showPointMapToolMarkers(self)
      self.__highlight.show()
                             
   def clear(self):
      QadGetPoint.clear(self)
      self.__highlight.reset()
      self.mode = None


   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)

      self.__highlight.reset()
      if self.mode == Qad_lvdb_maptool_ModeEnum.ASK_FOR_LV_FUSE_NUMBER:
         print("hello world")

   def canvasPressEvent(self, event):
      QadGetPoint.canvasPressEvent(self, event)

      self.__highlight.reset()

      if self.mode == Qad_lvdb_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CREATE:
         point = self.toMapCoordinates(self.canvas.mouseLastXY())
         self.x = point[0]
         self.y = point[1]     

   def canvasReleaseEvent(self, event):
      QadGetPoint.canvasReleaseEvent(self, event)

      self.__highlight.reset()

      if self.mode == Qad_lvdb_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CREATE:
         features = []
         layer = QgsProject.instance().mapLayersByName('LVDB-FP')[0]
         pr = layer.dataProvider()
         feature = QgsFeature(layer.fields())
         geom = QgsGeometry().fromPointXY(QgsPointXY(self.x, self.y))
         feature.setGeometry(
                    self.mapToLayerCoordinates(layer, geom))
         features.append(feature)
         
         for feat in features:
            layer.select(feat.id())
            if event.button() == Qt.RightButton:
               self.canvas.unsetMapTool(self)
            else:
               self.iface.openFeatureForm(layer, feat, False)
               if event.button() == QMessageBox.OK:
                  pr.addFeature(feat)
                  
                  layer.triggerRepaint()  
               
                                    
                                 
         
    
   def activate(self):
      QadGetPoint.activate(self)            
      self.__highlight.show()          

   def deactivate(self):
      try: # necessario perché se si chiude QGIS parte questo evento nonostante non ci sia più l'oggetto maptool !
         QadGetPoint.deactivate(self)
         self.__highlight.hide()
      except:
         pass

   def setMode(self, mode):
      self.mode = mode
      # si richiede il primo punto per calcolo offset
      
      if self.mode == Qad_lvdb_maptool_ModeEnum.NONE_KNOWN_ASK_FOR_CREATE:
         self.setDrawMode(QadGetPointDrawModeEnum.NONE) 
         self.setStartPoint(self.tmpPoint)
         self.__highlight.reset()
      elif self.mode == Qad_lvdb_maptool_ModeEnum.ASK_FOR_LV_FUSE_NUMBER:
         self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
         self.__highlight.reset()
      elif self.mode == Qad_lvdb_maptool_ModeEnum.FUSE_NUMBER_KNOWN_ASK_FOR_LVDBFP_ANGLE:
         self.setSelectionMode(QadGetPointSelectionModeEnum.NONE)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      elif self.mode == Qad_lvdb_maptool_ModeEnum.LVDBFP_ANGLE_KNOWN_ASK_FOR_DRAW_CONDUCTOR:
         self.setSelectionMode(QadGetPointSelectionModeEnum.NONE)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      elif self.mode == Qad_lvdb_maptool_ModeEnum.DRAW_CONDUCTOR_KNOWN_ASK_FOR_FILLING_ATTRIBUTES:
         self.setSelectionMode(QadGetPointSelectionModeEnum.NONE)
         self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      
      
