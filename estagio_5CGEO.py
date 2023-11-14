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

import os
import sys
import inspect
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from qgis.core import (Qgis,
                       QgsPoint,
                       QgsPointXY,
                       QgsGeometry,
                       QgsApplication)

from .estagio_5CGEO_provider import Estagio5CGEOProvider
from qgis.utils import iface
cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

class Estagio5CGEOPlugin(object):

    def __init__(self, iface):
        self.iface = iface

    
    def initProcessing(self):
        self.provider = Estagio5CGEOProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)
    
    def initGui(self):
        self.initProcessing()
        icon1 = os.path.join(os.path.join(cmd_folder, 'apara_linha.png'))
        icon2 = os.path.join(os.path.join(cmd_folder, 'fecha_linha.png'))
        icon3 = os.path.join(os.path.join(cmd_folder, 'exp_linha.png'))
        icon4 = os.path.join(os.path.join(cmd_folder, 'suav_linha.png'))
        self.action1 = QAction(QIcon(icon1), 'Aparar linha', self.iface.mainWindow())
        self.action2 = QAction(QIcon(icon2), 'Fechar linha', self.iface.mainWindow())
        self.action3 = QAction(QIcon(icon3), 'Expandir linha', self.iface.mainWindow())
        self.action4 = QAction(QIcon(icon4), 'Suavizar linha', self.iface.mainWindow())
        self.iface.addToolBarIcon(self.action1)
        self.iface.addToolBarIcon(self.action2)
        self.iface.addToolBarIcon(self.action3)
        self.iface.addToolBarIcon(self.action4)
        self.action1.triggered.connect(self.run1)
        self.action2.triggered.connect(self.run2)
        self.action3.triggered.connect(self.run3)
        self.action4.triggered.connect(self.run4)
        self.action1.setShortcut("Ctrl+Alt+Q")
        self.action2.setShortcut("Ctrl+Alt+F")
        self.action3.setShortcut("Ctrl+Alt+E")
        self.action4.setShortcut("Ctrl+Alt+S")

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.removeToolBarIcon(self.action1)
        self.iface.removeToolBarIcon(self.action2)
        self.iface.removeToolBarIcon(self.action3)
        self.iface.removeToolBarIcon(self.action4)

    def run1(self): #Aparar linhas
        inputLyr = iface.activeLayer()
        inputFeat = inputLyr.selectedFeatures()
        tol = 10 #Pode ser ajustado conforme necessidade

        # Check if a layer is selected
        if not inputFeat or len(inputFeat) == 1:
            iface.messageBar().pushMessage('Por favor, selecione ao menos duas feições',  level=Qgis.Critical)

        else:    
            #Criação de uma camada de linhas de interseção entre os produtos
            for linhas in inputFeat:
                geometria = linhas.geometry()

                for parts in geometria.parts(): vertices = list(parts)

                ponto_inicial = vertices[0]
                ponto_final = vertices[-1]

                for lines in inputFeat:
                    geometry = lines.geometry()

                    if linhas.id() != lines.id() and geometria.intersects(geometry):
                        vertice = geometria.intersection(geometry).asPoint()
                        dist1 = vertice.distance(QgsPointXY(ponto_inicial))
                        dist2 = vertice.distance(QgsPointXY(ponto_final))
                    
                        if dist1 < tol: new_geometry = QgsGeometry.fromPolyline([QgsPoint(vertice), ponto_final])
                        elif dist2 < tol: new_geometry = QgsGeometry.fromPolyline([ponto_inicial, QgsPoint(vertice)])
                        else: continue

                        linhas.setGeometry(new_geometry)
                        inputLyr.updateFeature(linhas)
                        self.iface.messageBar().pushMessage(f'Linha {linhas.id()} foi aparada.')


    def run2(self): #Fechar linhas
        inputLyr = iface.activeLayer()
        distance = 10 #Pode ser ajustado conforme necessidade

        # Check if a layer is selected
        if not inputLyr.selectedFeatures():
            iface.messageBar().pushMessage('Please select a feature',  level=Qgis.Critical)

        else:    
            #Criação de uma camada de linhas de interseção entre os produtos
            for linhas in inputLyr.selectedFeatures():
                geometria = linhas.geometry()
                for parts in geometria.parts():vertices = list(parts)

                #Atribuição dos pontos extremos
                ponto_inicial = vertices[0]
                ponto_final = vertices[-1]

                #Distância entre os pontos extremos
                distancia = ponto_final.distance(ponto_inicial)

                #Condição para caso a distância entre os pontos extremos distam menor que a distancia minima
                if distancia <= distance: vertices.append(ponto_inicial)
                
                #Inserção da linha fechada à camada
                linha_fechada = QgsGeometry.fromPolyline(vertices)
                linhas.setGeometry(linha_fechada)
                inputLyr.updateFeature(linhas)
                self.iface.messageBar().pushMessage(f'Linha {linhas.id()} fechada.')

    def run3(self): #Expandir linhas
        inputLyr = iface.activeLayer()
        inputFeat = inputLyr.selectedFeatures()
        tol = 10 #Pode ser ajustado conforme necessidade

        # Check if a layer is selected
        if not inputFeat or len(inputFeat) == 1:
            iface.messageBar().pushMessage('Por favor, selecione ao menos duas feições',  level=Qgis.Critical)

        else:    
           #Criação de uma camada de linhas de interseção entre os produtos
            for linhas in inputFeat: 
                geometria = linhas.geometry()
                #feedback.pushInfo(f'\nA linha {linhas} do tipo {type(linhas)} e a geometria {geometria} do tipo {type(geometria)}.')
                for parts in geometria.parts():vertices = list(parts)

                #Primeira extremidade da linha
                ponto_inicial = vertices[1]
                ponto_final = vertices[0]
                self.operation(ponto_inicial, ponto_final, inputFeat, linhas, geometria, tol, vertices, 1, inputLyr)

                #Segunda extremidade da linha
                ponto_inicial = vertices[-2]
                ponto_final = vertices[-1]
                self.operation(ponto_inicial, ponto_final, inputFeat, linhas, geometria, tol, vertices, 2, inputLyr)

    def operation(self, ponto_inicial, ponto_final, inputFeat, linhas, geometria, tol, vertices, extremidade, inputLyr):
        extremidade = extremidade
        #Obtenção do vetor direção
        vetor_direcao = ponto_final - ponto_inicial

        #Obtenção do comprimento do vetor
        comprimento_vetor = (vetor_direcao.x()**2 + vetor_direcao.y()**2)**0.5
        
        # Normaliza o vetor direção
        if comprimento_vetor > 0:
            vetor_direcao = QgsPoint(vetor_direcao.x() / comprimento_vetor, vetor_direcao.y() / comprimento_vetor)
        
        ponto_inicial_extendido = QgsPoint(ponto_inicial.x() - tol * vetor_direcao.x(), ponto_inicial.y() - tol * vetor_direcao.y())
        ponto_final_extendido = QgsPoint(ponto_final.x() + tol * vetor_direcao.x(), ponto_final.y() + tol * vetor_direcao.y())
        linha_extendida = QgsGeometry.fromPolyline([ponto_inicial_extendido, ponto_final_extendido])
        
        for lines in inputFeat:
            geometry = lines.geometry()

            if geometria.disjoint(geometry) and linha_extendida.intersects(geometry) and linhas.id() != lines.id():
                ponto_referencia = linha_extendida.intersection(geometry).asPoint()
                ponto_referencia = QgsPoint(ponto_referencia.x() + 1 * vetor_direcao.x(), ponto_referencia.y() + 1 * vetor_direcao.y()) #Está estendido em mais 1 metro
                if extremidade == 1:
                    vertices[0] = ponto_referencia
                    linha_extendida = [point for point in vertices]

                else:
                    vertices[-1] = ponto_referencia
                    linha_extendida = [point for point in vertices]

                linha_extendida = QgsGeometry.fromPolyline(linha_extendida)               
                linhas.setGeometry(linha_extendida)
                inputLyr.updateFeature(linhas)
                self.iface.messageBar().pushMessage(f'Linha {linhas.id()} expandida.')
        
    def run4(self): #Suavizar linhas
        inputLyr = iface.activeLayer()

        #Definição de parâmetros
        iteracoes = 5
        deslocamento = 0.1

        # Check if a layer is selected
        if not inputLyr.selectedFeatures():
            iface.messageBar().pushMessage('Please select a feature',  level=Qgis.Critical)

        else:
            for linhas in inputLyr.selectedFeatures():
                geometria = linhas.geometry()
                
                #Obtendo a linha suavizada
                new_geometry = geometria.smooth(iteracoes, deslocamento)  #Iterações igual a 5 e deslocamento igual a 10%

                linhas.setGeometry(new_geometry)
                inputLyr.updateFeature(linhas)
                self.iface.messageBar().pushMessage(f'Linha {linhas.id()} suavizada com {iteracoes} iterações e {deslocamento*100}% de off set.')
