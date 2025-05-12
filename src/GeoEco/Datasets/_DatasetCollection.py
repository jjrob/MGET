# _DatasetCollection.py - Defines DatasetCollection, a queryable collection of
# Dataset instances.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import re

from ..DynamicDocString import DynamicDocString
from ..Exceptions import GeoEcoError
from ..Internationalization import _
from ..Logging import ProgressReporter
from ..Types import DateTimeTypeMetadata

from ._CollectibleObject import CollectibleObject


class DatasetCollection(CollectibleObject):
    __doc__ = DynamicDocString()

    def _GetCacheDirectory(self):
        return self._CacheDirectory

    def _SetCacheDirectory(self, value):
        self.__doc__.Obj.ValidatePropertyAssignment()
        self._CacheDirectory = value

    CacheDirectory = property(_GetCacheDirectory, _SetCacheDirectory, doc=DynamicDocString())

    def QueryDatasets(self, expression=None, reportProgress=True, **options):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Parse the query.

        parsedExpression, parentAttrValues = self._PrepareQuery(expression)

        # Log a message and start a progress reporter, if requested.

        if parsedExpression is not None:
            if reportProgress:
                self._LogInfo(_('Querying %(dn)s for datasets matching the expression "%(expr)s".'), {'dn': self.DisplayName, 'expr': expression})
            else:
                self._LogDebug(_('%(class)s 0x%(id)016X: Executing query for datasets matching expression: "%(expr)s"'), {'class': self.__class__.__name__, 'id': id(self), 'expr': expression})
        else:
            if reportProgress:
                self._LogInfo(_('Querying %(dn)s.'), {'dn': self.DisplayName})
            else:
                self._LogDebug(_('%(class)s 0x%(id)016X: Executing query for all datasets.'), {'class': self.__class__.__name__, 'id': id(self)})

        if reportProgress:
            progressReporter = ProgressReporter(progressMessage2=_('Query in progress: %(elapsed)s elapsed, %(opsCompleted)i datasets found so far, %(perOp)s per dataset.'),
                                                completionMessage=_('Query complete: %(elapsed)s elapsed, %(opsCompleted)i datasets found, %(perOp)s per dataset.'),
                                                loggingChannel=DatasetCollection._LoggingChannel)
            progressReporter.Start()
        else:
            progressReporter = None

        # Execute the query.

        try:
            datasets = self._QueryDatasets(parsedExpression, progressReporter, options, parentAttrValues)
        finally:
            if reportProgress:
                progressReporter.Stop()

        if not reportProgress:
            self._LogDebug(_('%(class)s 0x%(id)016X: Query complete. Returning %(i)i datasets.'), {'class': self.__class__.__name__, 'id': id(self), 'i': len(datasets)})

        # Return successfully.

        return datasets

    def GetOldestDataset(self, expression=None, **options):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Validate that the collection has a queryable attribute with
        # data type DateTimeTypeMetadata.

        attrs = self.GetQueryableAttributesWithDataType(DateTimeTypeMetadata)
        if len(attrs) <= 0:
            raise ValueError(_('This dataset collection does not have a queryable attribute defined with the data type DateTimeTypeMetadata. In order to retrieve the oldest dataset, a queryable attribute of that type must be defined.'))
        if len(attrs) > 1:      # Should never happen; CollectibleObject.__init__ prevents it
            raise ValueError(_('This dataset collection has multiple queryable attributes defined with the data type DateTimeTypeMetadata. In order to retrieve the oldest dataset, only one queryable attribute of that type must be defined.'))

        dateTimeAttrName = attrs[0].Name

        # Get the dataset.

        parsedExpression, parentAttrValues = self._PrepareQuery(expression)

        if parsedExpression is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Getting the oldest dataset matching expression: "%(expr)s"'), {'class': self.__class__.__name__, 'id': id(self), 'expr': expression})
        else:
            self._LogDebug(_('%(class)s 0x%(id)016X: Getting the oldest dataset.'), {'class': self.__class__.__name__, 'id': id(self)})

        dataset = self._GetOldestDataset(parsedExpression, options, parentAttrValues, dateTimeAttrName)

        if dataset is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: The oldest dataset is dated %(dt)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dt': dataset.GetQueryableAttributeValue(dateTimeAttrName).strftime('%Y-%m-%d %H:%M:%S')})
        elif parsedExpression is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: No datasets were found in this collection that match expression: "%(expr)s"'), {'class': self.__class__.__name__, 'id': id(self), 'expr': expression})
        else:
            self._LogDebug(_('%(class)s 0x%(id)016X: No datasets were found in this collection.'), {'class': self.__class__.__name__, 'id': id(self)})

        return dataset

    def GetNewestDataset(self, expression=None, **options):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Validate that the collection has a queryable attribute with
        # data type DateTimeTypeMetadata.

        attrs = self.GetQueryableAttributesWithDataType(DateTimeTypeMetadata)
        if len(attrs) <= 0:
            raise ValueError(_('This dataset collection does not have a queryable attribute defined with the data type DateTimeTypeMetadata. In order to retrieve the newest dataset, a queryable attribute of that type must be defined.'))
        if len(attrs) > 1:      # Should never happen; CollectibleObject.__init__ prevents it
            raise ValueError(_('This dataset collection has multiple queryable attributes defined with the data type DateTimeTypeMetadata. In order to retrieve the newest dataset, only one queryable attribute of that type must be defined.'))

        dateTimeAttrName = attrs[0].Name

        # Get the dataset.

        parsedExpression, parentAttrValues = self._PrepareQuery(expression)

        if parsedExpression is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Getting the newest dataset matching expression: "%(expr)s"'), {'class': self.__class__.__name__, 'id': id(self), 'expr': expression})
        else:
            self._LogDebug(_('%(class)s 0x%(id)016X: Getting the newest dataset.'), {'class': self.__class__.__name__, 'id': id(self)})

        dataset = self._GetNewestDataset(parsedExpression, options, parentAttrValues, dateTimeAttrName)

        if dataset is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: The newest dataset is dated %(dt)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dt': dataset.GetQueryableAttributeValue(dateTimeAttrName).strftime('%Y-%m-%d %H:%M:%S')})
        elif parsedExpression is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: No datasets were found in this collection that match expression: "%(expr)s"'), {'class': self.__class__.__name__, 'id': id(self), 'expr': expression})
        else:
            self._LogDebug(_('%(class)s 0x%(id)016X: No datasets were found in this collection.'), {'class': self.__class__.__name__, 'id': id(self)})

        return dataset

    def ImportDatasets(self, datasets, mode='Add', reportProgress=True, **options):
        self.__doc__.Obj.ValidateMethodInvocation()

        # If the caller provided an empty list, return now.

        if len(datasets) <= 0:
            if reportProgress:
                self._LogInfo(_('There are no datasets to import.'))
            return

        # Call the derived class to import the datasets.

        try:
            self._ImportDatasets(datasets, mode.lower(), reportProgress, options)

        # Ensure all of the datasets are closed. The derived class
        # should be closing them as it goes along, but we do it here
        # as an additional convenince to the derived class.

        finally:
            for dataset in datasets:
                dataset.Close()

    def __init__(self, parentCollection=None, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()
        super(DatasetCollection, self).__init__(parentCollection, queryableAttributes, queryableAttributeValues, lazyPropertyValues)
        self._CacheDirectory = cacheDirectory

    @classmethod
    def _GetQueryExpressionParser(cls):

        # If we have not built the parser yet, build it using the
        # pyparsing module.
        
        if not hasattr(DatasetCollection, '_QueryExpressionParser'):

            # Define helper classes and functions used to evaluate the
            # parsed expression.
            #
            # Many thanks to Paul McGuire for pyparsing examples that
            # inspired this code, particularly eval_arith.py.

            class _EvalLiteral(object):
                def __init__(self, tokens):
                    self.value = tokens[0]
                    
                def eval(self, valuesDict=None):
                    if self.value[0] in '0123456789.':
                        if '.' in self.value or 'e' in self.value.lower():
                            return float(self.value)
                        return int(self.value)
                    
                    if self.value[0] == '"':
                        return self.value[1:-1].replace('""', '"')
                    
                    if self.value[0] == "'":
                        return self.value[1:-1].replace("''", "'")

                    if self.value[0] == '#':
                        if len(self.value) == 21:
                            return datetime.datetime(int(self.value[1:5]), int(self.value[6:8]), int(self.value[9:11]), int(self.value[12:14]), int(self.value[15:17]), int(self.value[18:20]))     # The form of #YYYY-mm-dd HH:MM:SS#
                        return datetime.datetime(int(self.value[1:5]), int(self.value[6:8]), int(self.value[9:11]))     # The form of #YYYY-mm-dd#

                    if self.value.lower() in ['false', 'true']:
                        return self.value[0] in ['t', 'T']

                    raise ValueError(_('The token %(token)s cannot be parsed as a literal value.') % {'token': token[0]})

            class _EvalVariable(object):
                def __init__(self, tokens):
                    self.variable = tokens[0]
                    
                def eval(self, valuesDict=None):
                    if valuesDict is not None and self.variable in valuesDict:
                        return valuesDict[self.variable]
                    return None

            class _EvalSignOp(object):
                def __init__(self, tokens):
                    self.sign, self.value = tokens[0]
                    
                def eval(self, valuesDict=None):
                    val = self.value.eval(valuesDict)
                    if val is None:
                        return None
                    if self.sign == '-':
                        return -1 * val
                    return val

            def _OperatorOperands(tokenlist):
                it = iter(tokenlist)
                while 1:
                    try:
                        yield (next(it), next(it))
                    except StopIteration:
                        break

            class _EvalMultOp(object):
                def __init__(self, tokens):
                    self.value = tokens[0]

                def eval(self, valuesDict=None):
                    prod = self.value[0].eval(valuesDict)
                    if prod is None:
                        return None
                    for op, val in _OperatorOperands(self.value[1:]):
                        val = val.eval(valuesDict)
                        if val is None:
                            return None
                        elif op == '*':
                            prod *= val
                        elif op == '/':
                            prod /= val
                    return prod

            class _EvalAddOp(object):
                def __init__(self, tokens):
                    self.value = tokens[0]

                def eval(self, valuesDict=None):
                    sum = self.value[0].eval(valuesDict)
                    if sum is None:
                        return None
                    for op, val in _OperatorOperands(self.value[1:]):
                        val = val.eval(valuesDict)
                        if val is None:
                            return None
                        elif op == '+':
                            sum += val
                        elif op == '-':
                            sum -= val
                    return sum

            class _EvalLiteralList(object):
                def __init__(self, tokens):
                    self.tokens = tokens
                    
                def eval(self, valuesDict=None):
                    return [v.eval(valuesDict) for v in self.tokens[1:-1]]

            class _EvalComparisonOp(object):
                def __init__(self, tokens):
                    self.tokens = tokens

                def eval(self, valuesDict=None):
                    val1 = self.tokens[0].eval(valuesDict)
                    if val1 is None:
                        return None

                    if len(self.tokens) == 3:
                        val2 = self.tokens[2].eval(valuesDict)
                    else:
                        val2 = self.tokens[3].eval(valuesDict)
                    if val2 is None:
                        return None

                    if self.tokens[1] == '=':
                        return val1 == val2
                    if self.tokens[1] == '<':
                        return val1 < val2
                    if self.tokens[1] == '>':
                        return val1 > val2
                    if self.tokens[1] == '<=':
                        return val1 <= val2
                    if self.tokens[1] == '>=':
                        return val1 >= val2
                    if self.tokens[1] == '<>':
                        return val1 != val2

                    if self.tokens[1].lower() == 'matches':
                        if not isinstance(val1, str):
                            raise TypeError(_('%(value)s is not permitted as the left-hand operand of the matches operator; both operands of the matches operator must be strings.') % {'value': repr(val1)})
                        if not isinstance(val2, str):
                            raise TypeError(_('%(value)s is not permitted as the right-hand operand of the matches operator; both operands of the matches operator must be strings.') % {'value': repr(val2)})
                        return re.match(val2, val1, re.IGNORECASE) is not None

                    if self.tokens[1].lower() == 'in':
                        return val1 in val2

                    if self.tokens[1].lower() == 'not' and self.tokens[2].lower() == 'in':
                        return val1 not in val2

                    raise RuntimeError(_('Unknown comparison operator "%(op)s".') % {'op': self.tokens[1]})

            class _EvalNotOp(object):
                def __init__(self, tokens):
                    self.value = tokens[0]

                def eval(self, valuesDict=None):
                    val = self.value[1].eval(valuesDict)
                    if val is None:
                        return None
                    return not val

            class _EvalAndOp(object):
                def __init__(self, tokens):
                    self.value = tokens[0]

                def eval(self, valuesDict=None):
                    val = self.value[0].eval(valuesDict)
                    if val is not None and not val:
                        return False
                    gotNone = val is None
                    for op, val in _OperatorOperands(self.value[1:]):
                        val = val.eval(valuesDict)
                        if val is not None and not val:
                            return False
                        gotNone = gotNone or val is None
                    if gotNone:
                        return None
                    return True

            class _EvalOrOp(object):
                def __init__(self, tokens):
                    self.value = tokens[0]

                def eval(self, valuesDict=None):
                    val = self.value[0].eval(valuesDict)
                    if val:
                        return True
                    gotNone = val is None
                    for op, val in _OperatorOperands(self.value[1:]):
                        val = val.eval(valuesDict)
                        if val:
                            return True
                        gotNone = gotNone or val is None
                    if gotNone:
                        return None
                    return False

            # Import pyparsing classes.

            from pyparsing import CaselessKeyword, CaselessLiteral, Combine, nums, one_of, OpAssoc, infix_notation, Opt, ParserElement, QuotedString, Regex, Word

            try:
                from pyparsing import delimitedList as DelimitedList    # Changed in pyparsing 3.1.0a1; see https://github.com/pyparsing/pyparsing/issues/408#issuecomment-1488630192
            except:
                from pyparsing import DelimitedList

            # No longer do we enable "packrat" mode for higher performance.
            # See https://github.com/jjrob/MGET/issues/39: pyparsing
            # ParserElement.enable_packrat() unexpectedly deletes MGET objects
            # and should no longer be used

            # ParserElement.enable_packrat()

            # Define the parser using pyparsing.
            #
            # booleanExpr is the parser. It takes an expression
            # resembling a SQL where clause and a dictionary of
            # variable values and returns True or False. If the
            # dictionary does not contain all of the variables
            # referenced in the expression, the parser still works,
            # but if a missing variable causes the value of the
            # expression to be indeterminate--i.e. it the result
            # cannot be determined without knowing the value of the
            # variable, the parser returns None.

            booleanLiteral = CaselessKeyword('false') | CaselessKeyword('true')
            integerLiteral = Word(nums)
            floatLiteral = Combine(((Word(nums) + '.' + Opt(Word(nums))) | ('.' + Word(nums))) + Opt(CaselessLiteral('E') + Opt(one_of('+ -')) + Word(nums)))
            dateLiteral = Combine('#' + (Regex('[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}') | Regex('[0-9]{4}-[0-9]{2}-[0-9]{2}')) + '#')
            stringLiteral = QuotedString("'", "\\", "''", True, False) ^ QuotedString('"', "\\", '""', True, False)

            literal = booleanLiteral | integerLiteral | floatLiteral | dateLiteral | stringLiteral
            literal.set_parse_action(_EvalLiteral)

            variable = Regex('[a-zA-Z][a-zA-Z0-9_]*')
            variable.set_parse_action(_EvalVariable)

            arithExpr = infix_notation(literal | variable,
                                       [(one_of('+ -'), 1, OpAssoc.RIGHT, _EvalSignOp),
                                        (one_of('* /'), 2, OpAssoc.LEFT, _EvalMultOp),
                                        (one_of('+ -'), 2, OpAssoc.LEFT, _EvalAddOp)])

            literalList = '(' + DelimitedList(literal) + ')'
            literalList.set_parse_action(_EvalLiteralList)

            comparisonExpr = arithExpr + (one_of("= < > >= <= <>") | CaselessKeyword("matches")) + arithExpr | arithExpr + CaselessKeyword("in") + literalList | arithExpr + CaselessKeyword("not") + CaselessKeyword("in") + literalList
            comparisonExpr.set_parse_action(_EvalComparisonOp)
             
            booleanExpr = infix_notation(comparisonExpr,
                                         [(CaselessKeyword("not"), 1, OpAssoc.RIGHT, _EvalNotOp),
                                          (CaselessKeyword("and"), 2, OpAssoc.LEFT, _EvalAndOp),
                                          (CaselessKeyword("or"), 2, OpAssoc.LEFT, _EvalOrOp)])

            # Store the parser as a class attribute.

            setattr(DatasetCollection, '_QueryExpressionParser', booleanExpr)

        return DatasetCollection._QueryExpressionParser

    def _PrepareQuery(self, expression):

        # Parse the expression.

        if expression is not None and len(expression) > 0:
            parser = self._GetQueryExpressionParser()
            try:
                parsedExpression = parser.parse_string(expression, parse_all=True)[0]
            except Exception as e:
                raise ValueError(_('Failed to parse the query expression "%(expr)s". The parser reported %(e)s: %(msg)s') % {'expr': expression, 'e': e.__class__.__name__, 'msg': str(e)})
        else:
            parsedExpression = None

        # Build a dictionary of queryable attribute values defined by
        # us and our chain of parent collections, so that the derived
        # class can use it in evaluating the query.

        parentAttrValues = {}
        collection = self
        while collection is not None:
            if collection._QueryableAttributeValues is not None:
                parentAttrValues.update(collection._QueryableAttributeValues)
            collection = collection.ParentCollection

        # Return the parsed expression and dictionary.

        return parsedExpression, parentAttrValues

    # Private methods that the derived class should override.

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):
        raise NotImplementedError(_('The _QueryDatasets method of class %s has not been implemented.') % self.__class__.__name__)

    def _GetOldestDataset(self, parsedExpression, options, parentAttrValues, dateTimeAttrName):

        # The base class implementation just retrieves all of the
        # datasets and iterates through them to find the oldest one.
        # The derived class should override this if it can implement
        # it more efficiently.

        datasets = self._QueryDatasets(parsedExpression, None, options, parentAttrValues)
        if len(datasets) <= 0:
            return None
        
        oldest = 0
        for i in range(1, len(datasets)):
            if datasets[i].GetQueryableAttributeValue(dateTimeAttrName) < datasets[oldest].GetQueryableAttributeValue(dateTimeAttrName):
                oldest = i

        return datasets[oldest]

    def _GetNewestDataset(self, parsedExpression, options, parentAttrValues, dateTimeAttrName):

        # The base class implementation just retrieves all of the
        # datasets and iterates through them to find the newest one.
        # The derived class should override this if it can implement
        # it more efficiently.

        datasets = self._QueryDatasets(parsedExpression, None, options, parentAttrValues)
        if len(datasets) <= 0:
            return None
        
        newest = 0
        for i in range(1, len(datasets)):
            if datasets[i].GetQueryableAttributeValue(dateTimeAttrName) > datasets[newest].GetQueryableAttributeValue(dateTimeAttrName):
                newest = i

        return datasets[newest]

    def _ImportDatasets(self, datasets, mode, reportProgress, options):
        raise NotImplementedError(_('The _ImportDatasets method of class %s has not been implemented.') % self.__class__.__name__)


class CollectionIsEmptyError(GeoEcoError):
    __doc__ = DynamicDocString()
    
    def __init__(self, collectionDisplayName=None, expression=None):
        self.__doc__.Obj.ValidateMethodInvocation()
        self.CollectionDisplayName = collectionDisplayName
        self.Expression = expression

    def __str__(self):
        if self.CollectionDisplayName is None and self.Expression is None:
            return _('This collection contains no datasets.')
        if self.CollectionDisplayName is not None and self.Expression is None:
            return _('The %(dn)s contains no datasets.') % {'dn': self.CollectionDisplayName}
        return _('The %(dn)s contains no datasets matching the expression %(expr)s.') % {'dn': self.CollectionDisplayName, 'expr': self.Expression}


###################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets instead.
###################################################################################

__all__ = []
