# -*- python -*-
# Copyright (C) 2010, zy_sunshine.
# Author:  zy_sunshine <zy.netsec@gmail.com>
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.

import glob
from distutils.core import setup, Extension

module_bb = Extension('cmmseg',
                      include_dirs = ['/usr/local/mmseg3/include/mmseg'],
                      libraries = ['mmseg'],
                      library_dirs = ['/usr/local/mmseg3/lib'],
                      sources =  ['pymmseg.c', 'mmseg_interface.cpp',
                                  ]
        )

setup(name = 'cmmseg',
      version = '1.0',
      description = 'mmseg python api',
      author = 'zy_sunshine',
      author_email = 'zy.netsec@gmail.com',
      ext_modules = [module_bb])

