# DataManagement/Fields.py - Methods for performing common data management
# operations on table fields.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import sys

from ..Datasets.ArcGIS import ArcGISTable
from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger


class Field(object):
    __doc__ = DynamicDocString()

    @classmethod
    def CalculateFields(cls, table, fields, pythonExpressions, where=None, modulesToImport=None, statementsToExecFirst=None, statementsToExecPerRow=None):
        cls.__doc__.Obj.ValidateMethodInvocation()
        
        # Just return if the caller did not specify any fields.

        if len(fields) <= 0:
            Logger.Info(_('The list of fields to calculate is empty. No work needs to be done.'))
            return

        # Calculate the fields.

        rowsUpdated = 0
        
        if len(fields) == 1:        
            Logger.Info(_('Updating field "%(field)s" in "%(table)s"...') % {'field' : fields[0], 'table' : table.DisplayName})
        else:
            Logger.Info(_('Updating fields %(fields)s in "%(table)s"...') % {'fields' : repr(fields), 'table' : table.DisplayName})

        try:
            # Validate input parameters.

            if len(pythonExpressions) != len(fields):
                Logger.RaiseException(ValueError(_('The number of Python expressions (%(expr)i) is not the same as the number of fields (%(fields)i). Please provide exactly one expression for each field.' % {'expr': len(pythonExpressions), 'fields': len(fields)})))

            # Import the modules.

            if modulesToImport is not None:
                for m in modulesToImport:
                    Logger.Debug(_('Importing module %s.'), m)
                    try:
                        exec('import ' + str(m), globals(), sys._getframe().f_locals)
                    except:
                        Logger.LogExceptionAsError(_('Could not import Python module "%s".') % m)
                        raise

            # Execute the caller's statements, if any.

            if statementsToExecFirst is not None:
                for statement in statementsToExecFirst:
                    try:
                        exec(statement, globals(), sys._getframe().f_locals)
                    except:
                        Logger.LogExceptionAsError(_('Could not exec Python statement "%s".') % statement)
                        raise

            # Open an update cursor on the table.

            cur = table.OpenUpdateCursor(where=where)
            try:

                # Create the row object. This object allows the caller to access
                # table fields as attributes of itself and logs all accesses.

                row = _Row(cur)
                try:

                    # Update the rows.

                    while cur.NextRow():
                        if statementsToExecPerRow is not None:
                            for statement in statementsToExecPerRow:
                                try:
                                    exec(statement, globals(), sys._getframe().f_locals)
                                except:
                                    Logger.LogExceptionAsError(_('Could not exec Python statement "%s".') % statement)
                                    raise
                        for i in range(len(fields)):
                            try:
                                value = eval(pythonExpressions[i], globals(), sys._getframe().f_locals)
                            except:
                                Logger.LogExceptionAsError(_('Could not eval Python statement "%s".') % pythonExpressions[i])
                                raise
                            cur.SetValue(fields[i], value)
                        rowsUpdated += 1
                        cur.UpdateRow()
                        
                finally:
                    del row

            finally:
                del cur
                        
        except:
            if len(fields) == 1:        
                Logger.LogExceptionAsError(_('Could not calculate field "%(field)s" in "%(table)s".') % {'field' : fields[0], 'table' : table.DisplayName})
            else:
                Logger.LogExceptionAsError(_('Could not calculate fields %(fields)s in "%(table)s".') % {'fields' : repr(fields), 'table' : table.DisplayName})
            raise

    @classmethod
    def CalculateField(cls, table, field, pythonExpression, where=None, modulesToImport=None, statementsToExecFirst=None, statementsToExecPerRow=None):
        cls.__doc__.Obj.ValidateMethodInvocation()
        cls.CalculateFields(table, [field], [pythonExpression], where, modulesToImport, statementsToExecFirst, statementsToExecPerRow)

    @classmethod
    def CalculateArcGISFields(cls, table, fields, pythonExpressions, where=None, modulesToImport=None, statementsToExecFirst=None, statementsToExecPerRow=None):
        cls.__doc__.Obj.ValidateMethodInvocation()
        tableObj = ArcGISTable(table)
        cls.CalculateFields(tableObj, fields, pythonExpressions, where, modulesToImport, statementsToExecFirst, statementsToExecPerRow)
        return table

    @classmethod
    def CalculateArcGISField(cls, table, field, pythonExpression, where=None, modulesToImport=None, statementsToExecFirst=None, statementsToExecPerRow=None):
        cls.__doc__.Obj.ValidateMethodInvocation()
        tableObj = ArcGISTable(table)
        cls.CalculateFields(tableObj, [field], [pythonExpression], where, modulesToImport, statementsToExecFirst, statementsToExecPerRow)
        return table


class _Row(object):

    def __init__(self, cursor):
        self._Cursor = cursor

    def __getattr__(self, name):
        return self._Cursor.GetValue(name)


###############################################################################
# Metadata: module
###############################################################################

from ..ArcGIS import ArcGISDependency
from ..Datasets import Table
from ..Metadata import *
from ..Types import *

AddModuleMetadata(shortDescription=_('Functions for calculating field values from Python expressions.'))

###############################################################################
# Metadata: Field class
###############################################################################

AddClassMetadata(Field,
    shortDescription=_('Functions for calculating field values from Python expressions.'))

# Public method: Field.CalculateFields

AddMethodMetadata(Field.CalculateFields,
    shortDescription=_('Calculates values for one or more fields of a table using Python expressions.'))

AddArgumentMetadata(Field.CalculateFields, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Field),
    description=_(':class:`%s` or an instance of it.') % Field.__name__)

AddArgumentMetadata(Field.CalculateFields, 'table',
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    description=_(':class:`~GeoEco.Datasets.Table` that contains the fields to calculate.'),
    arcGISDisplayName=_('Table'))

AddArgumentMetadata(Field.CalculateFields, 'fields',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata()),
    description=_('Fields to calculate.'),
    arcGISDisplayName=_('Fields'),
    arcGISParameterDependencies=['table'])

AddArgumentMetadata(Field.CalculateFields, 'pythonExpressions',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata()),
    description=_(
"""Python expressions to evaluate for each field. There must be one expression
for each field.

For each row of the table, this function updates the values of the specified
fields by evaluating their corresponding expressions using the Python
:py:func:`eval` function. In your expressions, you can access the value of any
field by referencing the field as an attribute of the ``row`` object. For
example, if your table contains a ``SampledSST`` field and you want to
calculate the ``ActualSST`` field from it, you might calculate ``ActualSST``
with the following expression::

    row.SampledSST * 0.075 + 3.0

Your expression may be any Python statement appropriate for passing to the
:py:func:`eval` function. It must evaluate to a data type that is appropriate
for the field's data type:

* For string, text, or character fields, return a :py:class:`str`.

* For integer fields, return an :py:class:`int`.

* For floating point fields, return a :py:class:`float`.

* For date or datetime fields, return :py:class:`~datetime.datetime`.

* To set the field to a database NULL value, return Python :py:data:`None`.

Other database data types might work if the appropriate Python data type is
used, but these have not been tested.

For more information on Python syntax, please see the `Python
documentation <http://www.python.org/doc/>`_."""),
    arcGISDisplayName=_('Python expressions'))

CopyArgumentMetadata(Table.OpenSelectCursor, 'where', Field.CalculateFields, 'where')

AddArgumentMetadata(Field.CalculateFields, 'modulesToImport',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), canBeNone=True),
    description=_(
"""Python modules to import prior to evaluating the expressions. If you need
to access Python functions or classes that are provided by a module rather
than being built-in to the interpreter, list the module here. For example, to
be able to use the :py:class:`~datetime.datetime` class in your expressions,
list the :py:mod:`datetime` module here. In your expressions, you must refer
to the class using its fully-qualified name, ``datetime.datetime``."""),
    arcGISDisplayName=_('Python modules to import'))

AddArgumentMetadata(Field.CalculateFields, 'statementsToExecFirst',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), canBeNone=True),
    description=_(
"""Python statements to execute prior to looping through the rows of the
table. The statements are executed sequentially using the Python
:py:func:`exec` function. You can use Python statements to perform
initialization tasks such as setting variables that you reference from your
field expressions. For example, you might want to perform a calculation on all
of the rows that involves the current date and time, but you want the date and
time to remain constant while the rows are being updated. To obtain the
current date and time, you know you can import the :py:mod:`datetime` module
and then invoke :py:meth:`datetime.datetime.now`. But you do not want to
put this into your field expressions because the value will change as the
system clock ticks during your computations. Instead you can set the ``now``
variable using the statement::

    now = datetime.datetime.now()

and then reference it from your field expressions. (Don't forget to add
:py:mod:`datetime` to the list of modules to import first.)"""),
    arcGISDisplayName=_('Python statements to execute first'))

AddArgumentMetadata(Field.CalculateFields, 'statementsToExecPerRow',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), canBeNone=True),
    description=_(
"""Python statements to execute for every row after the row is retrieved but
before the field expressions are evaluated. The statements are executed
sequentially using the Python :py:func:`exec` function. You can use Python
statements to perform arbitrary tasks prior to evaluating your expressions.
For example, your table's rows may represent files from which you want to
extract a piece of metadata, but the extraction code cannot be expressed in a
single statement. You could provide the Python statements needed to open each
file, extract the metadata, and assign it to a variable. Your field expression
could then reference the variable, causing the metadata value to be stored in
the field."""),
    arcGISDisplayName=_('Python statements to execute for every row'))

# Public method: Field.CalculateField

AddMethodMetadata(Field.CalculateField,
    shortDescription=_('Calculates the value of a table field using a Python expression.')),

CopyArgumentMetadata(Field.CalculateFields, 'cls', Field.CalculateField, 'cls')

AddArgumentMetadata(Field.CalculateField, 'table',
    typeMetadata=ClassInstanceTypeMetadata(cls=Table),
    description=_(':class:`~GeoEco.Datasets.Table` that contains the field to calculate.'),
    arcGISDisplayName=_('Table'))

AddArgumentMetadata(Field.CalculateField, 'field',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Field to calculate.'),
    arcGISDisplayName=_('Field'),
    arcGISParameterDependencies=['table'])

AddArgumentMetadata(Field.CalculateField, 'pythonExpression',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Python expression to evaluate for the specified field.

For each row of the table, this function updates the values of the specified
fields by evaluating their corresponding expressions using the Python eval
function. In your expressions, you can access the value of any field by
referencing the field as an attribute of the ``row`` object. For example, if
your table contains a ``SampledSST`` field and you want to calculate the
``ActualSST`` field from it, you might calculate ``ActualSST`` with the
following expression::

    row.SampledSST * 0.075 + 3.0

Your expression may be any Python statement appropriate for passing to the
:py:func:`eval` function. It must evaluate to a data type that is appropriate
for the field's data type:

* For string, text, or character fields, return a :py:class:`str`.

* For integer fields, return an :py:class:`int`.

* For floating point fields, return a :py:class:`float`.

* For date or datetime fields, return :py:class:`~datetime.datetime`.

* To set the field to a database NULL value, return Python :py:data:`None`.

For more information on Python syntax, please see the `Python
documentation <http://www.python.org/doc/>`_."""),
    arcGISDisplayName=_('Python expression'))

CopyArgumentMetadata(Table.OpenSelectCursor, 'where', Field.CalculateField, 'where')

AddArgumentMetadata(Field.CalculateField, 'modulesToImport',
    typeMetadata=Field.CalculateFields.__doc__.Obj.Arguments[5].Type,
    description=_(
"""Python modules to import prior to evaluating the expression. If you need
to access Python functions or classes that are provided by a module rather
than being built-in to the interpreter, list the module here. For example, to
be able to use the :py:class:`~datetime.datetime` class in your expression,
list the :py:mod:`datetime` module here. In your expression, you must refer
to the class using its fully-qualified name, ``datetime.datetime``."""),
    arcGISDisplayName=_('Python modules to import'))

AddArgumentMetadata(Field.CalculateField, 'statementsToExecFirst',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), canBeNone=True),
    description=_(
"""Python statements to execute prior to looping through the rows of the
table. The statements are executed sequentially using the Python :py:func:`exec`
function. You can use Python statements to perform initialization tasks such
as setting variables that you reference from your field expression. For
example, you might want to perform a calculation on all of the rows that
involves the current date and time, but you want the date and time to remain
constant while the rows are being updated. To obtain the current date and
time, you know you can import the datetime module and then invoke
:py:meth:`datetime.datetime.now`. But you do not want to put this into your field
expression because the value will change as the system clock ticks during your
computations. Instead you can set the ``now`` variable using the statement::

    now = datetime.datetime.now()

and then reference it from your field expression. (Don't forget to add
datetime to the list of modules to import first.)"""),
    arcGISDisplayName=_('Python statements to execute first'))

AddArgumentMetadata(Field.CalculateField, 'statementsToExecPerRow',
    typeMetadata=ListTypeMetadata(elementType=UnicodeStringTypeMetadata(), canBeNone=True),
    description=_(
"""Python statements to execute for every row after the row is retrieved but
before the field expression is evaluated. The statements are executed
sequentially using the Python :py:func:`exec` function. You can use Python
statements to perform arbitrary tasks prior to evaluating your expression. For
example, your table's rows may represent files from which you want to extract
a piece of metadata, but the extraction code cannot be expressed in a single
statement. You could provide the Python statements needed to open each file,
extract the metadata, and assign it to a variable. Your field expression could
then reference the variable, causing the metadata value to be stored in the
field."""),
    arcGISDisplayName=_('Python statements to execute for every row'))

# Public method: Field.CalculateArcGISFields

AddMethodMetadata(Field.CalculateArcGISFields,
    shortDescription=_('Calculates values for one or more fields of a table using Python expressions.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Calculate Fields Using Python Expressions'),
    arcGISToolCategory=_('Data Management\\Fields'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(Field.CalculateFields, 'cls', Field.CalculateArcGISFields, 'cls')

AddArgumentMetadata(Field.CalculateArcGISFields, 'table',
    typeMetadata=ArcGISTableViewTypeMetadata(mustExist=True),
    description=_('Table that contains the fields to calculate.'),
    arcGISDisplayName=Field.CalculateFields.__doc__.Obj.Arguments[1].ArcGISDisplayName)

AddArgumentMetadata(Field.CalculateArcGISFields, 'fields',
    typeMetadata=ListTypeMetadata(ArcGISFieldTypeMetadata(mustExist=True)),
    description=Field.CalculateFields.__doc__.Obj.Arguments[2].Description,
    arcGISDisplayName=Field.CalculateFields.__doc__.Obj.Arguments[2].ArcGISDisplayName,
    arcGISParameterDependencies=Field.CalculateFields.__doc__.Obj.Arguments[2].ArcGISParameterDependencies)

CopyArgumentMetadata(Field.CalculateFields, 'pythonExpressions', Field.CalculateArcGISFields, 'pythonExpressions')

AddArgumentMetadata(Field.CalculateArcGISFields, 'where',
    typeMetadata=SQLWhereClauseTypeMetadata(canBeNone=True),
    description=Field.CalculateFields.__doc__.Obj.Arguments[4].Description,
    arcGISDisplayName=_('Where clause'),
    arcGISParameterDependencies=['table'])

CopyArgumentMetadata(Field.CalculateFields, 'modulesToImport', Field.CalculateArcGISFields, 'modulesToImport')
CopyArgumentMetadata(Field.CalculateFields, 'statementsToExecFirst', Field.CalculateArcGISFields, 'statementsToExecFirst')
CopyArgumentMetadata(Field.CalculateFields, 'statementsToExecPerRow', Field.CalculateArcGISFields, 'statementsToExecPerRow')

AddResultMetadata(Field.CalculateArcGISFields, 'outputTable',
    typeMetadata=ArcGISTableViewTypeMetadata(),
    description=Field.CalculateArcGISFields.__doc__.Obj.Arguments[1].Description,
    arcGISDisplayName=_('Output table'),
    arcGISParameterDependencies=['table'])

# Public method: Field.CalculateArcGISField

AddMethodMetadata(Field.CalculateArcGISField,
    shortDescription=_('Calculates the value of a table field using a Python expression.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Calculate Field Using a Python Expression'),
    arcGISToolCategory=_('Data Management\\Fields'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(Field.CalculateFields, 'cls', Field.CalculateArcGISField, 'cls')

AddArgumentMetadata(Field.CalculateArcGISField, 'table',
    typeMetadata=ArcGISTableViewTypeMetadata(mustExist=True),
    description=_('Table that contains the field to calculate.'),
    arcGISDisplayName=Field.CalculateField.__doc__.Obj.Arguments[1].ArcGISDisplayName)

AddArgumentMetadata(Field.CalculateArcGISField, 'field',
    typeMetadata=ArcGISFieldTypeMetadata(mustExist=True),
    description=_('Field to calculate.'),
    arcGISDisplayName=Field.CalculateField.__doc__.Obj.Arguments[2].ArcGISDisplayName,
    arcGISParameterDependencies=Field.CalculateField.__doc__.Obj.Arguments[2].ArcGISParameterDependencies)

CopyArgumentMetadata(Field.CalculateField, 'pythonExpression', Field.CalculateArcGISField, 'pythonExpression')
CopyArgumentMetadata(Field.CalculateArcGISFields, 'where', Field.CalculateArcGISField, 'where')
CopyArgumentMetadata(Field.CalculateField, 'modulesToImport', Field.CalculateArcGISField, 'modulesToImport')
CopyArgumentMetadata(Field.CalculateField, 'statementsToExecFirst', Field.CalculateArcGISField, 'statementsToExecFirst')
CopyArgumentMetadata(Field.CalculateField, 'statementsToExecPerRow', Field.CalculateArcGISField, 'statementsToExecPerRow')

AddResultMetadata(Field.CalculateArcGISField, 'outputTable',
    typeMetadata=ArcGISTableViewTypeMetadata(),
    description=Field.CalculateArcGISField.__doc__.Obj.Arguments[1].Description,
    arcGISDisplayName=_('Output table'),
    arcGISParameterDependencies=['table'])

###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['Field']
