import os
from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension(
            name='GeoEco._MetadataUtils',
            sources=[os.path.join('src', 'GeoEco', '_MetadataUtils.cpp')],
        ),
    ]
)
