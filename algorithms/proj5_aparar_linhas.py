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
from code import interact
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.Qt import QVariant, QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProject,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingException,
                       QgsWkbTypes,
                       QgsExpressionContextUtils,
                       QgsPointXY,
                       QgsPoint,
                       QgsPointLocator,
                       QgsSpatialIndex,
                       QgsFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsExpression,
                       QgsVectorLayer,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterVectorLayer,
                       QgsFields,
                       QgsFeature,
                       QgsField,
                       QgsGeometry,
                       QgsGeometryUtils,
                       QgsGeometryCollection,
                       QgsMarkerSymbol)
import processing
from PyQt5.QtGui import QColor


class Projeto5Solucao(QgsProcessingAlgorithm):
    """
    
    Este algoritmo realiza a revisão de ligação entre produtos.

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    # Camadas de input
    INPUT = 'INPUT'

    # Camadas de output
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, self.tr('Insira a camada de linha'), 
                                                            types=[QgsProcessing.TypeVectorLine], 
                                                            defaultValue=None))
                              
        self.addParameter(QgsProcessingParameterNumber(self.DISTANCIA,
                                                       self.tr('Insira a distância de busca'),
                                                       defaultValue=0.01,
                                                       type=QgsProcessingParameterNumber.Double))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Erros'), 
                                                            type=QgsProcessing.TypeVectorPoint, 
                                                            createByDefault=True, 
                                                            supportsAppend=True, 
                                                            defaultValue='TEMPORARY_OUTPUT'))
        
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        drenagem = self.parameterAsVectorLayer(parameters,self.DRENAGEM,context)
        vias = self.parameterAsVectorLayer(parameters,self.VIAS,context)
        energia = self.parameterAsVectorLayer(parameters,self.ENERGIA,context)
        curvas = self.parameterAsVectorLayer(parameters,self.CURVAS,context)
        moldura = self.parameterAsVectorLayer(parameters,self.MOLDURA,context)
        distancia = self.parameterAsDouble(parameters,self.DISTANCIA,context)

        #Criação da camada de saída do tipo ponto com o tipo de erro
        fields = QgsFields()
        fields.append(QgsField("tipo_erro", QVariant.String))
        (output_sink, output_dest_id) = self.parameterAsSink(parameters,self.OUTPUT,context,
                                                             fields,1,drenagem.sourceCrs())

        #Criação de uma camada de linhas de interseção entre os produtos
        intersecoes = list()
        for molduras in moldura.getFeatures():
            geometryMoldura = molduras.geometry()
            idMoldura = molduras.id()
            
            for mold in moldura.getFeatures():
                geometryMold = mold.geometry()
                idMold = mold.id()

                if idMoldura != idMold:
                    if geometryMoldura.touches(geometryMold):
                        linha = geometryMoldura.intersection(geometryMold)
                        tipo = linha.type() #Está retornando 1 ou 0, sendo 1 para MultiLineString e 0 para Point

                        if tipo == 1:
                            intersecoes.append(linha)

        #Eliminação de linhas de contato duplicadas entre produtos
        unique_intersecoes = list()
        for i in intersecoes:
            is_duplicate = False
            for j in unique_intersecoes:
                if i.equals(j) or i.contains(j):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_intersecoes.append(i)

        #Criação das áreas de busca
        areas = list()
        for i in unique_intersecoes:
            area_busca = i.buffer(distancia, 8)
            areas.append(area_busca)

        for area in areas:
            #VERIFICAÇÃO DOS ERROS POR ATRIBUTO
            #Vericação de atributos sobre as linhas de drenagem
            bbox = area.boundingBox()
            for linhas in drenagem.getFeatures(bbox):
                geometryLinhas = linhas.geometry()
                nome = str(linhas.attributes()[2])
                if nome == 'NULL': continue

                for line in drenagem.getFeatures(bbox):
                    geometryLine = line.geometry()
                    name = str(line.attributes()[2])
                    if name == 'NULL': continue
                    
                    if nome != name and nome in name:
                        if geometryLinhas.touches(geometryLine):
                            p = geometryLinhas.intersection(geometryLine).asPoint()
                            p = QgsGeometry.fromPointXY(p)
                            if not geometryLinhas.contains(p):
                                feedback.pushInfo(f"O ponto {p} é o toque de {nome} com {name}.")
                                novo_feat = QgsFeature(fields)
                                novo_feat.setGeometry(p)
                                novo_feat.setAttribute(0, 'atributos distintos')
                                output_sink.addFeature(novo_feat)
        
            #VERIFICAÇÃO DAS GEOMETRIAS DESCONECTADAS
            #Verificação sobre as curvas de nível
            for linha in curvas.getFeatures(bbox):
                geometryLinhas = linha.geometry()
                for part in geometryLinhas.parts():
                    vertices = list(part)
                ponto_inicial = QgsGeometry.fromPointXY(QgsPointXY(vertices[0].x(), vertices[0].y()))
                ponto_final = QgsGeometry.fromPointXY(QgsPointXY(vertices[-1].x(), vertices[-1].y()))

                #Caso da curva de nível que intersepta a área de busca
                if geometryLinhas.within(area) or (geometryLinhas.intersects(area) and area.contains(ponto_inicial)) or (geometryLinhas.intersects(area) and area.contains(ponto_final)):
                    flag_i = True
                    flag_f = True
                    for line in curvas.getFeatures(bbox):
                        geometryLine = line.geometry()
                        if not (geometryLinhas.equals(geometryLine)):
                            if ponto_inicial.touches(geometryLine) or ponto_inicial.within(geometryLine): flag_i = False
                            if ponto_final.touches(geometryLine) or ponto_final.within(geometryLine): flag_f = False
                    if flag_i == True and area.contains(ponto_inicial):
                        novo_feat = QgsFeature(fields)
                        novo_feat.setGeometry(ponto_inicial)
                        novo_feat.setAttribute(0, 'geometria desconectada')
                        output_sink.addFeature(novo_feat)
                    if flag_f == True and area.contains(ponto_final):
                        novo_feat = QgsFeature(fields)
                        novo_feat.setGeometry(ponto_final)
                        novo_feat.setAttribute(0, 'geometria desconectada')
                        output_sink.addFeature(novo_feat)

            #Verificação sobre as linhas de energia
            for linhas in energia.getFeatures(bbox):
                geometryLinhas = linhas.geometry()
                for part in geometryLinhas.parts():
                    vertices = list(part)
                ponto_inicial = QgsGeometry.fromPointXY(QgsPointXY(vertices[0].x(), vertices[0].y()))
                ponto_final = QgsGeometry.fromPointXY(QgsPointXY(vertices[-1].x(), vertices[-1].y()))

                if (geometryLinhas.intersects(area) and area.contains(ponto_inicial)) or (geometryLinhas.intersects(area) and area.contains(ponto_final)):
                    flag_i = True
                    flag_f = True
                    for line in energia.getFeatures(bbox):
                        geometryLine = line.geometry()
                        if not (geometryLinhas.equals(geometryLine)):
                            if ponto_inicial.touches(geometryLine) or ponto_inicial.within(geometryLine): flag_i = False
                            if ponto_final.touches(geometryLine) or ponto_final.within(geometryLine): flag_f = False
                    if flag_i == True and area.contains(ponto_inicial):
                        novo_feat = QgsFeature(fields)
                        novo_feat.setGeometry(ponto_inicial)
                        novo_feat.setAttribute(0, 'geometria desconectada')
                        output_sink.addFeature(novo_feat)
                    if flag_f == True and area.contains(ponto_final):
                        novo_feat = QgsFeature(fields)
                        novo_feat.setGeometry(ponto_final)
                        novo_feat.setAttribute(0, 'geometria desconectada')
                        output_sink.addFeature(novo_feat)
                   
        return {self.OUTPUT: output_dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Aparar linhas'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return 'Aparar linhas'

    """def groupId(self):
        
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        
        return 'Projeto 5'"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto5Solucao()
