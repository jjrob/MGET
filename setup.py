import os
from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension(
            name='GeoEco.MetadataUtils',
            sources=[os.path.join('src', 'GeoEco', 'MetadataUtils.cpp')],
        ),
    ]
)
