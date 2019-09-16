#!/usr/bin/env python

# based on https://martinopilia.com/posts/2018/09/15/building-python-extension.html
# and https://github.com/m-pilia/disptools/blob/master/python_c_extension/CMakeLists.txt

import os
import subprocess
import sys

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

# Command line flags forwarded to CMake
cmake_cmd_args = []
for f in sys.argv:
    if f.startswith('-D'):
        cmake_cmd_args.append(f)
for f in cmake_cmd_args:
    sys.argv.remove(f)
    
disable_libsnark = False
if "--disable-libsnark" in sys.argv:
    disable_libsnark = True
    sys.argv.remove("--disable-libsnark")

disable_qaptools = False
if "--disable-qaptools" in sys.argv:
    disable_qaptools = True
    sys.argv.remove("--disable-qaptools")
    
qaptools_bin = None
for i in sys.argv:
    if i.startswith("--qaptools-bin="):
        qaptools_bin = i[15:]
        sys.argv.remove(i)
        break
    
if "-h" in sys.argv or "--help" in sys.argv:
    print("PySNARK setup.py\n\n" +
          "PySNARK options:\n\n" +
    
          "  --disable-libsnark  disable libsnark backend\n" +
          "  --disable-qaptools  disable qaptools backend\n" +
          "  --qaptools=bin=...  use precompiled qaptools from given directory\n" +
          "  -D...               arguments for cmake compilation of libsnark/qaptools\n")

class CMakeExtension(Extension):
    def __init__(self, name, cmake_lists_dir='.', **kwa):
        Extension.__init__(self, name, sources=[], **kwa)
        self.cmake_lists_dir = os.path.abspath(cmake_lists_dir)

class CMakeBuild(build_ext):
    def build_extensions(self):
        # Ensure that CMake is present and working
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError('Cannot find CMake executable')

        for ext in self.extensions:
            extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
            
            tempdir = self.build_temp+"/"+ext.name

            cmake_args = [
                '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={}'.format(extdir),
                '-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={}'.format(extdir),
                '-DCMAKE_SWIG_OUTDIR={}'.format(extdir),
                '-DSWIG_OUTFILE_DIR={}'.format(tempdir),
                '-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY={}'.format(tempdir),
                '-DPYTHON_EXECUTABLE={}'.format(sys.executable)                
            ]

            cmake_args += cmake_cmd_args

            if not os.path.exists(tempdir):
                os.makedirs(tempdir)
                
            # Config
            subprocess.check_call(['cmake', ext.cmake_lists_dir] + cmake_args,
                                  cwd=tempdir)

            # Build
            subprocess.check_call(['cmake', '--build', '.'],
                                  cwd=tempdir)

if disable_qaptools and disable_libsnark:  
    my_exts = None
else:
    my_exts=[] + [CMakeExtension("pysnark.libsnark.all", cmake_lists_dir="depends/python-libsnark")] if not disable_libsnark else [] + [CMakeExtension("pysnark.qaptools.all", cmake_lists_dir="depends/qaptools") if not disable_qaptools else []]


setup(name='PySNARK',
      version='0.2',
      description='Python zk-SNARK execution environment',
      author='Meilof Veeningen',
      author_email='meilof@gmail.com',
      url='https://github.com/meilof/pysnark',
      packages=['pysnark'] +
                  (['pysnark.qaptools'] if not disable_qaptools else []) +
                  (['pysnark.libsnark'] if not disable_libsnark else []),
      package_data={'pysnark.qaptools': []} if not disable_qaptools else {},
      ext_modules = my_exts,
      cmdclass={'build_ext': CMakeBuild} if not (disable_qaptools and disable_libsnark) else {}
)

