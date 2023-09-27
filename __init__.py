# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ProjetosEstagio5CGEO
                                 A QGIS plugin
 Solução dos Estagiarios do 5 CGEO
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-04-04
        copyright            : (C) 2023 by Estagiarios 5 CGEO
        emails               : e.tadeu.eb@ime.eb.br
                               joao.pereira@ime.eb.br
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

__author__ = 'Estagiarios do 5 CGEO'
__date__ = '2023-04-04'
__copyright__ = '(C) 2023 by Estagiarios 5 CGEO'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load estagio_5CGEO class from file estagio_5CGEO.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .estagio_5CGEO import estagio_5CGEOPlugin
    return estagio_5CGEOPlugin()
