# Files_test.py - pytest tests for GeoEco.DataManagement.Files.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime
import os
import pytest

from GeoEco.DataManagement.Fields import Field
from GeoEco.DataManagement.Files import File
from GeoEco.Datasets.SQLite import SQLiteDatabase


def exampleFilesList():
    files = [['a.txt', 1000, datetime.datetime(2010,1,1,0,0,0)],
             ['b.txt', 1000, datetime.datetime(2010,1,1,1,0,0)],
             ['c.txt', 10000, datetime.datetime(2010,2,1)],
             ['sub_x' + os.path.sep + 'd.txt', 1000, datetime.datetime(2011,1,1)],
             ['sub_x' + os.path.sep + 'e.txt', 1000, datetime.datetime(2012,1,1)],
             ['sub_y' + os.path.sep + 'f.txt', 1000, datetime.datetime(2013,2,11)],
             ['sub_y' + os.path.sep + 'g.dat', 10000, datetime.datetime(2014,2,12)],
             ['sub_z' + os.path.sep + 'h.txt', 1000, datetime.datetime(2015,11,22)],
             ['sub_z' + os.path.sep + 'i.dat', 10000, datetime.datetime(2016,11,23)],
            ]
    return files


@pytest.fixture
def exampleFilesPath(tmp_path):
    files = [[tmp_path / p, size, modTime] for [p, size, modTime] in exampleFilesList()]

    for p, size, modTime in files:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open(mode='wb') as f:
            f.truncate(size)
        epoch = modTime.timestamp()
        os.utime(str(p), (epoch, epoch))

    return tmp_path


def exampleFilesWithDatesList():
    files = [['sst_20100102_123456.txt', datetime.datetime(2010, 1, 2, 12, 34, 56)],
             ['sst_20100304_123456.txt', datetime.datetime(2010, 3, 4, 12, 34, 56)],
             ['sst_20100506_123456.txt', datetime.datetime(2010, 5, 6, 12, 34, 56)],
             ['sst_20100708_123456.txt', datetime.datetime(2010, 7, 8, 12, 34, 56)],
             ['sst_20100910_123456.txt', datetime.datetime(2010, 9, 10, 12, 34, 56)],
             ['sst_20101112_123456.txt', datetime.datetime(2010, 11, 12, 12, 34, 56)]]
    return files


@pytest.fixture
def exampleFilesWithDatesPath(tmp_path):
    files = [tmp_path / p[0] for p in exampleFilesWithDatesList()]

    for p in files:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open(mode='wb') as f:
            f.truncate(1000)

    return tmp_path


class TestFiles():

    def test_Delete(self, exampleFilesPath):
        p = exampleFilesPath / 'a.txt'

        assert p.is_file()
        File.Delete(str(p))
        assert not p.is_file()

        File.Delete(str(p))     # Doesn't fail if file doesn't exist


    def test_DeleteList(self, exampleFilesPath):
        pList = [exampleFilesPath / 'a.txt', 
                 exampleFilesPath / 'b.txt', 
                 exampleFilesPath / 'c.txt']

        assert all([p.is_file() for p in pList])
        File.DeleteList([str(p) for p in pList])
        assert not any([p.is_file() for p in pList])

        File.DeleteList([str(p) for p in pList])    # Doesn't fail if files don't exist


    def test_DeleteTable(self, exampleFilesPath):
        pList = [exampleFilesPath / 'a.txt', 
                 exampleFilesPath / 'b.txt', 
                 exampleFilesPath / 'c.txt']

        db = SQLiteDatabase(':memory:')
        table = db.CreateTable('TempTable1')
        table.AddField('File', 'string')
        with table.OpenInsertCursor() as cursor:
            for p in pList:
                cursor.SetValue('File', str(p))
                cursor.InsertRow()

        assert all([p.is_file() for p in pList])
        File.DeleteTable(table, 'File', where="File <> '%s'" % str(pList[0]).replace('\\','\\\\'))
        assert pList[0].is_file()
        assert not any([p.is_file() for p in pList[1:]])

        File.DeleteTable(table, 'File')
        assert not any([p.is_file() for p in pList])

        File.DeleteTable(table, 'File')     # Doesn't fail if files don't exist


    def test_FindAndCreateTable(self, exampleFilesPath):
        db = SQLiteDatabase(':memory:')

        # Without recursion; root level has just .txt files

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table1', fileField='File')
        assert len(list(exampleFilesPath.glob('*.txt'))) > 0
        assert db.QueryDatasets("TableName = 'Table1'", reportProgress=False)[0].GetRowCount() == len(list(exampleFilesPath.glob('*.txt')))

        # With recursion, just .txt files

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table2', fileField='File', wildcard='*.txt', searchTree=True)
        assert len(list(exampleFilesPath.glob('**/*.txt'))) > 0
        assert db.QueryDatasets("TableName = 'Table2'", reportProgress=False)[0].GetRowCount() == len(list(exampleFilesPath.glob('**/*.txt')))

        # minSize and maxSize

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table3', fileField='File', searchTree=True, maxSize=1000)
        assert db.QueryDatasets("TableName = 'Table3'", reportProgress=False)[0].GetRowCount() == 6

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table4', fileField='File', searchTree=True, minSize=10000)
        assert db.QueryDatasets("TableName = 'Table4'", reportProgress=False)[0].GetRowCount() == 3

        # minDateModified and maxDateModified

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table5', fileField='File', searchTree=True, minDateModified=datetime.datetime(2011,1,1))
        assert db.QueryDatasets("TableName = 'Table5'", reportProgress=False)[0].GetRowCount() == 6

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table6', fileField='File', searchTree=True, minDateModified=datetime.datetime(2010,1,1,0,0,1))
        assert db.QueryDatasets("TableName = 'Table6'", reportProgress=False)[0].GetRowCount() == 8

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table7', fileField='File', searchTree=True, maxDateModified=datetime.datetime(2013,1,1))
        assert db.QueryDatasets("TableName = 'Table7'", reportProgress=False)[0].GetRowCount() == 5

        # Fields being populated correctly, excluding relativePathField

        files = [[exampleFilesPath / p, size, modTime] for [p, size, modTime] in exampleFilesList()]

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table8', fileField='File', searchTree=True, sizeField='Size', dateCreatedField='DateCreated', dateModifiedField='DateModified')
        table = db.QueryDatasets("TableName = 'Table8'", reportProgress=False)[0]
        results = table.Query(orderBy='File ASC')

        assert all([results['File'][i] == str(files[i][0]) for i in range(len(files))])
        assert all([results['Size'][i] == files[i][1] for i in range(len(files))])
        assert all([results['DateModified'][i] == files[i][2] for i in range(len(files))])

        # Relative path being populated correctly

        relativePaths = [str(p) for [p, size, modTime] in exampleFilesList()]

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table9', fileField='File', searchTree=True, relativePathField='RelativePath', basePath=str(exampleFilesPath))
        table = db.QueryDatasets("TableName = 'Table9'", reportProgress=False)[0]
        results = table.Query(orderBy='File ASC')

        assert all([results['RelativePath'][i] == str(relativePaths[i]) for i in range(len(relativePaths))])


    def test_FindAndCreateTable_ParseDates(self, exampleFilesWithDatesPath):
        db = SQLiteDatabase(':memory:')

        File.FindAndCreateTable(directory=str(exampleFilesWithDatesPath), database=db, table='Table5', fileField='File', parsedDateField='ParsedDate', dateParsingExpression='%Y%m%d_%H%M%S')
        table = db.QueryDatasets("TableName = 'Table5'", reportProgress=False)[0]
        results = table.Query(orderBy='File ASC')
        expectedDates = [expectedDate for [p, expectedDate] in exampleFilesWithDatesList()]

        assert all([results['ParsedDate'][i] == expectedDates[i] for i in range(len(expectedDates))])


    def test_DeleteTable(self, exampleFilesPath):
        db = SQLiteDatabase(':memory:')

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table2', fileField='File', searchTree=True, sizeField='Size')
        table = db.QueryDatasets("TableName = 'Table2'", reportProgress=False)[0]
        assert table.GetRowCount() == len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat')))

        File.DeleteTable(table, 'File', where='Size > 1000')
        assert len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat'))) == len([efl for efl in exampleFilesList() if efl[1] <= 1000])

        File.DeleteTable(table, 'File')
        assert len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat'))) == 0


    def test_FindAndDelete(self, exampleFilesPath):
        File.FindAndDelete(str(exampleFilesPath), searchTree=True, minSize=1001)
        assert len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat'))) == len([efl for efl in exampleFilesList() if efl[1] <= 1000])

        File.FindAndDelete(str(exampleFilesPath), searchTree=True)
        assert len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat'))) == 0


    def test_CopyTable(self, exampleFilesPath, tmp_path_factory):
        db = SQLiteDatabase(':memory:')

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table2', fileField='SourceFile', searchTree=True, sizeField='Size', relativePathField='SourceFileRelativePath', basePath=str(exampleFilesPath))
        table = db.QueryDatasets("TableName = 'Table2'", reportProgress=False)[0]
        assert table.GetRowCount() == len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat')))

        table.AddField('DestFile', 'string')
        destDir = tmp_path_factory.mktemp('test_CopyTable__dest')
        Field.CalculateField(table, 'DestFile', "os.path.join(r'%s', row.SourceFileRelativePath)" % destDir, modulesToImport=['os'])

        File.CopyTable(table, sourceFileField='SourceFile', destinationFileField='DestFile', where='Size > 1000')
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == 3
        destFiles = [destDir / p for [p, size, modTime] in exampleFilesList() if size > 1000]
        assert all([f.is_file() for f in destFiles])

        with pytest.raises(ValueError, match='.*already exists.*'):
            File.CopyTable(table, sourceFileField='SourceFile', destinationFileField='DestFile')

        File.CopyTable(table, sourceFileField='SourceFile', destinationFileField='DestFile', skipExisting=True)
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == len(exampleFilesList())


    def test_FindAndCopy(self, exampleFilesPath, tmp_path_factory):
        destDir = tmp_path_factory.mktemp('test_FindAndCopy__dest')

        File.FindAndCopy(str(exampleFilesPath), str(destDir), searchTree=True, maxSize=1000)
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == 6
        destFiles = [destDir / p for [p, size, modTime] in exampleFilesList() if size <= 1000]
        assert all([f.is_file() for f in destFiles])

        with pytest.raises(ValueError, match='.*already exists.*'):
            File.FindAndCopy(str(exampleFilesPath), str(destDir), searchTree=True)

        File.FindAndCopy(str(exampleFilesPath), str(destDir), searchTree=True, skipExisting=True)
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == 9

        File.FindAndDelete(str(destDir), wildcard="*.dat", searchTree=True)
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == 7
        File.FindAndCopy(str(exampleFilesPath), str(destDir), searchTree=True, overwriteExisting=True)
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == 9


    def test_MoveTable(self, exampleFilesPath, tmp_path_factory):
        db = SQLiteDatabase(':memory:')

        File.FindAndCreateTable(directory=str(exampleFilesPath), database=db, table='Table2', fileField='SourceFile', searchTree=True, sizeField='Size', relativePathField='SourceFileRelativePath', basePath=str(exampleFilesPath))
        table = db.QueryDatasets("TableName = 'Table2'", reportProgress=False)[0]
        assert table.GetRowCount() == len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat')))

        table.AddField('DestFile', 'string')
        destDir = tmp_path_factory.mktemp('test_MoveTable__dest')
        Field.CalculateField(table, 'DestFile', "os.path.join(r'%s', row.SourceFileRelativePath)" % destDir, modulesToImport=['os'])

        File.MoveTable(table, sourceFileField='SourceFile', destinationFileField='DestFile', where='Size > 1000')
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == 3
        destFiles = [destDir / p for [p, size, modTime] in exampleFilesList() if size > 1000]
        assert all([f.is_file() for f in destFiles])
        assert len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat'))) == 6

        File.MoveTable(table, sourceFileField='SourceFile', destinationFileField='DestFile', where='Size <= 1000')
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == len(exampleFilesList())
        assert len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat'))) == 0

        File.CopyTable(table, sourceFileField='DestFile', destinationFileField='SourceFile')

        with pytest.raises(ValueError, match='.*already exists.*'):
            File.MoveTable(table, sourceFileField='SourceFile', destinationFileField='DestFile')

        File.MoveTable(table, sourceFileField='SourceFile', destinationFileField='DestFile', skipExisting=True)
        File.MoveTable(table, sourceFileField='SourceFile', destinationFileField='DestFile', overwriteExisting=True)


    def test_FindAndMove(self, exampleFilesPath, tmp_path_factory):
        destDir = tmp_path_factory.mktemp('test_FindAndMove__dest')

        File.FindAndMove(str(exampleFilesPath), str(destDir), searchTree=True, maxSize=1000)
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == 6
        destFiles = [destDir / p for [p, size, modTime] in exampleFilesList() if size <= 1000]
        assert all([f.is_file() for f in destFiles])
        assert len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat'))) == 3

        File.FindAndMove(str(exampleFilesPath), str(destDir), searchTree=True, skipExisting=True)
        assert len(list(destDir.glob('**/*.txt')) + list(destDir.glob('**/*.dat'))) == 9
        assert len(list(exampleFilesPath.glob('**/*.txt')) + list(exampleFilesPath.glob('**/*.dat'))) == 0
