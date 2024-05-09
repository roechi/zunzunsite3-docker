import sys, os, time, multiprocessing, io, string, pickle
from bs4 import BeautifulSoup # don't need everything, it has several components

import settings
import django.http # to raise 404's
import django.utils.encoding
from django import db
from django.db import close_old_connections
from django.contrib.sessions.backends.db import SessionStore
from django.template.loader import render_to_string

import reportlab
import reportlab.platypus
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import reportlab.lib.pagesizes

from . import DataObject
from . import ClassForAttachingProperties
from . import ReportsAndGraphs

import zunzun.forms
from . import DefaultData

import pyeq3

from . import pid_trace


def ParallelWorker_CreateReportOutput(inReportObject):
    try:
        if inReportObject.dataObject.equation.GetDisplayName() == 'User Defined Function': # User Defined Function will not pickle, see http://support.picloud.com/entries/122330-an-error-i-don-t-understand
            inReportObject.dataObject.equation.userDefinedFunctionText = inReportObject.dataObject.userDefinedFunctionText
            inReportObject.dataObject.equation.ParseAndCompileUserFunctionString(inReportObject.dataObject.equation.userDefinedFunctionText)
            
        inReportObject.CreateReportOutput()

        return [inReportObject.name, inReportObject.stringList, ''] # name for lookup, stringList for data, empty string for no exception
    except:
        import logging
        
        s = '\n'
        for item in dir(inReportObject.dataObject):
            
            if -1 != str(item).find('__'): # internal python objects
                continue
            if -1 != str(eval('inReportObject.dataObject.' + str(item))).find('bound'): # internal python objects
                continue
                
            s += str(item) + ': ' + str(eval('inReportObject.dataObject.' + str(item))) + '\n\n'
            
        logging.basicConfig(filename = os.path.join(settings.TEMP_FILES_DIR,  str(os.getpid()) + '.log'),level=logging.DEBUG)
        logging.exception('Exception creating report, inReportObject.dataObject yields:\n\n' + s)
        return [inReportObject.name, 0, 'Exception creating report, see log file']


def ParallelWorker_CreateCharacterizerOutput(inReportObject):
    try:
        inReportObject.CreateCharacterizerOutput()

        return [inReportObject.name, inReportObject.stringList, ''] # name for lookup, stringList for data
    except:
        import logging
        logging.basicConfig(filename = os.path.join(settings.TEMP_FILES_DIR,  str(os.getpid()) + '.log'),level=logging.DEBUG)
        logging.exception('Exception characterizer output')

        s = '\n'
        for item in dir(inReportObject.dataObject):
            
            if -1 != str(item).find('__'): # internal python objects
                continue
            if -1 != str(eval('inReportObject.dataObject.' + str(item))).find('bound'): # internal python objects
                continue
                
            s += str(item) + ': ' + str(eval('inReportObject.dataObject.' + str(item))) + '\n\n'
            
        logging.basicConfig(filename = os.path.join(settings.TEMP_FILES_DIR,  str(os.getpid()) + '.log'),level=logging.DEBUG)
        logging.exception('Exception creating characterizer, inReportObject.dataObject yields:\n\n' + s)
        
        return [inReportObject.name, 0, 'Exception characterizer output, see log file']


# from http://code.activestate.com/recipes/576832-improved-reportlab-recipe-for-page-x-of-y/
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 7)
        self.drawRightString(200*mm, 20*mm, "Page %d of %d" % (self._pageNumber, page_count))
        self.drawCentredString(25*mm, 20*mm, 'https://bitbucket.org/zunzuncode/zunzunsite3')



class StatusMonitoredLongRunningProcessPage(object):

    def __init__(self):

        self.parallelChunkSize = 16
        self.oneSecondTimes = 0

        self.inEquationName = ''
        self.inEquationFamilyName = ''

        self.session_data = None
        self.session_status = None
        self.session_functionfinder = None

        self.statisticalDistribution = False
        self.userDefinedFunction = False
        self.spline = False

        self.userInterfaceRequired = True
        self.reniceLevel = 10
        self.ppCount = 0
        self.completedWorkItemsList = []
        self.boundForm = None
        self.evaluationForm = None

        self.pool = None

        self.characterizerOutputTrueOrReportOutputFalse = False
        self.evaluateAtAPointFormNeeded = True

        self.equationInstance = 0

        self.extraExampleDataTextForWeightedFitting = '''Weighted fitting requires an additional number to
be used as a weight when fitting. The site does
not calculate any weights, which are used as:
   error = weight * (predicted - actual)
You must provide any weights you wish to use.
'''

        self.defaultData1D = DefaultData.defaultData1D
        self.defaultData2D = DefaultData.defaultData2D
        self.defaultData3D = DefaultData.defaultData3D


    def PerformWorkInParallel(self):
        pass


    def SaveSpecificDataToSessionStore(self):
        pass


    def GenerateListOfWorkItems(self):
        pass


    def GetParallelProcessCount(self):
        pid_trace.pid_trace()

        # limit based on free memory
        f = os.popen('vmstat', 'r')
        f.readline()
        f.readline()
        line = f.readline()
        f.close()
        freeRAM = line.split()[3]
        cache = line.split()[5]
        ppCount = int((float(freeRAM) + float(cache)) / 80000.0)

        if ppCount > multiprocessing.cpu_count(): # *three* extra processes
            ppCount = multiprocessing.cpu_count()
        if ppCount < 1: # need at least one process
            ppCount = 1

        # now limit based on CPU load
        f = open('/proc/loadavg', 'r')
        line = f.readline()
        f.close()
        load = float(line.split()[0])
        if load > (float(multiprocessing.cpu_count()) + 0.5) and ppCount > 3:
            ppCount = 3
        if load > (float(multiprocessing.cpu_count()) + 1.0) and ppCount > 2:
            ppCount = 2
        if load > (float(multiprocessing.cpu_count()) + 1.5) and ppCount > 1:
            ppCount = 1

        pid_trace.pid_trace()
        return ppCount


    def CreateReportPDF(self):
        pid_trace.pid_trace()

        specialExceptionFileText = 'Entered CreateReportPDF'
        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Creating PDF Output File"})
        try:
            specialExceptionFileText = 'Top of function'

            scale = 72.0 / 300.0 # dpi conversion factor for PDF file images

            self.pdfFileName = self.dataObject.uniqueString + ".pdf"
            pageElements = []

            styles = reportlab.lib.styles.getSampleStyleSheet()

            styles.add(reportlab.lib.styles.ParagraphStyle(name='CenteredBodyText', parent=styles['BodyText'], alignment=reportlab.lib.enums.TA_CENTER))
            styles.add(reportlab.lib.styles.ParagraphStyle(name='SmallCode', parent=styles['Code'], fontSize=6, alignment=reportlab.lib.enums.TA_LEFT)) # 'Code' and wordwrap=CJK causes problems

            myTableStyle = [('ALIGN', (1,1), (-1,-1), 'CENTER'),
                            ('VALIGN', (1,1), (-1,-1), 'MIDDLE')]

            largeLogoImage = reportlab.platypus.Image(os.path.join(settings.TEMP_FILES_DIR, 'static_images/logo.png'), 25 * scale * 3, 25 * scale * 3)

            tableRow = [largeLogoImage,
                        'ZunZunSite3',
                        largeLogoImage]

            table = reportlab.platypus.Table([tableRow], style=myTableStyle)

            pageElements.append(table)

            pageElements.append(reportlab.platypus.XPreformatted('<br/><br/><br/><br/>', styles['CenteredBodyText']))

            if self.inEquationName:
                pageElements.append(reportlab.platypus.Paragraph(self.inEquationName, styles['CenteredBodyText']))
            pageElements.append(reportlab.platypus.XPreformatted('<br/><br/>', styles['CenteredBodyText']))

            titleXML = self.pdfTitleHTML.replace('sup>', 'super>').replace('SUP>', 'super>').replace('<br>', '<br/>').replace('<BR>', '<br/>')
            pageElements.append(reportlab.platypus.Paragraph(titleXML, styles['CenteredBodyText']))

            pageElements.append(reportlab.platypus.XPreformatted('<br/><br/>', styles['CenteredBodyText']))
            pageElements.append(reportlab.platypus.Paragraph(time.asctime(time.localtime()) + ' local server time', styles['CenteredBodyText']))

            pageElements.append(reportlab.platypus.PageBreak())

            verseInfo = self.GetVerseInfo()
            pageElements.append(reportlab.platypus.Paragraph(verseInfo[0], styles['CenteredBodyText']))
            pageElements.append(reportlab.platypus.XPreformatted('<br/><br/>', styles['CenteredBodyText']))
            pageElements.append(reportlab.platypus.Paragraph(verseInfo[1], styles['CenteredBodyText']))
            pageElements.append(reportlab.platypus.XPreformatted('<br/><br/>', styles['CenteredBodyText']))
            pageElements.append(reportlab.platypus.Paragraph('Read or search the King James Bible online at<br/>http://quod.lib.umich.edu/k/kjv/', styles['CenteredBodyText']))

            pageElements.append(reportlab.platypus.PageBreak())

            # make a page for each report output, with report name as page header
            # graphs may not exist if they raised an exception at creation time, trap and handle this condition
            for report in self.textReports:
                specialExceptionFileText = report.name
                pageElements.append(reportlab.platypus.Preformatted(report.name, styles['SmallCode']))
                pageElements.append(reportlab.platypus.XPreformatted('<br/><br/><br/>', styles['CenteredBodyText']))

                if report.stringList[0] == '</pre>': # corrects fit statistics not in PDF
                    report.stringList = report.stringList[1:]
                
                joinedString = str('\n').join(report.stringList)
                
                if -1 != report.name.find('Coefficients'):
                    joinedString = joinedString.replace('<sup>', '^')
                    joinedString = joinedString.replace('<SUP>', '^')

                soup = BeautifulSoup(joinedString, "lxml")

                notUnicodeList = []
                for i in soup.findAll(text=True):
                    notUnicodeList.append(str(i))
                replacedText = str('').join(notUnicodeList)

                replacedText = replacedText.replace('\t', '    ') # convert tabs to four spaces
                replacedText = replacedText.replace('\r\n', '\n')

                rebuiltText = ''
                for line in replacedText.split('\n'):
                    if line == '':
                        rebuiltText += '\n'
                    else:
                        if line[0] == '<':
                            splitLine = line.split('>')
                            if len(splitLine) > 1:
                                newLine = splitLine[len(splitLine)-1]
                            else:
                                newLine = ''
                        else:
                            newLine = line

                        # crude line wrapping
                        if len(newLine) > 500:
                            rebuiltText += newLine[:100] + '\n'
                            rebuiltText += newLine[100:200] + '\n'
                            rebuiltText += newLine[200:300] + '\n'
                            rebuiltText += newLine[300:400] + '\n'
                            rebuiltText += newLine[400:500] + '\n'
                            rebuiltText += newLine[500:] + '\n'
                        elif len(newLine) > 400:
                            rebuiltText += newLine[:100] + '\n'
                            rebuiltText += newLine[100:200] + '\n'
                            rebuiltText += newLine[200:300] + '\n'
                            rebuiltText += newLine[300:400] + '\n'
                            rebuiltText += newLine[400:] + '\n'
                        elif len(newLine) > 300:
                            rebuiltText += newLine[:100] + '\n'
                            rebuiltText += newLine[100:200] + '\n'
                            rebuiltText += newLine[200:300] + '\n'
                            rebuiltText += newLine[300:] + '\n'
                        elif len(newLine) > 200:
                            rebuiltText += newLine[:100] + '\n'
                            rebuiltText += newLine[100:200] + '\n'
                            rebuiltText += newLine[200:] + '\n'
                        elif len(newLine) > 100:
                            rebuiltText += newLine[:100] + '\n'
                            rebuiltText += newLine[100:] + '\n'
                        else:
                            rebuiltText += newLine + '\n'
                            
                pageElements.append(reportlab.platypus.Preformatted(rebuiltText, styles['SmallCode']))

                pageElements.append(reportlab.platypus.PageBreak())

            for report in self.graphReports:
                if report.animationFlag: # pdf files cannot contain GIF animations
                    continue
                if os.path.isfile(report.physicalFileLocation):
                    specialExceptionFileText = report.name
                    pageElements.append(reportlab.platypus.Paragraph(report.name, styles['CenteredBodyText']))
                    pageElements.append(reportlab.platypus.XPreformatted('<br/><br/>', styles['CenteredBodyText']))
                    try:
                        im = reportlab.platypus.Image(report.physicalFileLocation, self.dataObject.graphWidth * scale, self.dataObject.graphHeight * scale)
                    except:
                        time.sleep(1.0)
                        im = reportlab.platypus.Image(report.physicalFileLocation, self.dataObject.graphWidth * scale, self.dataObject.graphHeight * scale)
                    im.hAlign = 'CENTER'
                    pageElements.append(im)
                    if report.stringList != []:
                        pageElements.append(reportlab.platypus.Preformatted(report.name, styles['SmallCode']))
                        pageElements.append(reportlab.platypus.XPreformatted('<br/><br/><br/>', styles['CenteredBodyText']))
                        for line in report.stringList:
                            replacedLine = line.replace('<br>', '<br/>').replace('<BR>', '<br/>').replace('<pre>', '').replace('</pre>', '').replace('<tr>', '').replace('</tr>', '').replace('<td>', '').replace('</td>', '').replace('sup>', 'super>').replace('SUP>', 'super>').replace('\r\n', '\n').replace('\n', '<br/>').replace('&nbsp;', ' ')
                            pageElements.append(reportlab.platypus.XPreformatted(replacedLine, styles['SmallCode']))

                pageElements.append(reportlab.platypus.PageBreak())

            specialExceptionFileText = 'calling doc.build(pageElements) 0'
            try:
                doc = reportlab.platypus.SimpleDocTemplate(os.path.join(settings.TEMP_FILES_DIR, self.pdfFileName), pagesize=reportlab.lib.pagesizes.letter)
                specialExceptionFileText = 'calling doc.build(pageElements) 1'
                doc.build(pageElements, canvasmaker=NumberedCanvas)
            except:
                time.sleep(1.0)
                doc = reportlab.platypus.SimpleDocTemplate(os.path.join(settings.TEMP_FILES_DIR, self.pdfFileName), pagesize=reportlab.lib.pagesizes.letter)
                specialExceptionFileText = 'calling doc.build(pageElements) 2'
                doc.build(pageElements, canvasmaker=NumberedCanvas)
        except:
            import logging
            logging.basicConfig(filename = os.path.join(settings.TEMP_FILES_DIR,  str(os.getpid()) + '.log'),level=logging.DEBUG)
            logging.exception('Exception creating PDF file')
            
            self.pdfFileName = '' # empty string used as a flag
        pid_trace.delete_pid_trace_file()


    def BaseCreateAndInitializeDataObject(self, xName, yName, zName):
        dataObject = DataObject.DataObject()

        dataObject.ErrorString = ''
        dataObject.logLinX = 'LIN'
        dataObject.logLinY = 'LIN'
        dataObject.logLinZ = 'LIN'

        settings.TEMP_FILES_DIR = settings.TEMP_FILES_DIR
        dataObject.WebsiteHTMLLocation = settings.STATIC_URL
        dataObject.WebsiteImageLocation = settings.STATIC_URL

        dataObject.dimensionality = self.dimensionality

        dataObject.IndependentDataName1 = xName
        if dataObject.dimensionality > 1:
            dataObject.IndependentDataName2 = ''
            dataObject.DependentDataName = yName
        if dataObject.dimensionality > 2:
            dataObject.IndependentDataName2 = yName
            dataObject.DependentDataName = zName

        dataObject.uniqueString = 'LRP_' + str(os.getpid()) + '_' + str(time.time()).replace('.', '_')
        dataObject.physicalStatusFileName = os.path.join(settings.TEMP_FILES_DIR, dataObject.uniqueString + '.html')
        dataObject.websiteStatusFileName = dataObject.WebsiteHTMLLocation + dataObject.uniqueString + '.html'

        return dataObject


    def CommonCreateAndInitializeDataObject(self, FF = False):
        pid_trace.pid_trace()

        self.dataObject = self.BaseCreateAndInitializeDataObject('', '', '')
        self.dataObject.equation = 0
        self.dataObject.fittedStatisticalDistributionsList = []
        self.dataObject.IndependentDataArray = self.boundForm.cleaned_data['IndependentData']
        if self.dataObject.dimensionality > 1:
            self.dataObject.DependentDataArray = self.boundForm.cleaned_data['DependentData']

        self.dataObject.IndependentDataName1 = self.boundForm.cleaned_data['dataNameX']
        if self.dataObject.dimensionality > 1:
            self.dataObject.IndependentDataName2 = ''
            self.dataObject.DependentDataName = self.boundForm.cleaned_data['dataNameY']
        if self.dataObject.dimensionality > 2:
            self.dataObject.IndependentDataName2 = self.boundForm.cleaned_data['dataNameY']
            self.dataObject.DependentDataName = self.boundForm.cleaned_data['dataNameZ']
            try:
                self.dataObject.dataPointSize3D = self.boundForm.cleaned_data['dataPointSize3D']
            except:
                pass

        pid_trace.pid_trace()

        if self.dataObject.dimensionality == 2:
            self.dataObject.logLinX = self.boundForm.cleaned_data['logLinX']
            self.dataObject.logLinY = self.boundForm.cleaned_data['logLinY']

        if True == FF: # function finder, return here
            return self.dataObject

        self.dataObject.graphWidth = int(self.boundForm.cleaned_data['graphSize'].split('x')[0])
        self.dataObject.graphHeight = int(self.boundForm.cleaned_data['graphSize'].split('x')[1])

        if self.dataObject.dimensionality > 1:
            pid_trace.pid_trace()
            self.dataObject.Extrapolation_x = self.boundForm.cleaned_data['graphScaleX']
            self.dataObject.Extrapolation_x_min = self.boundForm.cleaned_data['minManualScaleX']
            self.dataObject.Extrapolation_x_max = self.boundForm.cleaned_data['maxManualScaleX']

            pid_trace.pid_trace()
            self.dataObject.ScientificNotationX = self.boundForm.cleaned_data['scientificNotationX']
            self.dataObject.ScientificNotationY = self.boundForm.cleaned_data['scientificNotationY']
            self.dataObject.Extrapolation_y = self.boundForm.cleaned_data['graphScaleY']
            self.dataObject.Extrapolation_y_min = self.boundForm.cleaned_data['minManualScaleY']
            self.dataObject.Extrapolation_y_max = self.boundForm.cleaned_data['maxManualScaleY']
            
        if self.dataObject.dimensionality > 2:
            pid_trace.pid_trace()
            self.dataObject.animationWidth = int(self.boundForm.cleaned_data['animationSize'].split('x')[0])
            self.dataObject.animationHeight = int(self.boundForm.cleaned_data['animationSize'].split('x')[1])
            self.dataObject.ScientificNotationZ = self.boundForm.cleaned_data['scientificNotationZ']
            self.dataObject.Extrapolation_z = self.boundForm.cleaned_data['graphScaleZ']
            self.dataObject.Extrapolation_z_min = self.boundForm.cleaned_data['minManualScaleZ']
            self.dataObject.Extrapolation_z_max = self.boundForm.cleaned_data['maxManualScaleZ']
            self.dataObject.logLinZ = self.boundForm.cleaned_data['logLinZ']

        pid_trace.pid_trace()

        # can only take log of positive data
        if self.dataObject.logLinX == 'LOG' and min(self.dataObject.IndependentDataArray[0]) <= 0.0:
            self.dataObject.ErrorString = 'Your X data (' + self.dataObject.IndependentDataName1 + ') contains a non-positive value and you have selected logarithmic X scaling. I cannot take the log of a non-positive number.'
        if self.dataObject.dimensionality == 2:
            if self.dataObject.logLinY == 'LOG' and min(self.dataObject.DependentDataArray) <= 0.0:
                self.dataObject.ErrorString = 'Your Y data (' + self.dataObject.DependentDataName + ') contains a non-positive value and you have selected logarithmic Y scaling. I cannot take the log of a non-positive number.'
        if self.dataObject.dimensionality == 3:
            if self.dataObject.logLinY == 'LOG' and min(self.dataObject.IndependentDataArray[1]) <= 0.0:
                self.dataObject.ErrorString = 'Your Y data (' + self.dataObject.IndependentDataName1 + ') contains a non-positive value and you have selected logarithmic Y scaling. I cannot take the log of a non-positive number.'
            if self.dataObject.logLinZ == 'LOG' and min(self.dataObject.DependentDataArray) <= 0.0:
                self.dataObject.ErrorString = 'Your Z data (' + self.dataObject.DependentDataName + ') contains a non-positive value and you have selected logarithmic Z scaling. I cannot take the log of a non-positive number.'

        pid_trace.pid_trace()

        if self.dataObject.dimensionality == 3:            
            self.dataObject.animationWidth = int(self.boundForm.cleaned_data['animationSize'].split('x')[0])
            self.dataObject.animationHeight = int(self.boundForm.cleaned_data['animationSize'].split('x')[1])
            self.dataObject.azimuth3D = float(self.boundForm.cleaned_data['rotationAnglesAzimuth'])
            self.dataObject.altimuth3D = float(self.boundForm.cleaned_data['rotationAnglesAltimuth'])
            
        pid_trace.delete_pid_trace_file()


    def SaveDictionaryOfItemsToSessionStore(self, inSessionStoreName, inDictionary):
        pid_trace.pid_trace(inSessionStoreName)
        
        session = eval('self.session_' + inSessionStoreName)
        if session is None:
            pid_trace.pid_trace('No session in sessionstore, creating new session')
            session = eval('SessionStore(self.session_key_' + inSessionStoreName + ')')
            
        pid_trace.pid_trace()
        
        for i in list(inDictionary.keys()):
            item = inDictionary[i]
            pid_trace.pid_trace(str(i) + ' type: ' + str(type(item)))
            pickled = pickle.dumps(item, pickle.HIGHEST_PROTOCOL).hex()
            pid_trace.pid_trace(str(i) + ' saving to session')
            if str(i) == 'processID':
                pid_trace.pid_trace(str(item) + ' pickled = ' + pickled)
            session[i] = pickled
            pid_trace.pid_trace(str(i) + ' saved to session')

        pid_trace.pid_trace()

        if inSessionStoreName == 'status':
            session["timestamp"] = pickle.dumps(time.time(), pickle.HIGHEST_PROTOCOL).hex()

        # sometimes database is momentarily locked, so retry on exception to mitigate
        s = session
        save_complete = False
        saveRetries = 0
        while not save_complete:
            try:
                s.save()
                save_complete = True
            except Exception as e:
                time.sleep(0.1) # wait 1/10 second before retry
                saveRetries += 1 # increment retry count
                if saveRetries > 100: # 10 per second * 10 seconds
                    raise e # re-raise exception from save operation
            
        pid_trace.pid_trace()

        db.connections.close_all()
        close_old_connections()
        session = None

        pid_trace.delete_pid_trace_file()


    def LoadItemFromSessionStore(self, inSessionStoreName, inItemName):
        pid_trace.pid_trace()
        
        session = eval('self.session_' + inSessionStoreName)
        if session is None:
            session = eval('SessionStore(self.session_key_' + inSessionStoreName + ')')
        try:
            returnItem = session[inItemName]
        except:
            returnItem = pickle.dumps(None, pickle.HIGHEST_PROTOCOL).hex()
        db.connections.close_all()
        close_old_connections()
        session = None
                
        returnItem = pickle.loads(bytes.fromhex(returnItem))
        
        pid_trace.delete_pid_trace_file()
        
        return returnItem


    def PerformAllWork(self):
        pid_trace.pid_trace()

        self.SaveDictionaryOfItemsToSessionStore('status', {'processID':os.getpid()})

        pid_trace.pid_trace()

        self.GenerateListOfWorkItems()

        pid_trace.pid_trace()

        self.PerformWorkInParallel()

        pid_trace.pid_trace()

        self.GenerateListOfOutputReports()

        pid_trace.pid_trace()

        self.CreateOutputReportsInParallelUsingProcessPool()

        self.CreateReportPDF()

        pid_trace.pid_trace()

        self.RenderOutputHTMLToAFileAndSetStatusRedirect()

        pid_trace.delete_pid_trace_file()


    def CreateOutputReportsInParallelUsingProcessPool(self):
        pid_trace.pid_trace()

        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Running All Reports"})

        countOfReportsRun = 0
        reportsToBeRunInParallel = self.graphReports + self.textReports
        totalNumberOfReportsToBeRun = len(reportsToBeRunInParallel)

        begin = -self.parallelChunkSize
        end = 0
        indices = []

        chunks = totalNumberOfReportsToBeRun // self.parallelChunkSize
        modulus = totalNumberOfReportsToBeRun % self.parallelChunkSize

        pid_trace.pid_trace()
        
        for i in range(chunks):
            begin += self.parallelChunkSize
            end += self.parallelChunkSize
            indices.append([begin, end])

        if modulus:
            indices.append([end, end + 1 + modulus])

        pid_trace.pid_trace()

        for i in indices:
            parallelChunkResultsList = []

            self.pool = multiprocessing.Pool(self.GetParallelProcessCount())
            for item in reportsToBeRunInParallel[i[0]:i[1]]:
                try:
                    item.dataObject.equation.modelRelativeError
                except:
                    item.dataObject.equation.modelRelativeError = None
                if self.characterizerOutputTrueOrReportOutputFalse:
                    parallelChunkResultsList.append(self.pool.apply_async(ParallelWorker_CreateCharacterizerOutput, (item,)))
                else:
                    if item.dataObject.equation.GetDisplayName() == 'User Defined Function': # User Defined Function will not pickle, see http://support.picloud.com/entries/122330-an-error-i-don-t-understand, regenerate in the parallel pool
                        item.dataObject.userDefinedFunctionText = item.dataObject.equation.userDefinedFunctionText
                        item.dataObject.equation.userFunctionCodeObject = None
                        item.dataObject.equation.safe_dict = None
                    parallelChunkResultsList.append(self.pool.apply_async(ParallelWorker_CreateReportOutput, (item,)))

            for r in parallelChunkResultsList:
                returnedValue = r.get()
                for report in reportsToBeRunInParallel[i[0]:i[1]]:
                    if report.name == returnedValue[0]:
                        if returnedValue[2]: # exception during parallel processing
                            report.exception = True
                        report.stringList = returnedValue[1]
                countOfReportsRun += 1
                self.Reports_CheckOneSecondSessionUpdates(countOfReportsRun, totalNumberOfReportsToBeRun)

            self.pool.close()
            self.pool.join()
            self.pool = None
            
        pid_trace.delete_pid_trace_file()


    def Reports_CheckOneSecondSessionUpdates(self, countOfReportsRun, totalNumberOfReportsToBeRun):
        if self.oneSecondTimes != int(time.time()):
            self.CheckIfStillUsed()
            processcountString = '<br><br>Currently using 1 process (the server is busy)'
            if len(multiprocessing.active_children()) > 1:
                processcountString = '<br><br>Currently using ' + str(len(multiprocessing.active_children())) + ' parallel processes'
            self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Created %s of %s Reports and Graphs %s" % (countOfReportsRun, totalNumberOfReportsToBeRun, processcountString)})
            self.oneSecondTimes = int(time.time())


    def CheckIfStillUsed(self):
        import time
        if self.LoadItemFromSessionStore('status', 'processID') == None:
            return

        # if a new process ID is in the session data, another process was started and this process was abandoned
        if self.LoadItemFromSessionStore('status', 'processID') != os.getpid() and self.LoadItemFromSessionStore('status', 'processID') != 0:
            
            time.sleep(1.0)

            pid_trace.pid_trace()

            if self.pool:
                self.pool.close()
                self.pool.join()
                self.pool = None
            for p in multiprocessing.active_children():
                p.terminate()
                
            pid_trace.delete_pid_trace_file()

            os._exit(0) # kills pool processes

        # if the status has not been checked in the past 30 seconds, this process was abandoned
        if (time.time() - self.LoadItemFromSessionStore('status', 'time_of_last_status_check')) > 300:

            pid_trace.pid_trace()

            time.sleep(1.0)
            if self.pool:
                self.pool.close()
                self.pool.join()
                self.pool = None
            for p in multiprocessing.active_children():
                p.terminate()
                
            pid_trace.delete_pid_trace_file()
                
            os._exit(0) # kills pool processes


    def SetInitialStatusDataIntoSessionVariables(self, request):
        pid_trace.pid_trace()
        self.SaveDictionaryOfItemsToSessionStore('status',
                                                 {'currentStatus':'Initializing',
                                                  'start_time':time.time(),
                                                  'time_of_last_status_check':time.time(),
                                                  'redirectToResultsFileOrURL':''})

        self.SaveDictionaryOfItemsToSessionStore('data',
                                                 {'textDataEditor_' + str(self.dimensionality) + 'D':request.POST['textDataEditor'],
                                                  'commaConversion':request.POST['commaConversion'],
                                                  'IndependentDataName1':self.dataObject.IndependentDataName1,
                                                  'IndependentDataName2':self.dataObject.IndependentDataName2,
                                                  'DependentDataName':self.dataObject.DependentDataName})
        pid_trace.delete_pid_trace_file()


    def GetVerseInfo(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(dir_path, 'Verses.txt'), 'r')
        verses = f.readlines()
        f.close()
        index = ((int(time.time()) % len(verses)) // 2) * 2
        reference = verses[index]
        verse = verses[index + 1]
        return [reference, verse]


    def SpecificCodeForGeneratingListOfOutputReports(self):
        pid_trace.pid_trace()

        self.functionString = 'PrepareForReportOutput'
        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Calculating Error Statistics"})
        self.dataObject.CalculateErrorStatistics()

        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Calculating Parameter Statistics"})
        self.dataObject.equation.CalculateCoefficientAndFitStatistics()

        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Generating Report Objects"})
        self.ReportsAndGraphsCategoryDict = ReportsAndGraphs.FittingReportsDict(self.dataObject)

        pid_trace.delete_pid_trace_file()


    def GenerateListOfOutputReports(self):
        pid_trace.pid_trace()
        
        self.textReports = []
        self.graphReports = []

        # calculate data statistics and graph boundaries
        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Calculating Data Statistics"})
        self.dataObject.CalculateDataStatistics()

        if self.dataObject.dimensionality > 1:
            self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Calculating Graph Boundaries"})
            self.dataObject.CalculateGraphBoundaries()

        pid_trace.pid_trace()

        self.SpecificCodeForGeneratingListOfOutputReports()

        # generate required text reports
        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Generating List Of Text Reports"})
        for i in self.ReportsAndGraphsCategoryDict["Text Reports"]:
            exec('i.' + self.functionString + '()')
            if i.name != '':
                self.textReports.append(i)

        pid_trace.pid_trace()

        # select required graph reports
        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Generating List Of Graphical Reports"})
        for i in self.ReportsAndGraphsCategoryDict["Graph Reports"]:
            exec('i.' + self.functionString + '()')
            if i.name != '':
                self.graphReports.append(i)

        pid_trace.delete_pid_trace_file()


    def RenderOutputHTMLToAFileAndSetStatusRedirect(self):
        pid_trace.pid_trace()

        self.SaveSpecificDataToSessionStore()

        self.SaveDictionaryOfItemsToSessionStore('status', {'currentStatus':"Generating Output HTML"})

        itemsToRender = {}

        import time
        itemsToRender['scripture'] = self.GetVerseInfo()

        itemsToRender['dimensionality'] = str(self.dimensionality)

        itemsToRender['header_text'] = 'ZunZunSite3<br>' + self.webFormName
        itemsToRender['title_string'] = 'ZunZunSite3 ' + self.webFormName.replace('<br>', ' ')

        itemsToRender['textReports'] = self.textReports

        # get animation file sizes
        for i in self.graphReports:
            if i.animationFlag:
                try:
                    fileBytes = os.path.getsize(i.physicalFileLocation)
                except:
                    fileBytes = 0
                    
                # from https://stackoverflow.com/questions/14996453/python-libraries-to-calculate-human-readable-filesize-from-bytes
                suffixes = ['Bytes', 'KBytes', 'MBytes', 'GBytes', 'TBytes', 'PBytes']
                idx = 0
                while fileBytes >= 1024 and idx < len(suffixes)-1:
                    fileBytes /= 1024.
                    idx += 1
                f = ('%.2f' % fileBytes).rstrip('0').rstrip('.')
                i.fileSize = '%s %s' % (f, suffixes[idx])
                
        itemsToRender['graphReports'] = self.graphReports

        itemsToRender['pdfFileName'] = self.pdfFileName

        itemsToRender['statisticalDistributions'] = self.statisticalDistribution

        itemsToRender['feedbackForm'] = zunzun.forms.FeedbackForm()

        itemsToRender['equationInstance'] = self.equationInstance
        if self.evaluateAtAPointFormNeeded:
            itemsToRender['EvaluateAtAPointForm'] = eval('zunzun.forms.EvaluateAtAPointForm_' + str(self.dimensionality) + 'D()')
            itemsToRender['IndependentDataName1'] = self.dataObject.IndependentDataName1
            itemsToRender['IndependentDataName2'] = self.dataObject.IndependentDataName2
        itemsToRender['loadavg'] = os.getloadavg()
        
        pid_trace.pid_trace()
        
        try:
            f = open(os.path.join(settings.TEMP_FILES_DIR, self.dataObject.uniqueString + ".html"), "w")
            f.write(render_to_string('zunzun/equation_fit_or_characterizer_results.html', itemsToRender))
            f.flush()
            f.close()
        except:
            import logging
            logging.basicConfig(filename = os.path.join(settings.TEMP_FILES_DIR,  str(os.getpid()) + '.log'),level=logging.DEBUG)
            logging.exception('Exception rendering HTML to a file')
            
        self.SaveDictionaryOfItemsToSessionStore('status', {'redirectToResultsFileOrURL':os.path.join(settings.TEMP_FILES_DIR, self.dataObject.uniqueString + ".html")})
        
        pid_trace.delete_pid_trace_file()


    def CreateUnboundInterfaceForm(self, request): # OVERRIDDEN in fittingBaseClass
        pid_trace.pid_trace()
        dictionaryToReturn = {}
        dictionaryToReturn['dimensionality'] = str(self.dimensionality)

        dictionaryToReturn['header_text'] = 'ZunZunSite3 ' + str(self.dimensionality) + 'D Interface<br>' + self.webFormName
        dictionaryToReturn['title_string'] = 'ZunZunSite3 ' + str(self.dimensionality) + 'D Interface ' + self.webFormName

        # make a dimensionality-based unbound Django form
        self.unboundForm = eval('zunzun.forms.CharacterizeDataForm_' + str(self.dimensionality) + 'D()')

        # set the form to have either default or session text data
        temp = self.LoadItemFromSessionStore('data', 'textDataEditor_' + str(self.dimensionality) + 'D')
        if temp:
            self.unboundForm.fields['textDataEditor'].initial = temp
        else:
            self.unboundForm.fields['textDataEditor'].initial = zunzun.forms.formConstants.initialDataEntryText + eval('self.defaultData' + str(self.dimensionality) + 'D')
        temp = self.LoadItemFromSessionStore('data', 'commaConversion')
        if temp:
            self.unboundForm.fields['commaConversion'].initial = temp
        self.unboundForm.weightedFittingPossibleFlag = 0 # weightedFittingChoice not used in characterizers
        dictionaryToReturn['mainForm'] = self.unboundForm

        dictionaryToReturn['statisticalDistributions'] = self.statisticalDistribution

        pid_trace.delete_pid_trace_file()
        return dictionaryToReturn


    def CreateBoundInterfaceForm(self, request): # OVERRIDDEN in fittingBaseClass
        pid_trace.pid_trace()
        self.boundForm = eval('zunzun.forms.CharacterizeDataForm_' + str(self.dimensionality) + 'D(request.POST)')
        self.boundForm.dimensionality = str(self.dimensionality)
        self.boundForm['statisticalDistributionsSortBy'].required = self.statisticalDistribution
        pid_trace.delete_pid_trace_file()

