# _FTPDirectoryTree.py - Defines FTPDirectoryTree, a DatasetCollectionTree
# representing a directory on an FTP server.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import ftplib
import os
import socket
import time
import sys

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _

from . import DatasetCollectionTree


class FTPDirectoryTree(DatasetCollectionTree):
    __doc__ = DynamicDocString()

    def _GetDatasetType(self):
        return self._DatasetType

    DatasetType = property(_GetDatasetType, doc=DynamicDocString())

    def _GetHost(self):
        return self._Host

    Host = property(_GetHost, doc=DynamicDocString())

    def _GetPort(self):
        return self._Port

    Port = property(_GetPort, doc=DynamicDocString())

    def _GetUser(self):
        return self._User

    User = property(_GetUser, doc=DynamicDocString())

    def _GetPassword(self):
        return self._Password

    Password = property(_GetPassword, doc=DynamicDocString())

    def _GetPath(self):
        return self._Path

    Path = property(_GetPath, doc=DynamicDocString())

    def _GetCacheTree(self):
        return self._CacheTree

    CacheTree = property(_GetCacheTree, doc=DynamicDocString())

    def __init__(self, datasetType, host, port=21, user='anonymous', password='anonymous@', path=None, timeout=60, maxRetryTime=120, pathParsingExpressions=None, cacheTree=True, queryableAttributes=None, queryableAttributeValues=None, lazyPropertyValues=None, cacheDirectory=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        super(FTPDirectoryTree, self).__init__(pathParsingExpressions, queryableAttributes=queryableAttributes, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues, cacheDirectory=cacheDirectory)

        self._FTP = None                    # ftplib FTP object
        self._LoginSucceeded = False        # True if we ever logged in successfully one time. Only used to control how many times we retry. If we previously logged in successfully, we'll retry logins indefinitely. But if we've never succeeded, we'll only try to log in three times before failing, because the user or password are probably wrong.

        self._DatasetType = datasetType
        self._Host = host
        self._Port = port
        self._User = user
        self._Password = password

        if path is not None and path != '/':
            path = path.rstrip('/')
            if len(path) <= 0:
                path = None
        self._Path = path

        if sys.version_info.major > 2 or sys.version_info.major == 2 and sys.version_info.minor >= 6:
            self._Timeout = timeout
        else:
            self._Timeout = None
        self._MaxRetryTime = maxRetryTime

        self._CacheTree = cacheTree
        if self._CacheTree:
            self._TreeCache = {}
        else:
            self._TreeCache = None

        if self._User.lower() == 'anonymous':
            if self._Path is not None:
                self._DisplayName = _('FTP server %(host)s (port %(port)s, user %(user)s, password %(password)s), path %(path)s') % {'user': self._User, 'password': self._Password, 'host': self._Host, 'port': self._Port, 'path': self._Path}
            else:
                self._DisplayName = _('FTP server %(host)s (port %(port)s, user %(user)s, password %(password)s)') % {'user': self._User, 'password': self._Password, 'host': self._Host, 'port': self._Port}
        else:
            if self._Path is not None:
                self._DisplayName = _('FTP server %(host)s (port %(port)s, user %(user)s), path %(path)s') % {'user': self._User, 'host': self._Host, 'port': self._Port, 'path': self._Path}
            else:
                self._DisplayName = _('FTP server %(host)s (port %(port)s, user %(user)s)') % {'user': self._User, 'host': self._Host, 'port': self._Port}

    def _GetDisplayName(self):
        return self._DisplayName

    def _ListContents(self, pathComponents):

        # If we are supposed to cache the tree, probe our cache for the
        # contents of this directory.

        components = []
        if self.Path is not None:
            components.append(self.Path)
        components.extend(pathComponents)
        if len(components) > 0:
            directory = '/'.join(components)
        else:
            directory = None

        if self._CacheTree and directory in self._TreeCache:
            self._LogDebug(_('%(class)s 0x%(id)016X: Retrieved cached contents of directory %(dir)s'), {'class': self.__class__.__name__, 'id': id(self), 'dir': directory})
            return self._TreeCache[directory]

        # We did not retrieve the contents of this directory from the cache.
        # Get the contents from the server and update the cache (if required).
        
        contents = [s.split('/')[-1] for s in self._RetryFTPOperation(self._ListDirectory, (directory,))]
        contents.sort()
        
        if self._CacheTree:
            self._TreeCache[directory] = contents

        return contents

    def _ListDirectory(self, directory):
        if directory is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Trying FTP.nlst(%(dir)r)'), {'class': self.__class__.__name__, 'id': id(self), 'dir': directory})
            try:
                return self._FTP.nlst(directory)
            except Exception as e:
                raise RuntimeError(_('Failed to obtain a directory listing of %(dir)s from FTP server %(host)s. Check that the server is operating properly and that your computer can connect to it. If necessary, contact the server\'s operator for assistance. Error details: %(e)s: %(msg)s.') % {'dir': directory, 'host': self._Host, 'e': e.__class__.__name__, 'msg': e})
        else:
            self._LogDebug(_('%(class)s 0x%(id)016X: Trying FTP.nlst()'), {'class': self.__class__.__name__, 'id': id(self)})
            try:
                return self._FTP.nlst()
            except Exception as e:
                raise RuntimeError(_('Failed to obtain a directory listing from FTP server %(host)s. Check that the server is operating properly and that your computer can connect to it. If necessary, contact the server\'s operator for assistance. Error details: %(e)s: %(msg)s.') % {'host': self._Host, 'e': e.__class__.__name__, 'msg': e})

    def _ConstructFoundObject(self, pathComponents, attrValues, options):
        return self.DatasetType(os.path.join(*pathComponents), parentCollection=self, queryableAttributeValues=attrValues, cacheDirectory=self.CacheDirectory, **options)

    def _GetLocalFile(self, pathComponents):

        # We need a place to cache the downloaded file. Check whether
        # we or our parent collections have a cache directory defined.
        # If so, use it. If not, create a temporary one.

        cacheDirectory = None
        obj = self
        while obj is not None:
            if obj.CacheDirectory is not None:
                cacheDirectory = obj.CacheDirectory
                if not os.path.isdir(cacheDirectory):
                    self._LogDebug(_('Creating cache directory %(dir)s.') % {'dir': cacheDirectory})
                    os.makedirs(cacheDirectory)
                break
            obj = obj.ParentCollection
        
        if cacheDirectory is None:
            cacheDirectory = self._CreateTempDirectory()

        # If the file does not already exist, download it.

        localFile = os.path.join(cacheDirectory, pathComponents[-1])
        if not os.path.isfile(localFile):
            components = []
            if self.Path is not None:
                components.append(self.Path)
            components.extend(pathComponents)
            self._RetryFTPOperation(self._DownloadFile, ('/'.join(components), localFile))

        return localFile, True          # True indicates that it is ok for the caller to delete the downloaded file after decompressing it, to save space

    def _DownloadFile(self, remotePath, localPath):

        # Open the file for appending and seek to the end. If we are being
        # called again after a failure, we will resume the where we left off.

        try:
            f = open(localPath, 'ab')
        except Exception as e:
            raise RuntimeError(_('Failed to open temporary file %(local)s to receive downloaded data. Error details: %(e)s: %(msg)s.') % {'local': localPath, 'e': e.__class__.__name__, 'msg': e})

        try:
            try:
                f.seek(0, 2)
                position = f.tell()
            except Exception as e:
                raise RuntimeError(_('Failed to seek to the end of temporary file %(local)s. Error details: %(e)s: %(msg)s.') % {'local': localPath, 'e': e.__class__.__name__, 'msg': e})

            # Initiate the download. This will return a socket for the FTP
            # data connection.

            try:
                sock, size = self._FTP.ntransfercmd('RETR ' + remotePath, f.tell())
            except Exception as e:
                raise RuntimeError(_('Failed to initiate a download of %(remote)s from FTP server %(host)s. The FTP RETR command failed with: %(e)s: %(msg)s.') % {'remote': remotePath, 'host': self._Host, 'e': e.__class__.__name__, 'msg': e})

            try:
                if position > 0:
                    if size is not None:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Resuming download of %(remote)s to %(local)s at byte %(position)s. Expected download size: %(size)s bytes.'), {'class': self.__class__.__name__, 'id': id(self), 'remote': remotePath, 'local': localPath, 'position': position, 'size': size})
                    else:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Resuming download of %(remote)s to %(local)s at byte %(position)s.'), {'class': self.__class__.__name__, 'id': id(self), 'remote': remotePath, 'local': localPath, 'position': position})
                else:
                    if size is not None:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Downloading %(remote)s to %(local)s. Expected download size: %(size)s bytes.'), {'class': self.__class__.__name__, 'id': id(self), 'remote': remotePath, 'local': localPath, 'size': size})
                    else:
                        self._LogDebug(_('%(class)s 0x%(id)016X: Downloading %(remote)s to %(local)s.'), {'class': self.__class__.__name__, 'id': id(self), 'remote': remotePath, 'local': localPath})

                # Download 4 KB chunks, following the Python 2.7 socket.recv()
                # documentation which says "For best match with hardware and
                # network realities, the value of bufsize should be a
                # relatively small power of 2, for example, 4096". Note that
                # ftplib's own implementation of retrbinary() from Python 2.7
                # uses 8192. I don't think the difference will be critical.

                while True:
                    try:
                        chunk = sock.recv(4096)
                    except Exception as e:
                        raise RuntimeError(_('The download of %(remote)s from FTP server %(host)s was interrupted. Error details: %(e)s: %(msg)s.') % {'remote': remotePath, 'host': self._Host, 'e': e.__class__.__name__, 'msg': e})

                    if chunk is None or len(chunk) <= 0:
                        break

                    try:
                        f.write(chunk)
                    except Exception as e:
                        raise RuntimeError(_('Failed to write downloaded data to temporary file %(local)s. Error details: %(e)s: %(msg)s.') % {'local': localPath, 'e': e.__class__.__name__, 'msg': e})

            finally:
                try:
                    sock.close()
                except:
                    pass
        finally:
            try:
                f.close()
            except:
                pass

        # ftplib's implementation of retrbinary() from Python 2.7 calls the
        # undocumented FTP.voidresp() method, which checks the response from
        # the server to ensure it is within the range of successful codes. I'm
        # not sure what the consequence of not doing this might be, so I'm
        # going to follow ftplib's example and call it here.

        self._FTP.voidresp()
        self._LogDebug(_('%(class)s 0x%(id)016X: Download complete.'), {'class': self.__class__.__name__, 'id': id(self)})

    def _RetryFTPOperation(self, func, params):
        
        # Loop until success or we reach the timeout.

        try:
            message = None
            started = time.perf_counter()
            attempt = 0
            loginFailures = 0
            nextUpdate = None
            gp = None

            while True:
                attempt += 1
                try:
                    # If we are not connected, try to connect and log in.

                    if self._FTP is None:
                        self._FTP = ftplib.FTP()
                        try:
                            if sys.version_info.major > 2 or sys.version_info.major == 2 and sys.version_info.minor >= 6:
                                self._LogDebug(_('%(class)s 0x%(id)016X: Trying FTP.connect(%(host)r, %(port)r, %(timeout)r).'), {'class': self.__class__.__name__, 'id': id(self), 'host': self._Host, 'port': self._Port, 'timeout': self._Timeout})
                                self._FTP.connect(self._Host, self._Port, self._Timeout)
                            else:
                                self._LogDebug(_('%(class)s 0x%(id)016X: Trying FTP.connect(%(host)r, %(port)r) with no timeout (timeout not supported by this version of Python).'), {'class': self.__class__.__name__, 'id': id(self), 'host': self._Host, 'port': self._Port})
                                self._FTP.connect(self._Host, self._Port)
                        except Exception as e:
                            self._FTP = None
                            message = _('Failed to open FTP connection to server %(host)r, port %(port)r. Verify that the server hostname and port are correct. If they are, check that the server is operating properly and that your computer can connect to it. If necessary, contact the server\'s operator for assistance. Error details: %(e)s: %(msg)s.') % {'host': self._Host, 'port': self._Port, 'e': e.__class__.__name__, 'msg': e}
                            raise

                        if self._User.lower() == 'anonymous':
                            self._LogDebug(_('%(class)s 0x%(id)016X: FTP.connect() successful. Trying FTP.login(%(user)r, %(password)r)'), {'class': self.__class__.__name__, 'id': id(self), 'user': self._User, 'password': self._Password})
                        else:
                            self._LogDebug(_('%(class)s 0x%(id)016X: FTP.connect() successful. Trying FTP.login(%(user)r, <password hidden>)'), {'class': self.__class__.__name__, 'id': id(self), 'user': self._User})

                        try:
                            self._FTP.login(self._User, self._Password)
                        except Exception as e:
                            self._Close()
                            loginFailures += 1
                            message = _('Failed to log in to FTP server %(host)r as user %(user)r. Verify that the user name and password are correct. If necessary, contact the server\'s operator for assistance. Error details: %(e)s: %(msg)s.') % {'host': self._Host, 'user': self._User, 'e': e.__class__.__name__, 'msg': e}
                            raise

                        self._LoginSucceeded = True
                        loginFailures = 0
                        self._RegisterForCloseAtExit()
                        self._LogDebug(_('%(class)s 0x%(id)016X: FTP.login() successful. Setting transfer mode to binary.'), {'class': self.__class__.__name__, 'id': id(self)})

                        # Switch to binary mode so that FTP.transfercmd will
                        # use binary mode.

                        try:
                            self._FTP.voidcmd('TYPE I')
                        except Exception as e:
                            self._Close()
                            message = _('Failed to switch the FTP transfer type to binary for the FTP connection to server %(host)r. This error is unusual. If it reoccurs and will not stop, please contact the MGET development team for assistance. Error details: FTP.voidcmd(\'TYPE I\') failed with %(e)s: %(msg)s.') % {'host': self._Host, 'e': e.__class__.__name__, 'msg': e}
                            raise

                        # We will do downloads in FTP passive mode, which is
                        # Python's default and much more compatible with
                        # typical firewall setups than active mode. A problem
                        # with passive mode is that while the download is
                        # happening on the data connection, the control
                        # connection is idle. If it is idle for too long, it
                        # may be closed by intervening firewalls. It appears
                        # that this can sometimes cause the download to fail.
                        #
                        # One suggestion for dealing with this is to
                        # periodically send NOOP commands on the control
                        # connection, e.g.: 
                        # http://stackoverflow.com/questions/19705438/python-ftplib-transfercmd-binary-mode
                        # But apparently not all servers support that
                        # (see https://curl.haxx.se/mail/curlpython-2010-12/0000.html
                        # and https://www.smartftp.com/forums/index.php?/topic/13479-sending-keep-alives-during-ftp-upload/).
                        # I observed this problem with the CMEMS FTP server
                        # ftp.sltac.cls.fr. When a NOOP was sent on the
                        # control connection while a RETR download was active
                        # on the data connection, the server would not reply
                        # to the NOOP, eventually causing ftplib to time out.
                        #
                        # The alternative suggestion is to enable TCP
                        # keepalive on the control connection, e.g. 
                        # http://stackoverflow.com/questions/5269012/using-threading-to-keep-ftp-control-port-alive
                        # But a problem with this approach is that the default
                        # keep alive time for Windows can be quite high, such
                        # as two hours
                        # (https://blogs.technet.microsoft.com/nettracer/2010/06/03/things-that-you-may-want-to-know-about-tcp-keepalives/).
                        # It appears this will be too long. When I browsed the
                        # CMEMS FTP server with Firefox and left it idle for a
                        # few minutes, I had to log in again. This is not 100%
                        # definitive evidence, as I did not have a download
                        # active at the time; the server could be smart enough
                        # to keep the control connection open if a download is
                        # active. But there are many stories on the internet
                        # of intervening firewalls closing the idle control
                        # connection after a few minutes, or even 1 minute.
                        #
                        # To try to mitigate that, set the keepalive timer to
                        # 15 seconds, e.g. 
                        # http://stackoverflow.com/questions/12248132/how-to-change-tcp-keepalive-timer-using-python-script

                        self._FTP.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)        # This call may be unnecessary given the call below.

                        if sys.platform == 'win32':
                            self._FTP.sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 15000, 3000))       # onoff=1, keepalivetime=15000 ms, keepaliveinterval=3000 ms

                    # Call the requested function. If it fails, close the FTP
                    # connection. Note: do not call self._Close() to close the
                    # connection. That will cause the base class _Close() to
                    # be called, which will delete any temporary directories
                    # we have created. We do not want that; if an intermittant
                    # failure caused an FTP download to fail, we want to be
                    # able to resume downloading the file where we left off,
                    # which will not work if the temp directory is deleted.

                    try:
                        returnValue = func(*params)
                    except Exception as e:
                        message = e
                        self._LogDebug(_('%(class)s 0x%(id)016X: Sending FTP QUIT'), {'class': self.__class__.__name__, 'id': id(self)})
                        try:
                            self._FTP.quit()
                        except Exception as e:
                            self._LogDebug(_('%(class)s 0x%(id)016X: FTP.quit() failed and raised %(e)s: %(msg)s. Closing the connection.'), {'class': self.__class__.__name__, 'id': id(self), 'e': e.__class__.__name__, 'msg': e})
                            try:
                                self._FTP.close()
                            except:
                                pass
                        self._FTP = None
                        raise

                # If an exception was raised, execute the retry logic.

                except Exception as e:

                    # If we have exceeded the maximum retry time, reraise.
                    
                    now = time.perf_counter()
                    if self._MaxRetryTime is None or self._MaxRetryTime < 0 or now >= started + self._MaxRetryTime:
                        raise

                    # If this was the first attempt, log a warning and immediately try again.

                    if attempt == 1:
                        if message is not None:
                            self._LogWarning(message)
                            self._LogWarning(_('Retrying...'))
                        nextUpdate = now + 300
                        continue

                    # If this is the second login failure and we have never
                    # succeeded, reraise.

                    if loginFailures >= 2 and not self._LoginSucceeded:
                        raise

                    # Otherwise, log a debug message and calculate how many
                    # seconds we should sleep before trying again. If 15
                    # seconds or less have elapsed, sleep for 1 second. If
                    # between 15 and 60 seconds, sleep for 5 seconds. If
                    # longer than 60 seconds, sleep for 30 seconds.

                    self._LogDebug(_('%(class)s 0x%(id)016X: %(msg)s'), {'class': self.__class__.__name__, 'id': id(self), 'msg': message})

                    sleepFor = 0

                    if now - started <= 15:
                        if self._Timeout is not None and self._Timeout < 1:
                            sleepFor = 1. - self._Timeout
                        else:
                            sleepFor = 1.
                            
                    elif now - started <= 60:
                        if self._Timeout is not None and self._Timeout < 5:
                            sleepFor = 5. - self._Timeout
                        else:
                            sleepFor = 5.
                            
                    else:
                        if self._Timeout is not None and self._Timeout < 30:
                            sleepFor = 30. - self._Timeout
                        else:
                            sleepFor = 30.

                    # If the ArcGIS geoprocessor was initialized, we might be
                    # running from the ArcGIS geoprocessing GUI. The GUI gives
                    # the user the ability to cancel the running tool. The
                    # canceling mechanism is implemented by geoprocessor
                    # functions checking for the cancel request and raising
                    # arcgisscripting.ExecuteAbort when the cancel occurs.
                    #
                    # So: If the geoprocessor was initialized, sleep for 1
                    # second at a time and call a trivial geoprocessor
                    # function each time. If a cancel was requested, the
                    # function will raise arcgisscripting.ExecuteAbort.
                    #
                    # Otherwise, just sleep for the entire amount.

                    if gp is None:
                        from ...ArcGIS import GeoprocessorManager
                        gp = GeoprocessorManager.GetGeoprocessor()
                        
                    if gp is not None:
                        if sleepFor > 0:
                            for i in range(int(sleepFor)):
                                time.sleep(1)
                                gp.GetParameterAsText(0)
                        else:
                            gp.GetParameterAsText(0)
                            
                    elif sleepFor > 0:
                        time.sleep(sleepFor)

                    # If five minutes have elapsed since we last updated the
                    # user, tell him we are still retrying.

                    if nextUpdate is not None and now >= nextUpdate:
                        self._LogWarning(_('Still retrying; %(elapsed)s elapsed since the problem started...') % {'elapsed': str(datetime.timedelta(seconds=now-started))})
                        nextUpdate = now + 300

                    # Now try again.

                    continue

                else:
                    if nextUpdate:
                        self._LogWarning(_('Retry successful.'))
                    break

        except Exception as e:
            if e.__class__.__name__ == 'ExecuteAbort' and str(e).lower() == 'cancelled function':
                self._Close()
                raise
            if message is not None:
                if self._LoginSucceeded or loginFailures < 2:
                    self._LogError(_('The operation was retried for %(retry)i seconds without success. Aborting.') % {'retry': self._MaxRetryTime})
                raise RuntimeError(message)
            else:
                raise

        return returnValue

    def _Close(self):
        if hasattr(self, '_FTP') and self._FTP is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Sending FTP QUIT'), {'class': self.__class__.__name__, 'id': id(self)})
            try:
                self._FTP.quit()
            except Exception as e:
                self._LogDebug(_('%(class)s 0x%(id)016X: FTP.quit() failed and raised %(e)s: %(msg)s. Closing the connection.'), {'class': self.__class__.__name__, 'id': id(self), 'e': e.__class__.__name__, 'msg': e})
                try:
                    self._FTP.close()
                except:
                    pass
            self._FTP = None
        super(FTPDirectoryTree, self)._Close()


###############################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.Collections instead.
###############################################################################################

__all__ = []
