# SQLite_test.py - pytest tests for GeoEco.Datasets.SQLite.
#
# Copyright (C) 2026 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

import datetime

import pytest

from GeoEco.Datasets.SQLite import SQLiteDatabase


class TestSQLite():

    @staticmethod
    def _CreateExampleTable():

        # Use detect_types=0 so these tests exercise MGET's own handling of
        # date/time fields rather than relying on sqlite3's built-in type
        # conversion behavior.

        db = SQLiteDatabase(':memory:', detect_types=0)
        table = db.CreateTable('TempTable1')

        table.AddField('FloatField', 'float64')
        table.AddField('IntField', 'int32')
        table.AddField('StrField', 'string', isNullable=True)
        table.AddField('DateTimeField', 'datetime')

        return db, table

    @staticmethod
    def _InsertExampleRows(table):
        rows = [
            (1.1, 1, 'abc', datetime.datetime(2000, 1, 2, 3, 4, 5)),
            (2.2, 2, 'def', datetime.datetime(2000, 6, 7, 8, 9, 10)),
            (3.3, 3, None, datetime.datetime(2000, 11, 12, 13, 14, 15)),
        ]

        with table.OpenInsertCursor(reportProgress=False) as cursor:
            for float_value, int_value, str_value, dt_value in rows:
                cursor.SetValue('FloatField', float_value)
                cursor.SetValue('IntField', int_value)
                cursor.SetValue('StrField', str_value)
                cursor.SetValue('DateTimeField', dt_value)
                cursor.InsertRow()

        return rows

    def test_CreateTable_AddField(self):

        db, table = self._CreateExampleTable()
        try:
            assert db.TableExists('TempTable1')
            assert table.TableName == 'TempTable1'
            assert table.HasOID
            assert table.OIDFieldName == 'ObjectID'

            assert [field.Name for field in table.Fields] == ['ObjectID', 'FloatField', 'IntField', 'StrField', 'DateTimeField']
            assert [field.DataType for field in table.Fields] == ['oid', 'float64', 'int32', 'string', 'datetime']
            assert [field.IsNullable for field in table.Fields] == [False, False, False, True, False]
        finally:
            db.Close()

    def test_OpenSelectCursor(self):

        db, table = self._CreateExampleTable()
        try:
            expected_rows = self._InsertExampleRows(table)

            rows = []
            with table.OpenSelectCursor(reportProgress=False) as cursor:
                while cursor.NextRow():
                    rows.append((
                        cursor.GetOID(),
                        cursor.GetValue('FloatField'),
                        cursor.GetValue('IntField'),
                        cursor.GetValue('StrField'),
                        cursor.GetValue('DateTimeField'),
                    ))

            assert rows == [
                (1, expected_rows[0][0], expected_rows[0][1], expected_rows[0][2], expected_rows[0][3]),
                (2, expected_rows[1][0], expected_rows[1][1], expected_rows[1][2], expected_rows[1][3]),
                (3, expected_rows[2][0], expected_rows[2][1], expected_rows[2][2], expected_rows[2][3]),
            ]
            assert all(isinstance(row[4], datetime.datetime) for row in rows)
        finally:
            db.Close()

    def test_Query(self):

        db, table = self._CreateExampleTable()
        try:
            expected_rows = self._InsertExampleRows(table)

            result = table.Query(reportProgress=False)

            assert list(result.keys()) == ['ObjectID', 'FloatField', 'IntField', 'StrField', 'DateTimeField']
            assert result['ObjectID'] == [1, 2, 3]
            assert result['FloatField'] == [row[0] for row in expected_rows]
            assert result['IntField'] == [row[1] for row in expected_rows]
            assert result['StrField'] == [row[2] for row in expected_rows]
            assert result['DateTimeField'] == [row[3] for row in expected_rows]
            assert all(isinstance(value, datetime.datetime) for value in result['DateTimeField'])
        finally:
            db.Close()

    def test_Query_ToPandasDataFrame(self):

        pandas = pytest.importorskip('pandas')

        db, table = self._CreateExampleTable()
        try:
            expected_rows = self._InsertExampleRows(table)

            df = pandas.DataFrame(table.Query(reportProgress=False))

            assert list(df.columns) == ['ObjectID', 'FloatField', 'IntField', 'StrField', 'DateTimeField']
            assert df['ObjectID'].tolist() == [1, 2, 3]
            assert df['FloatField'].tolist() == [row[0] for row in expected_rows]
            assert df['IntField'].tolist() == [row[1] for row in expected_rows]

            # Pandas 3.x has a native string type, which uses nan to represent
            # a missing value rather than None. So df['StrField'].iloc[2] will
            # be None on pandas 2.x and nan on 3.x. We therefore can't use the
            # == operator to check for equality on 3.x. Use pandas.isna()
            # instead.

            assert df['StrField'].iloc[0] == expected_rows[0][2]
            assert df['StrField'].iloc[1] == expected_rows[1][2]
            assert pandas.isna(df['StrField'].iloc[2])

            assert df['DateTimeField'].tolist() == [row[3] for row in expected_rows]
        finally:
            db.Close()

    def test_OpenUpdateCursor(self):

        db, table = self._CreateExampleTable()
        try:
            self._InsertExampleRows(table)

            with table.OpenUpdateCursor(where='ObjectID >= 2', reportProgress=False) as cursor:
                assert cursor.NextRow()
                assert cursor.GetOID() == 2
                cursor.DeleteRow()

                assert cursor.NextRow()
                assert cursor.GetOID() == 3
                cursor.SetValue('FloatField', 3.333)
                cursor.SetValue('StrField', 'ghi')
                cursor.UpdateRow()

                assert not cursor.NextRow()

            result = table.Query(reportProgress=False)

            assert result['ObjectID'] == [1, 3]
            assert result['FloatField'] == [1.1, 3.333]
            assert result['IntField'] == [1, 3]
            assert result['StrField'] == ['abc', 'ghi']
            assert result['DateTimeField'] == [
                datetime.datetime(2000, 1, 2, 3, 4, 5),
                datetime.datetime(2000, 11, 12, 13, 14, 15),
            ]
        finally:
            db.Close()

    def test_InsertRow_DefaultValues(self):

        # Exercise the SQLite-specific DEFAULT VALUES path by inserting into a
        # table that has no settable fields beyond the auto-generated OID.

        db = SQLiteDatabase(':memory:', detect_types=0)
        table = db.CreateTable('TempTable1')

        with table.OpenInsertCursor(reportProgress=False) as cursor:
            cursor.InsertRow()

        assert table.GetRowCount() == 1

        rows = table.Query(reportProgress=False)
        assert list(rows.keys()) == ['ObjectID']
        assert rows['ObjectID'] == [1]

    def test_DateAndDateTime_RoundTrip(self):

        db = SQLiteDatabase(':memory:', detect_types=0)
        table = db.CreateTable('TempTable1')
        table.AddField('DateField', 'date', isNullable=True)
        table.AddField('DateTimeField', 'datetime', isNullable=True)

        try:
            with table.OpenInsertCursor(reportProgress=False) as cursor:
                cursor.SetValue('DateField', datetime.date(2001, 2, 3))
                cursor.SetValue('DateTimeField', datetime.datetime(2001, 2, 3, 4, 5, 6))
                cursor.InsertRow()

                cursor.SetValue('DateField', None)
                cursor.SetValue('DateTimeField', None)
                cursor.InsertRow()

            with table.OpenUpdateCursor(where='ObjectID = 2', reportProgress=False) as cursor:
                assert cursor.NextRow()
                cursor.SetValue('DateField', datetime.datetime(2004, 5, 6, 7, 8, 9))
                cursor.SetValue('DateTimeField', datetime.date(2004, 5, 7))
                cursor.UpdateRow()
                assert not cursor.NextRow()

            rows = []
            with table.OpenSelectCursor(orderBy='ObjectID', reportProgress=False) as cursor:
                while cursor.NextRow():
                    rows.append((
                        cursor.GetOID(),
                        cursor.GetValue('DateField'),
                        cursor.GetValue('DateTimeField'),
                    ))

            assert rows == [
                (1, datetime.datetime(2001, 2, 3, 0, 0, 0), datetime.datetime(2001, 2, 3, 4, 5, 6)),
                (2, datetime.datetime(2004, 5, 6, 0, 0, 0), datetime.datetime(2004, 5, 7, 0, 0, 0)),
            ]
            assert all(isinstance(row[1], datetime.datetime) for row in rows)
            assert all(isinstance(row[2], datetime.datetime) for row in rows)

            result = table.Query(reportProgress=False, orderBy='ObjectID')
            assert result['DateField'] == [
                datetime.datetime(2001, 2, 3, 0, 0, 0),
                datetime.datetime(2004, 5, 6, 0, 0, 0),
            ]
            assert result['DateTimeField'] == [
                datetime.datetime(2001, 2, 3, 4, 5, 6),
                datetime.datetime(2004, 5, 7, 0, 0, 0),
            ]
        finally:
            db.Close()

    def test_AddNonNullableField_AfterRowsExist(self):

        db = SQLiteDatabase(':memory:', detect_types=0)
        table = db.CreateTable('TempTable1')
        table.AddField('IntField', 'int32')

        try:
            with table.OpenInsertCursor(reportProgress=False) as cursor:
                cursor.SetValue('IntField', 1)
                cursor.InsertRow()
                cursor.SetValue('IntField', 2)
                cursor.InsertRow()

            assert [field.Name for field in table.Fields] == ['ObjectID', 'IntField']
            assert table.GetFieldByName('AddedIntField') is None

            table.AddField('AddedIntField', 'int32', isNullable=False)

            assert [field.Name for field in table.Fields] == ['ObjectID', 'IntField', 'AddedIntField']
            assert table.GetFieldByName('AddedIntField') is not None
            assert table.GetFieldByName('AddedIntField').DataType == 'int32'
            assert table.GetFieldByName('AddedIntField').IsNullable is False

            result = table.Query(reportProgress=False, orderBy='ObjectID')
            assert result['ObjectID'] == [1, 2]
            assert result['IntField'] == [1, 2]
            assert result['AddedIntField'] == [0, 0]

            with table.OpenInsertCursor(reportProgress=False) as cursor:
                cursor.SetValue('IntField', 3)
                cursor.SetValue('AddedIntField', 4)
                cursor.InsertRow()

            result = table.Query(reportProgress=False, orderBy='ObjectID')
            assert result['ObjectID'] == [1, 2, 3]
            assert result['IntField'] == [1, 2, 3]
            assert result['AddedIntField'] == [0, 0, 4]
        finally:
            db.Close()

    def test_OpenUpdateCursor_RestrictedFields_WithWhereAndOrderBy(self):

        db, table = self._CreateExampleTable()
        try:
            self._InsertExampleRows(table)

            with table.OpenUpdateCursor(fields=['ObjectID', 'StrField'], where='ObjectID >= 2', orderBy='ObjectID DESC', reportProgress=False) as cursor:
                assert cursor.NextRow()
                assert cursor.GetOID() == 3
                assert cursor.GetValue('StrField') is None

                with pytest.raises(RuntimeError, match='.*was not included in the list of requested fields.*'):
                    cursor.GetValue('IntField')

                cursor.SetValue('StrField', 'updated-3')
                cursor.UpdateRow()

                assert cursor.NextRow()
                assert cursor.GetOID() == 2
                assert cursor.GetValue('StrField') == 'def'
                cursor.SetValue('StrField', 'updated-2')
                cursor.UpdateRow()

                assert not cursor.NextRow()

            result = table.Query(fields=['ObjectID', 'StrField'], orderBy='ObjectID', reportProgress=False)
            assert result['ObjectID'] == [1, 2, 3]
            assert result['StrField'] == ['abc', 'updated-2', 'updated-3']
        finally:
            db.Close()

    def test_UnknownSQLiteType_IsIgnored(self):

        db = SQLiteDatabase(':memory:', detect_types=0)
        table = db.CreateTable('TempTable1')
        table.AddField('IntField', 'int32')

        try:
            db.Connection.execute('ALTER TABLE TempTable1 ADD COLUMN MysteryField NUMERIC;')
            db.Connection.execute('INSERT INTO TempTable1 (IntField, MysteryField) VALUES (?, ?);', (1, 123.45))

            table2 = db.QueryDatasets(reportProgress=False)[0]

            assert [field.Name for field in table2.Fields] == ['ObjectID', 'IntField']
            assert table2.GetFieldByName('MysteryField') is None

            result = table2.Query(reportProgress=False)
            assert list(result.keys()) == ['ObjectID', 'IntField']
            assert result['ObjectID'] == [1]
            assert result['IntField'] == [1]
        finally:
            db.Close()

    def test_CreateIndex_DeleteIndex(self):

        db, table = self._CreateExampleTable()
        try:
            self._InsertExampleRows(table)

            table.CreateIndex(['IntField'], 'idx_TempTable1_IntField', unique=True)

            result = db.Connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=?;",
                ('idx_TempTable1_IntField',)
            ).fetchone()[0]
            assert result == 1

            # Verify that the unique index is actually enforced.

            with table.OpenInsertCursor(reportProgress=False) as cursor:
                cursor.SetValue('FloatField', 4.4)
                cursor.SetValue('IntField', 1)   # duplicate of existing row
                cursor.SetValue('StrField', 'duplicate')
                cursor.SetValue('DateTimeField', datetime.datetime(2001, 1, 1, 0, 0, 0))
                with pytest.raises(RuntimeError):
                    cursor.InsertRow()

            # Deleting the index should remove the uniqueness constraint.

            table.DeleteIndex('idx_TempTable1_IntField')

            result = db.Connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=?;",
                ('idx_TempTable1_IntField',)
            ).fetchone()[0]
            assert result == 0

            with table.OpenInsertCursor(reportProgress=False) as cursor:
                cursor.SetValue('FloatField', 4.4)
                cursor.SetValue('IntField', 1)   # duplicate is now allowed
                cursor.SetValue('StrField', 'duplicate')
                cursor.SetValue('DateTimeField', datetime.datetime(2001, 1, 1, 0, 0, 0))
                cursor.InsertRow()

            result = table.Query(orderBy='ObjectID', reportProgress=False)
            assert result['ObjectID'] == [1, 2, 3, 4]
            assert result['IntField'] == [1, 2, 3, 1]

        finally:
            db.Close()

    def test_DeleteTable_TableExists(self):

        db = SQLiteDatabase(':memory:', detect_types=0)
        try:
            assert not db.TableExists('TempTable1')

            db.CreateTable('TempTable1')
            assert db.TableExists('TempTable1')

            db.DeleteTable('TempTable1')
            assert not db.TableExists('TempTable1')

            # Should silently succeed when the table does not exist.
            db.DeleteTable('TempTable1', failIfNotExists=False)
            assert not db.TableExists('TempTable1')

            # Should raise when requested.
            with pytest.raises(RuntimeError):
                db.DeleteTable('TempTable1', failIfNotExists=True)

        finally:
            db.Close()

    def test_QueryDatasets_TableNameQueryableAttribute(self):

        db = SQLiteDatabase(':memory:', detect_types=0)
        try:
            db.CreateTable('TempTable1')
            db.CreateTable('TempTable2')
            db.CreateTable('TempTable3')

            datasets = db.QueryDatasets(reportProgress=False)
            table_names = sorted([dataset.TableName for dataset in datasets])
            assert table_names == ['TempTable1', 'TempTable2', 'TempTable3']

            datasets = db.QueryDatasets("TableName = 'TempTable2'", reportProgress=False)
            assert len(datasets) == 1
            assert datasets[0].TableName == 'TempTable2'
            assert datasets[0].GetQueryableAttributeValue('TableName') == 'TempTable2'

            datasets = db.QueryDatasets("TableName in ('TempTable1', 'TempTable3')", reportProgress=False)
            table_names = sorted([dataset.TableName for dataset in datasets])
            assert table_names == ['TempTable1', 'TempTable3']

        finally:
            db.Close()
