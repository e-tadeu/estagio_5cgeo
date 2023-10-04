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
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
    QgsWkbTypes,
)

from .algRunner import AlgRunner
#from .validationAlgorithm import ValidationAlgorithm


class Projeto5Solucao(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    SELECTED = "SELECTED"
    TOLERANCE = "TOLERANCE"
    MIN_LENGTH = "MIN_LENGTH"
    OUTPUT = "OUTPUT"
    FLAGS = "FLAGS"

    def initAlgorithm(self, config):
        """
        Parameter setting.
        """
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT, self.tr("Input layer"), [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SELECTED, self.tr("Process only selected features")
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.TOLERANCE,
                self.tr("Snap radius"),
                parentParameterName=self.INPUT,
                minValue=-1.0,
                defaultValue=1.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_LENGTH,
                self.tr("Minimum size"),
                minValue=0,
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.1,
            )
        )
        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.OUTPUT, self.tr("Original layer with overlayed lines")
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.FLAGS, self.tr("{0} Flags").format(self.displayName())
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        layerHandler = LayerHandler()
        algRunner = AlgRunner()
        inputLyr = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        onlySelected = self.parameterAsBool(parameters, self.SELECTED, context)
        minLength = self.parameterAsDouble(parameters, self.MIN_LENGTH, context)
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        self.prepareFlagSink(parameters, inputLyr, QgsWkbTypes.LineString, context)

        multiStepFeedback = QgsProcessingMultiStepFeedback(4, feedback)
        multiStepFeedback.setCurrentStep(0)

        if tol > 0:
            multiStepFeedback.pushInfo(
                self.tr("Identifying dangles on {layer}...").format(
                    layer=inputLyr.name()
                )
            )
            dangleLyr = AlgRunner().runIdentifyDangles(
                inputLayer=inputLyr,
                searchRadius=tol,
                context=context,
                onlySelected=onlySelected,
                ignoreDanglesOnUnsegmentedLines=True,
                inputIsBoundaryLayer=True,
                feedback=multiStepFeedback,
            )

            multiStepFeedback.setCurrentStep(1)
            layerHandler.filterDangles(dangleLyr, tol, feedback=multiStepFeedback)

            multiStepFeedback.setCurrentStep(2)
            multiStepFeedback.pushInfo(
                self.tr("Snapping layer {layer} to dangles...").format(
                    layer=inputLyr.name()
                )
            )
            algRunner.runSnapLayerOnLayer(
                inputLyr,
                dangleLyr,
                tol,
                context,
                feedback=multiStepFeedback,
                onlySelected=onlySelected,
            )

        multiStepFeedback.setCurrentStep(3)
        multiStepFeedback.pushInfo(
            self.tr("Cleanning layer {layer}...").format(layer=inputLyr.name())
        )
        algRunner.runDsgToolsClean(
            inputLyr,
            context,
            snap=tol,
            feedback=multiStepFeedback,
            onlySelected=onlySelected,
        )

        #return {self.OUTPUT: inputLyr}
    
        if inputLyr is None:
            return {self.FLAGS: self.flag_id}
        # Compute the number of steps to display within the progress bar and
        # get features from source
        #feedbackTotal = 2
        #multiStepFeedback = QgsProcessingMultiStepFeedback(feedbackTotal, feedback)
        #multiStepFeedback.setCurrentStep(0)
        #multiStepFeedback.setProgressText(self.tr("Getting Dangles..."))
        #multiStepFeedback.setCurrentStep(1)
        #multiStepFeedback.setProgressText(self.tr("Raising flags..."))
        nDangles = dangleLyr.featureCount()
        if nDangles == 0:
            return {self.FLAGS: self.flag_id}
        # currentValue = feedback.progress()
        currentTotal = 100 / nDangles
        for current, feat in enumerate(dangleLyr.getFeatures()):
            if multiStepFeedback.isCanceled():
                break
            dangleGeom = feat.geometry()
            dangleBB = dangleGeom.boundingBox()
            request = QgsFeatureRequest().setNoAttributes().setFilterRect(dangleBB)
            lineGeometry = [
                i.geometry()
                for i in inputLyr.getFeatures(request)
                if i.geometry().intersects(dangleGeom)
            ][0]
            if lineGeometry.length() > minLength:
                continue
            self.flagFeature(
                lineGeometry,
                self.tr(
                    f"First order dangle on {inputLyr.name()} smaller than {minLength}"
                ),
            )
            multiStepFeedback.setProgress(current * currentTotal)
        return {self.OUTPUT: inputLyr, self.FLAGS: self.flag_id}

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
