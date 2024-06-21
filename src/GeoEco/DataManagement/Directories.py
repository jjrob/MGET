# DataManagement/Directories.py - Methods for performing common directory
# operations.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import errno
import glob
import inspect
import os
import re
import shutil
import tempfile

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger


class Directory(object):
    __doc__ = DynamicDocString()

    @classmethod
    def Copy(cls, sourceDirectory, destinationDirectory, deleteExistingDestinationDirectory=False, overwriteExistingFiles=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        Logger.Info(_('Copying directory %(in)s to %(out)s...') % {'in' : sourceDirectory, 'out' : destinationDirectory})
        try:
            # If the caller requested that the existing directory be
            # deleted, and it exists, delete it.

            if deleteExistingDestinationDirectory and os.path.isdir(destinationDirectory):
                Logger.Debug(_('Deleting existing directory %s'), destinationDirectory)
                Directory._LoggedRemovalFailure = False
                shutil.rmtree(destinationDirectory, onerror=Directory._LogFailedRemoval)
                if Directory._LoggedRemovalFailure:
                    Logger.RaiseException(ValueError(_('Could not delete all of the contents of existing directory %s') % destinationDirectory))
                else:
                    Logger.Info(_('Deleted existing directory %s'), destinationDirectory)
            
            # Copy the directory.

            cls._CopyTree(sourceDirectory, destinationDirectory, overwriteExistingFiles)        
        
        except:
            Logger.LogExceptionAsError(_('Could not copy directory %(source)s to %(dest)s') % {'source' :  sourceDirectory, 'dest' : destinationDirectory})
            raise

    @classmethod
    def _CopyTree(cls, sourceDirectory, destinationDirectory, overwriteExistingFiles):
        if not os.path.isdir(destinationDirectory):
            try:
                os.mkdir(destinationDirectory)
            except:
                Logger.LogExceptionAsError(_('Could not create directory %s') % destinationDirectory)
                raise
            Logger.Debug(_('Created directory %s'), destinationDirectory)
        names = os.listdir(sourceDirectory)
        for name in names:
            src = os.path.join(sourceDirectory, name)
            dest = os.path.join(destinationDirectory, name)
            if os.path.isdir(src):
                cls._CopyTree(src, dest, overwriteExistingFiles)
            else:
                if os.path.isfile(dest):
                    if overwriteExistingFiles:
                        try:
                            os.remove(dest)
                        except:
                            Logger.LogExceptionAsError(_('Could not delete existing destination file %s') % dest)
                            raise
                        Logger.Debug(_('Deleted existing destination file %s'), dest)
                    else:
                        Logger.RaiseException(ValueError(_('The existing destination file %s already exists. Delete the existing file or specify a new destination, and try again.') % dest))
                elif os.path.exists(dest):
                    Logger.RaiseException(ValueError(_('The existing destination path %s already exists, but it is a directory or some other non-file object. Delete the existing object or specify a new destination, and try again.') % dest))
                Logger.Debug(_('Copying file %(source)s to %(dest)s') % {'source' :  src, 'dest' : dest})
                try:
                    shutil.copy2(src, dest)
                except:
                    Logger.LogExceptionAsError(_('Could not copy file %(source)s to %(dest)s') % {'source' :  src, 'dest' : dest})
                    raise

    @classmethod
    def Create(cls, directory):
        cls.__doc__.Obj.ValidateMethodInvocation()
        try:
            # Return immediately if the directory already exists.

            if os.path.isdir(directory):
                Logger.Info(_('Directory %s will not be created because it already exists.'), directory)
                return
            
            # Create the directory, including any missing intermediate directories.

            os.makedirs(directory, exist_ok=True)
            Logger.Info(_('Created directory %s.'), directory)

        except:
            Logger.LogExceptionAsError(_('Could not create directory %s') % directory)
            raise

    @classmethod
    def CreateSubdirectory(cls, parentDirectory, subdirectoryName):
        cls.__doc__.Obj.ValidateMethodInvocation()
        directory = os.path.join(parentDirectory, subdirectoryName)
        cls.Create(directory=directory)
        return directory

    @classmethod
    def CreateTemporaryDirectory(cls):
        cls.__doc__.Obj.ValidateMethodInvocation()
        oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
        Logger.SetLogInfoAsDebug(True)
        try:
            try:
                # Determine the parent directory that will hold the
                # temporary directory. If an ArcGIS "scratch
                # workspace" is set, use the GeoEcoTemp subdirectory.

                from GeoEco.ArcGIS import GeoprocessorManager

                gp = GeoprocessorManager.GetWrappedGeoprocessor()
                if gp is not None and hasattr(gp, 'ScratchWorkspace') and isinstance(gp.ScratchWorkspace, str) and len(gp.ScratchWorkspace) > 0 and os.path.isdir(gp.ScratchWorkspace) and not gp.ScratchWorkspace.endswith('.gdb'):
                    parentDirectory = os.path.join(gp.ScratchWorkspace, 'GeoEcoTemp')

                # Otherwise, get the operating system temp directory
                # from Python and use the GeoEcoTemp subdirectory.
                
                else:
                    parentDirectory = os.path.join(tempfile.gettempdir(), 'GeoEcoTemp')

                # Create the parent directory, if it does not exist.

                if not os.path.isdir(parentDirectory):
                    if os.path.exists(parentDirectory):
                        Logger.RaiseException(ValueError(_('The path %s exists but it is not a directory. This path must be available to hold temporary files. If it exists, it must be a directory. Please delete the existing file (or whatever it is) and try again.') % parentDirectory))
                    cls.Create(parentDirectory)

                # Create the temporary directory in the parent directory.

                temporaryDirectory = None

                while temporaryDirectory is None:
                    temporaryDirectory = tempfile.mktemp(prefix='tmp', dir=parentDirectory)
                    if os.path.basename(temporaryDirectory).find('-') >= 0:
                        temporaryDirectory = None
                    else:
                        try:
                            os.mkdir(temporaryDirectory, 0o700)
                        except OSError as e:
                            if e.errno != errno.EEXIST:
                                raise
                            temporaryDirectory = None

                Logger.Debug(_('Created temporary directory %s'), temporaryDirectory)

            except:
                Logger.LogExceptionAsError(_('Could not create a temporary directory.'))
                raise
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

        return temporaryDirectory                

    @classmethod
    def Delete(cls, directory, removeTree=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        try:
            # For safety, do not allow the caller to remove a root directory.

            if directory == '\\' or directory == '/' or directory == '~/' or re.match(r'^[A-Za-z]:[\\/]$', directory) or re.match(r'^[\\/][\\/]\w+[\\/]\w+[\\/]?$', directory):
                Logger.RaiseException(ValueError(_('%s is a root directory. Deletion of root directories is not allowed.') % directory))

            # Remove the directory. If removeTree == True, use shutil.rmtree.

            if os.path.isdir(directory):
                Directory._LoggedRemovalFailure = False
                if removeTree:
                    shutil.rmtree(directory, onerror=Directory._LogFailedRemoval)
                else:
                    os.rmdir(directory)
                if Directory._LoggedRemovalFailure:
                    Logger.RaiseException(ValueError(_('Could not delete all of the contents of directory %s') % directory))
                else:
                    Logger.Info(_('Deleted directory %s'), directory)
            elif os.path.exists(directory):
                Logger.RaiseException(ValueError(_('The path %s exists as a file or some other non-directory object. To delete it, use a method that is appropriate for this type object. For example, to delete files, use File.Delete.') % directory))
            else:
                Logger.Info(_('Directory %s will not be deleted because it does not exist.'), directory)

        except:
            Logger.LogExceptionAsError(_('Could not delete directory %s') % directory)
            raise

    _LoggedRemovalFailure = False

    @staticmethod
    def _LogFailedRemoval(function, path, excinfo):
        Directory._LoggedRemovalFailure = True

        error = excinfo[0].__name__
        msg = excinfo[1]
        
        if function == os.remove:
            Logger.Error(_('Could not delete file %(path)s due to %(error)s: %(msg)s') % {'path' : path, 'error' : error, 'msg' : msg})
        elif function == os.rmdir:
            Logger.Error(_('Could not delete directory %(path)s due to %(error)s: %(msg)s') % {'path' : path, 'error' : error, 'msg' : msg})
        else:
            Logger.Error(_('Could not delete directory %(path)s. The directory contents could not be listed due to %(error)s: %(msg)s') % {'path' : path, 'error' : error, 'msg' : msg})

    @classmethod
    def Exists(cls, path):
        cls.__doc__.Obj.ValidateMethodInvocation()
        exists = os.path.exists(path)
        isDirectory = os.path.isdir(path)
        if not exists:
            Logger.Debug(_('The directory %(path)s does not exist.') % {'path': path})
        else:
            if isDirectory:
                Logger.Debug(_('The directory %(path)s exists.') % {'path': path})
            else:
                Logger.Debug(_('%(path)s exists but it is not a directory.') % {'path': path})
        return (exists, isDirectory)

    @classmethod
    def Find(cls, directory, wildcard='*', searchTree=False, mustBeEmpty=False, mustNotBeEmpty=False, minDateCreated=None, maxDateCreated=None, minDateModified=None, maxDateModified=None, basePath=None, getDateCreated=False, getDateModified=False, dateParsingExpression=None):
        cls.__doc__.Obj.ValidateMethodInvocation()
        if mustBeEmpty and mustNotBeEmpty:
            Logger.RaiseException(ValueError(_('The mustBeEmpty and mustNotBeEmpty options may not both be true (a directory cannot be empty and not empty at the same time).')))
        if minDateCreated is not None and maxDateCreated is not None and minDateCreated > maxDateCreated:
            Logger.RaiseException(ValueError(_('minDateCreated must be less than or equal to maxDateCreated.')))
        if minDateModified is not None and maxDateModified is not None and minDateModified > maxDateModified:
            Logger.RaiseException(ValueError(_('minDateModified must be less than or equal to maxDateModified.')))

        Logger.Info(_('Finding directories: directory="%(directory)s", wildcard="%(wildcard)s", searchTree=%(tree)s, mustBeEmpty=%(mustBeEmpty)s, mustNotBeEmpty=%(mustNotBeEmpty)s, minDateCreated=%(minDateCreated)s, maxDateCreated=%(maxDateCreated)s, minDateModified=%(minDateModified)s, maxDateModified=%(maxDateModified)s') % {'directory': directory, 'wildcard': wildcard, 'tree': searchTree, 'mustBeEmpty': mustBeEmpty, 'mustNotBeEmpty': mustNotBeEmpty, 'minDateCreated': minDateCreated, 'maxDateCreated': maxDateCreated, 'minDateModified': minDateModified, 'maxDateModified': maxDateModified})

        return cls._Find(directory,
                         wildcard,
                         searchTree,
                         mustBeEmpty,
                         mustNotBeEmpty,
                         minDateCreated,
                         maxDateCreated,
                         minDateModified,
                         maxDateModified,
                         basePath,
                         getDateCreated,
                         getDateModified,
                         dateParsingExpression)

    @classmethod
    def _Find(cls, directory, wildcard, searchTree, mustBeEmpty, mustNotBeEmpty, minDateCreated, maxDateCreated, minDateModified, maxDateModified, basePath, getDateCreated, getDateModified, dateParsingExpression, searchPattern=None, strptimePattern=None):

        # If the caller provided a dateParsingExpression, parse it into a
        # pattern we can pass the re.search() and a corresponding pattern we can
        # subsequently pass to time.strptime().

        from .Files import File

        if dateParsingExpression is not None and searchPattern is None:
            searchPattern, strptimePattern = File.ValidateDateParsingExpression(dateParsingExpression)

        # Find matching directories in the specified directory.

        results = []
        
        if basePath is not None:
            os.path.normpath(basePath)
            baseParts = basePath.split(os.sep)

        for o in glob.glob(os.path.join(directory, wildcard)):

            # Skip this object if it is not a directory.
            
            if not os.path.isdir(o):
                continue

            # Skip this directory if it does not match the caller's search criteria.

            if mustBeEmpty or mustNotBeEmpty:
                isEmpty = len(os.listdir(o)) <= 0

            if mustBeEmpty and not isEmpty or mustNotBeEmpty and isEmpty:
                continue

            if minDateCreated is not None or maxDateCreated is not None or minDateModified is not None or maxDateModified is not None or getDateCreated or getDateModified:
                s = os.stat(o)
                dateCreated = datetime.datetime.fromtimestamp(s.st_ctime)
                dateModified = datetime.datetime.fromtimestamp(s.st_mtime)
                
                if minDateCreated is not None and dateCreated < minDateCreated:
                    continue
                if maxDateCreated is not None and dateCreated > maxDateCreated:
                    continue
                if minDateModified is not None and dateModified < minDateModified:
                    continue
                if maxDateModified is not None and dateModified> maxDateModified:
                    continue

            # Append the absolute path to the result row.
            
            Logger.Debug(_('Found directory %s'), o)

            result = [o]

            # If requested, append the relative path to the result row.

            if basePath is not None:
                oParts = o.split(os.sep)
                i = 0
                while i < len(baseParts) and i < len(oParts) and os.path.normcase(baseParts[i]) == os.path.normcase(oParts[i]):
                    i += 1
                if i == 0:
                    result.append(o)
                else:
                    result.append(os.path.join(('..' + os.sep) * (len(baseParts) - i), os.sep.join(oParts[i:])))

            # If requested, append the other optional fields to the result row.
                
            if getDateCreated:
                result.append(dateCreated)
                
            if getDateModified:
                result.append(dateModified)

            # If requested, parse a date from the absolute path and append it
            # to the result row, in both datetime and UNIX time formats.

            if dateParsingExpression is not None:
                dateTime, unixTime = File.ParseDateFromPath(o, dateParsingExpression, searchPattern, strptimePattern)
                result.append(dateTime)
                result.append(unixTime)

            # Append this result row to the list of results to return.

            results.append(result)

        # Search child directories, if requested.
        
        if searchTree:
            for o in os.listdir(directory):
                o = os.path.join(directory, o)
                if os.path.isdir(o):
                    results.extend(cls._Find(o,
                                             wildcard,
                                             searchTree,
                                             mustBeEmpty,
                                             mustNotBeEmpty,
                                             minDateCreated,
                                             maxDateCreated,
                                             minDateModified,
                                             maxDateModified,
                                             basePath,
                                             getDateCreated,
                                             getDateModified,
                                             dateParsingExpression,
                                             searchPattern,
                                             strptimePattern))

        # Return successfully.

        return results        

    @classmethod
    def FindAndFillTable(cls, directory, insertCursor, directoryField, wildcard='*', searchTree=False, mustBeEmpty=False, mustNotBeEmpty=False, minDateCreated=None, maxDateCreated=None, minDateModified=None, maxDateModified=None, relativePathField=None, basePath=None, dateCreatedField=None, dateModifiedField=None, parsedDateField=None, dateParsingExpression=None, unixTimeField=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        fields = [directoryField, relativePathField, dateCreatedField, dateModifiedField, parsedDateField, unixTimeField]
        fieldsDict = {}
        for f in fields:
            if f is not None:
                if f.lower() in fieldsDict:
                    Logger.RaiseException(ValueError(_('The same field "%(field)s" is specified for two different parameters. Please specify a unique field name for each parameter.') % {'field': f}))
                fieldsDict[f.lower()] = True

        if parsedDateField is not None and dateParsingExpression is None:
            Logger.RaiseException(ValueError(_('If you specify a field to receive parsed dates, you must also specify a date parsing expression.')))

        if unixTimeField is not None and dateParsingExpression is None:
            Logger.RaiseException(ValueError(_('If you specify a field to receive UNIX times, you must also specify a date parsing expression.')))

        if relativePathField is None:
            basePath = None

        # Find the directories.

        Logger.Info(_('Finding directories and inserting rows into table "%(table)s": directory="%(directory)s", wildcard="%(wildcard)s", searchTree=%(tree)s, mustBeEmpty=%(mustBeEmpty)s, mustNotBeEmpty=%(mustNotBeEmpty)s, minDateCreated=%(minDateCreated)s, maxDateCreated=%(maxDateCreated)s, minDateModified=%(minDateModified)s, maxDateModified=%(maxDateModified)s') % {'table': insertCursor.Table, 'directory': directory, 'wildcard': wildcard, 'tree': searchTree, 'mustBeEmpty': mustBeEmpty, 'mustNotBeEmpty': mustNotBeEmpty, 'minDateCreated': minDateCreated, 'maxDateCreated': maxDateCreated, 'minDateModified': minDateModified, 'maxDateModified': maxDateModified})

        results = cls._Find(directory,
                            wildcard,
                            searchTree,
                            mustBeEmpty,
                            mustNotBeEmpty,
                            minDateCreated,
                            maxDateCreated,
                            minDateModified,
                            maxDateModified,
                            basePath,
                            dateCreatedField is not None,
                            dateModifiedField is not None,
                            dateParsingExpression)

        # Insert the rows.

        if len(results) > 0:
            insertCursor.SetRowCount(len(results))

            for result in results:
                value = result.pop(0)
                insertCursor.SetValue(directoryField, value)

                if relativePathField is not None:
                    value = result.pop(0)
                    insertCursor.SetValue(relativePathField, value)

                if dateCreatedField is not None:
                    value = result.pop(0)
                    insertCursor.SetValue(dateCreatedField, value)

                if dateModifiedField is not None:
                    value = result.pop(0)
                    insertCursor.SetValue(dateModifiedField, value)

                if parsedDateField is not None or unixTimeField is not None:
                    value = result.pop(0)
                    if parsedDateField is not None:
                        insertCursor.SetValue(parsedDateField, value)

                    value = result.pop(0)
                    if unixTimeField is not None:
                        insertCursor.SetValue(unixTimeField, value)

                insertCursor.InsertRow()

    @classmethod
    def FindAndCreateTable(cls, directory, database, table, directoryField, wildcard='*', searchTree=False, mustBeEmpty=False, mustNotBeEmpty=False, minDateCreated=None, maxDateCreated=None, minDateModified=None, maxDateModified=None, relativePathField=None, basePath=None, dateCreatedField=None, dateModifiedField=None, parsedDateField=None, dateParsingExpression=None, unixTimeField=None, pathFieldsDataType='string', dateFieldsDataType='datetime', unixTimeFieldDataType='int32', maxPathLength=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        fields = [directoryField, relativePathField, dateCreatedField, dateModifiedField, parsedDateField, unixTimeField]
        fieldsDict = {}
        for f in fields:
            if f is not None:
                if f.lower() in fieldsDict:
                    Logger.RaiseException(ValueError(_('The same field "%(field)s" is specified for two different parameters. Please specify a unique field name for each parameter.') % {'field': f}))
                fieldsDict[f.lower()] = True

        if parsedDateField is not None and dateParsingExpression is None:
            Logger.RaiseException(ValueError(_('If you specify a field to receive parsed dates, you must also specify a date parsing expression.')))

        if unixTimeField is not None and dateParsingExpression is None:
            Logger.RaiseException(ValueError(_('If you specify a field to receive UNIX times, you must also specify a date parsing expression.')))

        if relativePathField is None:
            basePath = None

        # If requested, delete the table if it already exists.
        
        if database.TableExists(table):
            if overwriteExisting:
                database.DeleteTable(table)
            else:
                Logger.RaiseException(ValueError(_('Cannot create table %s because it already exists.') % table))

        # Create the table and add the fields.

        tableObj = database.CreateTable(table)
        
        try:
            tableObj.AddField(directoryField, pathFieldsDataType, length=maxPathLength)

            if relativePathField is not None:
                tableObj.AddField(relativePathField, pathFieldsDataType, length=maxPathLength)

            if dateCreatedField is not None:
                tableObj.AddField(dateCreatedField, dateFieldsDataType)

            if dateModifiedField is not None:
                tableObj.AddField(dateModifiedField, dateFieldsDataType)

            if parsedDateField is not None:
                tableObj.AddField(parsedDateField, dateFieldsDataType)

            if unixTimeField is not None:
                tableObj.AddField(unixTimeField, unixTimeFieldDataType)

            # Create an insert cursor and fill the table.

            cursor = tableObj.OpenInsertCursor()
            try:
                cls.FindAndFillTable(directory,
                                     cursor,
                                     directoryField,
                                     wildcard,
                                     searchTree,
                                     mustBeEmpty,
                                     mustNotBeEmpty,
                                     minDateCreated,
                                     maxDateCreated,
                                     minDateModified,
                                     maxDateModified,
                                     relativePathField,
                                     basePath,
                                     dateCreatedField,
                                     dateModifiedField,
                                     parsedDateField,
                                     dateParsingExpression,
                                     unixTimeField)
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

        return table        

    @classmethod
    def FindAndCreateArcGISTable(cls, directory, workspace, table, directoryField, wildcard='*', searchTree=False, mustBeEmpty=False, mustNotBeEmpty=False, minDateCreated=None, maxDateCreated=None, minDateModified=None, maxDateModified=None, relativePathField=None, dateCreatedField=None, dateModifiedField=None, parsedDateField=None, dateParsingExpression=None, unixTimeField=None, maxPathLength=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # If the caller's workspace is a directory (rather than a database),
        # the geoprocessor's CreateTable tool will create a DBF table,
        # regardless of what file extension the caller placed on the table. Even
        # if the caller's extension is .csv or .txt, the geoprocessor will
        # replace it with .dbf. If the caller does not provide an extension, the
        # geoprocessor will tack on .dbf.
        #
        # Because we know the geoprocessor will do this, we do it here
        # preemptively, so we can check for and delete the existing table, if
        # desired by the caller.

        if os.path.isdir(workspace) and not workspace.lower().endswith('.gdb') and not table.lower().endswith('.dbf'):
            if table.find('.') >= 0:
                newTable = table[:table.find('.')] + '.dbf'
                Logger.Warning('When creating tables in the file system, the ArcGIS CreateTable tool ignores the extension you specify and always creates a dBASE table with the extension .dbf. It will create the table %(new)s even though you asked for %(old)s.' % {'new': newTable, 'old': table})
            else:
                newTable = table + '.dbf'
                Logger.Warning('The ArcGIS CreateTable tool always creates dBASE tables in the file system. Even though you did not specify a file extension for your table, .dbf will be used.')
            table = newTable

        # Create the table.
        
        from ..Datasets import QueryableAttribute
        from ..Datasets.ArcGIS import ArcGISWorkspace, ArcGISTable
        
        database = ArcGISWorkspace(path=workspace, 
                                   datasetType=ArcGISTable,
                                   pathParsingExpressions=[r'(?P<TableName>.+)'], 
                                   queryableAttributes=(QueryableAttribute('TableName', _('Table name'), UnicodeStringTypeMetadata()),))

        table = cls.FindAndCreateTable(directory,
                                       database,
                                       table,
                                       directoryField,
                                       wildcard,
                                       searchTree,
                                       mustBeEmpty,
                                       mustNotBeEmpty,
                                       minDateCreated,
                                       maxDateCreated,
                                       minDateModified,
                                       maxDateModified,
                                       relativePathField,
                                       workspace,
                                       dateCreatedField,
                                       dateModifiedField,
                                       parsedDateField,
                                       dateParsingExpression,
                                       unixTimeField,
                                       'string',
                                       'datetime',
                                       'int32',
                                       maxPathLength,
                                       overwriteExisting)

        # If it is a DBF table, delete the Field1 field. ArcGIS always creates
        # this field because, according to the documentation, DBF files must
        # always have at least one field, and it is not possible to give a field
        # to the geoprocessor's CreateTable tool. Also delete the M_S_O_F_T
        # field if it exists; this is created by the Microsoft ODBC dBASE
        # driver, which ArcGIS could conceivably use in the future.
        
        if os.path.isdir(workspace) and not workspace.lower().endswith('.gdb') and table.lower().endswith('.dbf'):
            tableObj = database.QueryDatasets(expression="TableName = '%s'" % table, reportProgress=False)[0]
            if tableObj.GetFieldByName('Field1') is not None:
                tableObj.DeleteField('Field1')
            if tableObj.GetFieldByName('M_S_O_F_T') is not None:
                tableObj.DeleteField('M_S_O_F_T')

        # Return successfully.
        
        return table

    @classmethod
    def Move(cls, sourceDirectory, destinationDirectory, deleteExistingDestinationDirectory=False, overwriteExistingFiles=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Moving directory %(in)s to %(out)s...') % {'in' : sourceDirectory, 'out' : destinationDirectory})
        try:
            try:
                # If the caller requested that the existing directory be
                # deleted, and it exists, delete it.

                if deleteExistingDestinationDirectory and os.path.isdir(destinationDirectory):
                    Logger.Debug(_('Deleting existing directory %s'), destinationDirectory)
                    Directory._LoggedRemovalFailure = False
                    shutil.rmtree(destinationDirectory, onerror=Directory._LogFailedRemoval)
                    if Directory._LoggedRemovalFailure:
                        Logger.RaiseException(ValueError(_('Could not delete all of the contents of existing directory %s') % destinationDirectory))
                    else:
                        Logger.Info(_('Deleted existing directory %s'), destinationDirectory)
            
                # Move the directory.

                cls._MoveTree(sourceDirectory, destinationDirectory, overwriteExistingFiles)            
            
            except:
                Logger.LogExceptionAsError(_('Could not move directory %(source)s to %(dest)s') % {'source' :  sourceDirectory, 'dest' : destinationDirectory})
                raise
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def _MoveTree(cls, sourceDirectory, destinationDirectory, overwriteExistingFiles):
        if os.path.isdir(destinationDirectory):
            names = os.listdir(sourceDirectory)
            for name in names:
                src = os.path.join(sourceDirectory, name)
                dest = os.path.join(destinationDirectory, name)
                if os.path.isdir(src):
                    cls._MoveTree(src, dest, overwriteExistingFiles)
                else:
                    if os.path.isfile(dest):
                        if overwriteExistingFiles:
                            try:
                                os.remove(dest)
                            except:
                                Logger.LogExceptionAsError(_('Could not delete existing destination file %s') % dest)
                                raise
                            Logger.LogExceptionAsError(_('Deleted existing destination file %s') % dest)
                        else:
                            Logger.RaiseException(ValueError(_('The existing destination file %s already exists. Delete the existing file or specify a new destination, and try again.') % dest))
                    elif os.path.exists(dest):
                        Logger.RaiseException(ValueError(_('The existing destination path %s already exists but it is a directory or some other non-file object. Delete the existing object or specify a new destination, and try again.') % dest))
                    try:
                        os.rename(src, dest)
                    except OSError:
                        try:
                            Logger.Debug(_('Copying file %(source)s to %(dest)s') % {'source' :  src, 'dest' : dest})
                            shutil.copy2(src, dest)
                        except:
                            Logger.LogExceptionAsError(_('Could not copy file %(source)s to %(dest)s') % {'source' :  src, 'dest' : dest})
                            raise
                        try:
                            os.remove(src)
                        except:
                            Logger.LogExceptionAsError(_('Could not delete source file %s') % src)
                            raise
                        Logger.LogExceptionAsError(_('Deleted source file %s') % src)
                    else:
                        Logger.Debug(_('Renamed directory %(source)s to %(dest)s') % {'source' :  src, 'dest' : dest})
            try:
                os.rmdir(sourceDirectory)
            except:
                Logger.LogExceptionAsError(_('Could not delete directory %s') % sourceDirectory)
                raise
        elif os.path.exists(destinationDirectory):
            Logger.RaiseException(ValueError(_('The existing destination path %s already exists but it is a file or some other non-directory object. Delete the existing object or specify a new destination, and try again.') % destinationDirectory))
        else:
            try:
                os.rename(sourceDirectory, destinationDirectory)
            except OSError:
                cls.Copy(sourceDirectory, destinationDirectory)
                cls.Delete(sourceDirectory, removeTree=True)
            else:
                Logger.Debug(_('Renamed directory %(source)s to %(dest)s') % {'source' :  sourceDirectory, 'dest' : destinationDirectory})


class TemporaryDirectory(object):
    __doc__ = DynamicDocString()

    _DirForTesting = None

    def __init__(self, automaticallyDelete=True):
        self.__doc__.Obj.ValidateMethodInvocation()
        if TemporaryDirectory._DirForTesting is not None:
            if os.path.isdir(TemporaryDirectory._DirForTesting):
                Directory._LoggedRemovalFailure = False
                shutil.rmtree(TemporaryDirectory._DirForTesting, onerror=Directory._LogFailedRemoval)
                if Directory._LoggedRemovalFailure:
                    Logger.RaiseException(RuntimeError(_('Testing stopped due to failure to delete directory.')))
            os.makedirs(TemporaryDirectory._DirForTesting)
            self._Path = TemporaryDirectory._DirForTesting
        else:
            self._Path = Directory.CreateTemporaryDirectory()
        self._AutomaticallyDelete = automaticallyDelete

    def __del__(self):
        if self._AutomaticallyDelete:
            try:
                logErrorsAsWarnings = Logger.GetLogErrorsAsWarnings()
                if not logErrorsAsWarnings:
                    Logger.SetLogErrorsAsWarnings(True)
                oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
                Logger.SetLogInfoAsDebug(True)
            except:
                pass
            try:
                Directory.Delete(self._Path, removeTree=True)
            except:
                pass
            try:
                if not logErrorsAsWarnings:
                    Logger.SetLogErrorsAsWarnings(False)
                Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)
            except:
                pass

    def _GetPath(self):
        return self._Path

    Path = property(_GetPath, doc=DynamicDocString())

    def _GetAutomaticallyDelete(self):
        return self._AutomaticallyDelete
    
    def _SetAutomaticallyDelete(self, value):
        self.__doc__.Obj.ValidatePropertyAssignment()
        self._AutomaticallyDelete = value

    AutomaticallyDelete = property(_GetAutomaticallyDelete, _SetAutomaticallyDelete, doc=DynamicDocString())

    def DecompressInputArgument(self, argName):    
        self.__doc__.Obj.ValidateMethodInvocation()
        oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
        Logger.SetLogInfoAsDebug(True)
        try:
            try:
                parentFrame = inspect.currentframe().f_back
                try:
                    # Verify that we're being called from an instancemethod or
                    # classmethod.
                    
                    funcName = parentFrame.f_code.co_name
                    (args, varargs, varkw, _locals) = inspect.getargvalues(parentFrame)
                    assert len(args) > 0 and args[0] in _locals and hasattr(_locals[args[0]], funcName) and inspect.ismethod(getattr(_locals[args[0]], funcName)) and getattr(_locals[args[0]], funcName).__func__.__code__ == parentFrame.f_code, 'TemporaryDirectory.DecompressInputArgument should only be called from instance methods or classmethods.'

                    # Verify that the method's __doc__ attribute contains a
                    # DynamicDocString with a MethodMetadata object inside.

                    from GeoEco.Metadata import MethodMetadata                
                    method = getattr(_locals[args[0]], funcName)
                    assert isinstance(method.__doc__, DynamicDocString) and isinstance(method.__doc__.Obj, MethodMetadata), 'TemporaryDirectory.DecompressInputArgument should only be called instance methods or classmethods that have their __doc__ attribute set to an instance of DynamicDocString and the Obj property of DynamicDocString set to an instance of MethodMetadata.'
                    methodMetadata = method.__doc__.Obj

                    # Verify that the metadata for the specified argument says the
                    # argument can be compressed.

                    from GeoEco.DataManagement.Files import FileTypeMetadata
                    argMetadata = methodMetadata.GetArgumentByName(argName)
                    assert argMetadata is not None, 'TemporaryDirectory.DecompressInputArgument requires that the calling method, %s.%s.%s, have an argument named %s.' % (methodMetadata.Class.Module.Name, methodMetadata.Class.Name, methodMetadata.Name, argName)
                    assert isinstance(argMetadata.Type, FileTypeMetadata), 'TemporaryDirectory.DecompressInputArgument requires that the ArgumentMetadata.Type for argument %s of the calling method %s.%s.%s be an instance of GeoEco.Types.FileTypeMetadata.' % (argName, methodMetadata.Class.Module.Name, methodMetadata.Class.Name, methodMetadata.Name)
                    assert argMetadata.Type.MayBeCompressed, 'TemporaryDirectory.DecompressInputArgument requires that the ArgumentMetadata.Type.MayBeCompressed be True for argument %s of the calling method %s.%s.%s.' % (argName, methodMetadata.Class.Module.Name, methodMetadata.Class.Name, methodMetadata.Name)

                    # If the file specified by the argument is not decompressible,
                    # just return the path to the original file.

                    compressedFile = _locals[argName]
                    from GeoEco.DataManagement.Files import File
                    if compressedFile is None or not File.IsDecompressible(compressedFile):
                        return compressedFile

                    # Otherwise decompress the file to a subdirectory named for
                    # the argument, and return the decompressed file.

                    return File.Decompress(compressedFile, os.path.join(self.Path, argName), decompressedFileToReturn=argMetadata.Type.DecompressedFileToUse)

                finally:
                    del parentFrame         # Explicitly delete frame object to avoid memory cycle (see Python docs for more info).
                    
            except:
                Logger.LogExceptionAsError(_('Could not decompress the input file specified by the %(arg)s parameter to directory %(dir)s') % {'arg' : argName, 'dir' : self.Path})
                raise
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)


###############################################################################
# Metadata: module
###############################################################################

from GeoEco.ArcGIS import ArcGISDependency
from ..Datasets import Database, InsertCursor
from GeoEco.Metadata import *
from GeoEco.Types import *

AddModuleMetadata(shortDescription=_('Functions for common directory operations.'))


###############################################################################
# Metadata: Directory class
###############################################################################

AddClassMetadata(Directory,
    shortDescription=_('Functions for common directory operations.'))

# Public method: Directory.Copy

AddMethodMetadata(Directory.Copy,
    shortDescription=_('Copies a directory, including its subdirectories and files.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Copy Directory'),
    arcGISToolCategory=_('Data Management\\Directories\\Copy'))

AddArgumentMetadata(Directory.Copy, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=Directory),
    description=_(':class:`%s` class or an instance of it.') % Directory.__name__)

AddArgumentMetadata(Directory.Copy, 'sourceDirectory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_('Directory to copy. The directory may contain subdirectories and files. Other types of file system objects, such as symbolic links, are not allowed.'),
    arcGISDisplayName=_('Source directory'))

AddArgumentMetadata(Directory.Copy, 'destinationDirectory',
    typeMetadata=DirectoryTypeMetadata(mustBeDifferentThanArguments=['sourceDirectory'], createParentDirectories=True),
    description=_('Copy to create. Missing directories in this path will be created if they do not exist.'),
    direction='Output',
    arcGISDisplayName=_('Destination directory'))

AddArgumentMetadata(Directory.Copy, 'deleteExistingDestinationDirectory',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""This parameter is ignored if the destination directory does not already
exist. If True, the existing destination directory, including all
subdirectories and files, will be deleted and replaced with the source
directory. If False, the destination directory will not be deleted first, and
the files in the source directory (and all subdirectories) will be copied into
the existing destination directory."""))

AddArgumentMetadata(Directory.Copy, 'overwriteExistingFiles',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, destination files will be overwritten, if they exist. If False, a
:py:exc:`ValueError` will be raised if any destination file exists. This
parameter is ignored if `deleteExistingDestinationDirectory` is True, since
that parameter will cause any existing files to be deleted."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

# Public method: Directory.Create

AddMethodMetadata(Directory.Create,
    shortDescription=_('Creates a directory, including any parent directories that are missing.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Directory'),
    arcGISToolCategory=_('Data Management\\Directories\\Create'))

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.Create, 'cls')

AddArgumentMetadata(Directory.Create, 'directory',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Directory to create. Missing directories in this path will be created if they do not exist.'),
    direction='Output',
    arcGISDisplayName=_('Directory'))

# Public method: Directory.CreateSubdirectory

AddMethodMetadata(Directory.CreateSubdirectory,
    shortDescription=_('Creates a subdirectory within a parent directory.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Subdirectory'),
    arcGISToolCategory=_('Data Management\\Directories\\Create'))

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.CreateSubdirectory, 'cls')

AddArgumentMetadata(Directory.CreateSubdirectory, 'parentDirectory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_('Directory in which the subdirectory should be created.'),
    arcGISDisplayName=_('Parent directory'))

AddArgumentMetadata(Directory.CreateSubdirectory, 'subdirectoryName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the subdirectory to create. You may specify a simple directory
name, such as ``MyDir``, or a relative path that includes subdirectories, such
as ``FirstLevel\\SecondLevel\\MyDir``. Whatever you specify will be appended
to the parent directory and all missing directories in the complete path will
be created."""),
    arcGISDisplayName=_('Subdirectory name'))

AddResultMetadata(Directory.CreateSubdirectory, 'subdirectory',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Path of the newly-created subdirectory.'),
    arcGISDisplayName=_('Subdirectory'))

# Public method: Directory.CreateTemporaryDirectory

AddMethodMetadata(Directory.CreateTemporaryDirectory,
    shortDescription=_('Creates a directory suitable for holding temporary files.'),
    longDescription=_(
"""The directory's path will take the form
``parentDirectory/GeoEcoTemp/randomName`` (On Windows computers, backslashes
will be used instead of forward slashes.) ``parentDirectory`` will be one of
the following locations (the first one that is found to exist):

1. The ArcGIS geoprocessor's ``arcpy.env.ScratchWorkspace`` if it has been set
   to something.
2. The directory named by the ``TMPDIR`` environment variable. 
3. The directory named by the ``TEMP`` environment variable. 
4. The directory named by the ``TMP`` environment variable. 
5. A platform-specific location: 
   - On Windows, the directories ``C:\\TEMP``, ``C:\\TMP``, ``\\TEMP``, and ``\\TMP``, in that order. 
   - On all other platforms, the directories ``/tmp``, ``/var/tmp``, and ``/usr/tmp``, in that order. 
6. As a last resort, the current working directory of the process hosting the
   Python interpreter.

``randomName`` will be a random, non-existing name beginning with ``tmp``.

You must manually delete the temporary directory when you are finished using it.
(It will not be automatically deleted for you.)"""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Create Temporary Directory'),
    arcGISToolCategory=_('Data Management\\Directories\\Create'))

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.CreateTemporaryDirectory, 'cls')

AddResultMetadata(Directory.CreateTemporaryDirectory, 'directory',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Path of the newly-created temporary directory.'),
    arcGISDisplayName=_('Directory'))

# Public method: Directory.Delete

AddMethodMetadata(Directory.Delete,
    shortDescription=_('Deletes a directory.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Delete Directory'),
    arcGISToolCategory=_('Data Management\\Directories\\Delete'))

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.Delete, 'cls')

AddArgumentMetadata(Directory.Delete, 'directory',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Directory to delete.'),
    arcGISDisplayName=_('Directory'))

AddArgumentMetadata(Directory.Delete, 'removeTree',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, all files and subdirectories contained in the directory will be
deleted. If False, the directory must be empty or deletion will fail."""),
    arcGISDisplayName=_('Remove entire tree'))

# Public method: Directory.Exists

AddMethodMetadata(Directory.Exists,
    shortDescription=_('Tests that a specified path exists and is a directory.'))

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.Exists, 'cls')

AddArgumentMetadata(Directory.Exists, 'path',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Path to test.'))

AddResultMetadata(Directory.Exists, 'result',
    typeMetadata=TupleTypeMetadata(elementType=BooleanTypeMetadata(), minLength=2, maxLength=2),
    description=_('A two-item :py:class:`tuple`, where the first item is True if the specified path exists, and the second is True if the specified path exists and is a directory.'))

# Public method: Directory.Find

AddMethodMetadata(Directory.Find,
    shortDescription=_('Finds subdirectories within a directory.'),
    longDescription=_(
"""On Windows, this function makes no distinction between hidden and
visible directories. Hidden directories are traversed and handled just
like visible directories.

Directories are returned in an arbitrary order determined by the
operating system and the search algorithm."""))

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.Find, 'cls')

AddArgumentMetadata(Directory.Find, 'directory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_('Directory to search.'),
    arcGISDisplayName=_('Directory to search'))

AddArgumentMetadata(Directory.Find, 'wildcard',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""UNIX-style "glob" wildcard expression specifying the directories
to find.

The glob syntax supports the following patterns:

* ``?`` - matches any single character
* ``*`` - matches zero or more characters
* ``[seq]`` - matches any single character in ``seq``
* ``[!seq]`` - matches any single character not in ``seq``

``seq`` is one or more characters, such as ``abc``. You may specify character
ranges using a dash. For example, ``a-z0-9`` specifies all of the characters
in the English alphabet and the decimal digits ``0`` through ``9``.

You may specify subdirectories in the glob expression. For example, the
expression ``cruise*/sst*`` will find all paths beginning with sst that are
contained in directories beginning with cruise.

The operating system determines whether ``/`` or ``\\`` is used as the
directory separator. On Windows, both will work. On Linux, ``/`` must be used.

The operating system determines if matching is case sensitive. On Windows,
matching is case-insensitive. On Linux, matching is case-sensitive."""),
    arcGISDisplayName=_('Wildcard expression'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(Directory.Find, 'searchTree',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, subdirectories will be searched.'),
    arcGISDisplayName=_('Search directory tree'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(Directory.Find, 'mustBeEmpty',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, only empty directories will be found.'),
    arcGISDisplayName=_('Directories must be empty'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(Directory.Find, 'mustNotBeEmpty',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, only non-empty directories will be found.'),
    arcGISDisplayName=_('Directories must not be empty'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(Directory.Find, 'minDateCreated',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Minimum creation date, in the local time zone, of the directories to find,
as reported by the operating system. If provided, only directories that were
created on or after this date will be found. You may provide a date with or
without a time. If you do not provide a time, it is assumed to be
midnight."""),
    arcGISDisplayName=_('Minimum creation date'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(Directory.Find, 'maxDateCreated',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Maximum creation date, in the local time zone, of the directories to find,
as reported by the operating system. If provided, only directories that were
created on or before this date will be found. You may provide a date with or
without a time. If you do not provide a time, it is assumed to be
midnight."""),
    arcGISDisplayName=_('Maximum creation date'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(Directory.Find, 'minDateModified',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Minimum modification date, in the local time zone, of the directories to
find, as reported by the operating system. If provided, only directories that
were modified on or after this date will be found. You may provide a date with
or without a time. If you do not provide a time, it is assumed to be
midnight."""),
    arcGISDisplayName=_('Minimum modification date'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(Directory.Find, 'maxDateModified',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Maximum modification date, in the local time zone, of the directories to
find, as reported by the operating system. If provided, only directories that
were modified on or before this date will be found. You may provide a date
with or without a time. If you do not provide a time, it is assumed to be
midnight."""),
    arcGISDisplayName=_('Maximum modification date'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(Directory.Find, 'basePath',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Absolute path from which relative paths to the directories will be
calculated. If provided, relative paths will be calculated and returned by
this function.

For example, if the base path was::

    C:\\Data\\Files

the relative paths for the directories::

    C:\\Data\\Files\\Group1\\d1
    C:\\Data\\Files\\d1
    C:\\Data\\d1
    C:\\d1
    D:\\d1
    \\\\MyServer\\Data\\d1

would be::    

    Group1\\d1
    d1
    ..\\d1
    ..\\..\\d1
    D:\\d1
    \\\\MyServer\\Data\\d1

"""))

AddArgumentMetadata(Directory.Find, 'getDateCreated',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""'If True, the creation date of each directory will be returned by this
function."""))

AddArgumentMetadata(Directory.Find, 'getDateModified',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""'If True, the modification date of each directory will be returned by this
function."""))

_DateParsingExpressionSyntaxDocumentation = _(
"""The expression is a standard Python :py:ref:`re-syntax` with additional
codes for matching fragments of dates:

    ``%d`` - Day of the month as a decimal number (range: ``01`` to ``31``)

    ``%H`` - Hour (24-hour clock) as a decimal number (range: ``00`` to ``23``)

    ``%j`` - Day of the year as a decimal number (range: ``001`` to ``366``)

    ``%m`` - Month as a decimal number (range: ``01`` to ``12``)

    ``%M`` - Minute as a decimal number (range: ``00`` to ``59``)

    ``%S`` - Second as a decimal number (range: ``00`` to ``61``)

    ``%y`` - Year without century as a decimal number (range: ``00`` to ``99``)

    ``%Y`` - Year with century as a decimal number (range: ``0001`` to ``9999``)

    ``%%`` - A literal ``%`` character

A date is parsed from a path as follows:

1. The date fragment codes in your expression are replaced by regular
   expression groups to produce a true regular expression. For example, if
   your expression is ``%Y_%m_%d``, it is converted to the regular expression
   ``(\\d\\d\\d\\d)_(\\d\\d)_(\\d\\d)``.

2. :py:func:`re.search` is invoked to find the first occurrence of the regular
   expression in the path. The search proceeds from left to right.

3. If an occurrence is found, the regular expression groups are extracted and
   :py:func:`time.strptime` is invoked to parse a date from the groups.

Notes:

* Your expression must include at least one date fragment code, but it need
  not include all of them. If a particular code is missing, the following
  default values will be used: year ``1900``, month ``01``, day ``01``, hour
  ``00``, minute ``00``, second ``00``.

* You cannot specify a given date fragment code more than once.

* You cannot specify date fragment codes that might conflict. For example, you
  cannot specify both ``%j`` and ``%d`` because this could result in
  conflicting values for the day.

* For ``%y``, values ``00`` to ``68`` are interpreted as years ``2000``
  through ``2068``, while ``69`` through ``99`` are interpreted as years
  ``1969`` through ``1999``.

* Remember that the entire path is searched for your expression, from left to
  right. The first occurrence of it may be in the parent directories.

* The date fragment codes are case-sensitive.

* If the underlying storage format can hold the time as well as the date in a
  single field, the time will be stored along with the date. If the table
  cannot hold the time and date in a single field, then only the date will be
  stored. This is the case, for example, with dBASE III and IV tables (.dbf
  files), often used by ArcGIS.

* The timezone of the parsed date is assumed to be UTC.

Example:

The expression::

    %Y.*%j

will parse dates from a series of directories similar to those maintained by
NASA PO.DAAC for holding GOES SST data, in which the date and day of year
define the subdirectory structure::

    C:\\SST\\goes10-12\\2005\\001
    C:\\SST\\goes10-12\\2005\\002
    C:\\SST\\goes10-12\\2005\\003
    ...

""")

AddArgumentMetadata(Directory.Find, 'dateParsingExpression',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""'Expression for parsing dates from the paths of each directory. If
provided, dates will be parsed and returned by this function.

""") +
_DateParsingExpressionSyntaxDocumentation)

AddResultMetadata(Directory.Find, 'directories',
    typeMetadata=ListTypeMetadata(ListTypeMetadata(elementType=AnyObjectTypeMetadata())),
    description=_(
""":py:class:`list` of :py:class:`list`\\ s of the directories that were found
and the requested metadata about them. The items of the inner
:py:class:`list`\\ s are:

* Path (:py:class:`str`) - always returned.

* Relative path (:py:class:`str`) - only returned if `basePath` is provided.

* Creation date (:py:class:`~datetime.datetime`) - only returned if
  `getCreationDate` is True.

* Modification date (:py:class:`~datetime.datetime`) - only returned if
  `getModificationDate` is True.

* Parsed date (:py:class:`~datetime.datetime`) - only returned if
  `dateParsingExpression` is provided.

* Parsed UNIX time (:py:class:`int`) - only returned if
  `dateParsingExpression` is provided. It is the same value as the previous
  column, but in UNIX time format. UNIX times are 32-bit signed integers that
  are the number of seconds since 1970-01-01 00:00:00 UTC. This tool assumes
  the date that was parsed is in the UTC timezone. The UNIX time values
  produced by this tool do not include leap seconds; this tool assumes that a
  regular year is 31536000 seconds and a leap year is 31622400 seconds.

"""))

# Public method: Directory.FindAndFillTable

AddMethodMetadata(Directory.FindAndFillTable,
    shortDescription=_('Finds subdirectories within a directory and inserts a row for each one into an existing table.'),
    longDescription=Directory.Find.__doc__.Obj.LongDescription)

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.FindAndFillTable, 'cls')
CopyArgumentMetadata(Directory.Find, 'directory', Directory.FindAndFillTable, 'directory')

AddArgumentMetadata(Directory.FindAndFillTable, 'insertCursor',
    typeMetadata=ClassInstanceTypeMetadata(cls=InsertCursor),
    description=_('Insert cursor opened to the table that will receive the rows. The cursor will still be open when this function returns.'))

AddArgumentMetadata(Directory.FindAndFillTable, 'directoryField',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the field to receive absolute paths to the directories that were found.'),
    arcGISDisplayName=_('Directory path field'))

CopyArgumentMetadata(Directory.Find, 'wildcard', Directory.FindAndFillTable, 'wildcard')
CopyArgumentMetadata(Directory.Find, 'searchTree', Directory.FindAndFillTable, 'searchTree')
CopyArgumentMetadata(Directory.Find, 'mustBeEmpty', Directory.FindAndFillTable, 'mustBeEmpty')
CopyArgumentMetadata(Directory.Find, 'mustNotBeEmpty', Directory.FindAndFillTable, 'mustNotBeEmpty')
CopyArgumentMetadata(Directory.Find, 'minDateCreated', Directory.FindAndFillTable, 'minDateCreated')
CopyArgumentMetadata(Directory.Find, 'maxDateCreated', Directory.FindAndFillTable, 'maxDateCreated')
CopyArgumentMetadata(Directory.Find, 'minDateModified', Directory.FindAndFillTable, 'minDateModified')
CopyArgumentMetadata(Directory.Find, 'maxDateModified', Directory.FindAndFillTable, 'maxDateModified')

AddArgumentMetadata(Directory.FindAndFillTable, 'relativePathField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive paths of the directories that were found,
relative to `basePath`. For example, if `basePath` was::

    C:\\Data\\Files

the relative paths for the directories::

    C:\\Data\\Files\\Group1\\d1
    C:\\Data\\Files\\d1
    C:\\Data\\d1
    C:\\d1
    D:\\d1
    \\\\MyServer\\Data\\d1

would be::    

    Group1\\d1
    d1
    ..\\d1
    ..\\..\\d1
    D:\\d1
    \\\\MyServer\\Data\\d1

"""))

AddArgumentMetadata(Directory.FindAndFillTable, 'basePath',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Absolute path from which relative paths will be calculated and stored in
the `relativePathField`. Please see the documentation for that field for more
information."""))

AddArgumentMetadata(Directory.FindAndFillTable, 'dateCreatedField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive the creation dates of the directories that
were found."""),
    arcGISDisplayName=_('Directory creation date field'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(Directory.FindAndFillTable, 'dateModifiedField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive the modification dates of the directories that
were found."""),
    arcGISDisplayName=_('Directory modification date field'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(Directory.FindAndFillTable, 'parsedDateField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive dates parsed from the paths of the directories
that were found. You must also specify a date parsing expression."""),
    arcGISDisplayName=_('Parsed date field'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(Directory.FindAndFillTable, 'dateParsingExpression',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Expression for parsing dates from the paths of the directories that were
found. The expression will be ignored if you do not also specify a field to
receive the dates or the equivalent UNIX time.

""") + _DateParsingExpressionSyntaxDocumentation,
    arcGISDisplayName=_('Date parsing expression'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(Directory.FindAndFillTable, 'unixTimeField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive dates, in "UNIX time" format, parsed from the
paths of the directories that were found. You must also specify a date parsing
expression.

UNIX times are 32-bit signed integers that are the number of seconds since
1970-01-01 00:00:00 UTC. This tool assumes the date that was parsed is in the
UTC timezone. The UNIX time values produced by this tool do not include leap
seconds; this tool assumes that a regular year is 31536000 seconds and a leap
year is 31622400 seconds."""),
    arcGISDisplayName=_('UNIX time field'),
    arcGISCategory=_('Output table options'))

# Public method: Directory.FindAndCreateTable

AddMethodMetadata(Directory.FindAndCreateTable,
    shortDescription=_('Finds subdirectories within a directory and creates a table that lists them.'),
    longDescription=Directory.Find.__doc__.Obj.LongDescription)

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.FindAndCreateTable, 'cls')
CopyArgumentMetadata(Directory.Find, 'directory', Directory.FindAndCreateTable, 'directory')

AddArgumentMetadata(Directory.FindAndCreateTable, 'database',
    typeMetadata=ClassInstanceTypeMetadata(cls=Database),
    description=_('Database that will receive the new table.'))

AddArgumentMetadata(Directory.FindAndCreateTable, 'table',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the table to create. The table must not exist.'))

CopyArgumentMetadata(Directory.FindAndFillTable, 'directoryField', Directory.FindAndCreateTable, 'directoryField')
CopyArgumentMetadata(Directory.FindAndFillTable, 'wildcard', Directory.FindAndCreateTable, 'wildcard')
CopyArgumentMetadata(Directory.FindAndFillTable, 'searchTree', Directory.FindAndCreateTable, 'searchTree')
CopyArgumentMetadata(Directory.FindAndFillTable, 'mustBeEmpty', Directory.FindAndCreateTable, 'mustBeEmpty')
CopyArgumentMetadata(Directory.FindAndFillTable, 'mustNotBeEmpty', Directory.FindAndCreateTable, 'mustNotBeEmpty')
CopyArgumentMetadata(Directory.FindAndFillTable, 'minDateCreated', Directory.FindAndCreateTable, 'minDateCreated')
CopyArgumentMetadata(Directory.FindAndFillTable, 'maxDateCreated', Directory.FindAndCreateTable, 'maxDateCreated')
CopyArgumentMetadata(Directory.FindAndFillTable, 'minDateModified', Directory.FindAndCreateTable, 'minDateModified')
CopyArgumentMetadata(Directory.FindAndFillTable, 'maxDateModified', Directory.FindAndCreateTable, 'maxDateModified')
CopyArgumentMetadata(Directory.FindAndFillTable, 'relativePathField', Directory.FindAndCreateTable, 'relativePathField')
CopyArgumentMetadata(Directory.FindAndFillTable, 'basePath', Directory.FindAndCreateTable, 'basePath')
CopyArgumentMetadata(Directory.FindAndFillTable, 'dateCreatedField', Directory.FindAndCreateTable, 'dateCreatedField')
CopyArgumentMetadata(Directory.FindAndFillTable, 'dateModifiedField', Directory.FindAndCreateTable, 'dateModifiedField')
CopyArgumentMetadata(Directory.FindAndFillTable, 'parsedDateField', Directory.FindAndCreateTable, 'parsedDateField')
CopyArgumentMetadata(Directory.FindAndFillTable, 'dateParsingExpression', Directory.FindAndCreateTable, 'dateParsingExpression')
CopyArgumentMetadata(Directory.FindAndFillTable, 'unixTimeField', Directory.FindAndCreateTable, 'unixTimeField')

AddArgumentMetadata(Directory.FindAndCreateTable, 'pathFieldsDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the directory path fields. This should be
``string`` unless you have a specific reason to choose something else."""))

AddArgumentMetadata(Directory.FindAndCreateTable, 'dateFieldsDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the directory creation date, directory
modification date, and parsed date fields. This should be ``datetime`` if the
underlying storage format supports dates with times, or ``date`` if only dates
are supported."""))

AddArgumentMetadata(Directory.FindAndCreateTable, 'unixTimeFieldDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the UNIX date field. Because UNIX dates are
32-bit signed integers, this should be ``int32`` or ``int64``."""))

AddArgumentMetadata(Directory.FindAndCreateTable, 'maxPathLength',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=1),
    description=_(
"""Maximum length of a path for this operating system. This value is used to
specify the width of the field that is created. You should provide a value
only if the underlying database requires that you specify a width for string
fields. If you provide a value that is too small to hold one of the paths that
is found, this function will fail when it finds that path."""))

AddArgumentMetadata(Directory.FindAndCreateTable, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output table will be overwritten, if it exists. If False, a
:py:exc:`ValueError` will be raised if the output table exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

AddResultMetadata(Directory.FindAndCreateTable, 'createdTable',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the table that was created.'))

# Public method: Directory.FindAndCreateArcGISTable

AddMethodMetadata(Directory.FindAndCreateArcGISTable,
    shortDescription=_('Finds subdirectories within a directory and creates a table that lists them.'),
    longDescription=Directory.FindAndCreateTable.__doc__.Obj.LongDescription,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Find Directories'),
    arcGISToolCategory=_('Data Management\\Directories'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.FindAndCreateArcGISTable, 'cls')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'directory', Directory.FindAndCreateArcGISTable, 'directory')

AddArgumentMetadata(Directory.FindAndCreateArcGISTable, 'workspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(mustExist=True),
    description=_('Workspace in which the table should be created.'),
    arcGISDisplayName=_('Output workspace'))

AddArgumentMetadata(Directory.FindAndCreateArcGISTable, 'table',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name of the table to create.

If the output workspace is a directory (rather than a database) a dBASE table
(.dbf file) will be created. It is not possible to create other types of
tables in the file system (e.g. comma or space-delimited text files). This
restriction is imposed by the ArcGIS :arcpy_management:`Create-Table` tool,
which is used to create the table. If you omit an extension from the table
name, .dbf will be added automatically. If you specify another extension, such
as .csv or .txt, it will be replaced with .dbf."""),
    arcGISDisplayName=_('Output table name'))

CopyArgumentMetadata(Directory.FindAndCreateTable, 'directoryField', Directory.FindAndCreateArcGISTable, 'directoryField')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'wildcard', Directory.FindAndCreateArcGISTable, 'wildcard')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'searchTree', Directory.FindAndCreateArcGISTable, 'searchTree')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'mustBeEmpty', Directory.FindAndCreateArcGISTable, 'mustBeEmpty')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'mustNotBeEmpty', Directory.FindAndCreateArcGISTable, 'mustNotBeEmpty')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'minDateCreated', Directory.FindAndCreateArcGISTable, 'minDateCreated')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'maxDateCreated', Directory.FindAndCreateArcGISTable, 'maxDateCreated')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'minDateModified', Directory.FindAndCreateArcGISTable, 'minDateModified')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'maxDateModified', Directory.FindAndCreateArcGISTable, 'maxDateModified')

AddArgumentMetadata(Directory.FindAndCreateArcGISTable, 'relativePathField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive paths of the directories that were found,
relative to the database or directory that contains the output table. For
example, if the path to the table is::

    C:\\Data\\Files\\FoundFiles.dbf

the relative paths for the directories::

    C:\\Data\\Files\\Group1\\d1
    C:\\Data\\Files\\d1
    C:\\Data\\d1
    C:\\d1
    D:\\d1
    \\\\MyServer\\Data\\d1

would be::    

    Group1\\d1
    d1
    ..\\d1
    ..\\..\\d1
    D:\\d1
    \\\\MyServer\\Data\\d1

If the table is in a file geodatabase::

    C:\\Data\\Files\\FileInfo.gdb\\FoundFiles

the relative paths would be::    

    ..\\Group1\\d1
    ..\\d1
    ..\\..\\d1
    ..\\..\\..\\d1
    D:\\d1
    \\\\MyServer\\Data\\d1

"""),
    arcGISDisplayName=_('Relative path field'),
    arcGISCategory=_('Output table options'))

CopyArgumentMetadata(Directory.FindAndCreateTable, 'dateCreatedField', Directory.FindAndCreateArcGISTable, 'dateCreatedField')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'dateModifiedField', Directory.FindAndCreateArcGISTable, 'dateModifiedField')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'parsedDateField', Directory.FindAndCreateArcGISTable, 'parsedDateField')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'dateParsingExpression', Directory.FindAndCreateArcGISTable, 'dateParsingExpression')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'unixTimeField', Directory.FindAndCreateArcGISTable, 'unixTimeField')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'maxPathLength', Directory.FindAndCreateArcGISTable, 'maxPathLength')
CopyArgumentMetadata(Directory.FindAndCreateTable, 'overwriteExisting', Directory.FindAndCreateArcGISTable, 'overwriteExisting')

AddResultMetadata(Directory.FindAndCreateArcGISTable, 'createdTable',
    typeMetadata=ArcGISTableTypeMetadata(),
    description=_('Table that was created.'),
    arcGISDisplayName=_('Output table'))

# Public method: Directory.Move

AddMethodMetadata(Directory.Move,
    shortDescription=_('Moves a directory, including its subdirectories and files.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Move Directory'),
    arcGISToolCategory=_('Data Management\\Directories\\Move'))

CopyArgumentMetadata(Directory.Copy, 'cls', Directory.Move, 'cls')

AddArgumentMetadata(Directory.Move, 'sourceDirectory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_(
"""Directory to move. The directory may contain subdirectories and files.
Other types of file system objects, such as symbolic links, are not
allowed."""),
    arcGISDisplayName=_('Source directory'))

AddArgumentMetadata(Directory.Move, 'destinationDirectory',
    typeMetadata=DirectoryTypeMetadata(mustBeDifferentThanArguments=['sourceDirectory'], createParentDirectories=True),
    description=_(
"""New path for the directory.

If the destination directory is on the same drive or file system as the source
directory, the source directory will simply be renamed to the destination
directory.

If the destination directory is on a different drive or file system, the
source directory will be copied to the destination directory and then
deleted."""),
    direction='Output',
    arcGISDisplayName=_('Destination directory'))

AddArgumentMetadata(Directory.Move, 'deleteExistingDestinationDirectory',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""This parameter is ignored if the destination directory does not already
exist. If True, the existing destination directory, including all
subdirectories and files, will be deleted and replaced with the source
directory. If False, the destination directory will not be deleted first, and
the files in the source directory (and all subdirectories) will be moved into
the existing destination directory."""))

CopyArgumentMetadata(Directory.Copy, 'overwriteExistingFiles', Directory.Move, 'overwriteExistingFiles')


###############################################################################
# Metadata: TemporaryDirectory class
###############################################################################

AddClassMetadata(TemporaryDirectory,
    shortDescription=_('Represents a temporary working directory, suitable for storing temporary files during processing.'),
    longDescription=_(
"""Note:
    This class is part of the internal implementation of GeoEco and is not
    intended to be used by external callers."""))

# Public properties

AddPropertyMetadata(TemporaryDirectory.AutomaticallyDelete,
    typeMetadata=BooleanTypeMetadata(),
    shortDescription=_(
"""If True (the default), the directory will be automatically deleted with the
last reference to the :class:`TemporaryDirectory` object is released and
``TemporaryDirectory.__del__()`` is called by the Python garbage collector. If
False, the directory will not be automatically deleted. The caller should
delete the directory. Non-automatic deletion is used primarily for debugging
during GeoEco development."""))

# Constructor

AddMethodMetadata(TemporaryDirectory.__init__,
    shortDescription=_(
"""Constructs a new :class:`%s` instance and creates a randomly-named
directory in the location suitable for holding temporary directories.""") % Metadata.__name__,
    longDescription=_(
"""The directory is created by calling
:func:`GeoEco.DataManagement.Directories.Directory.CreateTemporaryDirectory`.
Please see the documentation for that function for more information on where
the directory is created and what it it is named."""))

AddArgumentMetadata(TemporaryDirectory.__init__, 'self',
    typeMetadata=ClassInstanceTypeMetadata(cls=TemporaryDirectory),
    description=_(':class:`%s` instance.') % TemporaryDirectory.__name__)

AddArgumentMetadata(TemporaryDirectory.__init__, 'automaticallyDelete',
    typeMetadata=TemporaryDirectory.AutomaticallyDelete.__doc__.Obj.Type,
    description=TemporaryDirectory.AutomaticallyDelete.__doc__.Obj.ShortDescription)

AddResultMetadata(TemporaryDirectory.__init__, 'tempDir',
    typeMetadata=ClassInstanceTypeMetadata(cls=TemporaryDirectory),
    description=_(':class:`%s` instance.') % TemporaryDirectory.__name__)

# Destructor

AddMethodMetadata(TemporaryDirectory.__del__,
    shortDescription=_('Deletes the temporary directory.'))

CopyArgumentMetadata(TemporaryDirectory.__init__, 'self', TemporaryDirectory.__del__, 'self')

# Public Properties

AddPropertyMetadata(TemporaryDirectory.Path,
    typeMetadata=DirectoryTypeMetadata(),
    shortDescription=_('Path of the temporary directory.'))

# Public method: TemporaryDirectory.DecompressInputArgument

AddMethodMetadata(TemporaryDirectory.DecompressInputArgument,
    shortDescription=_('Decompresses the file specified by a method\'s input argument into the temporary directory.'),
    longDescription=_(
"""Note:
    This method is part of the internal implementation of GeoEco and is not
    intended to be used by external callers.

:func:`DecompressInputArgument` is intended to be called from methods that
allow their callers to pass in the path of a compressed file as an input
argument. If the passed-in path is a compressed file,
:func:`DecompressInputArgument` will decompress it to the temporary directory
and return the path of the decompressed file. If the passed-in path is not a
compressed file, :func:`DecompressInputArgument` will return the passed-in
path.

For a usage example, see
:func:`GeoEco.DataManagement.BinaryRasters.BinaryRaster.SwapBytes`."""))

CopyArgumentMetadata(TemporaryDirectory.__init__, 'self', TemporaryDirectory.DecompressInputArgument, 'self')

AddArgumentMetadata(TemporaryDirectory.DecompressInputArgument, 'argName',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Name an input argument that may be a compressed file.

The calling method must pass in the name of one of its arguments. Do not pass
in the path of the compressed file. The
:attr:`~GeoEco.Metadata.ArgumentMetadata.Type` for the argument must be an
instance of :class:`~GeoEco.Types.FileTypeMetadata`.
:func:`DecompressInputArgument` obtains the value of the argument (the path of
the compressed file) from the local variables of the calling method's stack
frame."""))

AddResultMetadata(TemporaryDirectory.DecompressInputArgument, 'decompressedFile',
    typeMetadata=FileTypeMetadata(),
    description=_(
"""Path of the decompressed file.

If the path provided to the calling function for the named argument is a path
to a file that is not compressed, it will be returned.

If it is a path to a compressed file that is not an archive (i.e. only one
file is compressed within it), the compressed file will be extracted to a
subdirectory in the temporary directory, and the path to the decompressed file
will be returned.

If the compressed file is an archive, the return value is the path to the
decompressed file specified by the
:attr:`~GeoEco.Types.FileTypeMetadata.DecompressedFileToUse` property of the
:class:`~GeoEco.Types.FileTypeMetadata` for the named argument."""))


###############################################################################
# Batch processing versions of methods
###############################################################################

from GeoEco.BatchProcessing import BatchProcessing
from GeoEco.DataManagement.Fields import Field

BatchProcessing.GenerateForMethod(Directory.Copy,
    inputParamNames=['sourceDirectory'],
    inputParamFieldArcGISDisplayNames=[_('Source directory field')],
    inputParamDescriptions=[_(
"""%s paths of the directories to copy.

The directories may contain subdirectories and files. Other types of
file system objects, such as symbolic links, are not allowed.""")],
    outputParamNames=['destinationDirectory'],
    outputParamFieldArcGISDisplayNames=[_('Destination directory field')],
    outputParamExpressionArcGISDisplayNames=[_('Destination directory Python expression')],
    outputParamDescriptions=[_('%s paths of the destination directories.')],
    outputParamExpressionDescriptions=[
"""Python expression used to calculate the absolute path of the destination
directory. The expression may be any Python statement appropriate for passing
to the eval function and must return a Unicode string. The expression may
reference the following variables:

* ``directoryToSearch`` - the value provided for the directory to search
  parameter

* ``rootDestination`` - the value provided for the root destination
  directory parameter

* ``sourceDirectory`` - the absolute path of the source directory

The default expression, 
``os.path.join(rootDestination, sourceDirectory[len(directoryToSearch)+1:])``,
copies the directory to the root destination directory to the same relative
location as it appears in the directory to search. The destination directory
path is calculated by stripping the directory to search from the source
directory and replacing it with the root destination directory.

For more information on Python syntax, please see the `Python documentation
<http://www.python.org/doc/>`_."""],
    outputParamDefaultExpressions=['os.path.join(rootDestination, sourceDirectory[len(directoryToSearch)+1:])'],
    processListMethodName='CopyList',
    processListMethodShortDescription=_('Copies a list of directories.'),
    processTableMethodName='CopyTable',
    processTableMethodShortDescription=_('Copies the directories listed in a table.'),
    processArcGISTableMethodName='CopyArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Copy Directories Listed in Table'),
    findAndProcessMethodName='FindAndCopy',
    findAndProcessMethodArcGISDisplayName='Find and Copy Directories',
    findAndProcessMethodShortDescription=_('Finds and copies directories in a directory.'),
    findMethod=Directory.FindAndCreateTable,
    findOutputFieldParams=['directoryField'],
    findAdditionalParams=['wildcard', 'searchTree', 'mustBeEmpty', 'mustNotBeEmpty', 'minDateCreated', 'maxDateCreated', 'minDateModified', 'maxDateModified'],
    outputLocationTypeMetadata=DirectoryTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Directory to receive copies of the directories.'),
    outputLocationParamArcGISDisplayName=_('Root destination directory'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    directoryToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputDirectory\']\n    rootDestination = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputDirectory\']\nfinally:\n    del f\n'], ['sourceDirectory = row.sourceDirectory']],
    calculatedOutputsArcGISCategory=_('Destination directory name options'),
    skipExistingDescription=_('If True, copying will be skipped for destination directories that already exist.'))

BatchProcessing.GenerateForMethod(Directory.Delete,
    inputParamNames=['directory'],
    inputParamFieldArcGISDisplayNames=[_('Directory field')],
    inputParamDescriptions=[_('%s paths of the directories to delete.')],
    constantParamNames=['removeTree'],
    processListMethodName='DeleteList',
    processListMethodShortDescription=_('Deletes a list of directories.'),
    processTableMethodName='DeleteTable',
    processTableMethodShortDescription=_('Deletes the directories listed in a table.'),
    processArcGISTableMethodName='DeleteArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Delete Directories Listed in Table'),
    findAndProcessMethodName='FindAndDelete',
    findAndProcessMethodArcGISDisplayName='Find and Delete Directories',
    findAndProcessMethodShortDescription=_('Finds and deletes directories in a directory.'),
    findMethod=Directory.FindAndCreateTable,
    findOutputFieldParams=['directoryField'],
    findAdditionalParams=['wildcard', 'searchTree', 'mustBeEmpty', 'mustNotBeEmpty', 'minDateCreated', 'maxDateCreated', 'minDateModified', 'maxDateModified'])

BatchProcessing.GenerateForMethod(Directory.Move,
    inputParamNames=['sourceDirectory'],
    inputParamFieldArcGISDisplayNames=[_('Source directory field')],
    inputParamDescriptions=[_('%s paths of the directories to move.')],
    outputParamNames=['destinationDirectory'],
    outputParamFieldArcGISDisplayNames=[_('Destination directory field')],
    outputParamExpressionArcGISDisplayNames=[_('Destination directory Python expression')],
    outputParamDescriptions=[_('%s paths of the destination directories.')],
    outputParamExpressionDescriptions=[Directory.FindAndCopy.__doc__.Obj.GetArgumentByName('destinationDirectoryPythonExpression').Description],
    outputParamDefaultExpressions=[Directory.FindAndCopy.__doc__.Obj.GetArgumentByName('destinationDirectoryPythonExpression').Default],
    processListMethodName='MoveList',
    processListMethodShortDescription=_('Moves a list of directories.'),
    processTableMethodName='MoveTable',
    processTableMethodShortDescription=_('Moves the directories listed in a table.'),
    processArcGISTableMethodName='MoveArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Move Directories Listed in Table'),
    findAndProcessMethodName='FindAndMove',
    findAndProcessMethodArcGISDisplayName='Find and Move Directories',
    findAndProcessMethodShortDescription=_('Finds and moves directories in a directory.'),
    findMethod=Directory.FindAndCreateTable,
    findOutputFieldParams=['directoryField'],
    findAdditionalParams=['wildcard', 'searchTree', 'mustBeEmpty', 'mustNotBeEmpty', 'minDateCreated', 'maxDateCreated', 'minDateModified', 'maxDateModified'],
    outputLocationTypeMetadata=DirectoryTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Directory to receive the directories.'),
    outputLocationParamArcGISDisplayName=_('Root destination directory'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    directoryToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputWorkspace\']\n    rootDestination = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputWorkspace\']\nfinally:\n    del f\n'], ['sourceDirectory = row.sourceDirectory']],
    calculatedOutputsArcGISCategory=_('Destination directory name options'),
    skipExistingDescription=_('If True, moving will be skipped for destination directories that already exist.'))


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['Directory', 'TemporaryDirectory']
