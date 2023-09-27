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

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
from .algorithms.proj1_identifica_poligonos_vizinhos_sem_mudanca_atributo import Projeto1Solucao
from .algorithms.proj2_identifica_mudanca_atributo_linha import Projeto2Solucao
from .algorithms.proj3_suavizar_linhas import Projeto3Solucao
from .algorithms.proj4_fechar_linhas import Projeto4Solucao
from .algorithms.proj5_aparar_linhas import Projeto4Solucao
from .algorithms.proj6_expandir_linhas import Projeto4Solucao


class ProgramacaoAplicadaGrupo4Provider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(Projeto1Solucao())
        self.addAlgorithm(Projeto2Solucao())
        self.addAlgorithm(Projeto3Solucao())
        self.addAlgorithm(Projeto4Solucao())
        self.addAlgorithm(Projeto3Solucao())
        self.addAlgorithm(Projeto4Solucao())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'ProgramacaoAplicadaGrupo4'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('ProgramacaoAplicadaGrupo4')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
