# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProgramacaoAplicadaGrupo4
                                 A QGIS plugin
 Solução do Grupo 4
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-04-04
        copyright            : (C) 2023 by Grupo 4
        emails               : e.tadeu.eb@ime.eb.br
                               raulmagno@ime.eb.br
                               arthur.cavalcante@ime.eb.br
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

__author__ = 'Grupo 4'
__date__ = '2023-04-04'
__copyright__ = '(C) 2023 by Grupo 4'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ProgramacaoAplicadaGrupo4 class from file ProgramacaoAplicadaGrupo4.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .estagio_5CGEO import ProgramacaoAplicadaGrupo4Plugin
    return ProgramacaoAplicadaGrupo4Plugin()