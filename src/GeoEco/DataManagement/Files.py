# DataManagement/Files.py - Methods for performing common file operations.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import bz2
import datetime
import glob
import gzip
import inspect
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
import zipfile
import zlib

from ..DynamicDocString import DynamicDocString
from ..Internationalization import _
from ..Logging import Logger


class File(object):
    __doc__ = DynamicDocString()

    @classmethod
    def Copy(cls, sourceFile, destinationFile, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        Logger.Info(_('Copying file %(source)s to %(dest)s') % {'source' :  sourceFile, 'dest' : destinationFile})
        try:
            shutil.copy2(sourceFile, destinationFile)        
        except:
            Logger.LogExceptionAsError(_('Could not copy file %(source)s to %(dest)s') % {'source' :  sourceFile, 'dest' : destinationFile})
            raise

    @classmethod
    def CopySilent(cls, sourceFile, destinationFile, overwriteExisting=False):
        oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
        Logger.SetLogInfoAsDebug(True)
        try:
            cls.Copy(sourceFile, destinationFile, overwriteExisting)
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def Decompress(cls, compressedFile, destinationDirectory, overwriteExisting=False, decompressedFileToReturn=None):
        cls.__doc__.Obj.ValidateMethodInvocation()
        try:
            # Fail if this file is not a format we can handle.

            if not cls.IsDecompressible(compressedFile):
                Logger.RaiseException(ValueError(_('The file %s is not in a supported compression format. Please see the GeoEco documentation for the supported formats.') % compressedFile))

            oldLogInfoAsDebug = Logger.LogInfoAndSetInfoToDebug(_('Decompressing file %(file)s to directory %(dir)s...') % {'file' : compressedFile, 'dir' : destinationDirectory})
            try:
                # Create the destination directory.

                from .Directories import Directory
                Directory.Create(destinationDirectory)

                # Handle archive files, which may have multiple destination files.

                if compressedFile.lower().endswith('.tar') or compressedFile.lower().endswith('.tar.bz2') or compressedFile.lower().endswith('.tar.gz') or compressedFile.lower().endswith('.zip'):
                    if decompressedFileToReturn is None:
                        Logger.RaiseException(TypeError(_('File %s is an archive. The decompressedFileToReturn parameter is required for archive files; please provide a value.') % compressedFile))

                    # Handle tar files, which may be uncompressed (.tar) or compressed
                    # with bzip2 (.tar.bz2) or gzip (.tar.gz).

                    if compressedFile.lower().endswith('.tar') or compressedFile.lower().endswith('.tar.gz') or compressedFile.lower().endswith('.tar.bz2'):
                        Logger.Debug(_('Decompressing %(source)s to directory %(dest)s') % {'source' : compressedFile, 'dest' : destinationDirectory})
                        tar = tarfile.open(compressedFile)
                        try:
                            tar.errorlevel = 2            # Any kind of problem should raise an exception
                            for member in tar.getmembers():
                                destinationPath = os.path.normpath(os.path.join(destinationDirectory, member.name))
                                if member.isdir():
                                    if os.path.isdir(destinationPath):
                                        continue
                                    elif os.path.exists(destinationPath):
                                        Logger.RaiseException(ValueError(_('The path %s already exists but it is not a directory. The compressed file contains a directory with that path. The decompression function will not overwrite an existing file or other non-directory object with a directory. Delete the existing object or choose another output directory, and try again.') % destinationPath))
                                elif member.isfile():
                                    if os.path.isfile(destinationPath):
                                        if overwriteExisting:
                                            cls.Delete(destinationPath)
                                        else:
                                            Logger.RaiseException(ValueError(_('The file %s already exists. Delete it or choose another output directory, and try again.') % destinationPath))
                                    elif os.path.exists(destinationPath):
                                        Logger.RaiseException(ValueError(_('The path %s already exists but it is not a file. The compressed file contains a file with that path. The decompression function will not overwrite an existing directory or other non-file object with a file. Delete the existing object or choose another output directory, and try again.') % destinationPath))
                                else:
                                    Logger.RaiseException(ValueError(_('The archive %(src)s contains an object %(obj)s that is not a file or directory. For example, it might be a symbolic link. The decompression function can only decompress files and directories. Please remove %(obj)s from the archive and try again.') % {'src' : compressedFile, 'obj' : member.name}))
                                Logger.Debug(_('Writing %s'), destinationPath)
                                tar.extract(member, destinationDirectory)
                        finally:
                            tar.close()

                    # Handle ZIP files (.zip).

                    elif compressedFile.lower().endswith('.zip'):
                        Logger.Debug(_('Decompressing %(source)s to directory %(dest)s') % {'source' : compressedFile, 'dest' : destinationDirectory})
                        z = zipfile.ZipFile(compressedFile)
                        try:
                            for name in z.namelist():
                                destinationPath = os.path.join(destinationDirectory, os.path.normpath(name))

                                # If the destination path is a directory, just create it.

                                if name.endswith('\\') or name.endswith('/'):
                                    Directory.Create(destinationPath)

                                # If the destination path is a file, extract it.

                                else:                        
                                    Directory.Create(os.path.dirname(destinationPath))      # This may be redundant.
                                    if os.path.isfile(destinationPath):
                                        if overwriteExisting:
                                            cls.Delete(destinationPath)
                                        else:
                                            Logger.RaiseException(ValueError(_('The file %s already exists. Delete it or choose another output directory, and try again.') % destinationPath))
                                    elif os.path.exists(destinationPath):
                                        Logger.RaiseException(ValueError(_('The path %s already exists but it is not a file. The compressed file contains a file with that path. The decompression function will not overwrite an existing directory or other non-file object with a file. Delete the existing object or choose another output directory, and try again.') % destinationPath))
                                    Logger.Debug(_('Writing %s'), destinationPath)
                                    fout = open(destinationPath, 'wb')
                                    try:
                                        fout.write(z.read(name))
                                    finally:
                                        fout.close()
                        finally:
                            z.close()

                    # Find the destination file to return.

                    if decompressedFileToReturn is not None:
                        matchingFiles = glob.glob(os.path.join(destinationDirectory, os.path.normpath(decompressedFileToReturn)))
                        if len(matchingFiles) < 1:
                            Logger.RaiseException(ValueError(_('The filename or glob expression %(glob)s did not match any files in destination directory %(dir)s. Please specify a filename or glob expression that matches a file.') % {'glob' : decompressedFileToReturn, 'dir' : destinationDirectory}))
                        elif len(matchingFiles) > 1:
                            Logger.RaiseException(ValueError(_('The glob expression %(glob)s matched %(files)i files in destination directory %(dir)s. Please specify a glob expression that matches exactly one file.') % {'glob' : decompressedFileToReturn, 'files' : len(matchingFiles), 'dir' : destinationDirectory}))
                        if not os.path.isfile(matchingFiles[0]):
                            Logger.RaiseException(ValueError(_('The filename or glob expression %(glob)s matched %(obj)s, but it is not a file. Please specify a glob expression that matches a file.') % {'glob' : decompressedFileToReturn, 'obj' : matchingFiles[0]}))
                        result = matchingFiles[0]
                    else:
                        result = None

                # Handle bzip2 (.bz2) and gzip (.gz) files. The Python interface for
                # these files is very similar, so we can use the same code for both.

                elif compressedFile.lower().endswith('.bz2') or compressedFile.lower().endswith('.gz'):
                    destinationFile = os.path.join(destinationDirectory, os.path.basename(os.path.splitext(compressedFile)[0]))
                    if os.path.isfile(destinationFile):
                        if overwriteExisting:
                            cls.Delete(destinationFile)
                        else:
                            Logger.RaiseException(ValueError(_('The file %s already exists. Delete it or choose another output directory, and try again.') % destinationFile))
                    elif os.path.exists(destinationFile):
                        Logger.RaiseException(ValueError(_('The path %s already exists but it is not a file. The compressed file contains a file with that path. The decompression function will not overwrite an existing directory or other non-file object with a file. Delete the existing object or choose another output directory, and try again.') % destinationFile))
                    Logger.Debug(_('Decompressing %(source)s to %(dest)s') % {'source' : compressedFile, 'dest' : destinationFile})
                    if compressedFile.lower().endswith('.bz2'):
                        fin = bz2.BZ2File(compressedFile)
                    else:
                        fin = gzip.GzipFile(compressedFile)
                    try:
                        fout = open(destinationFile, 'wb')
                        try:
                            data = fin.read(1024*1024)
                            while data:
                                fout.write(data)
                                data = fin.read(1024*1024)
                        finally:
                            fout.close()
                    finally:
                        fin.close()
                    result = destinationFile

                # Handle UNIX "compress" files (.Z) and compressed tar files
                # (.tar.Z).

                if compressedFile.lower().endswith('.z'):
                    if compressedFile.lower().endswith('.tar.z') and decompressedFileToReturn is None:
                        Logger.RaiseException(TypeError(_('File %s is an archive. The decompressedFileToReturn parameter is required for archive files; please provide a value.') % compressedFile))

                    destinationFile = os.path.join(destinationDirectory, os.path.basename(os.path.splitext(compressedFile)[0]))
                    if os.path.exists(destinationFile):
                        Logger.RaiseException(ValueError(_('The file or directory %s already exists. Delete it or choose another output directory, and try again.') % destinationFile))

                    fin = open(compressedFile, 'rb')
                    try:
                        fout = open(destinationFile, 'wb')
                        try:
                            fout.write(zlib.decompress(fin.read(), 15 + 32))
                        finally:
                            fout.close()
                    finally:
                        fin.close()

                    # If the destination file is a tar file, untar it and delete the
                    # tar file, since it is temporary.

                    if destinationFile.lower().endswith('.tar'):
                        result = cls.Decompress(destinationFile, destinationDirectory, decompressedFileToReturn=decompressedFileToReturn)
                        File.Delete(destinationFile)

            finally:
                Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

            # Return successfully.

            return result        

        except:
            Logger.LogExceptionAsError(_('Could not decompress file %(file)s to directory %(dir)s') % {'file' : compressedFile, 'dir' : destinationDirectory})
            raise

    @classmethod
    def Delete(cls, path):
        cls.__doc__.Obj.ValidateMethodInvocation()
        try:
            if os.path.isfile(path):
                os.remove(path)
                Logger.Info(_('Deleted file %s.'), path)
            elif os.path.exists(path):
                Logger.RaiseException(ValueError(_('The path %s exists as a directory or some other non-file object. To delete it, use a method that is appropriate for this type object. For example, to delete directories, use Directory.Delete.') % path))
            else:
                Logger.Info(_('File %s was not deleted because it does not exist.'), path)
        except:
            Logger.LogExceptionAsError(_('Could not delete file %s') % path)
            raise

    @classmethod
    def DeleteSilent(cls, path):
        oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
        Logger.SetLogInfoAsDebug(True)
        try:
            cls.Delete(path)
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)

    @classmethod
    def Exists(cls, path):
        cls.__doc__.Obj.ValidateMethodInvocation()
        exists = os.path.exists(path)
        isFile = os.path.isfile(path)
        if not exists:
            Logger.Debug(_('The file %(path)s does not exist.') % {'path': path})
        else:
            if isFile:
                Logger.Debug(_('The file %(path)s exists.') % {'path': path})
            else:
                Logger.Debug(_('%(path)s exists but it is not a file.') % {'path': path})
        return (exists, isFile)

    @classmethod
    def Find(cls, directory, wildcard='*', searchTree=False, minSize=None, maxSize=None, minDateCreated=None, maxDateCreated=None, minDateModified=None, maxDateModified=None, basePath=None, getSize=False, getDateCreated=False, getDateModified=False, dateParsingExpression=None):
        cls.__doc__.Obj.ValidateMethodInvocation()
        if minSize is not None and maxSize is not None and minSize > maxSize:
            Logger.RaiseException(ValueError(_('minSize must be less than or equal to maxSize.')))
        if minDateCreated is not None and maxDateCreated is not None and minDateCreated > maxDateCreated:
            Logger.RaiseException(ValueError(_('minDateCreated must be less than or equal to maxDateCreated.')))
        if minDateModified is not None and maxDateModified is not None and minDateModified > maxDateModified:
            Logger.RaiseException(ValueError(_('minDateModified must be less than or equal to maxDateModified.')))

        Logger.Info(_('Finding files: directory="%(directory)s", wildcard="%(wildcard)s", searchTree=%(tree)s, minSize=%(minSize)s, maxSize=%(maxSize)s, minDateCreated=%(minDateCreated)s, maxDateCreated=%(maxDateCreated)s, minDateModified=%(minDateModified)s, maxDateModified=%(maxDateModified)s') % {'directory': directory, 'wildcard': wildcard, 'tree': searchTree, 'minSize': minSize, 'maxSize': maxSize, 'minDateCreated': minDateCreated, 'maxDateCreated': maxDateCreated, 'minDateModified': minDateModified, 'maxDateModified': maxDateModified})

        return cls._Find(directory,
                         wildcard,
                         searchTree,
                         minSize,
                         maxSize,
                         minDateCreated,
                         maxDateCreated,
                         minDateModified,
                         maxDateModified,
                         basePath,
                         getSize,
                         getDateCreated,
                         getDateModified,
                         dateParsingExpression)

    @classmethod
    def _Find(cls, directory, wildcard, searchTree, minSize, maxSize, minDateCreated, maxDateCreated, minDateModified, maxDateModified, basePath, getSize, getDateCreated, getDateModified, dateParsingExpression, searchPattern=None, strptimePattern=None):

        # If the caller provided a dateParsingExpression, parse it into a
        # pattern we can pass the re.search() and a corresponding pattern we can
        # subsequently pass to time.strptime().

        if dateParsingExpression is not None and searchPattern is None:
            searchPattern, strptimePattern = File.ValidateDateParsingExpression(dateParsingExpression)

        # Find matching files in the specified directory.

        results = []

        if basePath is not None:
            os.path.normpath(basePath)
            baseParts = basePath.split(os.sep)
        
        for o in glob.glob(os.path.join(directory, wildcard)):

            # Skip this object if it is not a file.
            
            if not os.path.isfile(o):
                continue

            # Skip this file if it does not match the caller's search criteria.
            
            if minSize is not None or maxSize is not None or minDateCreated is not None or maxDateCreated is not None or minDateModified is not None or maxDateModified is not None or getSize or getDateCreated or getDateModified:
                s = os.stat(o)
                dateCreated = datetime.datetime.fromtimestamp(s.st_ctime)
                dateModified = datetime.datetime.fromtimestamp(s.st_mtime)
                
                if minSize is not None and s.st_size < minSize:
                    continue
                if maxSize is not None and s.st_size > maxSize:
                    continue
                if minDateCreated is not None and dateCreated < minDateCreated:
                    continue
                if maxDateCreated is not None and dateCreated > maxDateCreated:
                    continue
                if minDateModified is not None and dateModified < minDateModified:
                    continue
                if maxDateModified is not None and dateModified> maxDateModified:
                    continue

            # Append the absolute path to the result row.
            
            Logger.Debug(_('Found file %s'), o)

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
                
            if getSize:
                result.append(s.st_size)
                
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
                                             minSize,
                                             maxSize,
                                             minDateCreated,
                                             maxDateCreated,
                                             minDateModified,
                                             maxDateModified,
                                             basePath,
                                             getSize,
                                             getDateCreated,
                                             getDateModified,
                                             dateParsingExpression,
                                             searchPattern,
                                             strptimePattern))

        # Return successfully.

        return results        

    @classmethod
    def ValidateDateParsingExpression(cls, dateParsingExpression):
        searchPattern = ''
        strptimePattern = ''
        foundPercentCharacter = False
        yearCount = 0
        monthCount = 0
        dayCount = 0
        dayOfYearCount = 0
        hourCount = 0
        minuteCount = 0
        secondCount = 0
        
        for i in range(len(dateParsingExpression)):
            if foundPercentCharacter:
                foundPercentCharacter = False
                if dateParsingExpression[i] == '%':
                    searchPattern += '%'
                elif dateParsingExpression[i] == 'Y':
                    searchPattern += r'(\d\d\d\d)'
                    strptimePattern += '%Y'
                    yearCount += 1
                elif dateParsingExpression[i] == 'y':
                    searchPattern += r'(\d\d)'
                    strptimePattern += '%y'
                    yearCount += 1
                elif dateParsingExpression[i] == 'm':
                    searchPattern += r'(\d\d)'
                    strptimePattern += '%m'
                    monthCount += 1
                elif dateParsingExpression[i] == 'd':
                    searchPattern += r'(\d\d)'
                    strptimePattern += '%d'
                    dayCount += 1
                elif dateParsingExpression[i] == 'j':
                    searchPattern += r'(\d\d\d)'
                    strptimePattern += '%j'
                    dayOfYearCount += 1
                elif dateParsingExpression[i] == 'H':
                    searchPattern += r'(\d\d)'
                    strptimePattern += '%H'
                    hourCount += 1
                elif dateParsingExpression[i] == 'M':
                    searchPattern += r'(\d\d)'
                    strptimePattern += '%M'
                    minuteCount += 1
                elif dateParsingExpression[i] == 'S':
                    searchPattern += r'(\d\d)'
                    strptimePattern += '%S'
                    secondCount += 1
                else:
                    Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains the unrecognized character "%(char)s" at position %(pos)i, where 0 is the first character in the expression. The character follows a %% character, indicating that it is a code for a date fragment, but "%(char)s" is not an allowed code. The allowed codes are d, H, j, m, M, S, y, and Y. Please specify one of these codes. The codes are case sensitive. You may also specify a second %%; two %% characters in a row will be interpreted as a literal %%. Please see the documentation for this tool for more information about the codes.') % {'expr': dateParsingExpression, 'char': dateParsingExpression[i], 'pos': i}))
                
            elif dateParsingExpression[i] == '%':
                foundPercentCharacter = True
                
            else:
                searchPattern += dateParsingExpression[i]

        if foundPercentCharacter:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" ends with a %% character. This is not allowed. Please remove the %% or follow it with a date fragment code or a second %% character.') % {'expr': dateParsingExpression}))

        if len(strptimePattern) <= 0:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" did not contain any date fragment codes. You must include at least one date fragment code in the expression. Please see this tool\'s documentation for examples.') % {'expr': dateParsingExpression}))

        if yearCount <= 0:
            Logger.Info(_('The date-parsing expression does not include a date fragment code for the year (%%Y or %%y). The year will assumed to be 1900.'))
        elif yearCount > 1:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains more than one date fragment code for the year (%%Y or %%y). It may only contain one code for the year.') % {'expr': dateParsingExpression}))

        if monthCount <= 0 and dayOfYearCount <= 0:
            Logger.Info(_('The date-parsing expression does not include a date fragment code for the month (%%m) or day of the year (%%j). The month will assumed to be January.'))
        elif monthCount > 1:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains more than one date fragment code for the month (%%m). It may only contain one code for the month.') % {'expr': dateParsingExpression}))
        elif monthCount == 1 and dayOfYearCount > 0:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains a date fragment code for both the month (%%m) and the day of the year(%%j). It may not contain both. Please remove one or the other.') % {'expr': dateParsingExpression}))

        if dayCount <= 0 and dayOfYearCount <= 0:
            Logger.Info(_('The date-parsing expression does not include a date fragment code for the day of the month (%%d) or day of the year (%%j). The day of the month will assumed to be 1.'))
        elif dayCount > 1:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains more than one date fragment code for the day of the month (%%d). It may only contain one code for the day of the month.') % {'expr': dateParsingExpression}))
        elif dayOfYearCount > 1:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains more than one date fragment code for the day of the month (%%d). It may only contain one code for the day of the month.') % {'expr': dateParsingExpression}))
        elif dayCount == 1 and dayOfYearCount == 1:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains a date fragment code for both the day of the month (%%d) and the day of the year(%%j). It may not contain both. Please remove one or the other.') % {'expr': dateParsingExpression}))

        if hourCount <= 0:
            Logger.Info(_('The date-parsing expression does not include a date fragment code for the hour (%%H). The hour will assumed to be 00.'))
        elif hourCount > 1:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains more than one date fragment code for the hour (%%H). It may only contain one code for the hour.') % {'expr': dateParsingExpression}))

        if minuteCount <= 0:
            Logger.Info(_('The date-parsing expression does not include a date fragment code for the minute (%%M). The minute will assumed to be 00.'))
        elif minuteCount > 1:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains more than one date fragment code for the minute (%%M). It may only contain one code for the minute.') % {'expr': dateParsingExpression}))

        if secondCount <= 0:
            Logger.Info(_('The date-parsing expression does not include a date fragment code for the second (%%S). The second will assumed to be 00.'))
        elif secondCount > 1:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(expr)s" contains more than one date fragment code for the second (%%S). It may only contain one code for the second.') % {'expr': dateParsingExpression}))

        Logger.Debug(_('Transformed the date-parsing expression "%(e1)s" into the regular expression "%(e2)s" and strptime expression "%(e3)s".') % {'e1': dateParsingExpression, 'e2': searchPattern, 'e3': strptimePattern})

        return searchPattern, strptimePattern        

    @classmethod
    def ParseDateFromPath(cls, path, dateParsingExpression, searchPattern, strptimePattern):

        # Find the first occurrence of searchPattern in path.
        
        matchObj = re.search(searchPattern, path, re.IGNORECASE)
        if matchObj is None:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(e1)s" failed to parse a date from the path "%(path)s". If you intended that a date be parsed from this path, adjust your date-parsing expression so that will work for this path. If you do not want to parse a date from this path, adjust your search parameters to omit it. Error details: The regular expression pattern "%(e2)s", produced from the date-parsing expression, was not found in the path.') % {'e1': dateParsingExpression, 'e2': searchPattern, 'path': path}))

        # Concatenate all the regular expression groups into a single string
        # and parse that with strptimePattern.

        try:
            t = time.strptime(''.join(matchObj.groups()), strptimePattern)
        except Exception as e:
            Logger.RaiseException(ValueError(_('The date-parsing expression "%(e1)s" failed to parse a date from the path "%(path)s". If you intended that a date be parsed from this path, adjust your date-parsing expression so that will work for this path. If you do not want to parse a date from this path, adjust your search parameters to omit it. Error details: The regular expression "%(e1)s", produced from the date-parsing expression, was found in the path. The resulting regular expression groups were joined into the string "%(groups)s". But when that string was parsed by the strptime function using the expression "%(e3)s", also produced from the date-parsing expression, that function reported: %(error): %(msg)s') % {'e1': dateParsingExpression, 'e2': searchPattern, 'e3': strptimePattern, 'path': path, 'groups': ''.join(matchObj.groups()), 'error': e.__class__.__name__, 'msg': e}))

        # Return the parsed date/time, as a datetime.datetime object and as a
        # UNIX time.

        d = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])
        delta = d - datetime.datetime(1970, 1, 1, 0, 0, 0)
        return d, delta.days * 86400 + delta.seconds

    @classmethod
    def FindAndFillTable(cls, directory, insertCursor, fileField, wildcard='*', searchTree=False, minSize=None, maxSize=None, minDateCreated=None, maxDateCreated=None, minDateModified=None, maxDateModified=None, relativePathField=None, basePath=None, sizeField=None, dateCreatedField=None, dateModifiedField=None, parsedDateField=None, dateParsingExpression=None, unixTimeField=None):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        fields = [fileField, relativePathField, sizeField, dateCreatedField, dateModifiedField, parsedDateField, unixTimeField]
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

        # Find the files.

        Logger.Info(_('Finding files and inserting rows into table "%(table)s": directory="%(directory)s", wildcard="%(wildcard)s", searchTree=%(tree)s, minSize=%(minSize)s, maxSize=%(maxSize)s, minDateCreated=%(minDateCreated)s, maxDateCreated=%(maxDateCreated)s, minDateModified=%(minDateModified)s, maxDateModified=%(maxDateModified)s') % {'table': insertCursor.Table, 'directory': directory, 'wildcard': wildcard, 'tree': searchTree, 'minSize': minSize, 'maxSize': maxSize, 'minDateCreated': minDateCreated, 'maxDateCreated': maxDateCreated, 'minDateModified': minDateModified, 'maxDateModified': maxDateModified})

        results = cls._Find(directory,
                            wildcard,
                            searchTree,
                            minSize,
                            maxSize,
                            minDateCreated,
                            maxDateCreated,
                            minDateModified,
                            maxDateModified,
                            basePath,
                            sizeField is not None,
                            dateCreatedField is not None,
                            dateModifiedField is not None,
                            dateParsingExpression)

        # Insert the rows.

        if len(results) > 0:
            insertCursor.SetRowCount(len(results))

            for result in results:
                value = result.pop(0)
                insertCursor.SetValue(fileField, value)

                if relativePathField is not None:
                    value = result.pop(0)
                    insertCursor.SetValue(relativePathField, value)

                if sizeField is not None:
                    value = result.pop(0)
                    insertCursor.SetValue(sizeField, value)

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
    def FindAndCreateTable(cls, directory, database, table, fileField, wildcard='*', searchTree=False, minSize=None, maxSize=None, minDateCreated=None, maxDateCreated=None, minDateModified=None, maxDateModified=None, relativePathField=None, basePath=None, sizeField=None, dateCreatedField=None, dateModifiedField=None, parsedDateField=None, dateParsingExpression=None, unixTimeField=None, pathFieldsDataType='string', sizeFieldDataType='float64', dateFieldsDataType='datetime', unixTimeFieldDataType='int32', maxPathLength=None, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()

        # Perform additional validation.

        fields = [fileField, relativePathField, sizeField, dateCreatedField, dateModifiedField, parsedDateField, unixTimeField]
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
            tableObj.AddField(fileField, pathFieldsDataType, length=maxPathLength)

            if relativePathField is not None:
                tableObj.AddField(relativePathField, pathFieldsDataType, length=maxPathLength)

            if sizeField is not None:
                tableObj.AddField(sizeField, sizeFieldDataType)

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
                                     fileField,
                                     wildcard,
                                     searchTree,
                                     minSize,
                                     maxSize,
                                     minDateCreated,
                                     maxDateCreated,
                                     minDateModified,
                                     maxDateModified,
                                     relativePathField,
                                     basePath,
                                     sizeField,
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
    def FindAndCreateArcGISTable(cls, directory, workspace, table, fileField, wildcard='*', searchTree=False, minSize=None, maxSize=None, minDateCreated=None, maxDateCreated=None, minDateModified=None, maxDateModified=None, relativePathField=None, sizeField=None, dateCreatedField=None, dateModifiedField=None, parsedDateField=None, dateParsingExpression=None, unixTimeField=None, maxPathLength=None, overwriteExisting=False):
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
                                       fileField,
                                       wildcard,
                                       searchTree,
                                       minSize,
                                       maxSize,
                                       minDateCreated,
                                       maxDateCreated,
                                       minDateModified,
                                       maxDateModified,
                                       relativePathField,
                                       workspace,
                                       sizeField,
                                       dateCreatedField,
                                       dateModifiedField,
                                       parsedDateField,
                                       dateParsingExpression,
                                       unixTimeField,
                                       'string',
                                       'float64',
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
    def IsDecompressible(cls, compressedFile):
        cls.__doc__.Obj.ValidateMethodInvocation()
        compressedFile = compressedFile.lower()
        if compressedFile.endswith('.bz2') or compressedFile.endswith('.gz') or compressedFile.endswith('.tar') or compressedFile.endswith('.z') or compressedFile.endswith('.zip'):
            return True
        return False

    @classmethod
    def Move(cls, sourceFile, destinationFile, overwriteExisting=False):
        cls.__doc__.Obj.ValidateMethodInvocation()
        Logger.Info(_('Moving file %(source)s to %(dest)s') % {'source' :  sourceFile, 'dest' : destinationFile})
        try:
            shutil.move(sourceFile, destinationFile)        
        except:
            Logger.LogExceptionAsError(_('Could not move file %(source)s to %(dest)s') % {'source' :  sourceFile, 'dest' : destinationFile})
            raise

    @classmethod
    def MoveSilent(cls, sourceFile, destinationFile, overwriteExisting=False):
        oldLogInfoAsDebug = Logger.GetLogInfoAsDebug()
        Logger.SetLogInfoAsDebug(True)
        try:
            cls.Move(sourceFile, destinationFile, overwriteExisting)
        finally:
            Logger.SetLogInfoAsDebug(oldLogInfoAsDebug)


###############################################################################
# Metadata: module
###############################################################################

from ..ArcGIS import ArcGISDependency
from ..Datasets import Database, InsertCursor
from ..Metadata import *
from ..Types import *

AddModuleMetadata(shortDescription=_('Functions for common file operations.'))

###############################################################################
# Metadata: File class
###############################################################################

AddClassMetadata(File,
    shortDescription=_('Functions for common file operations.'))

# Public method: File.Copy

AddMethodMetadata(File.Copy,
    shortDescription=_('Copies a file.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Copy File'),
    arcGISToolCategory=_('Data Management\\Files\\Copy'))

AddArgumentMetadata(File.Copy, 'cls',
    typeMetadata=ClassOrClassInstanceTypeMetadata(cls=File),
    description=_(':class:`%s` or an instance of it.') % File.__name__)

AddArgumentMetadata(File.Copy, 'sourceFile',
    typeMetadata=FileTypeMetadata(mustExist=True),
    description=_('File to copy.'),
    arcGISDisplayName=_('Source file'))

AddArgumentMetadata(File.Copy, 'destinationFile',
    typeMetadata=FileTypeMetadata(mustBeDifferentThanArguments=['sourceFile'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_('Copy to create. Missing directories in this path will be created if they do not exist.'),
    direction='Output',
    arcGISDisplayName=_('Destination file'))

AddArgumentMetadata(File.Copy, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, the destination file will be overwritten, if it exists. If False, a :py:exc:`ValueError` will be raised if the destination file exists.'),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

# Public method: File.CopySilent

AddMethodMetadata(File.CopySilent,
    shortDescription=_('Copies a file and logs a debug message rather than an informational message.'),
    longDescription=_(
"""This method does the same thing as the :py:func:`File.Copy` method, except
it logs a debug message rather than an informational message. It is intended
for use when the file-copy operation is not important enough to warrant
notifying the user (for example, when an output file is extracted from a
temporary directory to the final location)."""))

CopyArgumentMetadata(File.Copy, 'cls', File.CopySilent, 'cls')
CopyArgumentMetadata(File.Copy, 'sourceFile', File.CopySilent, 'sourceFile')
CopyArgumentMetadata(File.Copy, 'destinationFile', File.CopySilent, 'destinationFile')
CopyArgumentMetadata(File.Copy, 'overwriteExisting', File.CopySilent, 'overwriteExisting')

# Public method: File.Decompress

AddMethodMetadata(File.Decompress,
    shortDescription=_('Decompresses a file into a directory.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Decompress File'),
    arcGISToolCategory=_('Data Management\\Files\\Decompress'))

CopyArgumentMetadata(File.Copy, 'cls', File.Decompress, 'cls')

AddArgumentMetadata(File.Decompress, 'compressedFile',
    typeMetadata=FileTypeMetadata(mustExist=True),
    description=_(
"""File to decompress.

The file must be in a supported compression format. The formats presently
supported are:

* ``.bz2`` - a single file compressed in `bzip2 <https://gitlab.com/bzip2/bzip2/>`_ format
* ``.gz`` - a single file compressed in `gzip <https://www.gzip.org>`_ format
* ``.tar`` - one or more files archived in UNIX `tar <https://en.wikipedia.org/wiki/Tar_(computing)>`_ format
* ``.zip`` - one or more files archived and compressed in `ZIP <https://en.wikipedia.org/wiki/ZIP_(file_format)>`_ format
* ``.Z`` - a single file compressed in UNIX `"compress" <https://en.wikipedia.org/wiki/Compress_(software)>`_ format

``tar`` files that are compressed in bzip2 (``.tar.bz2``), gzip (``.tar.gz``)
or compress format (``.tar.Z``) are automatically handled."""),
    arcGISDisplayName=_('Compressed file'))

AddArgumentMetadata(File.Decompress, 'destinationDirectory',
    typeMetadata=DirectoryTypeMetadata(),
    description=_('Directory to receive the decompressed files. The directory will be created if it does not already exist.'),
    arcGISDisplayName=_('Destination directory'))

AddArgumentMetadata(File.Decompress, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, the extracted destination files will be overwritten, if they already exist. If False, a :py:exc:`ValueError` will be raised if any destination files already exist.'),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

AddArgumentMetadata(File.Decompress, 'decompressedFileToReturn',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""File name or wildcard pattern that identifies the decompressed file to
return.

If the compressed file is not an archive (a format that allows multiple files
to be stored within a single archive file) this parameter is ignored, and the
path of the single decompressed will be automatically returned. It will have
the same file name as the compressed file, minus the extension.

If the compressed file is an archive and this parameter is not provided,
nothing is returned.

If the compressed file is an archive and a plain filename is provided for
this parameter, the path of that decompressed file will be returned.

If the compressed file is an archive and a wildcard pattern is provided for
this parameter, the path of the decompressed file matching that pattern will
be returned. The pattern must match exactly one decompressed file or a
:py:exc:`ValueError` will be raised.

If the archive includes subdirectories, the filename or wildcard pattern must
account for this. For example, if the archive includes these files::

    variables.txt
    data\\chl.txt
    data\\sst.txt
    data\\bathy.txt

then the ``bathy.txt`` file must be specified as ``data\\bathy.txt``, not
``bathy.txt``. On the other hand, ``variables.txt`` does not occur in a
subdirectory, so it should be specified as ``variables.txt``.

If the destination directory already contains files and directories other than
those extracted from the archive, they are candidates to be returned. Beware
of this, lest your filename or wildcard pattern return a pre-existing file
rather than a newly-extracted one.

The wildcard syntax is the "glob" syntax used by UNIX shells. The ``*``
character matches zero or more characters. The ``?`` character matches exactly
one character. The ``[]`` sequence may be used to match exactly one character
within a range. For example, if the following files were decompressed::

    chl_1992_013.txt
    chl_1992_01.txt
    chl_1992.txt
    chl_summary.txt
    sst_1992_013.txt
    sst_1992_01.txt
    sst_1992.txt
    sst_summary.txt

The file ``chl_1992_01.txt`` could be identified by the patterns::

    chl_1992_01.txt
    chl_????_??.txt
    chl*_??.txt
    chl*_[0-9][0-9].*

"""),
    arcGISDisplayName=_('Decompressed file to return'))

AddResultMetadata(File.Decompress, 'decompressedFile',
    typeMetadata=FileTypeMetadata(),
    description=_(
"""Path of the decompressed file.

If the compressed file is not an archive (a format that allows multiple files
to be stored within a single archive file), the path of the single
decompressed will be returned. It will have the same file name as the
compressed file, minus the extension.

If the compressed file is not an archive, the returned file is specified by
`decompressedFileToReturn`."""),
    arcGISDisplayName=_('Decompressed file'))

# Public method: File.Delete

AddMethodMetadata(File.Delete,
    shortDescription=_('Deletes a file.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Delete File'),
    arcGISToolCategory=_('Data Management\\Files\\Delete'))

CopyArgumentMetadata(File.Copy, 'cls', File.Delete, 'cls')

AddArgumentMetadata(File.Delete, 'path',
    typeMetadata=FileTypeMetadata(),
    description=_('File to delete.'),
    arcGISDisplayName=_('File'))

# Public method: File.DeleteSilent

AddMethodMetadata(File.DeleteSilent,
    shortDescription=_('Deletes a file and logs a debug message rather than an informational message.'),
    longDescription=_(
"""This method does the same thing as :meth:`~File.Delete`, except it logs a
debug message rather than an informational message. It is intended for use
when the file-move operation is not imporant enough to warrent notifying the
user (for example, when an output file is extracted from a temporary directory
to the final location)."""))

CopyArgumentMetadata(File.Delete, 'cls', File.DeleteSilent, 'cls')
CopyArgumentMetadata(File.Delete, 'path', File.DeleteSilent, 'path')

# Public method: File.Exists

AddMethodMetadata(File.Exists,
    shortDescription=_('Tests that a specified path exists and is a file.'))

CopyArgumentMetadata(File.Copy, 'cls', File.Exists, 'cls')

AddArgumentMetadata(File.Exists, 'path',
    typeMetadata=FileTypeMetadata(),
    description=_('Path to test.'))

AddResultMetadata(File.Exists, 'result',
    typeMetadata=TupleTypeMetadata(elementType=BooleanTypeMetadata(), minLength=2, maxLength=2),
    description=_('A two-item :py:class:`tuple`, where the first item is True if the specified path exists, and the second is True if the specified path exists and is a file.'))

# Public method: File.Find

AddMethodMetadata(File.Find,
    shortDescription=_('Finds files within a directory.'),
    longDescription=_(
"""On Windows, this function makes no distinction between hidden and visible
directories. Hidden directories are traversed and handled just like visible
directories.

Files are returned in an arbitrary order determined by the operating system
and the search algorithm."""))

CopyArgumentMetadata(File.Copy, 'cls', File.Find, 'cls')

AddArgumentMetadata(File.Find, 'directory',
    typeMetadata=DirectoryTypeMetadata(mustExist=True),
    description=_('Directory to search.'),
    arcGISDisplayName=_('Directory to search'))

AddArgumentMetadata(File.Find, 'wildcard',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""UNIX-style "glob" wildcard expression specifying the pathnames to find.

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

AddArgumentMetadata(File.Find, 'searchTree',
    typeMetadata=BooleanTypeMetadata(),
    description=_('If True, subdirectories will be searched.'),
    arcGISDisplayName=_('Search directory tree'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(File.Find, 'minSize',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    description=_(
"""Minimum size, in bytes, of files to find. If provided, only files that are
this size or larger will be found."""),
    arcGISDisplayName=_('Minimum size'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(File.Find, 'maxSize',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=0),
    description=_(
"""Maximum size, in bytes, of files to find. If provided, only files
that are this size or smaller will be found."""),
    arcGISDisplayName=_('Maximum size'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(File.Find, 'minDateCreated',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Minimum creation date, in the local time zone, of the files to find, as
reported by the operating system. If provided, only files that were created on
or after this date will be found. You may provide a date with or without a
time. If you do not provide a time, it is assumed to be midnight."""),
    arcGISDisplayName=_('Minimum creation date'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(File.Find, 'maxDateCreated',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Maximum creation date, in the local time zone, of the files to find, as
reported by the operating system. If provided, only files that were created on
or before this date will be found. You may provide a date with or without a
time. If you do not provide a time, it is assumed to be midnight."""),
    arcGISDisplayName=_('Maximum creation date'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(File.Find, 'minDateModified',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Minimum modification date, in the local time zone, of the files to find, as
reported by the operating system. If provided, only files that were modified
on or after this date will be found. You may provide a date with or without a
time. If you do not provide a time, it is assumed to be midnight."""),
    arcGISDisplayName=_('Minimum modification date'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(File.Find, 'maxDateModified',
    typeMetadata=DateTimeTypeMetadata(canBeNone=True),
    description=_(
"""Maximum modification date, in the local time zone, of the files to find, as
reported by the operating system. If provided, only files that were modified
on or before this date will be found. You may provide a date with or without a
time. If you do not provide a time, it is assumed to be midnight."""),
    arcGISDisplayName=_('Maximum modification date'),
    arcGISCategory=_('Search options'))

AddArgumentMetadata(File.Find, 'basePath',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Absolute path from which relative paths to the files will be calculated. If
provided, relative paths will be calculated and returned by this function.

For example, if the base path was::

    C:\\Data\\Files

the relative paths for the files::

    C:\\Data\\Files\\Group1\\f1
    C:\\Data\\Files\\f1
    C:\\Data\\f1
    C:\\f1
    D:\\f1
    \\\\MyServer\\Data\\f1

would be::    

    Group1\\f1
    f1
    ..\\f1
    ..\\..\\f1
    D:\\f1
    \\\\MyServer\\Data\\f1

"""))

AddArgumentMetadata(File.Find, 'getSize',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the size of each file will be returned by this function."""))

AddArgumentMetadata(File.Find, 'getDateCreated',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the creation date of each file will be returned by this
function."""))

AddArgumentMetadata(File.Find, 'getDateModified',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the modification date of each file will be returned by this
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

Examples:

The expression::

    %Y%j

will parse dates from many popular oceanographic satellite data
products, such as::

    A2007006.L3b_DAY.main.bz2           MODIS Aqua from NASA OceanColor
    S1997247.L3b_DAY.main.bz2           SeaWiFS from NASA OceanColor
    1990182.s04d1pfv50-sst-16b.hdf      AVHRR Pathfinder version 5.0 SST from NOAA NODC
    QS_XWGRD3_2003033.20070991747.gz    QuikSCAT winds from NASA JPL PO.DAAC

The expression::

    %Y_%j_%H

will parse dates from the hourly and 3-hour GOES SST products offered
by NASA JPL PO.DAAC::

    sst1_2005_033_17.gz                 An hourly GOES SST file
    sst3_2005_033_06.gz                 A 3-hour GOES SST file

The expression::

    %Y_%j_%H%M

will parse dates from the CoastWatch AVHRR SST product offered in HDF
format by NOAA CLASS (the CW_REGION product). Note that this product
includes the hour and minute of the satellite pass::

    2007_207_2214_n15_sr.hdf            A CoastWatch AVHRR file

""")

AddArgumentMetadata(File.Find, 'dateParsingExpression',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Expression for parsing dates from the paths of each file. If provided,
dates will be parsed and returned by this function.

""") +
_DateParsingExpressionSyntaxDocumentation)

AddResultMetadata(File.Find, 'files',
    typeMetadata=ListTypeMetadata(ListTypeMetadata(elementType=AnyObjectTypeMetadata())),
    description=_(
""":py:class:`list` of :py:class:`list`\\ s of the files that were found and
the requested metadata about them. The items of the inner :py:class:`list`\\ s
are:

* Path (:py:class:`str`) - always returned.

* Relative path (:py:class:`str`) - only returned if `basePath` is provided.

* Size (:py:class:`int`) - only returned if `getSize` is true.

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

# Public method: File.FindAndFillTable

AddMethodMetadata(File.FindAndFillTable,
    shortDescription=_('Finds files within a directory and inserts a row for each one into an existing table.'),
    longDescription=File.Find.__doc__.Obj.LongDescription)

CopyArgumentMetadata(File.Copy, 'cls', File.FindAndFillTable, 'cls')
CopyArgumentMetadata(File.Find, 'directory', File.FindAndFillTable, 'directory')

AddArgumentMetadata(File.FindAndFillTable, 'insertCursor',
    typeMetadata=ClassInstanceTypeMetadata(cls=InsertCursor),
    description=_('Insert cursor opened to the table that will receive the rows. The cursor will still be open when this function returns.'))

AddArgumentMetadata(File.FindAndFillTable, 'fileField',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the field to receive absolute paths to the files that were found.'),
    arcGISDisplayName=_('File path field'))

CopyArgumentMetadata(File.Find, 'wildcard', File.FindAndFillTable, 'wildcard')
CopyArgumentMetadata(File.Find, 'searchTree', File.FindAndFillTable, 'searchTree')
CopyArgumentMetadata(File.Find, 'minSize', File.FindAndFillTable, 'minSize')
CopyArgumentMetadata(File.Find, 'maxSize', File.FindAndFillTable, 'maxSize')
CopyArgumentMetadata(File.Find, 'minDateCreated', File.FindAndFillTable, 'minDateCreated')
CopyArgumentMetadata(File.Find, 'maxDateCreated', File.FindAndFillTable, 'maxDateCreated')
CopyArgumentMetadata(File.Find, 'minDateModified', File.FindAndFillTable, 'minDateModified')
CopyArgumentMetadata(File.Find, 'maxDateModified', File.FindAndFillTable, 'maxDateModified')

AddArgumentMetadata(File.FindAndFillTable, 'relativePathField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive paths of the files that were found, relative
to `basePath`. For example, if `basePath` was::

    C:\\Data\\Files

the relative paths for the files::

    C:\\Data\\Files\\Group1\\f1
    C:\\Data\\Files\\f1
    C:\\Data\\f1
    C:\\f1
    D:\\f1
    \\\\MyServer\\Data\\f1

would be::    

    Group1\\f1
    f1
    ..\\f1
    ..\\..\\f1
    D:\\f1
    \\\\MyServer\\Data\\f1

"""))

AddArgumentMetadata(File.FindAndFillTable, 'basePath',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Absolute path from which relative paths will be calculated and stored in
the `relativePathField`. Please see the documentation for that field for more
information."""))

AddArgumentMetadata(File.FindAndFillTable, 'sizeField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive the sizes of the files that were found."""),
    arcGISDisplayName=_('File size field'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(File.FindAndFillTable, 'dateCreatedField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive the creation dates of the files that were
found."""),
    arcGISDisplayName=_('File creation date field'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(File.FindAndFillTable, 'dateModifiedField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive the modification dates of the files that were
found."""),
    arcGISDisplayName=_('File modification date field'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(File.FindAndFillTable, 'parsedDateField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive dates parsed from the paths of the files that
were found. You must also specify a date parsing expression."""),
    arcGISDisplayName=_('Parsed date field'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(File.FindAndFillTable, 'dateParsingExpression',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Expression for parsing dates from the paths of the files that were found.
The expression will be ignored if you do not also specify a field to receive
the dates or the equivalent UNIX time.

""") + _DateParsingExpressionSyntaxDocumentation,
    arcGISDisplayName=_('Date parsing expression'),
    arcGISCategory=_('Output table options'))

AddArgumentMetadata(File.FindAndFillTable, 'unixTimeField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive dates, in "UNIX time" format, parsed from the
paths of the files that were found. You must also specify a date parsing
expression.

UNIX times are 32-bit signed integers that are the number of seconds since
1970-01-01 00:00:00 UTC. This tool assumes the date that was parsed is in the
UTC timezone. The UNIX time values produced by this tool do not include leap
seconds; this tool assumes that a regular year is 31536000 seconds and a leap
year is 31622400 seconds."""),
    arcGISDisplayName=_('UNIX time field'),
    arcGISCategory=_('Output table options'))

# Public method: File.FindAndCreateTable

AddMethodMetadata(File.FindAndCreateTable,
    shortDescription=_('Finds files within a directory and creates a table that lists them.'),
    longDescription=File.Find.__doc__.Obj.LongDescription)

CopyArgumentMetadata(File.Copy, 'cls', File.FindAndCreateTable, 'cls')
CopyArgumentMetadata(File.Find, 'directory', File.FindAndCreateTable, 'directory')

AddArgumentMetadata(File.FindAndCreateTable, 'database',
    typeMetadata=ClassInstanceTypeMetadata(cls=Database),
    description=_('Database that will receive the new table.'))

AddArgumentMetadata(File.FindAndCreateTable, 'table',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the table to create. The table must not exist.'))

CopyArgumentMetadata(File.FindAndFillTable, 'fileField', File.FindAndCreateTable, 'fileField')
CopyArgumentMetadata(File.FindAndFillTable, 'wildcard', File.FindAndCreateTable, 'wildcard')
CopyArgumentMetadata(File.FindAndFillTable, 'searchTree', File.FindAndCreateTable, 'searchTree')
CopyArgumentMetadata(File.FindAndFillTable, 'minSize', File.FindAndCreateTable, 'minSize')
CopyArgumentMetadata(File.FindAndFillTable, 'maxSize', File.FindAndCreateTable, 'maxSize')
CopyArgumentMetadata(File.FindAndFillTable, 'minDateCreated', File.FindAndCreateTable, 'minDateCreated')
CopyArgumentMetadata(File.FindAndFillTable, 'maxDateCreated', File.FindAndCreateTable, 'maxDateCreated')
CopyArgumentMetadata(File.FindAndFillTable, 'minDateModified', File.FindAndCreateTable, 'minDateModified')
CopyArgumentMetadata(File.FindAndFillTable, 'maxDateModified', File.FindAndCreateTable, 'maxDateModified')
CopyArgumentMetadata(File.FindAndFillTable, 'relativePathField', File.FindAndCreateTable, 'relativePathField')
CopyArgumentMetadata(File.FindAndFillTable, 'basePath', File.FindAndCreateTable, 'basePath')
CopyArgumentMetadata(File.FindAndFillTable, 'sizeField', File.FindAndCreateTable, 'sizeField')
CopyArgumentMetadata(File.FindAndFillTable, 'dateCreatedField', File.FindAndCreateTable, 'dateCreatedField')
CopyArgumentMetadata(File.FindAndFillTable, 'dateModifiedField', File.FindAndCreateTable, 'dateModifiedField')
CopyArgumentMetadata(File.FindAndFillTable, 'parsedDateField', File.FindAndCreateTable, 'parsedDateField')
CopyArgumentMetadata(File.FindAndFillTable, 'dateParsingExpression', File.FindAndCreateTable, 'dateParsingExpression')
CopyArgumentMetadata(File.FindAndFillTable, 'unixTimeField', File.FindAndCreateTable, 'unixTimeField')

AddArgumentMetadata(File.FindAndCreateTable, 'pathFieldsDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the file path fields. This should be
``string`` unless you have a specific reason to choose something else."""))

AddArgumentMetadata(File.FindAndCreateTable, 'sizeFieldDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the file size fields. This should be a
numeric type that supports large numbers, such as ``float64`` or
``int64``."""))

AddArgumentMetadata(File.FindAndCreateTable, 'dateFieldsDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the file creation date, file modification
date, and parsed date fields. This should be ``datetime`` if the underlying
storage format supports dates with times, or ``date`` if only dates are
supported."""))

AddArgumentMetadata(File.FindAndCreateTable, 'unixTimeFieldDataType',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_(
"""Data type to use when creating the UNIX date field. Because UNIX dates are
32-bit signed integers, this should be ``int32`` or ``int64``."""))

AddArgumentMetadata(File.FindAndCreateTable, 'maxPathLength',
    typeMetadata=IntegerTypeMetadata(canBeNone=True, minValue=1),
    description=_(
"""Maximum length of a path for this operating system. This value is used to
specify the width of the field that is created. You should provide a value
only if the underlying database requires that you specify a width for string
fields. If you provide a value that is too small to hold one of the paths that
is found, this function will fail when it finds that path."""))

AddArgumentMetadata(File.FindAndCreateTable, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=_(
"""If True, the output table will be overwritten, if it exists. If False, a
:py:exc:`ValueError` will be raised if the output table exists."""),
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

AddResultMetadata(File.FindAndCreateTable, 'createdTable',
    typeMetadata=UnicodeStringTypeMetadata(),
    description=_('Name of the table that was created.'))

# Public method: File.FindAndCreateArcGISTable

AddMethodMetadata(File.FindAndCreateArcGISTable,
    shortDescription=_('Finds files within a directory and creates a table that lists them.'),
    longDescription=File.FindAndCreateTable.__doc__.Obj.LongDescription,
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Find Files'),
    arcGISToolCategory=_('Data Management\\Files'),
    dependencies=[ArcGISDependency()])

CopyArgumentMetadata(File.Copy, 'cls', File.FindAndCreateArcGISTable, 'cls')
CopyArgumentMetadata(File.FindAndCreateTable, 'directory', File.FindAndCreateArcGISTable, 'directory')

AddArgumentMetadata(File.FindAndCreateArcGISTable, 'workspace',
    typeMetadata=ArcGISWorkspaceTypeMetadata(mustExist=True),
    description=_('Workspace in which the table should be created.'),
    arcGISDisplayName=_('Output workspace'))

AddArgumentMetadata(File.FindAndCreateArcGISTable, 'table',
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

CopyArgumentMetadata(File.FindAndCreateTable, 'fileField', File.FindAndCreateArcGISTable, 'fileField')
CopyArgumentMetadata(File.FindAndCreateTable, 'wildcard', File.FindAndCreateArcGISTable, 'wildcard')
CopyArgumentMetadata(File.FindAndCreateTable, 'searchTree', File.FindAndCreateArcGISTable, 'searchTree')
CopyArgumentMetadata(File.FindAndCreateTable, 'minSize', File.FindAndCreateArcGISTable, 'minSize')
CopyArgumentMetadata(File.FindAndCreateTable, 'maxSize', File.FindAndCreateArcGISTable, 'maxSize')
CopyArgumentMetadata(File.FindAndCreateTable, 'minDateCreated', File.FindAndCreateArcGISTable, 'minDateCreated')
CopyArgumentMetadata(File.FindAndCreateTable, 'maxDateCreated', File.FindAndCreateArcGISTable, 'maxDateCreated')
CopyArgumentMetadata(File.FindAndCreateTable, 'minDateModified', File.FindAndCreateArcGISTable, 'minDateModified')
CopyArgumentMetadata(File.FindAndCreateTable, 'maxDateModified', File.FindAndCreateArcGISTable, 'maxDateModified')

AddArgumentMetadata(File.FindAndCreateArcGISTable, 'relativePathField',
    typeMetadata=UnicodeStringTypeMetadata(canBeNone=True),
    description=_(
"""Name of the field to receive paths of the files that were found, relative
to the database or directory that contains the output table. For example, if
the path to the table is::

    C:\\Data\\Files\\FoundFiles.dbf

the relative paths for the files::

    C:\\Data\\Files\\Group1\\f1
    C:\\Data\\Files\\f1
    C:\\Data\\f1
    C:\\f1
    D:\\f1
    \\\\MyServer\\Data\\f1

would be::    

    Group1\\f1
    f1
    ..\\f1
    ..\\..\\f1
    D:\\f1
    \\\\MyServer\\Data\\f1

If the table is in a file geodatabase::

    C:\\Data\\Files\\FileInfo.gdb\\FoundFiles

the relative paths would be::    

    ..\\Group1\\f1
    ..\\f1
    ..\\..\\f1
    ..\\..\\..\\f1
    D:\\f1
    \\\\MyServer\\Data\\f1

"""),
    arcGISDisplayName=_('Relative path field'),
    arcGISCategory=_('Output table options'))

CopyArgumentMetadata(File.FindAndCreateTable, 'sizeField', File.FindAndCreateArcGISTable, 'sizeField')
CopyArgumentMetadata(File.FindAndCreateTable, 'dateCreatedField', File.FindAndCreateArcGISTable, 'dateCreatedField')
CopyArgumentMetadata(File.FindAndCreateTable, 'dateModifiedField', File.FindAndCreateArcGISTable, 'dateModifiedField')
CopyArgumentMetadata(File.FindAndCreateTable, 'parsedDateField', File.FindAndCreateArcGISTable, 'parsedDateField')
CopyArgumentMetadata(File.FindAndCreateTable, 'dateParsingExpression', File.FindAndCreateArcGISTable, 'dateParsingExpression')
CopyArgumentMetadata(File.FindAndCreateTable, 'unixTimeField', File.FindAndCreateArcGISTable, 'unixTimeField')
CopyArgumentMetadata(File.FindAndCreateTable, 'maxPathLength', File.FindAndCreateArcGISTable, 'maxPathLength')
CopyArgumentMetadata(File.FindAndCreateTable, 'overwriteExisting', File.FindAndCreateArcGISTable, 'overwriteExisting')

AddResultMetadata(File.FindAndCreateArcGISTable, 'createdTable',
    typeMetadata=ArcGISTableTypeMetadata(),
    description=_('Table that was created.'),
    arcGISDisplayName=_('Output table'))

# Public method: File.IsDecompressible

AddMethodMetadata(File.IsDecompressible,
    shortDescription=_('Returns True if the specified file is in a format that can be decompressed.'),
    longDescription=_(
"""This method examines the extension of the specified file to see if it
indicates the file is compressed in a format that is supported by the
decompression functions.

This method does not actually open the file, or even check its existence.
Thus, even if this method returns True, it does not guarantee decompression
will succeed if attempted."""),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('File Is Decompressible'),
    arcGISToolCategory=_('Data Management\\Files'))

CopyArgumentMetadata(File.Copy, 'cls', File.IsDecompressible, 'cls')

AddArgumentMetadata(File.IsDecompressible, 'compressedFile',
    typeMetadata=FileTypeMetadata(),
    description=_(
"""File to evaluate.

The compression formats presently supported are:

* ``.bz2`` - a single file compressed in `bzip2 <https://gitlab.com/bzip2/bzip2/>`_ format
* ``.gz`` - a single file compressed in `gzip <https://www.gzip.org>`_ format
* ``.tar`` - one or more files archived in UNIX `tar <https://en.wikipedia.org/wiki/Tar_(computing)>`_ format
* ``.zip`` - one or more files archived and compressed in `ZIP <https://en.wikipedia.org/wiki/ZIP_(file_format)>`_ format
* ``.Z`` - a single file compressed in UNIX `"compress" <https://en.wikipedia.org/wiki/Compress_(software)>`_ format

``tar`` files that are compressed in bzip2 (``.tar.bz2``), gzip (``.tar.gz``)
or compress format (``.tar.Z``) are automatically handled."""),
    arcGISDisplayName=_('File'))

AddResultMetadata(File.IsDecompressible, 'decompressible',
    typeMetadata=BooleanTypeMetadata(),
    description=_("""True if the specified file is in a format that can be decompressed."""),
    arcGISDisplayName=_('Decompressible'))

# Public method: File.Move

AddMethodMetadata(File.Move,
    shortDescription=_('Moves a file.'),
    isExposedAsArcGISTool=True,
    arcGISDisplayName=_('Move File'),
    arcGISToolCategory=_('Data Management\\Files\\Move'))

CopyArgumentMetadata(File.Copy, 'cls', File.Move, 'cls')

AddArgumentMetadata(File.Move, 'sourceFile',
    typeMetadata=FileTypeMetadata(mustExist=True),
    description=_('File to move.'),
    arcGISDisplayName=_('Source file'))

AddArgumentMetadata(File.Move, 'destinationFile',
    typeMetadata=FileTypeMetadata(mustBeDifferentThanArguments=['sourceFile'], deleteIfParameterIsTrue='overwriteExisting', createParentDirectories=True),
    description=_(
"""New path for the file.

Missing directories in this path will be created if they do not exist.

If the destination file is on the same drive or file system as the source
file, the source file will simply be renamed to the destination file.

If the destination file is on a different drive or file system, the source
file will be copied to the destination file and then deleted."""),
    direction='Output',
    arcGISDisplayName=_('Destination file'))

AddArgumentMetadata(File.Move, 'overwriteExisting',
    typeMetadata=BooleanTypeMetadata(),
    description=File.Copy.__doc__.Obj.Arguments[3].Description,
    initializeToArcGISGeoprocessorVariable='env.overwriteOutput')

# Public method: File.MoveSilent

AddMethodMetadata(File.MoveSilent,
    shortDescription=_('Moves a file and logs a debug message rather than an informational message.'),
    longDescription=_(
"""This method does the same thing as the :py:func:`File.Move` method, except
it logs a debug message rather than an informational message. It is intended
for use when the file-move operation is not important enough to warrant
notifying the user (for example, when an output file is extracted from a
temporary directory to the final location)."""))

CopyArgumentMetadata(File.Move, 'cls', File.MoveSilent, 'cls')
CopyArgumentMetadata(File.Move, 'sourceFile', File.MoveSilent, 'sourceFile')
CopyArgumentMetadata(File.Move, 'destinationFile', File.MoveSilent, 'destinationFile')
CopyArgumentMetadata(File.Move, 'overwriteExisting', File.MoveSilent, 'overwriteExisting')


###############################################################################
# Batch processing versions of methods
###############################################################################

from GeoEco.BatchProcessing import BatchProcessing
from GeoEco.DataManagement.Fields import Field

BatchProcessing.GenerateForMethod(File.Copy,
    inputParamNames=['sourceFile'],
    inputParamFieldArcGISDisplayNames=[_('Source file field')],
    inputParamDescriptions=[_('%s paths of the files to copy.')],
    outputParamNames=['destinationFile'],
    outputParamFieldArcGISDisplayNames=[_('Destination file field')],
    outputParamExpressionArcGISDisplayNames=[_('Destination file Python expression')],
    outputParamDescriptions=[_('%s paths of the destination files.')],
    outputParamExpressionDescriptions=[
"""Python expression used to calculate the absolute path of the destination
file. The expression may be any Python statement appropriate for passing to
the eval function and must return a Unicode string. The expression may
reference the following variables:

* ``directoryToSearch`` - the value provided for the directory to search
  parameter

* ``destinationDirectory`` - the value provided for the destination directory
  parameter

* ``sourceFile`` - the absolute path of the source file

The default expression, 
``os.path.join(destinationDirectory, sourceFile[len(directoryToSearch)+1:])``,
stores the file in the destination directory at the same relative location as
it appears in the directory to search. The destination path is calculated by
stripping the directory to search from the source path and replacing it with
the destination directory.

For more information on Python syntax, please see the `Python documentation
<http://www.python.org/doc/>`_."""],
    outputParamDefaultExpressions=['os.path.join(destinationDirectory, sourceFile[len(directoryToSearch)+1:])'],
    processListMethodName='CopyList',
    processListMethodShortDescription=_('Copies a list of files.'),
    processTableMethodName='CopyTable',
    processTableMethodShortDescription=_('Copies the files listed in a table.'),
    processArcGISTableMethodName='CopyArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Copy Files Listed in Table'),
    findAndProcessMethodName='FindAndCopy',
    findAndProcessMethodArcGISDisplayName='Find and Copy Files',
    findAndProcessMethodShortDescription=_('Finds and copies files in a directory.'),
    findMethod=File.FindAndCreateTable,
    findOutputFieldParams=['fileField'],
    findAdditionalParams=['wildcard', 'searchTree', 'minSize', 'maxSize', 'minDateCreated', 'maxDateCreated', 'minDateModified', 'maxDateModified'],
    outputLocationTypeMetadata=DirectoryTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Directory to receive copies of the files.'),
    outputLocationParamArcGISDisplayName=_('Destination directory'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    directoryToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputDirectory\']\n    destinationDirectory = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputDirectory\']\nfinally:\n    del f\n'], ['sourceFile = row.sourceFile']],
    calculatedOutputsArcGISCategory=_('Destination file name options'),
    skipExistingDescription=_('If True, copying will be skipped for destination files that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing destination files will be overwritten.'))

# Commenting out the batch-decompress functions because they do not
# work yet. I changed the batch-processing code and broke them
# somehow. See MGET ticket #344 for more info.

##BatchProcessing.GenerateForMethod(File.Decompress,
##    inputParamNames=['compressedFile'],
##    inputParamFieldArcGISDisplayNames=[_('Compressed file field')],
##    inputParamDescriptions=[_(
##"""%s paths of the files to decompress.
##
##The files must be in a supported compression format. The formats presently
##supported are:
##
##* .bz2 - a single file compressed in `bzip2 <http://www.bzip.org>`_ format
##* .gz - a single file compressed in `gzip <http://www.gzip.org>`_ format
##* .tar - one or more files archived in UNIX tar format
##* .zip - one or more files archived and compressed in `PK Zip <http://www.pkware.com>`_ format
##* .Z - a single file compressed in UNIX "compress" format
##
##tar files that are compressed in bzip2 (.tar.bz2), gzip (.tar.gz) or compress
##format (.tar.Z) are automatically handled.""")],
##    outputParamNames=['destinationDirectory'],
##    outputParamFieldArcGISDisplayNames=[_('Destination directory field')],
##    outputParamExpressionArcGISDisplayNames=[_('Destination directory Python expression')],
##    outputParamDescriptions=[_("""%s paths of the directories to receive the decompressed files.""")],
##    outputParamExpressionDescriptions=[
##"""Python expression used to calculate the absolute path of the
##destination directory for a given compressed file. The compressed file
##will be decompressed into this directory. If the compressed file is in
##an archive format such as .zip or .tar, all of the files and
##directories in the archive will be decompressed into this directory,
##replicating the directory structure of the archive.
##
##The expression may be any Python statement appropriate for passing to
##the eval function and must return a Unicode string. The expression may
##reference the following variables:
##
##* directoryToSearch - the value provided for the directory to search
##  parameter
##
##* rootDestination - the value provided for the root destination
##  directory parameter
##
##* compressedFile - the absolute path of the compressed file
##
##The default expression::
##
##    os.path.dirname(os.path.join(rootDestination, compressedFile[len(directoryToSearch)+1:]))
##
##decompresses the file into the root destination directory at the same
##relative location as it appears in the directory to search.
##
##For more information on Python syntax, please see the `Python
##documentation <http://www.python.org/doc/>`_."""],
##    outputParamDefaultExpressions=['os.path.dirname(os.path.join(rootDestination, compressedFile[len(directoryToSearch)+1:]))'],
##    constantParamNames=['decompressedFileToReturn'],
##    resultFieldArcGISDisplayNames=[_('Returned decompressed file field')],
##    resultFieldDescriptions=[_(
##"""Field to receive the path to the decompressed file returned by
##the decompressed file to return parameter.""")],
##    processListMethodName='DecompressList',
##    processListMethodShortDescription=_('Decompresses a list of files.'),
##    processListMethodResultDescription=_(
##"""List of paths to the decompressed files returned by the
##decompressedFileToReturn parameter. This list will be the same length
##as the compressedFileList, and each element is the decompressed file
##extracted from the compressed file specified in the corresponding
##element of compressedFileList."""),
##    processTableMethodName='DecompressTable',
##    processTableMethodShortDescription=_('Decompresses the files listed in a table.'),
##    processArcGISTableMethodName='DecompressArcGISTable',
##    processArcGISTableMethodArcGISDisplayName=_('Decompress Files Listed in Table'),
##    findAndProcessMethodName='FindAndDecompress',
##    findAndProcessMethodArcGISDisplayName='Find and Decompress Files',
##    findAndProcessMethodShortDescription=_('Finds and decompresses files in a directory.'),
##    findMethod=File.FindAndCreateTable,
##    findOutputFieldParams=['fileField'],
##    findAdditionalParams=['wildcard', 'searchTree', 'minSize', 'maxSize', 'minDateCreated', 'maxDateCreated', 'minDateModified', 'maxDateModified'],
##    outputLocationTypeMetadata=DirectoryTypeMetadata(createParentDirectories=True),
##    outputLocationParamDescription=_(
##"""Root destination directory for the decompressed files.
##
##The files may be decompressed into this directory or into
##subdirectories created within it, depending on the Python expression
##used to calculate the destination directory and whether the compressed
##file is an archive that contains directories within it."""),
##    outputLocationParamArcGISDisplayName=_('Root destination directory'),
##    calculateFieldMethod=Field.CalculateField,
##    calculateFieldExpressionParam='pythonExpression',
##    calculateFieldAdditionalParams=['modulesToImport'],
##    calculateFieldAdditionalParamsDefaults=[['os.path']],
##    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
##    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    directoryToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputDirectory\']\n    rootDestination = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputDirectory\']\nfinally:\n    del f\n'], ['compressedFile = row.compressedFile']],
##    calculatedOutputsArcGISCategory=_('Destination directory name options'),
##    constantParamsToOmitFromFindAndProcessMethod=['decompressedFileToReturn'],
##    overwriteExistingDescription=_('If True and skipExisting is False, existing files will be overwritten.'))

BatchProcessing.GenerateForMethod(File.Delete,
    inputParamNames=['path'],
    inputParamFieldArcGISDisplayNames=[_('File field')],
    inputParamDescriptions=[_('%s paths of the files to delete.')],
    processListMethodName='DeleteList',
    processListMethodShortDescription=_('Deletes a list of files.'),
    processTableMethodName='DeleteTable',
    processTableMethodShortDescription=_('Deletes the files listed in a table.'),
    processArcGISTableMethodName='DeleteArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Delete Files Listed in Table'),
    findAndProcessMethodName='FindAndDelete',
    findAndProcessMethodArcGISDisplayName='Find and Delete Files',
    findAndProcessMethodShortDescription=_('Finds and deletes files in a directory.'),
    findMethod=File.FindAndCreateTable,
    findOutputFieldParams=['fileField'],
    findAdditionalParams=['wildcard', 'searchTree', 'minSize', 'maxSize', 'minDateCreated', 'maxDateCreated', 'minDateModified', 'maxDateModified'])

BatchProcessing.GenerateForMethod(File.Move,
    inputParamNames=['sourceFile'],
    inputParamFieldArcGISDisplayNames=[_('Source file field')],
    inputParamDescriptions=[_('%s paths of the files to move.')],
    outputParamNames=['destinationFile'],
    outputParamFieldArcGISDisplayNames=[_('Destination file field')],
    outputParamExpressionArcGISDisplayNames=[_('Destination file Python expression')],
    outputParamDescriptions=[_('%s destination files.')],
    outputParamExpressionDescriptions=[File.FindAndCopy.__doc__.Obj.GetArgumentByName('destinationFilePythonExpression').Description],
    outputParamDefaultExpressions=[File.FindAndCopy.__doc__.Obj.GetArgumentByName('destinationFilePythonExpression').Default],
    processListMethodName='MoveList',
    processListMethodShortDescription=_('Moves a list of files.'),
    processTableMethodName='MoveTable',
    processTableMethodShortDescription=_('Moves the files listed in a table.'),
    processArcGISTableMethodName='MoveArcGISTable',
    processArcGISTableMethodArcGISDisplayName=_('Move Files Listed in Table'),
    findAndProcessMethodName='FindAndMove',
    findAndProcessMethodArcGISDisplayName='Find and Move Files',
    findAndProcessMethodShortDescription=_('Finds and moves files in a directory.'),
    findMethod=File.FindAndCreateTable,
    findOutputFieldParams=['fileField'],
    findAdditionalParams=['wildcard', 'searchTree', 'minSize', 'maxSize', 'minDateCreated', 'maxDateCreated', 'minDateModified', 'maxDateModified'],
    outputLocationTypeMetadata=DirectoryTypeMetadata(createParentDirectories=True),
    outputLocationParamDescription=_('Directory to receive the files.'),
    outputLocationParamArcGISDisplayName=_('Destination directory'),
    calculateFieldMethod=Field.CalculateField,
    calculateFieldExpressionParam='pythonExpression',
    calculateFieldAdditionalParams=['modulesToImport'],
    calculateFieldAdditionalParamsDefaults=[['os.path']],
    calculateFieldHiddenParams=['statementsToExecFirst', 'statementsToExecPerRow'],
    calculateFieldHiddenParamValues=[['import inspect\nf = inspect.currentframe()\ntry:\n    directoryToSearch = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'inputDirectory\']\n    destinationDirectory = f.f_back.f_back.f_back.f_back.f_back.f_locals[\'outputDirectory\']\nfinally:\n    del f\n'], ['sourceFile = row.sourceFile']],
    calculatedOutputsArcGISCategory=_('Destination file name options'),
    skipExistingDescription=_('If True, moving will be skipped for destination files that already exist.'),
    overwriteExistingDescription=_('If True and skipExisting is False, existing destination files will be overwritten.'))


###############################################################################
# Names exported by this module
###############################################################################

__all__ = ['File']
