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
from itertools import chain
from PyQt5.QtCore import QCoreApplication

from DsgTools.core.GeometricTools.layerHandler import LayerHandler
from qgis.core import (
    QgsDataSourceUri,
    QgsFeature,
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingOutputVectorLayer,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterVectorLayer,
    QgsWkbTypes,
)

from .algRunner import AlgRunner
#from .validationAlgorithm import ValidationAlgorithm


class Projeto5Solucao(QgsProcessingAlgorithm):
    INPUT_LINES = "INPUT_LINES"
    SELECTED = "SELECTED"
    SEARCH_RADIUS = "SEARCH_RADIUS"
    GEOGRAPHIC_BOUNDARY = "GEOGRAPHIC_BOUNDARY"

    def initAlgorithm(self, config):
        """
        Parameter setting.
        """
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LINES,
                self.tr("Linestring Layer"),
                types=[QgsProcessing.TypeVectorLine],
                #optional=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SELECTED, self.tr("Process only selected features")
            )
        )

        param = QgsProcessingParameterDistance(
            self.SEARCH_RADIUS, self.tr("Search Radius"), defaultValue=1.0
        )
        param.setMetadata({"widget_wrapper": {"decimals": 8}})
        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.GEOGRAPHIC_BOUNDARY,
                self.tr("Geographic Boundary"),
                [QgsProcessing.TypeVectorPolygon],
                optional=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        algRunner = AlgRunner()
        inputLineLyrList = self.parameterAsLayerList(
            parameters, self.INPUT_LINES, context
        )
        searchRadius = self.parameterAsDouble(parameters, self.SEARCH_RADIUS, context)
        geographicBoundary = self.parameterAsVectorLayer(
            parameters, self.GEOGRAPHIC_BOUNDARY, context
        )
        if inputLineLyrList == []:
            raise QgsProcessingException(self.tr("Select at least one layer"))
        onlySelected = self.parameterAsBool(parameters, self.SELECTED, context)
        lyrList = list(chain(inputLineLyrList))
        nLyrs = len(lyrList)
        multiStepFeedback = QgsProcessingMultiStepFeedback(
            nLyrs + 4 + 2 * (geographicBoundary is not None), feedback
        )
        multiStepFeedback.setCurrentStep(0)
        flagsLyr = algRunner.runIdentifyUnsharedVertexOnIntersectionsAlgorithm(
            lineLayerList=inputLineLyrList,
            onlySelected=onlySelected,
            context=context,
            feedback=multiStepFeedback,
            is_child_algorithm=True,
        )
        if geographicBoundary is not None:
            multiStepFeedback.setCurrentStep(1)
            flagsLyr = algRunner.runExtractByLocation(
                flagsLyr,
                geographicBoundary,
                context=context,
                feedback=multiStepFeedback,
                is_child_algorithm=True,
            )
        for current, lyr in enumerate(lyrList):
            if feedback.isCanceled():
                break
            multiStepFeedback.setCurrentStep(
                current + 1 + (geographicBoundary is not None)
            )
            algRunner.runSnapLayerOnLayer(
                inputLayer=lyr,
                referenceLayer=flagsLyr,
                tol=searchRadius,
                context=context,
                onlySelected=onlySelected,
                feedback=multiStepFeedback,
                behavior=1,
                buildCache=False,
                is_child_algorithm=True,
            )
        currentStep = current + 1 + (geographicBoundary is not None)
        multiStepFeedback.setCurrentStep(currentStep)
        newFlagsLyr = algRunner.runIdentifyUnsharedVertexOnIntersectionsAlgorithm(
            lineLayerList=inputLineLyrList,
            onlySelected=onlySelected,
            context=context,
            feedback=multiStepFeedback,
        )
        currentStep += 1
        if geographicBoundary is not None:
            multiStepFeedback.setCurrentStep(currentStep)
            newFlagsLyr = algRunner.runExtractByLocation(
                newFlagsLyr, geographicBoundary, context, feedback=multiStepFeedback
            )
            currentStep += 1
        if newFlagsLyr.featureCount() == 0:
            return {}

        multiStepFeedback.setCurrentStep(currentStep)
        algRunner.runCreateSpatialIndex(newFlagsLyr, context, multiStepFeedback)
        currentStep += 1
        multiStepFeedback.setCurrentStep(currentStep)
        LayerHandler().addVertexesToLayers(
            vertexLyr=newFlagsLyr,
            layerList=list(chain(inputLineLyrList)),
            searchRadius=searchRadius,
            feedback=multiStepFeedback,
        )

        return {}

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
        
        return 'Projeto 6'"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto5Solucao()
