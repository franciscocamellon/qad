"""
/***************************************************************************
 QAD
                                 A QGIS plugin
 Selezione di layer attraverso gli oggetti grafici
                             -------------------
        begin                : 2019-09-16
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
 This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
   
    # load Qad class from file qad
    from .qad import Qad
    return Qad(iface)
