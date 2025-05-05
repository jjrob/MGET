# _DatasetCollectionTree.py - Defines DatasetCollectionTree, a base class
# representing DatasetCollections that are organized as hierarchical trees.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import os
import re

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Logging import ProgressReporter
from ...Types import *

from .. import Dataset, DatasetCollection


class DatasetCollectionTree(DatasetCollection):
    __doc__ = DynamicDocString()

    def _GetPathParsingExpressions(self):
        return self._PathParsingExpressions

    PathParsingExpressions = property(_GetPathParsingExpressions, doc=DynamicDocString())

    def _GetPathCreationExpressions(self):
        return self._PathCreationExpressions

    PathCreationExpressions = property(_GetPathCreationExpressions, doc=DynamicDocString())

    def __init__(self, pathParsingExpressions=None, pathCreationExpressions=None, canSortByDate=True, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize the base class.

        super(DatasetCollectionTree, self).__init__(parentCollection, queryableAttributes, queryableAttributeValues, lazyPropertyValues, cacheDirectory)

        # Validate that either the pathParsingExpressions or
        # pathCreationExpressions or both were specified.

        if pathParsingExpressions is None and pathCreationExpressions is None:
            raise ValueError(_('pathParsingExpressions and pathCreationExpressions are both None. At least one of them must be specified.'))

        # Search the queryable attributes for one with the data type
        # DateTimeTypeMetadata. If we find one, it will require
        # special processing.

        attrs = self.GetQueryableAttributesWithDataType(DateTimeTypeMetadata)
        if len(attrs) > 1:      # Should never happen; CollectibleObject.__init__ prevents it
            raise ValueError(_('This dataset collection has multiple queryable attributes defined with the data type DateTimeTypeMetadata. In order to retrieve the oldest dataset, only one queryable attribute of that type must be defined.'))
        if len(attrs) == 1:
            dateTimeAttr = attrs[0]
        else:
            dateTimeAttr = None

        # If the caller provided path parsing expressions, map them to
        # the queryable attributes. Later, when executing a query,
        # we'll descend down the path parsing expressions as we drill
        # into the hierarchy. As we descend each level, we need to
        # know which queryable attributes have been determined by the
        # levels we've descended.

        adjustedPPE = None

        if pathParsingExpressions is not None:
            attrsForExpr = [None] * len(pathParsingExpressions)
            dateTimeComponents = []
            adjustedPPE = []

            for i in range(len(pathParsingExpressions)):
                if pathParsingExpressions[i].endswith('$'):
                    adjustedPPE.append(pathParsingExpressions[i])
                else:
                    adjustedPPE.append(pathParsingExpressions[i] + '$')

                ppeNames = re.findall(r'\(\?P<(\w+)>[^\)]+\)', adjustedPPE[i], re.IGNORECASE)
                attrsForExpr[i] = []

                for j in range(len(ppeNames)):
                    if ppeNames[j] not in ['Year', 'Month', 'Day', 'DayOfYear', 'Hour', 'Minute', 'Second']:
                        qa = self.GetQueryableAttribute(ppeNames[j])
                        if qa is None:
                            raise ValueError(_('pathParsingExpressions[%(i)i] includes a group named "%(group)s" but there is no queryable attribute with that name defined for this collection or its parents. For each named group in pathParsingExpressions, a there must be a queryable attribute defined for it.') % {'i': i, 'group': ppeNames[j]})
                        attrsForExpr[i].append([ppeNames[j], qa])
                    else:
                        if dateTimeAttr is None:
                            raise ValueError(_('pathParsingExpressions[%(i)i] includes the date/time component "%(group)s" but there is no queryable attribute defined for this dataset collection or its parents with the data type DateTimeTypeMetadata. In order to parse date/time components, a DateTimeTypeMetadata queryable attribute must be defined for the collection.') % {'i': i, 'group': ppeNames[j]})
                        attrsForExpr[i].append([ppeNames[j], dateTimeAttr])
                        if ppeNames[j] not in dateTimeComponents:
                            dateTimeComponents.append(ppeNames[j])

        # If the caller provided path creation expressions but not
        # path parsing expressions, map the path creation expressions
        # to the queryable attributes. Later, when importing datasets,
        # we'll use this mapping to create the destination path for
        # each dataset we import.
        #
        # If the caller specified both path creation expressions and
        # path parsing expressions, just validate that they are
        # compatible with each other.

        if pathCreationExpressions is not None:
            if pathParsingExpressions is None:
                attrsForExpr = [None] * len(pathCreationExpressions)
                dateTimeComponents = []
                dateTimeCompForPCEName = {'y': 'Year', 'Y': 'Year', 'b': 'Month', 'B': 'Month', 'm': 'Month', 'd': 'Day', 'j': 'DayOfYear', 'H': 'Hour', 'M': 'Minute', 'S': 'Second'}
            else:
                validPCENamesForPPEName = {'Year': 'yY', 'Month': 'bBm', 'Day': 'd', 'DayOfYear': 'j', 'Hour': 'H', 'Minute': 'M', 'Second': 'S'}

            for i in range(len(pathCreationExpressions)):
                pceNames = re.findall(r'%%([yYbBmdjHMS])|%\((\w+)\)|%{1,2}[^%]', pathCreationExpressions[i], re.IGNORECASE)
                
                if pathParsingExpressions is None:
                    attrsForExpr[i] = []
                elif len(pceNames) != len(attrsForExpr[i]):
                    raise ValueError(_('pathParsingExpressions[%(i)i] contains %(g1)i named groups but pathCreationExpressions[%(i)i] contains %(g2)i substitution groups. The number of named groups in pathParsingExpressions[%(i)i] must equal the number of substitution groups in pathCreationExpressions[%(i)i].') % {'i': i, 'g1': len(attrsForExpr[i]), 'g2': len(pceNames)})

                for j in range(len(pceNames)):
                    if pceNames[j][0] == '' and pceNames[j][1] == '':       # Ensure that all substitution groups are named groups
                        raise ValueError(_('Substitution group %(j)i (0 is the first group) of pathParsingExpressions[%(i)i] is invalid. It must be a named group or an allowed date/time formatter.') % {'i': i, 'j': j, 'i': i})

                    if pathParsingExpressions is None:
                        if pceNames[j][1] != '':
                            qa = self.GetQueryableAttribute(pceNames[j][1])
                            if qa is None:
                                raise ValueError(_('pathCreationExpressions[%(i)i] includes a group named "%(group)s" but there is no queryable attribute with that name defined for this collection or its parents. For each named group in pathCreationExpressions, there must be a queryable attribute defined for it.') % {'i': i, 'group': pceNames[j][1]})
                            attrsForExpr[i].append([pceNames[j][1], qa])
                        else:
                            if dateTimeAttr is None:
                                raise ValueError(_('pathCreationExpressions[%(i)i] includes the date/time component "%(group)s" but there is no queryable attribute defined for this dataset collection or its parents with the data type DateTimeTypeMetadata. If the path creation expressions include date/time components, a DateTimeTypeMetadata queryable attribute must be defined for the collection.') % {'i': i, 'group': pceNames[j][0]})
                            dateTimeComp = dateTimeCompForPCEName[pceNames[j][0]]
                            attrsForExpr[i].append([dateTimeComp, dateTimeAttr])
                            if dateTimeComp not in dateTimeComponents:
                                dateTimeComponents.append(dateTimeComp)
                    else:
                        if attrsForExpr[i][j][0] not in ['Year', 'Month', 'Day', 'DayOfYear', 'Hour', 'Minute', 'Second']:
                            if pceNames[j][1] == '':
                                raise ValueError(_('pathParsingExpressions[%(i)i] includes a group named "%(group1)s" but the corresponding substitution group in pathCreationExpressions[%(i)i] is the date/time formatter %%%(group2)s. Because "%(group1)s" is not a date/time component, the corresponding substitution group in the corresponding path creation expression cannot be a date/time formatter.') % {'i': i, 'group1': attrsForExpr[i][j][0], 'group2': pceNames[j][0]})
                            if pceNames[j][1] != attrsForExpr[i][j][0]:
                                raise ValueError(_('pathParsingExpressions[%(i)i] includes a group named "%(group1)s" but the corresponding substitution group in pathCreationExpressions[%(i)i] is named "%(group2)s". The two lists of expressions must reference the same queryable attributes in the same order.') % {'i': i, 'group1': attrsForExpr[i][j][0], 'group2': pceNames[j][1]})
                        else:
                            if pceNames[j][0] == '':
                                raise ValueError(_('pathParsingExpressions[%(i)i] includes the date/time component "%(group1)s" but the corresponding substitution group in pathCreationExpressions[%(i)i] is not a date/time formatter (it is a group named "%(group2)s"). Because "%(group1)s" is a date/time component, the corresponding substitution group in the corresponding path creation expression must be a date/time formatter.') % {'i': i, 'group1': attrsForExpr[i][j][0], 'group2': pceNames[j][1]})
                            if pceNames[j][0] not in validPCENamesForPPEName[attrsForExpr[i][j][0]]:
                                raise ValueError(_('pathParsingExpressions[%(i)i] includes the date/time component "%(group1)s" but the corresponding substitution group in pathCreationExpressions[%(i)i] is the wrong date/time formatter (%%%(group2)s). The allowed date/time formatters for "%(group1)s" are: %(allowed)s') % {'i': i, 'group1': attrsForExpr[i][j][0], 'group2': pceNames[j][0], 'allowed': ', '.join(['%%' + c for c in validPCENamesForPPEName[attrsForExpr[i][j][0]]])})

        # If the queryable attributes contains an attribute with the
        # data type DateTimeTypeMetadata, perform additional
        # validation.

        if dateTimeAttr is not None:
            if pathParsingExpressions is not None:
                param = 'pathParsingExpressions'
            else:
                param = 'pathCreationExpressions'

            # Validate that the path expressions contain, at minimum,
            # the Year.

            if 'Year' not in dateTimeComponents:
                raise TypeError(_('This dataset collection includes a queryable attribute with the data type DateTimeTypeMetadata but %(param)s does not include a path component for the year.') % {'param': param})

            # Validate that if Day is specified, Month is also
            # specified.

            if 'Day' in dateTimeComponents and 'Month' not in dateTimeComponents:
                raise TypeError(_('%(param)s includes a path component for the day of the month but not the month. This is not allowed. Please add an expression for the month in addition to the day of the month.') % {'param': param})

        # Initialize our properties.
        
        self._PathParsingExpressions = adjustedPPE
        self._PathCreationExpressions = pathCreationExpressions
        self._AttrsForExpr = attrsForExpr
        self._DateTimeComponents = dateTimeComponents
        self._CanSortByDate = canSortByDate

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):
        if self.PathParsingExpressions is None:
            raise RuntimeError(_('Cannot query %(dn)s for datasets because the DatasetCollectionTree representing it was not instantiated with path parsing expressions.') % {'dn': self.DisplayName})
        return self._QueryRecursive(parsedExpression, progressReporter, options, [], 0, parentAttrValues, {}, 'normal')

    def _QueryRecursive(self, parsedExpression, progressReporter, options, pathComponents, depth, parentAttrValues, parsedAttrValues, queryType='normal'):

        # Extract key/value pairs from options that are intended for
        # us, so we do not pass them through to _ConstructFoundObject.

        closeDatasets = False
        getQueryableAttributesOnly = False

        if options is not None:
            constructOptions = {}
            constructOptions.update(options)
            
            if 'closeDatasets' in options:
                closeDatasets = bool(options['closeDatasets'])
                del constructOptions['closeDatasets']
                
            if 'getQueryableAttributesOnly' in options:
                getQueryableAttributesOnly = bool(options['getQueryableAttributesOnly'])
                del constructOptions['getQueryableAttributesOnly']
                if getQueryableAttributesOnly and queryType != 'normal':
                    raise RuntimeError('Programming error in this tool: DatasetCollectionTree._QueryRecursive(): queryType must be \'normal\' when getQueryableAttributesOnly is True. Please contact the author of this tool for assistance.')
        else:
            constructOptions = options

        # Enumerate the contents of the path.

        contents = self._ListContents(pathComponents)

        # If this is an 'oldest' or 'newest' query (rather than just a
        # 'normal' query), our objective is to return just one
        # dataset: the oldest or newest. To make this efficient, when
        # the path component at this level contains an element of the
        # date or time, sort the contents of the path in ascending or
        # descending order. Later, as we're iterating through the
        # contents of the path, we'll stop once we have found a single
        # dataset.

        if queryType != 'normal':
            sortByDate = False
            for [name, attr] in self._AttrsForExpr[depth]:
                if isinstance(attr.DataType, DateTimeTypeMetadata):
                    sortByDate = True
                    break

            if sortByDate:
                if queryType == 'oldest':
                    contents.sort()
                else:
                    contents.sort(reverse=True)

        # Iterate through the contents of the path, testing each item
        # against the query expression.

        datasetsFound = []
        
        for component in contents:

            # Parse the queryable attribute values derived from this
            # path component. If the component does not match the
            # regular expression for this level in the hierarchy, go
            # on to the next one.

            match = re.match(self._PathParsingExpressions[depth], component, re.IGNORECASE)
            if match is None:

                # The following message generates too much output for
                # certain collections. Uncomment it only when
                # necessary.

                #self._LogDebug(_('%(class)s 0x%(id)016X: Skipping path component "%(comp)s"; it does not match regular expression "%(re)s".'), {'class': self.__class__.__name__, 'id': id(self), 'comp': component, 're': self._PathParsingExpressions[depth]})

                continue
            
            componentAttrValues = {}
            for [name, attr] in self._AttrsForExpr[depth]:
                value = match.group(name)
                try:
                    if isinstance(attr.DataType, UnicodeStringTypeMetadata):
                        componentAttrValues[attr.Name] = str(value)
                    elif isinstance(attr.DataType, IntegerTypeMetadata):
                        componentAttrValues[attr.Name] = int(value)
                    elif isinstance(attr.DataType, FloatTypeMetadata):
                        componentAttrValues[attr.Name] = float(value)
                    else:
                        componentAttrValues[name] = int(value)    # Add datetime components as integers
                except Exception as e:
                    self._LogDebug(_('%(class)s 0x%(id)016X: Skipping path component "%(comp)s"; failed to parse queryable attribute %(attr)s from the string %(s)s due to %(e)s: %(msg)s.'), {'class': self.__class__.__name__, 'id': id(self), 'comp': component, 'attr': attr.Name, 's': repr(value), 'e': e.__class__.__name__, 'msg': e})
                    componentAttrValues = None
                    break

            if componentAttrValues is None:
                continue

            componentAttrValues.update(parsedAttrValues)

            # If the path parse expressions parse a datetime and we
            # have parsed all of the components specified in the
            # expressions, build a datetime value and add it to the
            # attribute values.

            if len(self._DateTimeComponents) > 0 and 'DateTime' not in componentAttrValues:
                foundAll = True
                for dtComp in self._DateTimeComponents:
                    if dtComp not in componentAttrValues and not (dtComp in ['Month', 'Day'] and 'DayOfYear' in componentAttrValues or dtComp == 'DayOfYear' and 'Month' in componentAttrValues and 'Day' in componentAttrValues):
                        foundAll = False
                        break

                if foundAll:
                    year = componentAttrValues['Year']
                    month = 1
                    day = 1
                    hour = 0
                    minute = 0
                    second = 0
                    
                    if 'Month' in componentAttrValues:
                        month = componentAttrValues['Month']
                    
                    if 'Day' in componentAttrValues:
                        day = componentAttrValues['Day']
                    
                    if 'Hour' in componentAttrValues:
                        hour = componentAttrValues['Hour']
                    
                    if 'Minute' in componentAttrValues:
                        minute = componentAttrValues['Minute']
                    
                    if 'Second' in componentAttrValues:
                        second = componentAttrValues['Second']

                    try:
                        dt = datetime.datetime(year, month, day, hour, minute, second)
                    except Exception as e:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Skipping path component "%(comp)s"; failed to construct a datetime instance from values [%(year)s, %(month)s, %(day)s, %(hour)s, %(minute)s, %(second)s] due to %(e)s: %(msg)s.'), {'class': self.__class__.__name__, 'id': id(self), 'comp': component, 'year': repr(year), 'month': repr(month), 'day': repr(day), 'hour': repr(hour), 'minute': repr(minute), 'second': repr(second), 'e': e.__class__.__name__, 'msg': e})
                        continue
                        
                    if 'DayOfYear' in componentAttrValues and not ('Month' in componentAttrValues and 'Day' in componentAttrValues):
                        try:
                            dt += datetime.timedelta(days=componentAttrValues['DayOfYear'] - 1)
                        except Exception as e:
                            self._LogDebug(_('%(class)s 0x%(id)016X: Skipping path component "%(comp)s"; failed to add datetime.timedelta(days=%(dayOfYear)s - 1) to the datetime %(dt)s.'), {'class': self.__class__.__name__, 'id': id(self), 'comp': component, 'dayOfYear': repr(componentAttrValues['DayOfYear']), 'dt': repr(dt)})
                            continue

                    offsetInDays = self.GetLazyPropertyValue('TOffsetFromParsedTime')
                    if offsetInDays is not None:
                        dt += datetime.timedelta(offsetInDays)

                    componentAttrValues['DateTime'] = dt
                    componentAttrValues['Year'] = dt.year
                    componentAttrValues['Month'] = dt.month
                    componentAttrValues['Day'] = dt.day
                    componentAttrValues['Hour'] = dt.hour
                    componentAttrValues['Minute'] = dt.minute
                    componentAttrValues['Second'] = dt.second
                    componentAttrValues['DayOfYear'] = int(dt.strftime('%j'))

            # If there are any queryable attributes defined that are
            # derived from the values we have parsed so far, derive
            # their values now.

            allAttrValues = {}
            allAttrValues.update(parentAttrValues)
            allAttrValues.update(componentAttrValues)

            obj = self
            while obj is not None:
                if obj._QueryableAttributes is not None:
                    for attr in obj._QueryableAttributes:
                        if attr.DerivedFromAttr is not None and attr.Name not in allAttrValues and attr.DerivedFromAttr in allAttrValues:
                            if attr.DerivedValueMap is not None:
                                if allAttrValues[attr.DerivedFromAttr] in attr.DerivedValueMap:
                                    allAttrValues[attr.Name] = attr.DerivedValueMap[allAttrValues[attr.DerivedFromAttr]]
                            else:
                                value = attr.DerivedValueFunc(allAttrValues, allAttrValues[attr.DerivedFromAttr])
                                if value is not None:
                                    allAttrValues[attr.Name] = value
                obj = obj.ParentCollection

            # Test whether this path component matches the query
            # expression. This will return True or False, or None,
            # indicating that the result of the query expression is
            # indeterminate because it depends on the values of
            # queryable attributes that have not been obtained yet.

            if parsedExpression is not None:
                try:
                    result = parsedExpression.eval(allAttrValues)

                    # If the result was False, indicating that there
                    # are enough queryable attributes whose values are
                    # known to conclude that the path component does
                    # not match query expression, and the path parse
                    # expressions parse some date/time parts, and we
                    # have not parsed them all yet, and we have a lazy
                    # property named TOffsetFromParsedTime, it means
                    # that the date/time values we have parsed so far
                    # might not represent the ultimate values when
                    # parsing is complete.
                    #
                    # For example, consider the case of MODIS
                    # nighttime monthly SST files. In the directory
                    # structure, files are grouped in subdirectories
                    # by year. But the time range of a given file is
                    # 12:00:00 on the last day of the previous month
                    # to 12:00:00 of the last day of the month of the
                    # file. Therefore, files for the month of January
                    # actually begin in the previous year, e.g. the
                    # January 2004 file actually runs from 31-Dec-2003
                    # 12:00:00 to 31-Jan-2004 12:00:00. This is
                    # problematic. A query for "Year = 2003" should
                    # return this file (and not the January 2003
                    # file). We should descend into the 2004 directory
                    # in order to obtain the file that starts in 2003,
                    # even though the 2004 directory will resulting in
                    # us parsing Year as 2004 and therefore not
                    # matching the "Year = 2003" expression.
                    #
                    # To work around this, evaluate the expression
                    # again, adjusting the date/time parts we've
                    # parsed so far by the TOffsetFromParsedTime, to
                    # see if the result changes from False to None. If
                    # so, it means we should descend into this part of
                    # the tree because it is theoretically possible
                    # that the items within it could end up matching.
                    #
                    # This is very complicated, but at this time I do
                    # not know of a better way to handle datasets such
                    # as MODIS that do not include the time values in
                    # their file names.

                    if result == False and len(self._DateTimeComponents) > 0 and 'DateTime' not in allAttrValues and self.GetLazyPropertyValue('TOffsetFromParsedTime'):
                        if 'Year' in allAttrValues:
                            attrValuesToTry = {}
                            attrValuesToTry.update(allAttrValues)
                            tryPreviousYear = True
                            
                            if 'DayOfYear' in attrValuesToTry:
                                attrValuesToTry['DayOfYear'] = int((datetime.datetime(attrValuesToTry['Year'], 1, 1) + datetime.timedelta(days=attrValuesToTry['DayOfYear'] - 2)).strftime('%j'))
                                result = parsedExpression.eval(attrValuesToTry)
                                tryPreviousYear = result == False and attrValuesToTry['DayOfYear'] > allAttrValues['DayOfYear']

                            elif 'Month' in attrValuesToTry:
                                tryPreviousMonth = True
                                
                                if 'Day' in attrValuesToTry:    # It should be rare that Year, Month, Day has been parsed by DateTime has not been; it implies that Hour still must be parsed
                                    attrValuesToTry['Day'] = (datetime.datetime(attrValuesToTry['Year'], attrValuesToTry['Month'], attrValuesToTry['Day']) - datetime.timedelta(1)).day
                                    if attrValuesToTry['Day'] < allAttrValues['Day']:
                                        result = parsedExpression.eval(attrValuesToTry)
                                        tryPreviousMonth = False
                                        
                                if tryPreviousMonth:
                                    if attrValuesToTry['Month'] > 1:
                                        attrValuesToTry['Month'] -= 1
                                        result = parsedExpression.eval(attrValuesToTry)
                                        tryPreviousYear = False
                                    else:
                                        attrValuesToTry['Month'] = 12

                            if tryPreviousYear:
                                attrValuesToTry['Year'] -= 1
                                result = parsedExpression.eval(attrValuesToTry)
                        
                except Exception as e:
                    continue
            else:
                result = True

            if result is None or result:
                self._LogDebug(_('%(class)s 0x%(id)016X: Query result for path component "%(comp)s": %(result)s'), {'class': self.__class__.__name__, 'id': id(self), 'comp': component, 'result': repr(result)})

            # If we are still descending the path components (i.e.
            # this is not the deepest one), and we got a True or None,
            # recursively evaluate this component.

            if depth < len(self._PathParsingExpressions) - 1:
                if result or result is None:
                    datasetsFound.extend(self._QueryRecursive(parsedExpression, progressReporter, options, pathComponents + [component], depth + 1, parentAttrValues, componentAttrValues, queryType))

            # We have reached the deepest level of the path component
            # hierarchy. If the caller requested queryable attributes
            # only and the result was True (the path component matches
            # the query expression), then add this path and its
            # queryable attributes to the list to return.

            elif getQueryableAttributesOnly:
                if result:
                    datasetsFound.append([pathComponents + [component], allAttrValues])
                    if progressReporter is not None:
                        progressReporter.ReportProgress()

            # Otherwise (the caller wants full Dataset instances), if
            # the result was True (it matches) or None (we don't know
            # if it matches), construct an object for it. If that
            # object is a Dataset and the result was True, add it to
            # our list of datasets; if the result was None, don't add
            # it. If that object is a DatasetCollection, submit our
            # query to it to retreive the matching datasets.

            elif result or result is None:
                obj = self._ConstructFoundObject(pathComponents + [component], componentAttrValues, constructOptions)
                if obj is not None:
                    if isinstance(obj, Dataset):
                        if result:
                            datasetsFound.append(obj)
                            if closeDatasets:
                                obj.Close()
                            if progressReporter is not None:
                                progressReporter.ReportProgress()
                        else:
                            del obj
                    else:
                        datasetsFound.extend(obj._QueryDatasets(parsedExpression, progressReporter, options, allAttrValues))
                        if closeDatasets:
                            obj.Close()

            # If this is an 'oldest' or 'newest' query and the path
            # component at this level includes an element of the date
            # or time and we got some datasets, break out of the loop.
            
            if queryType != 'normal' and sortByDate and len(datasetsFound) > 0:
                break

        # If this is an 'oldest' or 'newest' query, walk through the
        # datasets we found and return the oldest or newest one. If
        # multiple datasets have the same oldest or newest date and
        # time, we pick whichever one happened to come first.

        if queryType != 'normal' and len(datasetsFound) > 0:
            best = 0
            bestDateTime = datasetsFound[0].GetQueryableAttributeValue('DateTime')
            
            for i in range(1, len(datasetsFound)):
                if queryType == 'oldest':
                    if datasetsFound[i].GetQueryableAttributeValue('DateTime') < bestDateTime:
                        best = i
                elif datasetsFound[i].GetQueryableAttributeValue('DateTime') > bestDateTime:
                    best = i

            datasetsFound = [datasetsFound[best]]

        # Return the datasets we found.

        return datasetsFound

    def _GetOldestDataset(self, parsedExpression, options, parentAttrValues, dateTimeAttrName):
        if self._CanSortByDate:
            datasetsFound = self._QueryRecursive(parsedExpression, None, options, [], 0, parentAttrValues, {}, 'oldest')
            if len(datasetsFound) > 0:
                return datasetsFound[0]
            return None

        return super(DatasetCollectionTree, self)._GetOldestDataset(parsedExpression, options, parentAttrValues, dateTimeAttrName)

    def _GetNewestDataset(self, parsedExpression, options, parentAttrValues, dateTimeAttrName):
        if self._CanSortByDate:
            datasetsFound = self._QueryRecursive(parsedExpression, None, options, [], 0, parentAttrValues, {}, 'newest')
            if len(datasetsFound) > 0:
                return datasetsFound[0]
            return None

        return super(DatasetCollectionTree, self)._GetNewestDataset(parsedExpression, options, parentAttrValues, dateTimeAttrName)

    def _ImportDatasets(self, datasets, mode, reportProgress, options):
        if self.PathCreationExpressions is None:
            raise RuntimeError(_('Cannot import datasets into %(dn)s because the DatasetCollectionTree representing it was not instantiated with path creation expressions.') % {'dn': self.DisplayName})

        if reportProgress:
            self._LogInfo(_('Importing %(count)i datasets into %(dn)s with mode "%(mode)s".') % {'count': len(datasets), 'dn': self.DisplayName, 'mode': mode})
        else:
            self._LogDebug(_('%(class)s 0x%(id)016X: Importing %(count)i datasets into %(dn)s with mode "%(mode)s".') % {'class': self.__class__.__name__, 'id': id(self), 'count': len(datasets), 'dn': self.DisplayName, 'mode': mode})

        # Build a dictionary mapping destination paths to the source
        # datasets that should be imported to those paths. In many
        # cases, as when we are a DirectoryTree of GDALDatasets, each
        # source dataset will be imported to a unique destination
        # path. In some cases, as when we are a DirectoryTree of
        # NetCDFFiles, several source datasets may be imported to each
        # unique destination path.

        pathComponentsForPath = {}
        datasetsForPath = {}

        for dataset in datasets:

            # First, build a dictionary that maps the names of
            # attributes that appear in our path parsing and path
            # creation expressions to values of those attributes from
            # the source dataset. Fail if the source dataset does not
            # have all of these attributes.

            attrValues = {}
            gotDateTime = False

            for attrs in self._AttrsForExpr:
                for [name, attr] in attrs:
                    if issubclass(attr.DataType.__class__, DateTimeTypeMetadata):
                        attrName = 'DateTime'
                        gotDateTime = True
                    else:
                        attrName = attr.Name
                    if attrName not in attrValues:
                        attrValue = dataset.GetQueryableAttributeValue(attrName)
                        if attrValue is None:
                            raise ValueError(_('%(dn1)s does not have a queryable attribute named %(name)s. In order to import this dataset into %(dn2)s, it must have that queryable attribute.') % {'dn1': dataset.DisplayName, 'name': attrName, 'dn2': self.DisplayName})
                        
                        if attrName == 'DateTime':
                            offsetInDays = dataset.GetLazyPropertyValue('TOffsetFromParsedTime')
                            if offsetInDays is not None:
                                attrValue = datetime.datetime(attrValue.year, attrValue.month, attrValue.day, attrValue.hour, attrValue.minute, attrValue.second, attrValue.microsecond) - datetime.timedelta(offsetInDays)
                            
                        attrValues[attrName] = attrValue

            # Build the components of the destination path.

            pathComponents = []
            for expr in self._PathCreationExpressions:
                comp = expr % attrValues
                if gotDateTime:
                    comp = str(attrValues['DateTime'].strftime(comp))
                pathComponents.append(comp)

            # Add this path and source dataset to our dictionaries.

            path = os.path.join(*pathComponents)

            if path not in pathComponentsForPath:
                pathComponentsForPath[path] = pathComponents

            if path not in datasetsForPath:
                datasetsForPath[path] = []
            datasetsForPath[path].append(dataset)

        # Sort the destination paths so we always process them in the
        # same order.

        paths = list(pathComponentsForPath.keys())
        paths.sort()

        # If the mode is 'add', check for existing datasets.

        if mode == 'add':
            if reportProgress:
                self._LogInfo(_('Checking for existing destination datasets.'))
                progressReporter = ProgressReporter(progressMessage1=_('Still checking: %(elapsed)s elapsed, %(opsCompleted)i datasets checked, %(perOp)s per dataset, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                                    completionMessage=_('Finished checking: %(elapsed)s elapsed, %(opsCompleted)i datasets checked, %(perOp)s per dataset.'),
                                                    abortedMessage=_('Processing stopped before all datasets were checked: %(elapsed)s elapsed, %(opsCompleted)i datasets checked, %(perOp)s per dataset, %(opsIncomplete)i datasets not checked.'),
                                                    loggingChannel=DatasetCollection._LoggingChannel,
                                                    arcGISProgressorLabel=_('Checking for existing datasets'))
                progressReporter.Start(len(datasets))
            else:
                self._LogDebug(_('%(class)s 0x%(id)016X: Checking for existing destination datasets.') % {'class': self.__class__.__name__, 'id': id(self)})
                progressReporter = None

            try:
                i = 0
                datasetsToAdd = 0
                while i < len(paths):
                    self._RemoveExistingDatasetsFromList(pathComponentsForPath[paths[i]], datasetsForPath[paths[i]], progressReporter)
                    if len(datasetsForPath[paths[i]]) > 0:
                        datasetsToAdd += len(datasetsForPath[paths[i]])
                        i += 1
                    else:
                        del paths[i]
            finally:
                if reportProgress:
                    progressReporter.Stop()

            if datasetsToAdd <= 0:
                if reportProgress:
                    self._LogInfo(_('All %(count)i destination datasets already exist. No datasets will be imported.') % {'count': len(datasets)})
                else:
                    self._LogDebug(_('%(class)s 0x%(id)016X: All %(count)i destination datasets already exist. No datasets will be imported.') % {'class': self.__class__.__name__, 'id': id(self), 'count': len(datasets)})
                return

            if reportProgress:
                self._LogInfo(_('%(existing)i destination datasets already exist. Importing %(new)i datasets.') % {'existing': len(datasets) - datasetsToAdd, 'new': datasetsToAdd})
            else:
                self._LogDebug(_('%(class)s 0x%(id)016X: %(existing)i destination datasets already exist. Importing %(new)i datasets.') % {'class': self.__class__.__name__, 'id': id(self), 'existing': len(datasets) - datasetsToAdd, 'new': datasetsToAdd})
        else:
            datasetsToAdd = len(datasets)

        # Iterate through the paths, importing the datasets for each
        # one.

        if reportProgress:
            progressReporter = ProgressReporter(progressMessage1=_('Import in progress: %(elapsed)s elapsed, %(opsCompleted)i datasets imported, %(perOp)s per dataset, %(opsRemaining)i remaining, estimated completion time: %(etc)s.'),
                                                completionMessage=_('Import complete: %(elapsed)s elapsed, %(opsCompleted)i datasets imported, %(perOp)s per dataset.'),
                                                abortedMessage=_('Import stopped before all datasets were imported: %(elapsed)s elapsed, %(opsCompleted)i datasets imported, %(perOp)s per dataset, %(opsIncomplete)i datasets not imported.'),
                                                loggingChannel=DatasetCollection._LoggingChannel,
                                                arcGISProgressorLabel=_('Importing %(count)i datasets') % {'count': datasetsToAdd})
            progressReporter.Start(datasetsToAdd)
        else:
            progressReporter = None

        try:
            for path in paths:
                self._ImportDatasetsToPath(pathComponentsForPath[path], datasetsForPath[path], mode, progressReporter, options)
        finally:
            if reportProgress:
                progressReporter.Stop()

    # Private methods that the derived class should override.

    def _ListContents(self, pathComponents):
        raise NotImplementedError(_('The _ListContents method of class %s has not been implemented.') % self.__class__.__name__)

    def _ConstructFoundObject(self, pathComponents, attrValues, options):
        raise NotImplementedError(_('The _ConstructFoundObject method of class %s has not been implemented.') % self.__class__.__name__)

    def _RemoveExistingDatasetsFromList(self, pathComponents, datasets, progressReporter):
        raise NotImplementedError(_('The _RemoveExistingDatasetsFromList method of class %s has not been implemented.') % self.__class__.__name__)

    def _ImportDatasetsToPath(self, pathComponents, sourceDatasets, mode, progressReporter, options):
        raise NotImplementedError(_('The _ImportDatasetsToPath method of class %s has not been implemented.') % self.__class__.__name__)


###############################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Collections instead.
###############################################################################################

__all__ = []
