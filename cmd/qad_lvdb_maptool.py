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


from qgis.core import QgsWkbTypes, QgsGeometry


from .. import qad_utils
from ..qad_variables import QadVariables
from ..qad_getpoint import QadGetPoint, QadGetPointDrawModeEnum, QadGetPointSelectionModeEnum
from ..qad_highlight import QadHighlight
from ..qad_dim import QadDimStyles
from ..qad_msg import QadMsg
from ..qad_offset_fun import offsetPolyline
from ..qad_geom_relations import getQadGeomClosestPart


#===============================================================================
# Qad_lvdb_maptool_ModeEnum class.
#===============================================================================
class Qad_lvdb_maptool_ModeEnum():
   # si richiede il primo punto per calcolo offset 
   # NONE_KNOWN_ASK_FOR_BASE_PT = 1     
   # noto il primo punto per calcolo offset si richiede il secondo punto
   ASK_FOR_LV_FUSE_NUMBER = 1     
   # nota la distanza di offset si richiede il punto per stabilire da che parte
   FUSE_NUMBER_KNOWN_ASK_FOR_LVDBFP_ANGLE = 2
   # si richiede il punto di passaggio per stabilire da che parte e a quale offset
   LVDBFP_ANGLE_KNOWN_ASK_FOR_DRAW_CONDUCTOR = 3

   DRAW_CONDUCTOR_KNOWN_ASK_FOR_FILLING_ATTRIBUTES = 4

#===============================================================================
# Qad_offset_maptool class
#===============================================================================
class Qad_lvdb_maptool(QadGetPoint):
    
   def __init__(self, plugIn):
      QadGetPoint.__init__(self, plugIn)
                        
      self.basePt = None
      self.cacheEntitySet = None
      self.__highlight = QadHighlight(self.canvas)

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
   

   def addOffSetGeometries(self, newPt):
      self.__highlight.reset()
       
      # la funzione ritorna una lista con 
      # (<minima distanza>
      # <punto più vicino>
      # <indice della geometria più vicina>
      # <indice della sotto-geometria più vicina>
      # <indice della parte della sotto-geometria più vicina>
      # <"a sinistra di" se il punto é alla sinista della parte con i seguenti valori:
      # -   < 0 = sinistra (per linea, arco o arco di ellisse) o interno (per cerchi, ellissi)
      # -   > 0 = destra (per linea, arco o arco di ellisse) o esterno (per cerchi, ellissi)
      result = getQadGeomClosestPart(self.subGeom, newPt)
      leftOf = result[5]
       
      if self.offset < 0:
         offsetDistance = result[0] # minima distanza
      else:           
         offsetDistance = self.offset
 
         if leftOf < 0: # a sinistra (per linea, arco o arco di ellisse) o interno (per cerchi, ellissi)
            offsetDistance = offsetDistance + self.lastOffSetOnLeftSide
         else: # alla destra
            offsetDistance = offsetDistance + self.lastOffSetOnRightSide         
       
      lines = offsetPolyline(self.subGeom, \
                             offsetDistance, \
                             "left" if leftOf < 0 else "right", \
                             self.gapType)
 
      for line in lines:
         pts = line.asPolyline()
         if self.layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            if line[0] == line[-1]: # se é una linea chiusa
               offsetGeom = QgsGeometry.fromPolygonXY([pts])
            else:
               offsetGeom = QgsGeometry.fromPolylineXY(pts)
         else:
            offsetGeom = QgsGeometry.fromPolylineXY(pts)
 
         self.__highlight.addGeometry(self.mapToLayerCoordinates(self.layer, offsetGeom), self.layer)


   def canvasMoveEvent(self, event):
      QadGetPoint.canvasMoveEvent(self, event)
      
      if self.mode == Qad_lvdb_maptool_ModeEnum.ASK_FOR_LV_FUSE_NUMBER:
         # chamar a função que desnha os angulos referencia
         print('Hello world')                           
                                 
         
    
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
      if self.mode == Qad_lvdb_maptool_ModeEnum.ASK_FOR_LV_FUSE_NUMBER:
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
      
      # # noto il primo punto per calcolo offset si richiede il secondo punto
      # if self.mode == Qad_lvdb_maptool_ModeEnum.FIRST_OFFSET_PT_KNOWN_ASK_FOR_SECOND_PT:
      #    self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
      #    self.setDrawMode(QadGetPointDrawModeEnum.ELASTIC_LINE)
      #    self.setStartPoint(self.firstPt)
      #    self.onlyEditableLayers = False
      # # nota la distanza di offset si richiede il punto per stabilire da che parte
      # elif self.mode == Qad_lvdb_maptool_ModeEnum.OFFSET_KNOWN_ASK_FOR_SIDE_PT:
      #    self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
      #    self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      #    self.onlyEditableLayers = False
      # # si richiede il punto di passaggio per stabilire da che parte e a quale offset
      # elif self.mode == Qad_lvdb_maptool_ModeEnum.ASK_FOR_PASSAGE_PT:
      #    self.setSelectionMode(QadGetPointSelectionModeEnum.POINT_SELECTION)
      #    self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      #    self.onlyEditableLayers = False
      # # si richiede la selezione di un oggetto
      # elif self.mode == Qad_lvdb_maptool_ModeEnum.ASK_FOR_ENTITY_SELECTION:
      #    self.setSelectionMode(QadGetPointSelectionModeEnum.ENTITY_SELECTION)
      #    # solo layer lineari o poligono editabili che non appartengano a quote
      #    layerList = []
      #    for layer in qad_utils.getVisibleVectorLayers(self.plugIn.canvas): # Tutti i layer vettoriali visibili
      #       if (layer.geometryType() == QgsWkbTypes.LineGeometry or layer.geometryType() == QgsWkbTypes.PolygonGeometry) and \
      #          layer.isEditable():
      #          if len(QadDimStyles.getDimListByLayer(layer)) == 0:
      #             layerList.append(layer)
         
      #    self.layersToCheck = layerList
      #    self.setDrawMode(QadGetPointDrawModeEnum.NONE)
      #    self.onlyEditableLayers = True
