// _MetadataUtils.cpp - Implements C utility functions used by Metadata.py. Not
// intended to be called from any code outside of Metadata.py.
//
// Copyright (C) 2024 Jason J. Roberts
//
// This file is part of Marine Geospatial Ecology Tools (MGET) and is released
// under the terms of the 3-Clause BSD License. See the LICENSE file at the
// root of this project or https://opensource.org/license/bsd-3-clause for the
// full license text.


#include "Python.h"
#include "frameobject.h"

static PyObject *SaveChangesToFrameLocals(PyObject *self, PyObject *args)
{
    // The f_locals attribute of a frame object represents the local variables
    // for that stack frame. It is a dictionary that maps local variable names
    // to their values. The dictionary is writable but when you set a value, it
    // does not affect the "real" values of the local variables; if you examine
    // the value from code running in the frame itself, the value is unchanged.
    // This is because the f_locals dictionary is not the "real" storage
    // location of the locals. It is actually a copy, generated on first access,
    // that is used primarily for reading the values of the variables. It is
    // possible to push the changes to it back to the "real" storage location by
    // calling PyFrame_LocalsToFast. The purpose of SaveChangesToFrameLocals is
    // simply to call that function.
    //
    // For more information, search the Internet for the article titled
    // "frame.f_locals is writable".

    PyFrameObject *pFrame = NULL;

    if (!PyArg_ParseTuple(args, "O!", &PyFrame_Type, &pFrame) || pFrame == NULL)
    {
        PyErr_SetString(PyExc_TypeError, "Invalid arguments.");
        return NULL;
    }

    PyFrame_LocalsToFast(pFrame, 1);     // I think passing in 1 for the "clear" parameter ensures that you can set a local variable to None

    // Return successfully.

    Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef _MetadataUtilsMethods[] =
{
    {"SaveChangesToFrameLocals", SaveChangesToFrameLocals, METH_VARARGS, "Save the changes to the frame.f_locals dictionary to the actual frame object."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef _MetadataUtilsModule = {
    PyModuleDef_HEAD_INIT,
    "_MetadataUtils",   /* name of module */
    NULL,              /* module documentation, may be NULL */
    -1,                /* size of per-interpreter state of the module,
                          or -1 if the module keeps state in global variables. */
    _MetadataUtilsMethods
};


PyMODINIT_FUNC PyInit__MetadataUtils(void)
{
    return PyModule_Create(&_MetadataUtilsModule);
}
