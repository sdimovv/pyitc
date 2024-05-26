#!/usr/bin/env python3
#
# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html

import sys

import cffi

if len(sys.argv) != 3:
    raise RuntimeError("Requires two arguments")

header_file = sys.argv[1]
module_name = sys.argv[2]

ffibuilder = cffi.FFI()

with open(header_file) as f:
    ffibuilder.cdef(f.read())

ffibuilder.set_source(
    module_name,
    '#include "ITC.h"',
)

if __name__ == '__main__':
    ffibuilder.distutils_extension('.')
