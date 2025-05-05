# _OGRTabularLayer.py - Defines OGRTabularLayer, a DatasetCollectionTree
# representing a tabular dataset accessed through GDAL's osgeo.ogr.Layer class
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

from ...DynamicDocString import DynamicDocString
from ...Internationalization import _
from ...Logging import Logger

from .._Dataset import Dataset
from .._Table import Table, Field


# WARNING: This class is not fully implemented yet and should not be used at this time.

class OGRTabularLayer(Table):
    __doc__ = DynamicDocString()

    # Public classmethods for opening, creating, and deleting datasets

    @classmethod
    def Open(cls, dataSourceName, layerName, update=False, driverName=None):
        self.__doc__.Obj.ValidateMethodInvocation()
        return OGRTabularLayer(dataSourceName, layerName, update, driverName)

    @classmethod
    def Create(cls, dataSourceName, layerName, geometryType=None, srType=None, sr=None, options=None, driverName=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        if isinstance(cls, OGRTabularLayer):
            className = cls.__class__.__name__
        else:
            className = cls.__name__

        # Open the data source in update mode.

        dataSource = cls._OpenDataSource(dataSourceName, layerName, True, driverName)
        try:

            # Create the layer in the data source.

            if driverName is None:
                driverName = dataSource.GetDriver().GetName()

            if geometryType is not None and srType is not None:
                srObj = cls.ConvertSpatialReference(srType, sr, 'obj')
                wkt = cls.ConvertSpatialReference('obj', srObj, 'wkt')
            else:
                srObj = None
                wkt = None

            cls._LogDebug(_('%(class)s: Creating OGR layer "%(layer)s" in %(driver)s data source "%(ds)s" with geometry type = %(gt)s, spatial reference WKT = %(wkt)s, options = %(opt)s.'),
                          {'class': className, 'layer': layerName, 'driver': driverName, 'ds': dataSourceName, 'gt': geometryType, 'wkt': wkt, 'opt': repr(options)})

            if geometryType in Dataset._OGRGeometryForGeometryType:
                geometryType = Dataset._OGRGeometryForGeometryType[geometryType]
            else:
                Logger.RaiseException(ValueError(_('Cannot create OGR layer "%(layer)s" of %(driver)s data source "%(ds)s" with the geometry type %(gt)s. OGR does not support that geometry type.') % {'layer': layerName, 'driver': driverName, 'ds': dataSourceName, 'gt': geometryType}))

            try:
                dataSource.CreateLayer(layerName, srObj, geometryType, options)
            except Exception as e:
                Logger.RaiseException(RuntimeError(_('Failed to create layer "%(layer)s" in OGR %(driver)s data source "%(ds)s" with geometry type = %(gt)s, spatial reference WKT = %(wkt)s, options = %(opt)s. OGR reported  %(msg)s') % {'layer': layerName, 'driver': driverName, 'ds': dataSourceName, 'gt': geometryType, 'wkt': wkt, 'opt': repr(options), 'e': e.__class__.__name__, 'msg': e}))
        
        # Close the data source.
        
        finally:
            try:
                if driverName is not None:
                    cls._LogDebug(_('%(class)s: Closing OGR %(driver)s data source "%(ds)".'), {'class': className, 'driver': driverName, 'ds': dataSourceName})
                else:
                    cls._LogDebug(_('%(class)s: Closing OGR data source "%(ds)".'), {'class': className, 'ds': dataSourceName})
            except:
                pass
            dataSource = None

    @classmethod
    def Delete(cls, dataSourceName, layerName, driverName=None, failIfDoesNotExist=False):
        self.__doc__.Obj.ValidateMethodInvocation()

        if isinstance(cls, OGRTabularLayer):
            className = cls.__class__.__name__
        else:
            className = cls.__name__

        # Open the data source in update mode.

        dataSource = cls._OpenDataSource(dataSourceName, layerName, True, driverName)
        try:

            # Delete the layer from the data source.

            if driverName is None:
                driverName = dataSource.GetDriver().GetName()

            found = False
            for i in range(len(dataSource.GetLayerCount())):
                if dataSource.GetLayer(i).GetName() == layerName:
                    found = True
                    break

            if not found:
                if not failIfDoesNotExist:
                    cls._LogDebug(_('%(class)s: Not deleting OGR layer "%(layer)s" from %(driver)s data source "%(ds)s" because a layer with that name does not exist in the data source.'), {'class': className, 'layer': layerName, 'driver': driverName, 'ds': dataSourceName})
                    return
                Logger.RaiseException(ValueError(_('Cannot delete layer "%(layer)s" from OGR %(driver)s data source "%(ds)s" because a layer with that name does not exist in the data source.') % {'layer': layerName, 'driver': driverName, 'ds': dataSourceName}))

            cls._LogDebug(_('%(class)s: Deleting OGR layer "%(layer)s" from %(driver)s data source "%(ds)s".'), {'class': className, 'layer': layerName, 'driver': driverName, 'ds': dataSourceName})

            try:
                dataSource.DeleteLayer(i)
            except Exception as e:
                Logger.RaiseException(RuntimeError(_('Failed to delete layer "%(layer)s" from OGR %(driver)s data source "%(ds)s". OGR reported %(e)s: %(msg)s') % {'layer': layerName, 'driver': driverName, 'ds': dataSourceName, 'e': e.__class__.__name__, 'msg': e}))
        
        # Close the data source.
        
        finally:
            try:
                if driverName is not None:
                    cls._LogDebug(_('%(class)s: Closing OGR %(driver)s data source "%(ds)".'), {'class': className, 'driver': driverName, 'ds': dataSourceName})
                else:
                    cls._LogDebug(_('%(class)s: Closing OGR data source "%(ds)".'), {'class': className, 'ds': dataSourceName})
            except:
                pass
            dataSource = None

    # Public properties and instance methods

    def _GetLayerName(self):
        return self._LayerName

    LayerName = property(_GetLayerName, doc=DynamicDocString())

    def _GetDataSourceName(self):
        return self._DataSourceName

    DataSourceName = property(_GetDataSourceName, doc=DynamicDocString())

    def _GetDriverName(self):
        return self._DriverName

    DriverName = property(_GetDriverName, doc=DynamicDocString())

    def _GetIsUpdatable(self):
        return self._IsUpdatable

    IsUpdatable = property(_GetIsUpdatable, doc=DynamicDocString())

    # Overridden private base class methods

    @classmethod
    def _TestCapability(cls, capability):
        if capability == 'setspatialreference':
            if isinstance(cls, OGRTabularLayer):
                return RuntimeError(_('Cannot set the spatial reference of %(dn)s because OGR does not provide a method for setting spatial references.') % {'dn': cls.DisplayName})
            return RuntimeError(_('Cannot set spatial references because OGR does not provide a method setting spatial references.'))
            
        if capability == 'addfield':
            if isinstance(cls, OGRTabularLayer):
                if not cls.IsUpdatable:
                    return RuntimeError(_('Cannot add a field to %(dn)s because the data source was not opened in update mode.') % {'dn': cls.DisplayName})
                if not cls._CanAddField:
                    return RuntimeError(_('Cannot add a field to %(dn)s because OGR does not allow it. Most likely, the OGR %(driver)s driver does not support creation of fields.') % {'dn': cls.DisplayName, 'driver': cls.DriverName})
            return None

        if capability == 'deletefield':
            if isinstance(cls, OGRTabularLayer):
                return RuntimeError(_('Cannot delete a field from %(dn)s because OGR does not provide a method for deleting fields.') % {'dn': cls.DisplayName})
            return RuntimeError(_('Cannot delete fields from OGR layers because OGR does not provide a method for deleting fields.'))

        if capability in ['int32 datatype', 'float64 datatype', 'string datatype']:
            return None

        if capability == 'date datatype':
            if isinstance(cls, OGRTabularLayer) and cls.DriverName.lower() == 'pgeo':
                return TypeError(_('Cannot create a field of data type "date" in %(dn)s because that data type is not supported by the ESRI Personal Geodatabase format. Try the "datetime" data type instead.') % {'dn': cls.DisplayName})
            return None

        if capability == 'datetime datatype':
            if isinstance(cls, OGRTabularLayer) and cls.DriverName.lower() == 'esri shapefile':
                return TypeError(_('Cannot create a field of data type "datetime" in %(dn)s because that data type is not supported by shapefiles. Shapefiles can only store dates, not dates with times. Try the "date" data type instead.') % {'dn': cls.DisplayName})
            return None

        if capability == 'binary datatype':
            if isinstance(cls, OGRTabularLayer) and cls.DriverName.lower() == 'esri shapefile':
                return TypeError(_('Cannot create a field of data type "binary" in %(dn)s because that data type is not supported by shapefiles.') % {'dn': cls.DisplayName})
            return None

        if capability.endswith(' datatype'):
            if isinstance(cls, OGRTabularLayer):
                return TypeError(_('Cannot create a field of data type "%(dt)s" in %(dn)s because that data type is not supported.') % {'dt': capability.split()[0], 'dn': cls.DisplayName})
            else:
                return TypeError(_('Cannot create a field of data type "%(dt)s" because that data type is not supported by OGR.') % {'dt': capability.split()[0]})

        if capability.endswith(' isnullable'):
            if isinstance(cls, OGRTabularLayer) and cls.DriverName.lower() == 'esri shapefile' and not capability.startswith('date '):
                return TypeError(_('Cannot create a nullable field in %(dn)s because shapefiles do not support null values, except in date fields.') % {'dn': cls.DisplayName})
            return None

        if isinstance(cls, OGRTabularLayer):
            return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__class__.__name__, 'cap': capability})
        return RuntimeError(_('The %(cls)s class does not support the "%(cap)s" capability.') % {'cls': cls.__name__, 'cap': capability})

    def _AddField(self, name, dataType, length, precision, isNullable):
        if dataType == 'int32':
            dataType = self._ogr().OFTInteger
        elif dataType == 'float64':
            dataType = self._ogr().OFTReal
        elif dataType == 'string':
            dataType = self._ogr().OFTString
        elif dataType == 'date':
            dataType = self._ogr().OFTDate
        elif dataType == 'datetime':
            dataType = self._ogr().OFTDateTime
        elif dataType == 'binary':
            dataType = self._ogr().OFTBinary
        else:
            Logger.RaiseException(NotImplementedError(_('The _AddField method of class %(cls)s does not support the %(dt)s data type.') % {'cls': self.__class__.__name__, 'dt': dataType}))

        if cls.DriverName.lower() == 'esri shapefile' and length(name) > 10:
            Logger.RaiseException(ValueError(_('Cannot add a field named %(name)s to %(dn)s because the field name is too long. Shapefile fields must be no longer than 10 characters.') % {'name': name, 'dn': self.DisplayName}))

        fd = self._ogr().FieldDefn(name, dataType)
        if length is not None:
            fd.SetWidth(length)
        if precision is not None:
            fd.SetPrecision(precision)

        self._GetLayerByName().CreateField(fd)

    def _GetRowCount(self):
        return self._GetLayerByName().GetFeatureCount(True)

    # Other private properties and methods

    def __init__(self, dataSourceName, layerName, update=False, driverName=None):
        self.__doc__.Obj.ValidateMethodInvocation()

        # Open the data source.

        self._DisplayName = None
        self._DataSource = self._OpenDataSource(dataSourceName, layerName, update, driverName)
        try:

            # Get the layer and initialize the base class from it.

            self._LayerName = layerName
            self._DataSourceName = dataSourceName
            if driverName is not None:
                self._DriverName = driverName
            else:
                self._DriverName = self._DataSource.GetDriver().GetName()
            self._IsUpdatable = update

            if self._IsUpdatable:
                self._DisplayName = _('OGR layer "%(layer)s" of updatable %(driver)s data source "%(ds)s"') % {'layer': self._LayerName, 'driver': self._DriverName, 'ds': self._DataSourceName}
            else:
                self._DisplayName = _('OGR layer "%(layer)s" of %(driver)s data source "%(ds)s"') % {'layer': self._LayerName, 'driver': self._DriverName, 'ds': self._DataSourceName}
            self._LogDebug(_('%(class)s 0x%(id)016X: Opening %(dn)s.'), {'class': self.__class__.__name__, 'id': id(self), 'dn': self._DisplayName})

            layer = self._GetLayerByName()

            self._CanAddField = self._IsUpdatable and layer.TestCapability(self._ogr().OLCCreateField)

            oidFieldName = layer.GetFIDColumn()
            if not isinstance(oidFieldName, str) or len(oidFieldName) <= 0:
                oidFieldName = None

            featDefn = layer.GetLayerDefn()
            geometryType = featDefn.GetGeomType()
            if geometryType in Dataset._GeometryTypeForOGRGeometry:
                geometryType = Dataset._GeometryTypeForOGRGeometry[geometryType]
            else:
                self._LogWarning(_('OGR reports that layer "%(layer)s" of OGR %(driver)s data source "%(ds)s" has geometry type %(gt)i, which is not currently supported. Geometry will not be available for this layer.'), {'layer': self._LayerName, 'driver': self._DriverName, 'ds': self._DataSourceName, 'gt': geometryType})
                geometryType = None

            if self._DriverName.lower() == 'esri shapefile':
                if geometryType == 'LineString':
                    geometryType = 'MultiLineString'
                elif geometryType == 'Polygon':
                    geometryType = 'MultiPolygon'
                elif geometryType == 'LineString25D':
                    geometryType = 'MultiLineString25D'
                elif geometryType == 'Polygon25D':
                    geometryType = 'MultiPolygon25D'

            geometryFieldName = layer.GetGeometryColumn()
            if not isinstance(geometryFieldName, str) or len(geometryFieldName) <= 0:
                geometryFieldName = None

            if geometryType is not None:
                srType = 'obj'
                sr = layer.GetSpatialRef()
            else:
                srType = None
                sr = None

            if self._DriverName.lower() == 'esri shapefile':
                maxStringLength = 254
            else:
                maxStringLength = None

            fields = []
            for i in range(featDefn.GetFieldCount()):
                f = featDefn.GetFieldDefn(i)
                name = f.GetName()
                if name == oidFieldName:
                    dataType = 'oid'
                elif name == geometryFieldName:
                    dataType = 'geometry'
                else:
                    dataType = f.GetType()
                    if dataType == self._ogr().OFTInteger:
                        dataType = 'int32'
                    elif dataType == self._ogr().OFTReal:
                        dataType = 'float64'
                    elif dataType in [self._ogr().OFTString, self._ogr().OFTWideString]:
                        dataType = 'string'
                    elif dataType == self._ogr().OFTBinary:
                        dataType = 'binary'
                    elif dataType == self._ogr().OFTDate:
                        dataType = 'date'
                    elif dataType == self._ogr().OFTDateTime:
                        dataType = 'datetime'
                    else:
                        dataType = 'unknown'
                length = f.GetWidth()
                precision = f.GetPrecision()
                isNullable = self._DriverName.lower() != 'esri shapefile'       # OGR is not aware of nullability and assumes all fields are nullable. See http://lists.osgeo.org/pipermail/gdal-dev/2010-February/023583.html. We override this for shapefiles and conform to ESRI's spec (no shapefile fields are nullable).
                isSettable = dataType != 'oid'
                fields.append(Field(name, dataType, length, precision, isNullable, isSettable))

            super(ArcGISTable, self).__init__(parentCollection=parentCollection, queryableAttributeValues=queryableAttributeValues, lazyPropertyValues=lazyPropertyValues)

            super(OGRTabularLayer, self).__init__(hasOID=True,
                                                  oidFieldName=oidFieldName,
                                                  geometryType=geometryType,
                                                  geometryFieldName=geometryFieldName,
                                                  maxStringLength=maxStringLength,
                                                  fields=fields,
                                                  srType=srType,
                                                  sr=sr)

        # If we got an exception, release the data source. Otherwise we keep
        # it until we are destructed.
        
        except:
            if self._DataSource is not None:
                try:
                    self._LogDebug(_('%(class)s 0x%(id)016X: Closing OGR %(driver)s data source "%(ds)".'), {'class': self.__class__.__name__, 'id': id(self), 'driver': self._DriverName, 'ds': self._DataSourceName})
                except:
                    pass
                self._DataSource = None
            raise

    def _Close(self):

        # If we have a data source, release it.

        if hasattr(self, '_DataSource') and self._DataSource is not None:
            try:
                self._LogDebug(_('%(class)s 0x%(id)016X: Closing OGR %(driver)s data source "%(ds)".'), {'class': self.__class__.__name__, 'id': id(self), 'driver': self._DriverName, 'ds': self._DataSourceName})
            except:
                pass
            self._DataSource = None

        super(OGRTabularLayer, self)._Close()

    def _GetDisplayNameProperty(self):
        return self._DisplayName

    @classmethod
    def _OpenDataSource(cls, dataSourceName, layerName, update, driverName):
        if driverName is not None:
            if isinstance(cls, OGRTabularLayer):
                cls._LogDebug(_('%(class)s 0x%(id)016X: Opening OGR %(driver)s data source "%(ds)" with update=%(upd)s.'), {'class': cls.__class__.__name__, 'id': id(cls), 'driver': driverName, 'ds': dataSourceName, 'upd': update})
            else:
                cls._LogDebug(_('%(class)s: Opening OGR %(driver)s data source "%(ds)" with update=%(upd)s.'), {'class': cls.__name__, 'driver': driverName, 'ds': dataSourceName, 'upd': update})
            try:
                dataSource = cls._ogr().GetDriverByName(str(driverName)).Open(dataSourceName, update)
            except Exception as e:
                if update:
                    Logger.RaiseException(RuntimeError(_('Failed to open "%(ds)s" as an updatable OGR %(driver)s data source. OGR reported %(e)s: %(msg)s') % {'ds': dataSourceName, 'driver': driverName, 'e': e.__class__.__name__, 'msg': e}))
                Logger.RaiseException(RuntimeError(_('Failed to open "%(ds)s" as an OGR %(driver)s data source. OGR reported %(e)s: %(msg)s') % {'ds': dataSourceName, 'driver': driverName, 'e': e.__class__.__name__, 'msg': e}))
        else:
            if isinstance(cls, OGRTabularLayer):
                cls._LogDebug(_('%(class)s 0x%(id)016X: Opening OGR data source "%(ds)" with update=%(upd)s; OGR will select the driver.'), {'class': cls.__class__.__name__, 'id': id(cls), 'ds': dataSourceName, 'upd': update})
            else:
                cls._LogDebug(_('%(class)s: Opening OGR data source "%(ds)" with update=%(upd)s; OGR will select the driver.'), {'class': cls.__class__.__name__, 'ds': dataSourceName, 'upd': update})
            try:
                dataSource = cls._ogr().Open(dataSourceName, update)
            except Exception as e:
                if update:
                    Logger.RaiseException(RuntimeError(_('Failed to open "%(ds)s" as an updatable OGR data source. OGR reported %(e)s: %(msg)s') % {'ds': dataSourceName, 'e': e.__class__.__name__, 'msg': e}))
                Logger.RaiseException(RuntimeError(_('Failed to open "%(ds)s" as an OGR data source. OGR reported %(e)s: %(msg)s') % {'ds': dataSourceName, 'e': e.__class__.__name__, 'msg': e}))
        return dataSource

    def _GetLayerByName(self):
        try:
            layer = self._DataSource.GetLayerByName(self._LayerName)
        except Exception as e:
            if self._IsUpdatable:
                Logger.RaiseException(RuntimeError(_('Failed to open "%(layer)s" as an OGR layer of updatable %(driver)s data source "%(ds)s". OGR reported %(e)s: %(msg)s') % {'layer': self._LayerName, 'driver': self._DriverName, 'ds': self._DataSourceName, 'e': e.__class__.__name__, 'msg': e}))
            Logger.RaiseException(RuntimeError(_('Failed to open "%(layer)s" as an an OGR layer of %(driver)s data source "%(ds)s". OGR reported %(e)s: %(msg)s') % {'layer': self._LayerName, 'driver': self._DriverName, 'ds': self._DataSourceName, 'e': e.__class__.__name__, 'msg': e}))
        if layer is None:
            Logger.RaiseException(ValueError(_('Failed to open "%(layer)s" as an an OGR layer of %(driver)s data source "%(ds)s". OGR\'s Dataset.GetLayerByName() function returned NULL, which usually indicates that the layer does not exist.') % {'layer': self._LayerName, 'driver': self._DriverName, 'ds': self._DataSourceName}))
        return layer


########################################################################################
# This module is not meant to be imported directly. Import GeoEco.Datasets.GDAL instead.
########################################################################################

__all__ = []
