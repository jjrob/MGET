# ClimateIndices.py - Defines functions for accessing NOAA climate indices.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import copy
import decimal
import datetime
import os
import re

from ...Datasets import QueryableAttribute, Database, Table
from ...Datasets.ArcGIS import ArcGISWorkspace, ArcGISTable
from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Logging import Logger, ProgressReporter


class PSLClimateIndices(object):
    __doc__ = DynamicDocString()

    # Methods for parsing a single climate index time series.

    @classmethod
    def _StringToList(cls, s, dataSource, setNoDataValuesToNone=None):

        # Split the input string into lines.

        lines = s.splitlines()
        numLines = len(lines)

        # Parse the first and last year.

        if numLines <= 0:
            Logger.RaiseException(ValueError(_('The %(source)s is too short. It ended before the first and last year could be parsed.') % {'source': dataSource}))

        line = lines[0].strip()
        if not re.match('\\d\\d\\d\\d\\s+\\d\\d\\d\\d', line):
            Logger.RaiseException(ValueError(_('Error on line 1 of the %(source)s: the line does not contain exactly two years.') % {'source': dataSource}))
            
        values = line.split()
        firstYear = int(values[0])
        lastYear = int(values[1])

        if firstYear > lastYear:
            Logger.RaiseException(ValueError(_('Error on line 1 of the %(source)s: the first year is greater than the last year.') % {'source': dataSource}))

        # Parse the "no data" value.

        noDataValueIndex = 1 + (lastYear - firstYear + 1)
        if numLines < noDataValueIndex + 1:
            Logger.RaiseException(ValueError(_('The %(source)s is too short. Given that the first year is %(first)i and the last year is %(last)i, the data is expected to be at least %(expected)i lines long, but it is only %(actual)i lines long.') % {'source': dataSource, 'first': firstYear, 'last': lastYear, 'expected': noDataValueIndex + 1, 'actual': numLines}))

        line = lines[noDataValueIndex].strip()
        if not re.match('[-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?', line):
            Logger.RaiseException(ValueError(_('Error on line %(line) of the %(source)s: the line does not contain exactly one floating point value. (This line is expected to contain is the "no data" value.)') % {'source': dataSource, 'line': noDataValueIndex + 1}))

        noDataValue = float(line)

        # Parse the index values into a table (a list of lists) where each row
        # represents the value of an index at a given year and month. The
        # first column is year, second is month (an integer ranging from 1 to
        # 12), and third is the index value.

        table = []

        for i in range(1, lastYear - firstYear + 2):
            line = lines[i].strip()
            if not re.match('\\d\\d\\d\\d(\\s+[-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?){12}', line):
                Logger.RaiseException(ValueError(_('Error on line %(line)i of the %(source)s: the line does not contain exactly one year followed by twelve floating point values. (This line is expected to contain the climate index data for the year %(year)i.)') % {'source': dataSource, 'line': i + 1, 'year': firstYear + 1 - 1}))

            values = line.split()
            year = int(values[0])
            if year != firstYear + i - 1:
                Logger.RaiseException(ValueError(_('Error on line %(line) of the %(source)s: the first value was expected to be the year %(expected)i, but it is %(actual)i.') % {'source': dataSource, 'line': i + 1, 'expected': firstYear + i - 1, 'actual': year}))
            
            for month in range(1, 13):
                value = float(values[month])
                if value == noDataValue and setNoDataValuesToNone:
                    table.append([datetime.datetime(year, month, 1), None])
                else:
                    table.append([datetime.datetime(year, month, 1), value])

        # Parse the comment that appears after the "no data" value (if any).

        if numLines <= noDataValueIndex + 1:
            comment = ''
        else:
            comment = '\n'.join(lines[noDataValueIndex + 1:]).strip()
            Logger.Info(_('The %(source)s contained the comment:\n"%(comment)s"') % {'source': dataSource, 'comment': comment})

        # Return successfully.

        if setNoDataValuesToNone:
            return table, None, comment
        else:
            return table, noDataValue, comment

    @classmethod
    def StringToList(cls, s, setNoDataValuesToNone=True):
        cls.__doc__.Obj.ValidateMethodInvocation()
        Logger.Debug(_('Parsing climate index data.'))
        return cls._StringToList(s, _('climate index data'), setNoDataValuesToNone)

    @classmethod
    def StringToTable(cls, s, database, table, field, dateDataType='datetime', intDataType='int32', floatDataType='float64', useNullForNoData=True, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        table, noDataValues, comments = cls._StringsToTable([s], [_('climate index data')], database, table, [field], dateDataType, intDataType, floatDataType, useNullForNoData, overwriteExisting)
        return table, noDataValues[0], comments[0]

    @classmethod
    def StringToArcGISTable(cls, s, table, field, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        noDataValues, comments = cls._StringsToArcGISTable([s], [_('climate index data')], table, [field], overwriteExisting)
        return noDataValues[0], comments[0]

    @classmethod
    def _GetStringFromFile(cls, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            Logger.LogExceptionAsError(_('Failed to read climate index time series data from file "%(path)s".') % {'path' : path})
            raise

    @classmethod
    def FileToList(cls, path, setNoDataValuesToNone=True):
        cls.__doc__.Obj.ValidateMethodInvocation()
        s = cls._GetStringFromFile(path)
        return cls._StringToList(s, _('climate index time series file "%(path)s"') % {'path' : path}, setNoDataValuesToNone)

    @classmethod
    def FileToTable(cls, path, database, table, field, dateDataType='datetime', intDataType='int32', floatDataType='float64', useNullForNoData=True, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        s = cls._GetStringFromFile(path)
        table, noDataValues, comments = cls._StringsToTable([s], [_('climate index time series file "%(path)s"') % {'path' : path}], database, table, [field], dateDataType, intDataType, floatDataType, useNullForNoData, overwriteExisting)
        return table, noDataValues[0], comments[0]

    @classmethod
    def FileToArcGISTable(cls, path, table, field, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        s = cls._GetStringFromFile(path)
        noDataValues, comments = cls._StringsToArcGISTable([s], [_('climate index time series file "%(path)s"') % {'path' : path}], table, [field], overwriteExisting)
        return noDataValues[0], comments[0]

    @classmethod
    def _GetStringFromUrl(cls, url):
        import requests

        try:
            response = requests.get(url, timeout=15)
        except:
            Logger.LogExceptionAsError('Failed to open climate index time series at URL %(url)s. The following error may provide more information' % {'url': url})
            raise

        return response.text

    @classmethod
    def UrlToList(cls, url, setNoDataValuesToNone=True):
        cls.__doc__.Obj.ValidateMethodInvocation()
        s = cls._GetStringFromUrl(url)
        return cls._StringToList(s, _('climate index time series at URL "%(url)s"') % {'url' : url}, setNoDataValuesToNone)

    @classmethod
    def UrlToTable(cls, url, database, table, field, dateDataType='datetime', intDataType='int32', floatDataType='float64', useNullForNoData=True, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        s = cls._GetStringFromUrl(url)
        table, noDataValues, comments = cls._StringsToTable([s], [_('climate index time series at URL "%(url)s"') % {'url' : url}], database, table, [field], dateDataType, intDataType, floatDataType, useNullForNoData, overwriteExisting)
        return table, noDataValues[0], comments[0]

    @classmethod
    def UrlToArcGISTable(cls, url, table, field, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        s = cls._GetStringFromUrl(url)
        noDataValues, comments = cls._StringsToArcGISTable([s], [_('climate index time series at URL "%(url)s"') % {'url' : url}], table, [field], overwriteExisting)
        return noDataValues[0], comments[0]

    # Methods for parsing multiple climate index time series and
    # returning them as a single table.

    @classmethod
    def _StringsToList(cls, strings, dataSources, setNoDataValuesToNone=True):

        # Parse each string.

        tables = []
        noDataValues = []
        comments = []

        for i in range(len(strings)):
            t, noDataValue, comment = cls._StringToList(strings[i], dataSources[i], setNoDataValuesToNone)
            tables.append(t)
            noDataValues.append(noDataValue)
            comments.append(comment)

        # Find the earliest start date among the parsed data.

        d = None
        
        for i in range(len(tables)):
            if d is None or d > tables[i][0][0]:
                d = tables[i][0][0]

        # Merge the tables.
            
        table = []
        noDataValues2 = copy.deepcopy(noDataValues)
        
        while len(tables) > 0:
            record = [d]

            i = 0
            while i < len(tables):
                if tables[i][0][0] == d:
                    value = tables[i][0][1]
                    del tables[i][0]
                        
                elif setNoDataValuesToNone:
                    value = None
                else:
                    value = noDataValues2[i]

                record.append(value)
                
                if len(tables[i]) <= 0:
                    del tables[i]
                    del noDataValues2[i]
                else:
                    i += 1

            table.append(record)

            if d.month < 12:
                d = datetime.datetime(d.year, d.month + 1, 1)
            else:
                d = datetime.datetime(d.year + 1, 1, 1)

        # Return successfully.

        return table, noDataValues, comments

    @classmethod
    def StringsToList(cls, strings, setNoDataValuesToNone=True):
        cls.__doc__.Obj.ValidateMethodInvocation()
        Logger.Debug(_('Parsing climate index data from %(num)i strings.') % {'num': len(strings)})
        return cls._StringsToList(strings, [_('climate index data in string %i') % i for i in range(1, len(strings) + 1)], setNoDataValuesToNone)

    @classmethod
    def _StringsToTable(cls, strings, dataSources, database, table, fields, dateDataType='datetime', intDataType='int32', floatDataType='float64', useNullForNoData=True, overwriteExisting=False):

        # Perform additional validation.

        fieldsDict = {}
        
        for field in fields:
            fieldLower = field.lower()

            if fieldLower in ['indexdate', 'indexyear', 'indexmonth']:
                Logger.RaiseException(ValueError(_('Climate index value fields may not be named IndexDate, IndexYear or IndexMonth. Please select a different name.')))

            if fieldLower in fieldsDict:
                Logger.RaiseException(ValueError(_('The list of climate index value fields contains the field name "%(name)s" more than once. Each field in this list must be unique. Please remove any duplicate entries.') % {'name': field}))

            fieldsDict[fieldLower] = None

        # Parse the strings.

        values, noDataValues, comments = cls._StringsToList(strings, dataSources, useNullForNoData)

        # If requested, delete the table if it already exists.
        
        if database.TableExists(table):
            if overwriteExisting:
                database.DeleteTable(table)
            else:
                Logger.RaiseException(ValueError(_('Cannot create table %s because it already exists.') % table))

        # Create the table and add the fields.

        Logger.Info(_('Writing %(num)i climate index records to table %(table)s.') % {'num': len(values), 'table': table})

        tableObj = database.CreateTable(table)
        
        try:
            dateField = 'IndexDate'
            tableObj.AddField(dateField, dateDataType)
            yearField = 'IndexYear'
            tableObj.AddField(yearField, intDataType)
            monthField = 'IndexMonth'
            tableObj.AddField(monthField, intDataType)

            for field in fields:
                tableObj.AddField(field, floatDataType, isNullable=useNullForNoData)

            # Create an insert cursor and fill the table.

            cursor = tableObj.OpenInsertCursor(rowCount=len(values))
            try:
                for i in range(len(values)):
                    d = values[i][0]
                    cursor.SetValue(dateField, d)
                    cursor.SetValue(yearField, d.year)
                    cursor.SetValue(monthField, d.month)

                    for j in range(len(fields)):
                        value = values[i][j+1]
                        if value is not None:
                            cursor.SetValue(fields[j], value)
                        elif useNullForNoData:
                            cursor.SetValue(fields[j], None)
                        else:
                            cursor.SetValue(fields[j], noDataValues[j])
                    
                    cursor.InsertRow()
            finally:
                del cursor

        # If an exception was raised, delete the table.
        
        except:
            try:
                database.DeleteTable(table)
            except:
                pass
            raise

        # Return successfully.

        if useNullForNoData:
            return table, [None] * len(fields), comments
        else:
            return table, noDataValues, comments

    @classmethod
    def StringsToTable(cls, strings, database, table, fields, dateDataType='datetime', intDataType='int32', floatDataType='float32', useNullForNoData=True, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        return cls._StringsToTable(strings, [_('climate index data in string %i') % i for i in range(1, len(strings) + 1)], database, table, fields, dateDataType, intDataType, floatDataType, useNullForNoData, overwriteExisting)

    @classmethod
    def _StringsToArcGISTable(cls, strings, dataSources, table, fields, overwriteExisting=False):

        # If the caller's table is in a directory (rather than a database),
        # the geoprocessor's CreateTable tool will create a DBF table,
        # regardless of what file extension the caller placed on the table.
        # Even if the caller's extension is .csv or .txt, the geoprocessor
        # will replace it with .dbf. If the caller does not provide an
        # extension, the geoprocessor will tack on .dbf.
        #
        # Because we know the geoprocessor will do this, we do it here
        # preemptively, so we can check for and delete the existing table, if
        # desired by the caller.

        workspace, table = os.path.split(table)

        if os.path.isdir(workspace) and not workspace.lower().endswith('.gdb') and not table.lower().endswith('.dbf'):
            if table.find('.') >= 0:
                newTable = table[:table.find('.')] + '.dbf'
                Logger.Warning('When creating tables in the file system, the ArcGIS CreateTable tool ignores the extension you specify and always creates a dBASE table with the extension .dbf. It will create the table %(new)s even though you asked for %(old)s.' % {'new': newTable, 'old': table})
            else:
                newTable = table + '.dbf'
                Logger.Warning('The ArcGIS CreateTable tool always creates dBASE tables in the file system. Even though you did not specify a file extension for your table, .dbf will be used.')
            table = newTable

        # If the table is a DBF, we cannot store NULL for "no data"
        # values.

        useNullForNoData = not (os.path.isdir(workspace) and table.lower().endswith('.dbf'))

        # Create the table.

        database = ArcGISWorkspace(path=workspace, 
                                   datasetType=ArcGISTable,
                                   pathParsingExpressions=[r'(?P<TableName>.+)'], 
                                   queryableAttributes=(QueryableAttribute('TableName', _('Table name'), UnicodeStringTypeMetadata()),))

        table, noDataValues, comments = cls._StringsToTable(strings,
                                                            dataSources,
                                                            database,
                                                            table,
                                                            fields,
                                                            'datetime',
                                                            'int32',
                                                            'float64',
                                                            useNullForNoData,
                                                            overwriteExisting)

        # If it is a DBF table, delete the Field1 field. ArcGIS always creates
        # this field because, according to the documentation, DBF files must
        # always have at least one field, and it is not possible to give a
        # field to the geoprocessor's CreateTable tool. Also delete the
        # M_S_O_F_T field if it exists; this is created by the Microsoft ODBC
        # dBASE driver, which ArcGIS could conceivably use in the future.

        if os.path.isdir(workspace) and not workspace.lower().endswith('.gdb') and table.lower().endswith('.dbf'):
            tableObj = database.QueryDatasets(expression="TableName = '%s'" % table, reportProgress=False)[0]
            if tableObj.GetFieldByName('Field1') is not None:
                tableObj.DeleteField('Field1')
            if tableObj.GetFieldByName('M_S_O_F_T') is not None:
                tableObj.DeleteField('M_S_O_F_T')

        # Return successfully.
        
        return noDataValues, comments

    @classmethod
    def StringsToArcGISTable(cls, strings, table, fields, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        cls._StringsToArcGISTable(strings, [_('climate index data in string %i') % i for i in range(1, len(strings) + 1)], table, fields, overwriteExisting)

    @classmethod
    def FilesToList(cls, paths, setNoDataValuesToNone=True):
        cls.__doc__.Obj.ValidateMethodInvocation()
        strings = list(map(cls._GetStringFromFile, paths))
        return cls._StringsToList(strings, [_('climate index time series file "%(path)s"') % {'path' : path} for path in paths], _('climate index time series file "%(path)s"') % {'path' : path}, setNoDataValuesToNone)

    @classmethod
    def FilesToTable(cls, paths, database, table, fields, dateDataType='datetime', intDataType='int32', floatDataType='float64', useNullForNoData=True, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        strings = list(map(cls._GetStringFromFile, paths))
        return cls._StringsToTable(strings, [_('climate index time series file "%(path)s"') % {'path' : path} for path in paths], database, table, fields, dateDataType, intDataType, floatDataType, useNullForNoData, overwriteExisting)

    @classmethod
    def FilesToArcGISTable(cls, paths, table, fields, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        strings = list(map(cls._GetStringFromFile, paths))
        cls._StringsToArcGISTable(strings, [_('climate index time series file "%(path)s"') % {'path' : path} for path in paths], table, fields, overwriteExisting)

    @classmethod
    def UrlsToList(cls, urls, setNoDataValuesToNone=True):
        cls.__doc__.Obj.ValidateMethodInvocation()
        strings = list(map(cls._GetStringFromUrl, urls))
        return cls._StringsToList(strings, [_('climate index time series at URL "%(url)s"') % {'url' : url} for url in urls], setNoDataValuesToNone)

    @classmethod
    def UrlsToTable(cls, urls, database, table, fields, dateDataType='datetime', intDataType='int32', floatDataType='float64', useNullForNoData=True, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        strings = list(map(cls._GetStringFromUrl, urls))
        return cls._StringsToTable(strings, [_('climate index time series at URL "%(url)s"') % {'url' : url} for url in urls], database, table, fields, dateDataType, intDataType, floatDataType, useNullForNoData, overwriteExisting)

    @classmethod
    def UrlsToArcGISTable(cls, urls, table, fields, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        strings = list(map(cls._GetStringFromUrl, urls))
        cls._StringsToArcGISTable(strings, [_('climate index time series at URL "%(url)s"') % {'url' : url} for url in urls], table, fields, overwriteExisting)

    @classmethod
    def ClassifyONIEpisodesInTimeSeriesList(cls, oniTable):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Make a copy of the input table, and sort it by date.

        oniTableCopy = copy.deepcopy(oniTable)
        oniTableCopy.sort(key=lambda item: item[0])

        # Walk through the dates and calculate the results.

        episodeStartIndex = None
        episodeType = None              # 1 == El Nino (warm), -1 == La Nina (cold), 0 == Normal
        lastYear = None
        lastMonth = None

        for i in range(len(oniTableCopy)):

            # Extract the values for this row.

            row = oniTableCopy[i]

            if not isinstance(row[0], datetime.datetime):
                Logger.RaiseException(ValueError(_('All sub-lists contained by the input list must contain a Python datetime.datetime object as the first element.')))
            if not isinstance(row[1], float):
                Logger.RaiseException(ValueError(_('All sub-lists contained by the input list must contain a float as the second element.')))

            year = row[0].year
            month = row[0].month
            value = row[1]

            # Validate that this row is the next month.

            if lastYear is not None:
                if lastMonth != 12 and (year != lastYear or month != lastMonth + 1) or lastMonth == 12 and (year != lastYear + 1 or month != 1):
                    Logger.RaiseException(ValueError(_('The input time series must form an unbroken sequence of monthly values. There must be exactly one value for each month, and no months may be skipped.')))

            lastYear = year
            lastMonth = month

            # Round the value to the nearest tenth decimal place, away
            # from zero. That appears to be done by NOAA to turn these
            # values, which are in hundredths:
            #
            # https://psl.noaa.gov/data/correlation/oni.data
            #
            # Into these values, which are in tenths, and are what is
            # actually used by NOAA to compute ONI:
            #
            # https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ensoyears.shtml
            #
            # Doing this rounding is actually quite complicated.

            Logger.Debug('%r %r %r %r' % (year, month, value, float(decimal.Decimal(str(value)).quantize(decimal.Decimal('0.1'), rounding=decimal.ROUND_HALF_UP))))
            value = float(decimal.Decimal(str(value)).quantize(decimal.Decimal('0.1'), rounding=decimal.ROUND_HALF_UP))

            # If we are in an episode, see if it is over.

            if episodeStartIndex is not None and (episodeType == -1 and value > -0.5 or episodeType == 1 and value < 0.5):

                # It is over. If it lasted at least five months, flag
                # those months with the episode type.

                if i - episodeStartIndex >= 5:
                    for j in range(episodeStartIndex, i):
                        oniTableCopy[j].append(episodeType)

                # Otherwise, flag those months with the "normal"
                # value.

                else:
                    for j in range(episodeStartIndex, i):
                        oniTableCopy[j].append(0)

                # Clear the episode variables.

                episodeStartIndex = None
                episodeType = None

            # If were not in an episode, or this month ended one,
            # check to see if this month started one.

            if episodeStartIndex is None:
                if value <= -0.5:
                    episodeStartIndex = i
                    episodeType = -1
                elif value >= 0.5:
                    episodeStartIndex = i
                    episodeType = 1
                else:
                    row.append(0)

        # If we ended in an episode, and it lasted at least five
        # months, flag those months with the episode type. Otherwise
        # flag them with the "normal" value.

        if episodeStartIndex is not None:
            if len(oniTableCopy) - episodeStartIndex >= 5:
                for j in range(episodeStartIndex, i+1):
                    oniTableCopy[j].append(episodeType)
            else:
                for j in range(episodeStartIndex, i+1):
                    oniTableCopy[j].append(0)

        # Return successfully.

        return oniTableCopy

    @classmethod
    def ClassifyONIEpisodesInTimeSeriesTable(cls, table, dateField, oniField, episodeField, noDataValue=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Read the rows of the table into a list.

        Logger.Info(_('Reading Oceanic Nino Index (ONI) values from field %(field)s of %(dn)s.') % {'field': oniField, 'dn': table.DisplayName})

        oniTable = []

        cursor = table.OpenSelectCursor(fields=[dateField, oniField, episodeField], orderBy=dateField)
        try:
            while cursor.NextRow():
                d = cursor.GetValue(dateField)
                if not isinstance(d, datetime.datetime):
                    Logger.RaiseException(ValueError(_('A row of the input table does not have a date in the field %(field)s. All rows of the table must have dates in this field.') % {'field': dateField}))

                oniValue = cursor.GetValue(oniField)
                if not isinstance(oniValue, (float, int, type(None))):
                    Logger.RaiseException(ValueError(_('A row of the input table does not have a floating point number, an integer, or NULL for field %(field)s. All rows of the table must have floating point numbers, integers, or NULL in this field.') % {'field': oniField}))

                if oniValue is not None and oniValue != -9.9:
                    oniTable.append([d, float(oniValue)])
                
        finally:
            del cursor

        # Classify the values in the list.

        oniTable = cls.ClassifyONIEpisodesInTimeSeriesList(oniTable)

        # Build a dictionary of values, for quick look up.

        episodeDictionary = {}

        for row in oniTable:
            episodeDictionary[row[0]] = row[2]

        # Write the episode values back to the table.

        Logger.Info(_('Writing episode values to field %(field)s.') % {'field': episodeField})

        cursor = table.OpenUpdateCursor(fields=[dateField, oniField, episodeField])
        try:
            while cursor.NextRow():
                d = cursor.GetValue(dateField)
                
                if d in episodeDictionary:
                    cursor.SetValue(episodeField, episodeDictionary[d])
                else:
                    cursor.SetValue(episodeField, noDataValue)
                    
                cursor.UpdateRow()
                
        finally:
            del cursor

    @classmethod
    def ClassifyONIEpisodesInTimeSeriesArcGISTable(cls, table, dateField, oniField, episodeField):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Determine if we can set missing values to NULL.

        tableObj = ArcGISTable(table)
        fieldObj = tableObj.GetFieldByName(episodeField)
        if fieldObj is None and field.IsNullable:
            noDataValue = None
        else:
            noDataValue = -9

        # Do the classification.

        cls.ClassifyONIEpisodesInTimeSeriesTable(tableObj, dateField, oniField, episodeField, noDataValue)

        # Return successfully.
        
        return table


###############################################################################
# Metadata: module
###############################################################################

from ...ArcGIS import ArcGISDependency
from ...Dependencies import PythonModuleDependency
from ...Metadata import *
from ...Types import *

AddModuleMetadata(shortDescription=_('Functions for working with NOAA climate indices.'))

###############################################################################
# Metadata: PSLClimateIndices class
###############################################################################

AddClassMetadata(PSLClimateIndices,
    shortDescription=_('Functions for working with `climate index time series <https://psl.noaa.gov/data/climateindices/>`__ provided by the NOAA Physical Sciences Laboratory (PSL).'))

# Public method: PSLClimateIndices.StringToList

AddMethodMetadata(PSLClimateIndices.StringToList,
    shortDescription=_('Returns a table of climate index values parsed from a string in NOAA PSL time series format.'))

AddArgumentMetadata(PSLClimateIndices.StringToList, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=PSLClimateIndices),
    description=_(':class:`%s` or an instance of it.') % PSLClimateIndices.__name__)

AddArgumentMetadata(PSLClimateIndices.StringToList, 's',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Multi-line string in the PSL time series format documented at
https://psl.noaa.gov/data/climateindices/list/::

    year1 yearN
    year1 janval febval marval aprval mayval junval julval augval sepval octval decval
    year2 janval febval marval aprval mayval junval julval augval sepval octval decval
    ...
    yearN janval febval marval aprval mayval junval julval augval sepval octval decval
    missing_value

For example, the North Atlantic Oscillation (NAO), available at
https://psl.noaa.gov/data/correlation/nao.data, looked like this (circa 2007)::

     1948 2007
     1948 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90
     1949 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90
     1950   0.92   0.40  -0.36   0.73  -0.59  -0.06  -1.26  -0.05   0.25   0.85  -1.26  -1.02
     1951   0.08   0.70  -1.02  -0.22  -0.59  -1.64   1.37  -0.22  -1.36   1.87  -0.39   1.32
     <Lines deleted for brevity>
     2007   0.22  -0.47   1.44   0.17   0.66  -1.31  -0.58  -0.14   0.72 -99.90 -99.90 -99.90
       -99.9
      NAO Index from CPC
     https://psl.noaa.gov/data/climateindices/list/ for info

Any lines following missing_value are treated as comments."""))

AddArgumentMetadata(PSLClimateIndices.StringToList, 'setNoDataValuesToNone',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the returned table will contain a :py:data:`None` wherever the
original data has a missing_value. If False, the table will contain the
missing_value as it appears in the original data."""))

AddResultMetadata(PSLClimateIndices.StringToList, 'table',
    typeMetadata=ListTypeMetadata(elementType=ListTypeMetadata(elementType=AnyObjectTypeMetadata(), minLength=2, maxLength=2)),
    description=_(
"""Table of climate index values parsed from the input data, represented as a
:py:class:`list` of :py:class:`list`\\ s. The outer list contains the rows of
the table. Each inner list contains the field values for a row.

There are two fields:

* ``Date`` - the date of the first day of the month and year of the climate
  index value (e.g. 1-March-1960), as a :py:class:`~datetime.datetime`.

* ``Value`` - the climate index value, as a :py:class:`float`. This value may
  be :py:data:`None` rather than the missing_value if `setNoDataValuesToNone`
  is True.

For example::

    [[datetime.datetime(1948, 1, 1, 0, 0), 2.5],
     [datetime.datetime(1948, 2, 1, 0, 0), None],
     [datetime.datetime(1948, 3, 1, 0, 0), 2.75],
     ...]

The rows will be ordered in ascending date order and all 12 months will be
included for every year. If these months occur in the future they will have
the missing_value (or :py:data:`None`)."""))

AddResultMetadata(PSLClimateIndices.StringToList, 'noDataValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""The value that means "no data is available" in the returned table. If
`setNoDataValuesToNone` is False, it will be the missing_value parsed from the
input data. If True, it will be :py:data:`None`."""))

AddResultMetadata(PSLClimateIndices.StringToList, 'comment',
    typeMetadata=UnicodeStringTypeMetadata(minLength=0),
    description=_(
"""The comment parsed from the input data. If no comment was present, an empty
string will be returned."""),
    arcGISDisplayName=_('Comment'))

# Public method: PSLClimateIndices.StringToTable

AddMethodMetadata(PSLClimateIndices.StringToTable,
    shortDescription=_('Creates a table of climate index values parsed from a string in NOAA PSL time series format.'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.StringToTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.StringToList, 's', PSLClimateIndices.StringToTable, 's')

AddArgumentMetadata(PSLClimateIndices.StringToTable, 'database',
    typeMetadata=ClassInstanceTypeMetadata(cls=Database),
    description=_('Database that will receive the new table.'))

AddArgumentMetadata(PSLClimateIndices.StringToTable, 'table',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Table to create and populate. The table will have four fields:

* ``IndexDate`` (date) - the date of the first day of the month and year of
  the climate index value (e.g. 1-March-1960), in the database's date data
  type.

* ``IndexYear`` (integer) - the year of the climate index value (e.g. 1990).

* ``IndexMonth`` (integer) - the month of the climate index value, ranging
  from 1 to 12.

* ``Value`` (float) - the climate index value for that month and year. The
  name of this field is specified by the `field` parameter, and need not be
  ``Value``.

The second two fields store the same data as the first field but are present
for your convenience, in case you prefer the year and month broken out as
integers.

The rows will be inserted in ascending date order and all 12 months will be
included for every year. If these months occur in the future they will be
assigned the missing_value parsed from the input data, or NULL if
`useNullForNoData` is True."""))

AddArgumentMetadata(PSLClimateIndices.StringToTable, 'field',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the field to receive the climate index value.'))

AddArgumentMetadata(PSLClimateIndices.StringToTable, 'dateDataType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['datetime']),
    description=_('Data type to use for the ``IndexDate`` field.'))

AddArgumentMetadata(PSLClimateIndices.StringToTable, 'intDataType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']),
    description=_('Data type to use for the ``IndexYear`` and ``IndexMonth`` fields.'))

AddArgumentMetadata(PSLClimateIndices.StringToTable, 'floatDataType',
    typeMetadata=UnicodeStringTypeMetadata(allowedValues=['float32', 'float64']),
    description=_('Data type to use for the ``Value`` field.'))

AddArgumentMetadata(PSLClimateIndices.StringToTable, 'useNullForNoData',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, a database NULL will be used wherever the original data has a
missing_value. If False, the table will contain the missing_value as it
appears in the original data."""))

AddArgumentMetadata(PSLClimateIndices.StringToTable, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output table will be overwritten, if it exists. If False, a
:py:exc:`ValueError` will be raised if the output table exists."""))

AddResultMetadata(PSLClimateIndices.StringToTable, 'outputTable',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('The created table.'))

CopyResultMetadata(PSLClimateIndices.StringToList, 'noDataValue', PSLClimateIndices.StringToTable, 'noDataValue')
CopyResultMetadata(PSLClimateIndices.StringToList, 'comment', PSLClimateIndices.StringToTable, 'comment')

# Public method: PSLClimateIndices.StringToArcGISTable

AddMethodMetadata(PSLClimateIndices.StringToArcGISTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from a string in NOAA PSL time series format.'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.StringToArcGISTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.StringToList, 's', PSLClimateIndices.StringToArcGISTable, 's')

AddArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'table',
    typeMetadata=ArcGISTableTypeMetadata(deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Table to create and populate. The table will have four fields:

* ``IndexDate`` (DATE) - the date of the first day of the month and year of
  the climate index value (e.g. 1-March-1960).

* ``IndexYear`` (LONG) - the year of the climate index value (e.g. 1990).

* ``IndexMonth`` (LONG) - the month of the climate index value, ranging from 1
  to 12.

* ``Value`` (DOUBLE) - the index value for that month and year. The name of
  this field is specified by the Climate Index Value Field parameter, and need
  not be "Value". If the output table is a dBASE table (a DBF file), the
  missing_value parsed from the input data will be used to represent "no data
  is available". For other types of tables, a database NULL will represent "no
  data is available".

The second two fields store the same data as the first field but are present
for your convenience, in case you prefer the year and month broken out as
integers.

The rows will be inserted in ascending date order and all 12 months will be
included for every year. If these months occur in the future they will have
the missing_value or NULL, as described above."""),
    direction='Output',
    arcGISDisplayName=_('Output table'))

AddArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'field',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the field to receive the climate index value.'),
    arcGISDisplayName=_('Climate index value field'))

AddArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output table will be overwritten, if it exists. If False, a
:py:exc:`ValueError` will be raised if the output table exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

AddResultMetadata(PSLClimateIndices.StringToArcGISTable, 'noDataValue',
    typeMetadata=FloatTypeMetadata(canBeNone=True),
    description=_(
"""The value that means "no data is available" in the output table. If the
output table is a dBASE table (a DBF file), the missing_value parsed from the
input data will be returned. For other types of tables, :py:data:`None` will
be returned, representing a database NULL."""),
    arcGISDisplayName=_('NoData value'))

CopyResultMetadata(PSLClimateIndices.StringToList, 'comment', PSLClimateIndices.StringToArcGISTable, 'comment')

# Public method: PSLClimateIndices.FileToList

AddMethodMetadata(PSLClimateIndices.FileToList,
    shortDescription=_('Returns a table of climate index values parsed from a text file in NOAA PSL time series format.'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.FileToList, 'cls')

AddArgumentMetadata(PSLClimateIndices.FileToList, 'path',
    typeMetadata=FileTypeMetadata(mayBeCompressed=True, mustExist=True),
    description=_(
"""Text file containing data for one climate index, in the PSL time series
format documented at https://psl.noaa.gov/data/climateindices/list/::

    year1 yearN
    year1 janval febval marval aprval mayval junval julval augval sepval octval decval
    year2 janval febval marval aprval mayval junval julval augval sepval octval decval
    ...
    yearN janval febval marval aprval mayval junval julval augval sepval octval decval
    missing_value

For example, the North Atlantic Oscillation (NAO), available at
https://psl.noaa.gov/data/correlation/nao.data, looked like this (circa 2007)::

     1948 2007
     1948 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90
     1949 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90
     1950   0.92   0.40  -0.36   0.73  -0.59  -0.06  -1.26  -0.05   0.25   0.85  -1.26  -1.02
     1951   0.08   0.70  -1.02  -0.22  -0.59  -1.64   1.37  -0.22  -1.36   1.87  -0.39   1.32
     <Lines deleted for brevity>
     2007   0.22  -0.47   1.44   0.17   0.66  -1.31  -0.58  -0.14   0.72 -99.90 -99.90 -99.90
       -99.9
      NAO Index from CPC
     https://psl.noaa.gov/data/climateindices/list/ for info

Any lines following missing_value are treated as comments."""),
    arcGISDisplayName=_('Input text file'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'setNoDataValuesToNone', PSLClimateIndices.FileToList, 'setNoDataValuesToNone')

CopyResultMetadata(PSLClimateIndices.StringToList, 'table', PSLClimateIndices.FileToList, 'table')
CopyResultMetadata(PSLClimateIndices.StringToList, 'noDataValue', PSLClimateIndices.FileToList, 'noDataValue')
CopyResultMetadata(PSLClimateIndices.StringToList, 'comment', PSLClimateIndices.FileToList, 'comment')

# Public method: PSLClimateIndices.FileToTable

AddMethodMetadata(PSLClimateIndices.FileToTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from a text file in NOAA PSL time series format.'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.FileToTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.FileToList, 'path', PSLClimateIndices.FileToTable, 'path')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'database', PSLClimateIndices.FileToTable, 'database')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'table', PSLClimateIndices.FileToTable, 'table')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'field', PSLClimateIndices.FileToTable, 'field')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'dateDataType', PSLClimateIndices.FileToTable, 'dateDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'intDataType', PSLClimateIndices.FileToTable, 'intDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'floatDataType', PSLClimateIndices.FileToTable, 'floatDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'useNullForNoData', PSLClimateIndices.FileToTable, 'useNullForNoData')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'overwriteExisting', PSLClimateIndices.FileToTable, 'overwriteExisting')

CopyResultMetadata(PSLClimateIndices.StringToTable, 'outputTable', PSLClimateIndices.FileToTable, 'outputTable')
CopyResultMetadata(PSLClimateIndices.StringToTable, 'noDataValue', PSLClimateIndices.FileToTable, 'noDataValue')
CopyResultMetadata(PSLClimateIndices.StringToTable, 'comment', PSLClimateIndices.FileToTable, 'comment')

# Public method: PSLClimateIndices.FileToArcGISTable

AddMethodMetadata(PSLClimateIndices.FileToArcGISTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from a text file in NOAA PSL time series format.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Table from PSL Climate Index Time Series in Text File'),
    arcGISToolCategory=_('Data Products\\NOAA Physical Sciences Laboratory\\Climate Indices'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.FileToArcGISTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.FileToList, 'path', PSLClimateIndices.FileToArcGISTable, 'path')
CopyArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'table', PSLClimateIndices.FileToArcGISTable, 'table')
CopyArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'field', PSLClimateIndices.FileToArcGISTable, 'field')
CopyArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'overwriteExisting', PSLClimateIndices.FileToArcGISTable, 'overwriteExisting')

CopyResultMetadata(PSLClimateIndices.StringToArcGISTable, 'noDataValue', PSLClimateIndices.FileToArcGISTable, 'noDataValue')
CopyResultMetadata(PSLClimateIndices.StringToArcGISTable, 'comment', PSLClimateIndices.FileToArcGISTable, 'comment')

# Public method: PSLClimateIndices.UrlToList

AddMethodMetadata(PSLClimateIndices.UrlToList,
    shortDescription=_('Returns a table of climate index values parsed from the NOAA PSL climate index time series data downloaded from a URL.'),
    dependencies=[PythonModuleDependency('requests', cheeseShopName='requests')])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.UrlToList, 'cls')

AddArgumentMetadata(PSLClimateIndices.UrlToList, 'url',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""URL to a text file containing climate index data in PSL time series format.

https://psl.noaa.gov/data/climateindices/list/ contains a large table that
lists the available climate index data produced by PSL. The left column
contains hyperlinks to the datasets and the right column contains the
descriptions of the datasets. Find the dataset you are interested in, extract
the URL from the hyperlink, and provide it to this tool.

For example, if you are interested in the Oceanic Niño Index (ONI), scroll
down the table until you reach ONI in the left column. Click on the ONI
hyperlink to bring up the page https://psl.noaa.gov/data/correlation/oni.data.
Copy/paste that URL from your browser."""),
    arcGISDisplayName=_('Input URL'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'setNoDataValuesToNone', PSLClimateIndices.UrlToList, 'setNoDataValuesToNone')

CopyResultMetadata(PSLClimateIndices.StringToList, 'table', PSLClimateIndices.UrlToList, 'table')
CopyResultMetadata(PSLClimateIndices.StringToList, 'noDataValue', PSLClimateIndices.UrlToList, 'noDataValue')
CopyResultMetadata(PSLClimateIndices.StringToList, 'comment', PSLClimateIndices.UrlToList, 'comment')

# Public method: PSLClimateIndices.UrlToTable

AddMethodMetadata(PSLClimateIndices.UrlToTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from NOAA PSL climate index time series data downloaded from a URL.'),
    dependencies=[PythonModuleDependency('requests', cheeseShopName='requests')])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.UrlToTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.UrlToList, 'url', PSLClimateIndices.UrlToTable, 'url')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'database', PSLClimateIndices.UrlToTable, 'database')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'table', PSLClimateIndices.UrlToTable, 'table')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'field', PSLClimateIndices.UrlToTable, 'field')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'dateDataType', PSLClimateIndices.UrlToTable, 'dateDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'intDataType', PSLClimateIndices.UrlToTable, 'intDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'floatDataType', PSLClimateIndices.UrlToTable, 'floatDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'useNullForNoData', PSLClimateIndices.UrlToTable, 'useNullForNoData')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'overwriteExisting', PSLClimateIndices.UrlToTable, 'overwriteExisting')

CopyResultMetadata(PSLClimateIndices.StringToTable, 'outputTable', PSLClimateIndices.UrlToTable, 'outputTable')
CopyResultMetadata(PSLClimateIndices.StringToTable, 'noDataValue', PSLClimateIndices.UrlToTable, 'noDataValue')
CopyResultMetadata(PSLClimateIndices.StringToTable, 'comment', PSLClimateIndices.UrlToTable, 'comment')

# Public method: PSLClimateIndices.UrlToArcGISTable

AddMethodMetadata(PSLClimateIndices.UrlToArcGISTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from NOAA PSL climate index time series data downloaded from a URL.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Table from PSL Climate Index Time Series at URL'),
    arcGISToolCategory=_('Data Products\\NOAA Physical Sciences Laboratory\\Climate Indices'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('requests', cheeseShopName='requests')])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.UrlToArcGISTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.UrlToList, 'url', PSLClimateIndices.UrlToArcGISTable, 'url')
CopyArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'table', PSLClimateIndices.UrlToArcGISTable, 'table')
CopyArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'field', PSLClimateIndices.UrlToArcGISTable, 'field')
CopyArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'overwriteExisting', PSLClimateIndices.UrlToArcGISTable, 'overwriteExisting')

CopyResultMetadata(PSLClimateIndices.StringToArcGISTable, 'noDataValue', PSLClimateIndices.UrlToArcGISTable, 'noDataValue')
CopyResultMetadata(PSLClimateIndices.StringToArcGISTable, 'comment', PSLClimateIndices.UrlToArcGISTable, 'comment')

# Public method: PSLClimateIndices.StringsToList

AddMethodMetadata(PSLClimateIndices.StringsToList,
    shortDescription=_('Returns a table of climate index values parsed from a list of strings, where each string is the data for a single climate index in NOAA PSL time series format.'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.StringsToList, 'cls')

AddArgumentMetadata(PSLClimateIndices.StringsToList, 'strings',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=1), minLength=1),
    description=_(
"""List of one or more multi-line strings in the PSL time series format
documented at https://psl.noaa.gov/data/climateindices/list/::

    year1 yearN
    year1 janval febval marval aprval mayval junval julval augval sepval octval decval
    year2 janval febval marval aprval mayval junval julval augval sepval octval decval
    ...
    yearN janval febval marval aprval mayval junval julval augval sepval octval decval
    missing_value

For example, the North Atlantic Oscillation (NAO), available at
https://psl.noaa.gov/data/correlation/nao.data, looked like this (circa 2007)::

     1948 2007
     1948 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90
     1949 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90
     1950   0.92   0.40  -0.36   0.73  -0.59  -0.06  -1.26  -0.05   0.25   0.85  -1.26  -1.02
     1951   0.08   0.70  -1.02  -0.22  -0.59  -1.64   1.37  -0.22  -1.36   1.87  -0.39   1.32
     <Lines deleted for brevity>
     2007   0.22  -0.47   1.44   0.17   0.66  -1.31  -0.58  -0.14   0.72 -99.90 -99.90 -99.90
       -99.9
      NAO Index from CPC
     https://psl.noaa.gov/data/climateindices/list/ for info

You should provide the entire text above as one string in the input list, the
entire text for a different climate index as the second string, and so on.

Any lines following missing_value are treated as comments."""))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'setNoDataValuesToNone', PSLClimateIndices.StringsToList, 'setNoDataValuesToNone')

AddResultMetadata(PSLClimateIndices.StringsToList, 'table',
    typeMetadata=ListTypeMetadata(elementType=ListTypeMetadata(elementType=AnyObjectTypeMetadata(), minLength=2)),
    description=_(
"""Table of index values parsed from the input data, represented as a list of
lists. The outer list contains the rows of the table. Each inner list contains
the field values for a row.

There are at least two fields:

* ``Date`` - the date of the first day of the month and year of the climate
  index value (e.g. 1-March-1960), as a :py:class:`~datetime.datetime`.

* ``Value`` - the index value of the first climate index in the input data, as
  a :py:class:`float`. This value may be :py:data:`None` rather than the
  missing_value if `setNoDataValuesToNone` is True.

There will be one ``Value`` field for each climate index that you provide as
input. For example, if you provide three climate indices, a table with four
fields will be returned::

    [[datetime.datetime(1948, 1, 1, 0, 0), 2.5, None, 1.0],
     [datetime.datetime(1948, 2, 1, 0, 0), 1.5, None, -2.0],
     [datetime.datetime(1948, 3, 1, 0, 0), 2.75, -8.0, 3.0],
     ...]

The rows will be ordered in ascending date order and all 12 months will be
included for every year. If these months occur in the future they will have
the missing_value (or :py:data:`None`). If the occur prior to the first month
for which data are available, as shown in the example above for the second
climate index, they will also have the missing_value (or :py:data:`None`)."""))

AddResultMetadata(PSLClimateIndices.StringsToList, 'noDataValues',
    typeMetadata=ListTypeMetadata(elementType=FloatTypeMetadata(canBeNone=True), minLength=1),
    description=_(
"""List of values that mean "no data is available" in the value fields of the
returned table. Each item in this list corresponds to one of the climate
indices you provide as input. If `setNoDataValuesToNone` is False, the list
items will be the missing_values parsed from the input data. If True, the list
items will all be :py:data:`None`."""))

AddResultMetadata(PSLClimateIndices.StringsToList, 'comments',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(minLength=0), minLength=1),
    description=_(
"""List of comments parsed from the input data. Each item in this list
corresponds to one of the climate indices you provide as input. If no comment
was present in the input data for an index, an empty string will be stored for
it in the list."""))

# Public method: PSLClimateIndices.StringsToTable

AddMethodMetadata(PSLClimateIndices.StringsToTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from a list of strings, where each string is the data for a single climate index in NOAA PSL time series format.'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.StringsToTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.StringsToList, 'strings', PSLClimateIndices.StringsToTable, 'strings')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'database', PSLClimateIndices.StringsToTable, 'database')

AddArgumentMetadata(PSLClimateIndices.StringsToTable, 'table',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Table to create and populate. The table will have at least four
fields:

* ``IndexDate`` (date) - the date of the first day of the month and year of
  the climate index value (e.g. 1-March-1960), in the database's date data
  type.

* ``IndexYear`` (integer) - the year of the climate index value (e.g. 1990).

* ``IndexMonth`` (integer) - the month of the climate index value, ranging
  from 1 to 12.

* ``Value`` (float) - the climate index value for that month and year. There
  will be one of these fields created for each climate index that you provide
  as inputs. The names of these field are specified by the `fields` parameter.

The second two fields store the same data as the first field but are present
for your convenience, in case you prefer the year and month broken out as
integers.

The rows will be inserted in ascending date order and all 12 months will be
included for every year. If these months occur in the future they will have
the missing_value parsed from the input data, or NULL if `useNullForNoData` is
True."""))

AddArgumentMetadata(PSLClimateIndices.StringsToTable, 'fields',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), minLength=1),
    description=_(
"""Names of the fields to receive the climate index values. You must provide a
field name for each climate index you provide as input."""),
    arcGISDisplayName=_('Climate index value fields'))

CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'dateDataType', PSLClimateIndices.StringsToTable, 'dateDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'intDataType', PSLClimateIndices.StringsToTable, 'intDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'floatDataType', PSLClimateIndices.StringsToTable, 'floatDataType')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'useNullForNoData', PSLClimateIndices.StringsToTable, 'useNullForNoData')
CopyArgumentMetadata(PSLClimateIndices.StringToTable, 'overwriteExisting', PSLClimateIndices.StringsToTable, 'overwriteExisting')

AddResultMetadata(PSLClimateIndices.StringsToTable, 'outputTable',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('The created table.'))

CopyResultMetadata(PSLClimateIndices.StringsToList, 'noDataValues', PSLClimateIndices.StringsToTable, 'noDataValues')
CopyResultMetadata(PSLClimateIndices.StringsToList, 'comments', PSLClimateIndices.StringsToTable, 'comments')

# Public method: PSLClimateIndices.StringsToArcGISTable

AddMethodMetadata(PSLClimateIndices.StringsToArcGISTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from a list of strings, where each string is the data for a single climate index in NOAA PSL time series format.'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.StringsToArcGISTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.StringsToList, 'strings', PSLClimateIndices.StringsToArcGISTable, 'strings')

AddArgumentMetadata(PSLClimateIndices.StringsToArcGISTable, 'table',
    typeMetadata=ArcGISTableTypeMetadata(deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""Table to create and populate. The table will have at least four fields:

* ``IndexDate`` (DATE) - the date of the first day of the month and year
  of the climate index value (e.g. 1-March-1960).

* ``IndexYear`` (LONG) - the year of the climate index value (e.g. 1990).

* ``IndexMonth`` (LONG) - the month of the climate index value, ranging from 1
  to 12.

* ``Value`` (DOUBLE) - the index value for that month and year. There will be
  one of these fields created for each climate index that you provide as
  inputs. The names of these field are specified by the Climate Index Value
  Fields parameter. If the output table is a dBASE table (a DBF file), the
  missing_value parsed from the input data will be used to represent "no data
  is available". For other types of tables, a database NULL will represent "no
  data is available".

The second two fields store the same data as the first field but are present
for your convenience, in case you prefer the year and month broken out as
integers.

The rows will be inserted in ascending date order and all 12 months will be
included for every year. If these months occur in the future they will have
the missing_value or NULL as described above."""),
    direction='Output',
    arcGISDisplayName=_('Output table'))

CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'fields', PSLClimateIndices.StringsToArcGISTable, 'fields')
CopyArgumentMetadata(PSLClimateIndices.StringToArcGISTable, 'overwriteExisting', PSLClimateIndices.StringsToArcGISTable, 'overwriteExisting')

# Public method: PSLClimateIndices.FilesToList

AddMethodMetadata(PSLClimateIndices.FilesToList,
    shortDescription=_('Creates and populates a table of climate index values parsed from a list of text files, where each file contains the data for a single climate index in NOAA PSL time series format.'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.FilesToList, 'cls')

AddArgumentMetadata(PSLClimateIndices.FilesToList, 'paths',
    typeMetadata=ListTypeMetadata(elementType=FileTypeMetadata(mayBeCompressed=True, mustExist=True), minLength=1),
    description=_(
"""List of text files, each containing data for one climate index in the PSL
time series format documented at
https://psl.noaa.gov/data/climateindices/list/::

    year1 yearN
    year1 janval febval marval aprval mayval junval julval augval sepval octval decval
    year2 janval febval marval aprval mayval junval julval augval sepval octval decval
    ...
    yearN janval febval marval aprval mayval junval julval augval sepval octval decval
    missing_value

For example, the North Atlantic Oscillation (NAO), available at
https://psl.noaa.gov/data/correlation/nao.data, looked like this (circa 2007)::

     1948 2007
     1948 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90
     1949 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90 -99.90
     1950   0.92   0.40  -0.36   0.73  -0.59  -0.06  -1.26  -0.05   0.25   0.85  -1.26  -1.02
     1951   0.08   0.70  -1.02  -0.22  -0.59  -1.64   1.37  -0.22  -1.36   1.87  -0.39   1.32
     <Lines deleted for brevity>
     2007   0.22  -0.47   1.44   0.17   0.66  -1.31  -0.58  -0.14   0.72 -99.90 -99.90 -99.90
       -99.9
      NAO Index from CPC
     https://psl.noaa.gov/data/climateindices/list/ for info

Any lines following missing_value are treated as comments."""),
    arcGISDisplayName=_('Input text files'))

CopyArgumentMetadata(PSLClimateIndices.StringsToList, 'setNoDataValuesToNone', PSLClimateIndices.FilesToList, 'setNoDataValuesToNone')

CopyResultMetadata(PSLClimateIndices.StringsToList, 'table', PSLClimateIndices.FilesToList, 'table')
CopyResultMetadata(PSLClimateIndices.StringsToList, 'noDataValues', PSLClimateIndices.FilesToList, 'noDataValues')
CopyResultMetadata(PSLClimateIndices.StringsToList, 'comments', PSLClimateIndices.FilesToList, 'comments')

# Public method: PSLClimateIndices.FilesToTable

AddMethodMetadata(PSLClimateIndices.FilesToTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from a list of text files, where each file contains the data for a single climate index in NOAA PSL time series format.'))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.FilesToTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.FilesToList, 'paths', PSLClimateIndices.FilesToTable, 'paths')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'database', PSLClimateIndices.FilesToTable, 'database')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'table', PSLClimateIndices.FilesToTable, 'table')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'fields', PSLClimateIndices.FilesToTable, 'fields')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'dateDataType', PSLClimateIndices.FilesToTable, 'dateDataType')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'intDataType', PSLClimateIndices.FilesToTable, 'intDataType')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'floatDataType', PSLClimateIndices.FilesToTable, 'floatDataType')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'useNullForNoData', PSLClimateIndices.FilesToTable, 'useNullForNoData')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'overwriteExisting', PSLClimateIndices.FilesToTable, 'overwriteExisting')

CopyResultMetadata(PSLClimateIndices.StringsToTable, 'outputTable', PSLClimateIndices.FilesToTable, 'outputTable')
CopyResultMetadata(PSLClimateIndices.StringsToTable, 'noDataValues', PSLClimateIndices.FilesToTable, 'noDataValues')
CopyResultMetadata(PSLClimateIndices.StringsToTable, 'comments', PSLClimateIndices.FilesToTable, 'comments')

# Public method: PSLClimateIndices.FilesToArcGISTable

AddMethodMetadata(PSLClimateIndices.FilesToArcGISTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from a list of text files, where each file contains the data for a single climate index in NOAA PSL time series format.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Table from PSL Climate Index Time Series in Text Files'),
    arcGISToolCategory=_('Data Products\\NOAA Physical Sciences Laboratory\\Climate Indices'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.FilesToArcGISTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.FilesToList, 'paths', PSLClimateIndices.FilesToArcGISTable, 'paths')
CopyArgumentMetadata(PSLClimateIndices.StringsToArcGISTable, 'table', PSLClimateIndices.FilesToArcGISTable, 'table')
CopyArgumentMetadata(PSLClimateIndices.StringsToArcGISTable, 'fields', PSLClimateIndices.FilesToArcGISTable, 'fields')
CopyArgumentMetadata(PSLClimateIndices.StringsToArcGISTable, 'overwriteExisting', PSLClimateIndices.FilesToArcGISTable, 'overwriteExisting')

# Public method: PSLClimateIndices.UrlsToList

AddMethodMetadata(PSLClimateIndices.UrlsToList,
    shortDescription=_('Creates and populates a table of climate index values parsed from NOAA PSL climate index time series data downloaded from a list of URLs.'),
    dependencies=[PythonModuleDependency('requests', cheeseShopName='requests')])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.UrlsToList, 'cls')

AddArgumentMetadata(PSLClimateIndices.UrlsToList, 'urls',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), minLength=1),
    description=_(
"""List of URLs to text files containing climate index data in PSL time series
format.

https://psl.noaa.gov/data/climateindices/list/ contains a large table that
lists the available climate index data produced by PSL. The left column
contains hyperlinks to the datasets and the right column contains the
descriptions of the datasets. Find the datasets you are interested in, extract
the URLs from the hyperlinks, and provide them to this tool.

For example, if you are interested in the Oceanic Niño Index (ONI), scroll
down the table until you reach ONI in the left column. Click on the ONI
hyperlink to bring up the page https://psl.noaa.gov/data/correlation/oni.data.
Copy/paste that URL from your browser."""),
    arcGISDisplayName=_('Input URLs'))

CopyArgumentMetadata(PSLClimateIndices.StringsToList, 'setNoDataValuesToNone', PSLClimateIndices.UrlsToList, 'setNoDataValuesToNone')

CopyResultMetadata(PSLClimateIndices.StringsToList, 'table', PSLClimateIndices.UrlsToList, 'table')
CopyResultMetadata(PSLClimateIndices.StringsToList, 'noDataValues', PSLClimateIndices.UrlsToList, 'noDataValues')
CopyResultMetadata(PSLClimateIndices.StringsToList, 'comments', PSLClimateIndices.UrlsToList, 'comments')

# Public method: PSLClimateIndices.UrlsToTable

AddMethodMetadata(PSLClimateIndices.UrlsToTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from NOAA PSL climate index time series data downloaded from a list of URLs.'),
    dependencies=[PythonModuleDependency('requests', cheeseShopName='requests')])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.UrlsToTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.UrlsToList, 'urls', PSLClimateIndices.UrlsToTable, 'urls')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'database', PSLClimateIndices.UrlsToTable, 'database')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'table', PSLClimateIndices.UrlsToTable, 'table')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'fields', PSLClimateIndices.UrlsToTable, 'fields')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'dateDataType', PSLClimateIndices.UrlsToTable, 'dateDataType')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'intDataType', PSLClimateIndices.UrlsToTable, 'intDataType')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'floatDataType', PSLClimateIndices.UrlsToTable, 'floatDataType')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'useNullForNoData', PSLClimateIndices.UrlsToTable, 'useNullForNoData')
CopyArgumentMetadata(PSLClimateIndices.StringsToTable, 'overwriteExisting', PSLClimateIndices.UrlsToTable, 'overwriteExisting')

CopyResultMetadata(PSLClimateIndices.StringsToTable, 'outputTable', PSLClimateIndices.UrlsToTable, 'outputTable')
CopyResultMetadata(PSLClimateIndices.StringsToTable, 'noDataValues', PSLClimateIndices.UrlsToTable, 'noDataValues')
CopyResultMetadata(PSLClimateIndices.StringsToTable, 'comments', PSLClimateIndices.UrlsToTable, 'comments')

# Public method: PSLClimateIndices.UrlsToArcGISTable

AddMethodMetadata(PSLClimateIndices.UrlsToArcGISTable,
    shortDescription=_('Creates and populates a table of climate index values parsed from NOAA PSL climate index time series data downloaded from a list of URLs.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Table from PSL Climate Index Time Series at URLs'),
    arcGISToolCategory=_('Data Products\\NOAA Physical Sciences Laboratory\\Climate Indices'),
    dependencies=[ArcGISDependency(), PythonModuleDependency('requests', cheeseShopName='requests')])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.UrlsToArcGISTable, 'cls')
CopyArgumentMetadata(PSLClimateIndices.UrlsToList, 'urls', PSLClimateIndices.UrlsToArcGISTable, 'urls')
CopyArgumentMetadata(PSLClimateIndices.StringsToArcGISTable, 'table', PSLClimateIndices.UrlsToArcGISTable, 'table')
CopyArgumentMetadata(PSLClimateIndices.StringsToArcGISTable, 'fields', PSLClimateIndices.UrlsToArcGISTable, 'fields')
CopyArgumentMetadata(PSLClimateIndices.StringsToArcGISTable, 'overwriteExisting', PSLClimateIndices.UrlsToArcGISTable, 'overwriteExisting')

# Public method: PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesList

AddMethodMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesList,
    shortDescription=_('Given a time series table of monthly Oceanic Niño Index (ONI) numerical values, classifies each month as part of a normal, El Niño (warm), or La Niña (cold) episode.'),
    longDescription=_(
"""At the time of this writing (in 2024), the NOAA Climate Prediction Center
(CPC) maintained a table of ONI values at
https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ensoyears.shtml.
A copy of these values were provided by the NOAA Physical Sciences Laboratory
(PSL) at https://psl.noaa.gov/data/correlation/oni.data. The CPC provided the
following definition of ONI and ONI episodes:

    "Warm and cold episodes based on a threshold of +/- 0.5 deg C for the
    Oceanic Niño Index (ONI) [3 month running mean of ERSST.v5 SST anomalies
    in the Niño 3.4 region (5N-5S, 120-170W)], based on centered 30-year base
    periods updated every 5 years. For historical purposes cold and warm
    episodes are defined when the threshold is met for a minimum of 5
    consecutive overlapping seasons."

This tool accepts as input a table of monthly ONI values and classifies each
month as a normal, El Niño (warm), or La Niña (cold) episode, according to
CPC's definition. To reproduce CPC's table using data from PSL with this tool,
you can:

1. Use the Create Table from PSL Climate Index Time Series at URL tool
   to create a table from https://psl.noaa.gov/data/correlation/oni.data.

2. Add a field called ``ONIEpisode`` to the table, with an integer data type.

3. Use this tool to populate that field. The episodes will be coded for each
   month as normal (0), La Niña (-1), or El Niño (1).

"""))

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesList, 'cls')

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesList, 'oniTable',
    typeMetadata=ListTypeMetadata(elementType=ListTypeMetadata(elementType=AnyObjectTypeMetadata(), minLength=2, maxLength=2), minLength=1),
    description=_(
"""Table of ONI values represented as a list of lists. The outer list contains
the rows of the table. Each inner list contains the field values for a row.

There are two fields:

* ``Date`` (:py:class:`~datetime.datetime`) - the date of the first day of the
  month and year of the climate index value (e.g. 1-Mar-1960). The date
  represents the middle month of the 3-month ONI averaging "season". For
  example, for the year 2000, the December-January-February (DJF) season must
  have the date 1-Jan-2000, while the January-February-March (JFM) season must
  have the date 1-Feb-2000. A given date must only appear once. The ONI
  records must be in ascending date order. There must be no skipped months
  (i.e. the records cannot proceed from 1-Mar-1960 to 1-May-1960, skipping
  1-Apr-1960).

* ``Value`` (:py:class:`float`) - the climate index value.

For example::

    [[datetime.datetime(1950, 1, 1, 0, 0), -1.7],
     [datetime.datetime(1950, 2, 1, 0, 0), -1.5],
     [datetime.datetime(1950, 3, 1, 0, 0), -1.4],
     ...]

"""))

AddResultMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesList, 'outputONITable',
    typeMetadata=ListTypeMetadata(elementType=ListTypeMetadata(elementType=AnyObjectTypeMetadata(), minLength=3, maxLength=3), minLength=1),
    description=_(
"""Copy of the input table with an extra value appended to the end,
e.g.::

    [[datetime.datetime(1950, 1, 1, 0, 0), -1.7, -1],
     [datetime.datetime(1950, 2, 1, 0, 0), -1.5, -1],
     [datetime.datetime(1950, 3, 1, 0, 0), -1.4, -1],
     ...]

The extra value is an integer and can be:

* ``-1`` - this month is a La Niña (cold) episode.

* ``0`` - this month is a normal episode.

* ``1`` - this month is an El Niño (warm) episode.

"""))

# Public method: PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable

AddMethodMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable,
    shortDescription=PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesList.__doc__.Obj.ShortDescription,
    longDescription=PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesList.__doc__.Obj.LongDescription)

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable, 'cls')

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable, 'table',
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    description=_(
"""Time series table of monthly ONI values. The table must have three fields:
a date field, a field that holds the numerical ONI value, and field that will
receive the episode code. Please see documentation for the following
parameters for more information."""))

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable, 'dateField',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Field that contains the date of the ONI value. The field must have a
datetime data type. The records in the table must form a sequence of months,
with the dates for the first day of the month (e.g. 1-Jan-2000, 1-Feb-2000,
1-Mar-2000, ...). The date represents the middle month of the 3-month ONI
averaging "season". For example, for the year 2000, the
December-January-February (DJF) season must have the date 1-Jan-2000, while
the January-February-March (JFM) season must have the date 1-Feb-2000. A given
date must only appear once."""))

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable, 'oniField',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Field that contains the ONI value. The field must have a floating point
data type. If an ONI value is not available for a month, this field should
have the value NULL (if supported by the database) or -9.9 (if NULL is not
supported)."""))

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable, 'episodeField',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Field to receive the ONI episode code. The field must have an integer data
type. It will be calculated as described in the introductory documentation for
this tool and set to one of these values:

* ``-1`` - this month is a La Niña (cold) episode.

* ``0`` - this month is a normal episode.

* ``1`` - this month is an El Niño (warm) episode.

* The value provided for the noDataValue parameter - the ONI episode
  could not be calculated for this month.

"""))

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable, 'noDataValue',
    typeMetadata=IntegerTypeMetadata(canBeNone=True),
    description=_(
"""Value to store in the ONI episode field when the ONI episode cannot be
calculated."""))

# Public method: PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable

AddMethodMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable,
    shortDescription=PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable.__doc__.Obj.ShortDescription,
    longDescription=_(
"""At the time of this writing (in 2024), the NOAA Climate Prediction Center
(CPC) maintained a table of ONI values at
https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ensoyears.shtml.
A copy of these values were provided by the NOAA Physical Sciences Laboratory
(PSL) at https://psl.noaa.gov/data/correlation/oni.data. The CPC provided the
following definition of ONI and ONI episodes:

    "Warm and cold episodes based on a threshold of +/- 0.5 deg C for the
    Oceanic Niño Index (ONI) [3 month running mean of ERSST.v5 SST anomalies
    in the Niño 3.4 region (5N-5S, 120-170W)], based on centered 30-year base
    periods updated every 5 years. For historical purposes cold and warm
    episodes are defined when the threshold is met for a minimum of 5
    consecutive overlapping seasons."

This tool accepts as input a table of monthly ONI values and classifies each
month as a normal, El Niño (warm), or La Niña (cold) episode, according to
CPC's definition. To reproduce CPC's table using data from PSL with this tool,
you can:

1. Use the Create Table from PSL Climate Index Time Series at URL tool to
   create a table from https://psl.noaa.gov/data/correlation/oni.data.

2. Add a field called ONIEpisode to the table, with an integer data type.

3. Use this tool to populate that field. The episodes will be coded for
   each month as normal (``0``), La Niña (``-1``), or El Niño (``1``).

"""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Classify Oceanic Niño Index (ONI) Episodes in Table'),
    arcGISToolCategory=_('Data Products\\NOAA Physical Sciences Laboratory\\Climate Indices'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(PSLClimateIndices.StringToList, 'cls', PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable, 'cls')

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable, 'table',
    typeMetadata=ArcGISTableViewTypeMetadata(mustExist=True),
    description=PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable.__doc__.Obj.GetArgumentByName('table').Description,
    arcGISDisplayName=_('ONI time series table'))

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable, 'dateField',
    typeMetadata=ArcGISFieldTypeMetadata(allowedFieldTypes=['datetime'], mustExist=True),
    description=PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable.__doc__.Obj.GetArgumentByName('dateField').Description,
    arcGISDisplayName=_('Input date field'),
    arcGISParameterDependencies=['table'])

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable, 'oniField',
    typeMetadata=ArcGISFieldTypeMetadata(allowedFieldTypes=['float32', 'float64'], mustExist=True),
    description=PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesTable.__doc__.Obj.GetArgumentByName('oniField').Description,
    arcGISDisplayName=_('Input ONI value field'),
    arcGISParameterDependencies=['table'])

AddArgumentMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable, 'episodeField',
    typeMetadata=ArcGISFieldTypeMetadata(allowedFieldTypes=['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64'], mustExist=True),
    description=_(
"""Field to receive the ONI episode code. The field must have an integer data
type. It will be calculated as described in the introductory documentation for
this tool and set to one of these values:

* ``-1`` - this month is a La Niña (cold) episode.

* ``0`` - this month is a normal episode.

* ``1`` - this month is an El Niño (warm) episode.

* ``NULL`` or ``-9`` - the ONI episode could not be calculated for this month.
  ``NULL`` will be used for databases that support NULL; ``-9`` will be used
  for databases that do not (e.g. DBF tables).

"""),
    arcGISDisplayName=_('Output episode field'),
    arcGISParameterDependencies=['table'])

AddResultMetadata(PSLClimateIndices.ClassifyONIEpisodesInTimeSeriesArcGISTable, 'outputTable',
    typeMetadata=ArcGISTableViewTypeMetadata(),
    description=_(
"""Time series table with the ONI episode field updated."""),
    arcGISDisplayName=_('Output table'))


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['PSLClimateIndices']
