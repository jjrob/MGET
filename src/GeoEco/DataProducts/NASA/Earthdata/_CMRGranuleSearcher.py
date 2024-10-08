# _CMRGranuleSearcher.py - Defines CMRGranuleSearcher.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import os
import pickle
import re
import time 

from ....Datasets import DatasetCollection
from ....DynamicDocString import DynamicDocString
from ....Internationalization import _


class CMRGranuleSearcher(DatasetCollection):
    __doc__ = DynamicDocString()

    def __init__(self, username, password, queryParams, linkTitleRegEx, queryableAttributes=None, timeout=60, maxRetryTime=300, cacheDirectory=None, metadataCacheLifetime=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Initialize our properties.

        self._Username = username
        self._Password = password
        self._QueryParams = queryParams
        self._LinkTitleRegEx = linkTitleRegEx
        self._Timeout = timeout
        self._MaxRetryTime = maxRetryTime
        self._MetadataCacheLifetime = metadataCacheLifetime

        self._Session = None
        self._QueryResults = None

        # Initialize the base class.

        super(CMRGranuleSearcher, self).__init__(queryableAttributes=queryableAttributes, cacheDirectory=cacheDirectory)

    def _Close(self):
        if self._Session is not None:
            self._LogDebug(_('%(class)s 0x%(id)016X: Closed.'), {'class': self.__class__.__name__, 'id': id(self)})
            self._Session.close()
            self._Session = None
        super(CMRGranuleSearcher, self)._Close()

    def _GetDisplayName(self):
        return _('NASA Earthdata CMR granules matching %(qp)r' % {'qp': self._QueryParams})

    def _QueryDatasets(self, parsedExpression, progressReporter, options, parentAttrValues):

        # Go through the list of URLs returned by the server, testing whether
        # each one matches the query expression. For each match, call the
        # derived class to construct a DatasetCollection instance for it,
        # query it, and return the resulting Datasets.

        datasetsFound = []

        for [url, title] in self._QueryServer()['URLList']:
            queryableAttributeValues = self._GetQueryableAttributeValuesForUrl(url, title)
            if queryableAttributeValues is None:
                continue

            if parsedExpression is not None:
                try:
                    matches = parsedExpression.eval(queryableAttributeValues)
                except Exception as e:
                    continue
            else:
                matches = True

            if matches or matches is None:
                collection = self._ConstructFoundObjectForUrl(url, title, queryableAttributeValues)
                datasetsFound.extend(collection._QueryDatasets(parsedExpression, progressReporter, options, queryableAttributeValues))

        return datasetsFound

    def _GetOldestDataset(self, parsedExpression, options, parentAttrValues, dateTimeAttrName):
        return self._GetOldestOrNewestDataset(parsedExpression, options, False)

    def _GetNewestDataset(self, parsedExpression, options, parentAttrValues, dateTimeAttrName):
        return self._GetOldestOrNewestDataset(parsedExpression, options, True)

    def _GetOldestOrNewestDataset(self, parsedExpression, options, newest):

        # Go through the list of URLs returned by the server in time order,
        # testing whether each one matches the query expression. For each
        # match, construct a NetCDFFile or HDF4SDSCollection instance and
        # query it. As soon as that query returns a dataset, return it.

        if not newest:
            urlList = self._QueryServer()['URLList']
        else:
            urlList = reversed(self._QueryServer()['URLList'])

        for [url, title] in urlList:
            queryableAttributeValues = self._GetQueryableAttributeValuesForUrl(url, title)
            if queryableAttributeValues is None:
                continue

            if parsedExpression is not None:
                try:
                    matches = parsedExpression.eval(queryableAttributeValues)
                except Exception as e:
                    continue
            else:
                matches = True

            if matches or matches is None:
                collection = self._ConstructFoundObjectForUrl(url, title, queryableAttributeValues)
                datasets = collection._QueryDatasets(parsedExpression, None, options, queryableAttributeValues)
                if len(datasets) > 0:
                    return datasets[0]

        # We did not find a matching dataset. Return None.

        return None

    def _QueryServer(self):

        # Querying the server is fairly slow. The most common situation is
        # that QueryParams will contain 'collection_concept_id' as the only
        # parameter, in which case we will retrieve all of the granule records
        # for the entire collection. If that is the case, and we have a cache
        # directory, we'll cache the result to optimize repeated uses of this.

        cacheMetadata = len(self._QueryParams) == 1 and 'collection_concept_id' in self._QueryParams and self.CacheDirectory is not None and self._MetadataCacheLifetime is not None
        if cacheMetadata:
            cachePath = os.path.join(self.CacheDirectory, 'Metadata_CCID_' + self._QueryParams['collection_concept_id'] + '.pickle')
            if os.path.isfile(cachePath):
                try:
                    with open(cachePath, 'rb') as f:
                        [cachedResults, cacheTime] = pickle.load(f)
                except:
                    self._LogWarning(_('Failed to read metadata from cache file %(file)s. We will delete the file and query the server instead.') % {'file': cachePath})
                    try:
                        os.remove(cachePath)
                    except:
                        pass
                else:
                    if datetime.datetime.now() - cacheTime <= datetime.timedelta(seconds=self._MetadataCacheLifetime):
                        self._LogDebug(_('Using cached NASA Earthdata granule metadata for collection_concept_id=%(ccid)s.') % {'ccid': self._QueryParams['collection_concept_id']})
                        self._QueryResults = cachedResults
                    else:
                        self._LogDebug(_('The cached NASA Earthdata granule metadata for collection_concept_id=%(ccid)s has expired.') % {'ccid': self._QueryParams['collection_concept_id']})

        # If we have not cached the results of the query, query the server.

        if self._QueryResults is None:
            self._LogInfo(_('Downloading metadata from NASA Earthdata for granules where %(params)s.') % {'params': ' and '.join(['%s=%s' % (key, val) for key, val in list(self._QueryParams.items())])})

            results = {'URLList': [], 'URLsForFile': {}}
            response = None
            while True:

                # Build the HTTP query parameters.

                params = {}
                params.update(self._QueryParams)
                params['page_size'] = 2000              # Max allowed by NASA
                params['sort_key[]'] = 'start_date'

                # Prepare the request URL.

                import requests
                url = 'https://cmr.Earthdata.nasa.gov/search/granules.json'
                req = requests.models.PreparedRequest()
                req.prepare_url(url, params)

                # If we've already been through the loop once and have a
                # response, include the received CMR-Search-After in the
                # response header.

                headers = {}
                if response is not None:
                    headers['CMR-Search-After'] = response.headers['CMR-Search-After']

                # Issue the request in a retry loop.

                started = time.perf_counter()
                attempt = 0
                nextUpdate = None
                gp = None
                jsonParseFailures = 0

                while True:
                    try:
                        attempt += 1
                        authURL = None

                        # Create the session, if we have not done so already.
                        # The session holds a connection and authorization
                        # cookies that we want to reuse on subsequent
                        # connections.

                        if self._Session is None:
                            self._Session = requests.Session()
                            self._RegisterForCloseAtExit()
                        
                        # Issue the request. 
                        
                        if 'CMR-Search-After' in headers:
                            self._LogDebug(_('%(class)s 0x%(id)016X: Issuing HTTP GET %(url)s with CMR-Search-After=%(sa)s.'), {'class': self.__class__.__name__, 'id': id(self), 'url': req.url, 'sa': headers['CMR-Search-After']})
                        else:
                            self._LogDebug(_('%(class)s 0x%(id)016X: Issuing HTTP GET %(url)s.'), {'class': self.__class__.__name__, 'id': id(self), 'url': req.url})
                        response = self._Session.get(req.url, headers=headers, timeout=self._Timeout)
                        self._LogDebug(_('%(class)s 0x%(id)016X: Received HTTP status code %(code)s.'), {'class': self.__class__.__name__, 'id': id(self), 'code': response.status_code})

                        # At the time of this writing, it did not appear that
                        # Earthdata required authentication in order to search
                        # for granules. But if we got status code 401
                        # Unauthorized, it means they do. In this case, they
                        # redirected us to another URL for logging in. The
                        # request library knows how to handle that; we can
                        # simply HTTP GET that page with the credentials and
                        # it will return cookies that requests will maintain
                        # in our session. We can then GET the original URL.

                        if response.status_code == 401:
                            self._Session.auth = (self._Username, self._Password)
                            authURL = response.url

                            self._LogDebug(_('%(class)s 0x%(id)016X: Issuing HTTP GET %(url)s.'), {'class': self.__class__.__name__, 'id': id(self), 'url': authURL})
                            response = self._Session.get(authURL, timeout=self._Timeout)
                            self._LogDebug(_('%(class)s 0x%(id)016X: Received HTTP status code %(code)s.'), {'class': self.__class__.__name__, 'id': id(self), 'code': response.status_code})

                            if response.status_code != 401:
                                authURL = None

                            response.raise_for_status()    # This will raise an exception if we got 401 again.

                            # If we got to here, our authentication was
                            # successful. Make the original request again.

                            if 'CMR-Search-After' in headers:
                                self._LogDebug(_('%(class)s 0x%(id)016X: Issuing HTTP GET %(url)s with CMR-Search-After=%(sa)s.'), {'class': self.__class__.__name__, 'id': id(self), 'url': req.url, 'sa': headers['CMR-Search-After']})
                            else:
                                self._LogDebug(_('%(class)s 0x%(id)016X: Issuing HTTP GET %(url)s.'), {'class': self.__class__.__name__, 'id': id(self), 'url': req.url})
                            response = self._Session.get(req.url, headers=headers, timeout=self._Timeout)
                            self._LogDebug(_('%(class)s 0x%(id)016X: Received HTTP status code %(code)s.'), {'class': self.__class__.__name__, 'id': id(self), 'code': response.status_code})

                        # Check the response code and raise an exception if it
                        # was not successful.

                        response.raise_for_status()

                        # Parse the returned JSON.

                        try:
                            result = response.json()
                        except:
                            jsonParseFailures += 1
                            raise
                        jsonParseFailures = 0

                        # Break out of the retry loop.

                        break

                    except Exception as e:

                        # If got a second JSON parse failure failure, reraise.

                        if jsonParseFailures > 1:
                            self._LogError(_('Failed to parse the JSON reponse returned by %(url)s. Following error messages may provide additional clues about the problem. Please contact the MGET development team for assistance.') % {'url': response.url})
                            raise

                        # If we have exceeded the maximum retry time, reraise.
                        
                        now = time.perf_counter()
                        if self._MaxRetryTime is None or self._MaxRetryTime < 0 or now >= started + self._MaxRetryTime:
                            raise

                        # If this was the first attempt, immediately try again.

                        errMsg = str(e)
                        if attempt == 1:
                            self._LogDebug(_('%(class)s 0x%(id)016X: On our first request, got %(e)s: %(msg)s. Performing one immediate retry...') % {'class': self.__class__.__name__, 'id': id(self), 'e': e.__class__.__name__, 'msg': errMsg})
                            continue

                        # If we got an authorization failure (HTTP 401), log
                        # an error suggesting common solutions and reraise the
                        # original exception, which ultimately will also be
                        # logged.

                        if authURL is not None:
                            self._LogError(_('The NASA server replied with HTTP error 401 (Unauthorized), which usually means that either the user name or password were not recognized, or the user name does not have access to the requested file. Please check the spelling of your user name and password, and verify that the NASA Earthdata system shows you as authorized to access the data. Following error messages may provide additional clues about the problem.'))
                            raise

                        # If we have not logged this problem yet, log a warning.

                        if nextUpdate is None:
                            self._LogWarning(_('Failed to download %(url)s from the NASA Earthdata: %(e)s: %(msg)s. Retrying...') % {'url': req.url, 'e': e.__class__.__name__, 'msg': errMsg})
                            nextUpdate = now + 300

                        # Calculate how many seconds we should sleep before
                        # trying again. If 15 seconds or less have elapsed,
                        # sleep for 1 second. If between 15 and 60 seconds,
                        # close the existing Session and sleep for 5 seconds.
                        # If longer than 60 seconds, sleep for 30 seconds.

                        sleepFor = 0

                        if now - started <= 15:
                            if self._Timeout is not None and self._Timeout > 0 and self._Timeout < 1:
                                sleepFor = self._Timeout
                            else:
                                sleepFor = 1.
                        else:
                            try:
                                self._Session.close()
                            except:
                                pass
                            self._Session = None

                            if now - started <= 60:
                                if self._Timeout is not None and self._Timeout > 0 and self._Timeout < 5:
                                    sleepFor = self._Timeout
                                else:
                                    sleepFor = 5.
                                    
                            elif self._Timeout is not None and self._Timeout > 0 and self._Timeout < 30:
                                sleepFor = self._Timeout
                            else:
                                sleepFor = 30.

                        # If the ArcGIS geoprocessor was initialized, we might
                        # be running from the ArcGIS geoprocessing GUI. The
                        # GUI gives the user the ability to cancel the running
                        # tool. The canceling mechanism is implemented by
                        # geoprocessor functions checking for the cancel
                        # request and raising arcgisscripting.ExecuteAbort
                        # when the cancel occurs.
                        #
                        # So: If the geoprocessor was initialized, sleep for 1
                        # second at a time and call a trivial geoprocessor
                        # function each time. If a cancel was requested, the
                        # function will raise arcgisscripting.ExecuteAbort.
                        #
                        # Otherwise, just sleep for the entire amount.

                        if gp is None:
                            from GeoEco.ArcGIS import GeoprocessorManager
                            gp = GeoprocessorManager.GetGeoprocessor()
                            
                        if gp is not None:
                            if sleepFor > 0:
                                for i in range(int(sleepFor)):
                                    time.sleep(1)
                                    gp.GetArgumentCount()
                            else:
                                gp.GetArgumentCount()
                                
                        elif sleepFor > 0:
                            time.sleep(sleepFor)

                        # If five minutes have elapsed since we last updated
                        # the user, tell them we are still retrying.

                        if nextUpdate is not None and now >= nextUpdate:
                            self._LogWarning(_('Still retrying; %(elapsed)s elapsed since the problem started...') % {'elapsed': str(datetime.timedelta(seconds=now-started))})
                            nextUpdate = now + 300

                        # Now try again.

                        continue

                # If we did not get any entries back, break out of this loop.

                if not isinstance(result, dict) or 'feed' not in result:
                    raise ValueError(_('The JSON returned by the NASA Earthdata server %(url)s did not contain a "feed" dictionary. This is unexpected; we don\'t know how to parse this response. Please contact the MGET development team for assistance.') % {'url': response.url})

                if not isinstance(result['feed'], dict) or 'entry' not in result['feed'] or not isinstance(result['feed']['entry'], list):
                    raise ValueError(_('The JSON returned by the NASA Earthdata server %(url)s did not contain an "entry" list. This is unexpected; we don\'t know how to parse this response. Please contact the MGET development team for assistance.') % {'url': response.url})

                if len(result['feed']['entry']) <= 0:
                    break

                # Iterate through the links of the returned entries.

                for entry in result['feed']['entry']:
                    if isinstance(entry, dict) and 'title' in entry and isinstance(entry['title'], str) and 'links' in entry and isinstance(entry['links'], list):
                        for link in entry['links']:
                            if isinstance(link, dict) and 'title' in link and isinstance(link['title'], str) and \
                               'href' in link and isinstance(link['href'], str) and len(link['href'].strip()) > 0 and \
                               (self._LinkTitleRegEx is None or re.match(self._LinkTitleRegEx, link['title'], re.IGNORECASE) is not None):
                                
                                results['URLList'].append([link['href'].strip(), entry['title'].strip()])
                                fileName = link['href'].strip().rsplit('/', 1)[-1]
                                if fileName not in results['URLsForFile']:
                                    results['URLsForFile'][fileName] = []
                                results['URLsForFile'][fileName].append(link['href'].strip())

            self._QueryResults = results

            # Store the result in the cache directory, if desired.

            if cacheMetadata:
                try:
                    if not os.path.isdir(os.path.dirname(cachePath)):
                        self._LogDebug(_('%(class)s 0x%(id)016X: Creating cache directory "%(path)s".'), {'class': self.__class__.__name__, 'id': id(self), 'path': os.path.dirname(cachePath)})
                        os.makedirs(os.path.dirname(cachePath))

                    self._LogDebug(_('%(class)s 0x%(id)016X: Writing granule cache file "%(path)s".'), {'class': self.__class__.__name__, 'id': id(self), 'path': cachePath})
                    with open(cachePath, 'wb') as f:
                        pickle.dump([results, datetime.datetime.now()], f)
                except Exception as e:
                    self._LogWarning(_('Failed to write granule metadata to cache directory "%(dir)s". Subsequent requests for this metadata will be downloaded from the server, rather than being served from the cache. The error was %(e)s: %(msg)s.'), {'dir': os.path.dirname(cachePath), 'e': e.__class__.__name__, 'msg': e})

        return self._QueryResults

    # This function is used by NetCDFFile and similar classes when they make
    # us their parent collection and then need to get the file. We perform the
    # downloading for them.

    def _GetLocalFile(self, pathComponents):

        # We need a place to cache the downloaded file. Check whether we or
        # our parent collections have a cache directory defined. If so, use
        # it. If not, create a temporary one.

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

        localFile = os.path.join(cacheDirectory, pathComponents[0])
        if not os.path.isfile(localFile):
            # Look up in our metadata cache the URL for this file.

            if self._QueryResults is None:
                raise ValueError(_('CMRGranuleSearcher._GetLocalFile() was called but _QueryResults is None. CMRGranuleSearcher must be instructed to query the NASA Earthdata server before it can be used to download files. Please contact the MGET development team for assistance.'))
            if pathComponents[0] not in self._QueryResults['URLsForFile']:
                raise ValueError(_('CMRGranuleSearcher._GetLocalFile(%(pc)r) was called but that file is not in the query results cached from the NASA Earthdata server. Please contact the MGET development team for assistance.') % {'pc': pathComponents})
            if len(self._QueryResults['URLsForFile'][pathComponents[0]]) != 1:
                raise ValueError(_('CMRGranuleSearcher._GetLocalFile(%(pc)r) was called there were %(count)s query results returned by the NASA Earthdata server with that file name. We expected that there would be exactly 1. Please contact the MGET development team for assistance.') % {'pc': pathComponents, 'count': len(self._QueryResults['URLsForFile'][localFile])})

            url = self._QueryResults['URLsForFile'][pathComponents[0]][0]

            # Do the download in a retry loop.

            import requests
            started = time.perf_counter()
            attempt = 0
            nextUpdate = None
            gp = None

            while True:
                try:
                    attempt += 1
                    authURL = None

                    # Create the session, if we have not done so already. The
                    # session holds a connection and authorization cookies
                    # that we want to reuse on subsequent connections.

                    if self._Session is None:
                        self._Session = requests.Session()
                        self._RegisterForCloseAtExit()
                    
                    # Issue the request. Note the use of stream=True, to allow
                    # downloading of large files. See
                    # https://stackoverflow.com/a/16696317
                    
                    self._LogDebug(_('%(class)s 0x%(id)016X: Issuing HTTP GET %(url)s.'), {'class': self.__class__.__name__, 'id': id(self), 'url': url})
                    response = self._Session.get(url, stream=True, timeout=self._Timeout)
                    self._LogDebug(_('%(class)s 0x%(id)016X: Received HTTP status code %(code)s.'), {'class': self.__class__.__name__, 'id': id(self), 'code': response.status_code})

                    # If we got status code 401 Unauthorized, they redirected
                    # us to another URL for logging in. The request library
                    # knows how to handle that; we can simply HTTP GET that
                    # page with the credentials and it will return cookies
                    # that the requests library will maintain in our session.
                    # It also redirects us to the original file, which is
                    # returned in the response.

                    if response.status_code == 401:
                        self._Session.auth = (self._Username, self._Password)
                        authURL = response.url

                        self._LogDebug(_('%(class)s 0x%(id)016X: Issuing HTTP GET %(url)s.'), {'class': self.__class__.__name__, 'id': id(self), 'url': authURL})
                        response = self._Session.get(authURL, stream=True, timeout=self._Timeout)
                        self._LogDebug(_('%(class)s 0x%(id)016X: Received HTTP status code %(code)s.'), {'class': self.__class__.__name__, 'id': id(self), 'code': response.status_code})

                        if response.status_code != 401:
                            authURL = None

                    # Check the response code and raise an exception if it was
                    # not successful.

                    response.raise_for_status()

                    # If we got to here, the response should be successful and
                    # Content-Type should be application/octet-stream,
                    # binary/octet-stream, or application/x-netcdf (and the
                    # content itself should be the file). Verify this.

                    if 'Content-Type' in response.headers and not (response.headers['Content-Type'].lower().startswith('application/octet-stream') or response.headers['Content-Type'].lower().startswith('binary/octet-stream') or response.headers['Content-Type'].lower().startswith('application/x-netcdf')):
                        raise ValueError(_('In response to our request to %(url)s, we expected the server to return data with Content-Type "application/octet-stream", "binary/octet-stream", or "application/x-netcdf", representing the file, but instead it returned Content-Type "%(ct)s". We do not know how to handle that kind of response.' % {'url': response.url, 'ct': response.headers['Content-Type']}))

                    # Store the returned data in the destination file.

                    tempFile = os.path.join(localFile + '.tmp')
                    self._LogDebug(_('%(class)s 0x%(id)016X: HTTP GET was successful. Writing the response to %(file)s'), {'class': self.__class__.__name__, 'id': id(self), 'file': tempFile})
                    try:
                        bytesWritten = 0
                        f = open(tempFile, 'wb')
                        try:
                            for chunk in response.iter_content(chunk_size=65536):
                                bytesWritten += len(chunk)
                                f.write(chunk)
                        finally:
                            f.close()
                        self._LogDebug(_('%(class)s 0x%(id)016X: Wrote %(bytes)s bytes. Renaming %(file1)s to %(file2)s'), {'class': self.__class__.__name__, 'id': id(self), 'bytes': bytesWritten, 'file1': tempFile, 'file2': os.path.basename(localFile)})
                        os.rename(tempFile, localFile)
                    finally:
                        try:
                            if os.path.exists(tempFile):
                                os.remove(tempFile)
                        except:
                            pass

                    # Break out of the retry loop.

                    break

                except Exception as e:

                    # If we have exceeded the maximum retry time, reraise.
                    
                    now = time.perf_counter()
                    if self._MaxRetryTime is None or self._MaxRetryTime < 0 or now >= started + self._MaxRetryTime:
                        raise

                    # If this was the first attempt, immediately try again.

                    errMsg = str(e)
                    if attempt == 1:
                        self._LogDebug(_('%(class)s 0x%(id)016X: On our first request, got %(e)s: %(msg)s. Performing one immediate retry...') % {'class': self.__class__.__name__, 'id': id(self), 'e': e.__class__.__name__, 'msg': errMsg})
                        continue

                    # If we got an authorization failure (HTTP 401), log an
                    # error suggesting common solutions and reraise the
                    # original exception, which ultimately will also be
                    # logged.

                    if authURL is not None:
                        self._LogError(_('The NASA server replied with HTTP error 401 (Unauthorized), which usually means that either the user name or password were not recognized, or the user name does not have access to the requested file. Please check the spelling of your user name and password, and verify that the NASA Earthdata system shows you as authorized to access the data. Following error messages may provide additional clues about the problem.'))
                        raise

                    # If we have not logged this problem yet, log a warning.

                    if nextUpdate is None:
                        self._LogWarning(_('Failed to download %(url)s from the NASA Earthdata: %(e)s: %(msg)s. Retrying...') % {'url': url, 'e': e.__class__.__name__, 'msg': errMsg})
                        nextUpdate = now + 300

                    # Calculate how many seconds we should sleep before trying
                    # again. If 15 seconds or less have elapsed, sleep for 1
                    # second. If between 15 and 60 seconds, close the existing
                    # Session and sleep for 5 seconds. If longer than 60
                    # seconds, sleep for 30 seconds.

                    sleepFor = 0

                    if now - started <= 15:
                        if self._Timeout is not None and self._Timeout > 0 and self._Timeout < 1:
                            sleepFor = self._Timeout
                        else:
                            sleepFor = 1.
                    else:
                        try:
                            self._Session.close()
                        except:
                            pass
                        self._Session = None

                        if now - started <= 60:
                            if self._Timeout is not None and self._Timeout > 0 and self._Timeout < 5:
                                sleepFor = self._Timeout
                            else:
                                sleepFor = 5.
                                
                        elif self._Timeout is not None and self._Timeout > 0 and self._Timeout < 30:
                            sleepFor = self._Timeout
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
                        from GeoEco.ArcGIS import GeoprocessorManager
                        gp = GeoprocessorManager.GetGeoprocessor()
                        
                    if gp is not None:
                        if sleepFor > 0:
                            for i in range(int(sleepFor)):
                                time.sleep(1)
                                gp.GetArgumentCount()
                        else:
                            gp.GetArgumentCount()
                            
                    elif sleepFor > 0:
                        time.sleep(sleepFor)

                    # If five minutes have elapsed since we last updated
                    # the user, tell him we are still retrying.

                    if nextUpdate is not None and now >= nextUpdate:
                        self._LogWarning(_('Still retrying; %(elapsed)s elapsed since the problem started...') % {'elapsed': str(datetime.timedelta(seconds=now-started))})
                        nextUpdate = now + 300

                    # Now try again.

                    continue
                
        return localFile, True          # True indicates that it is ok for the caller to delete the downloaded file after decompressing it, to save space

    # Private methods that the derived class should override.

    def _GetQueryableAttributeValuesForUrl(self, url, title):
        raise NotImplementedError(_('The _GetQueryableAttributeValuesForUrl method of class %s has not been implemented.') % self.__class__.__name__)

    def _ConstructFoundObjectForUrl(self, url, title, queryableAttributeValues):
        raise NotImplementedError(_('The _ConstructFoundObjectForUrl method of class %s has not been implemented.') % self.__class__.__name__)


######################################################################################################
# This module is not meant to be imported directly. Import GeoEco.DataProducts.NASA.Earthdata instead.
######################################################################################################

__all__ = []
