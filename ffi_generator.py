#!/usr/bin/env python3
#
# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
"""CFFI C ext code generator."""

import re
import sys
from pathlib import Path

import cffi  # type: ignore[import-untyped]

if len(sys.argv) != 4:  # noqa: PLR2004
    msg = "Requires three arguments"
    raise RuntimeError(msg)

header_file = sys.argv[1]
header_definitions_file = sys.argv[2]
module_name = sys.argv[3]

ffibuilder = cffi.FFI()

with Path(header_file).open("r") as f:
    contents = f.read()
    # On i686 linux systems 64-bit types are a GCC extension.
    # Thus, to suppress warnings about extension usage, the GCC preproccessor
    # will prepend an `__extension__` directive.
    # This confuses pycparser and is not needed, so just remove it.
    contents = re.sub(r"^__extension__.*\n", "", contents, flags=re.MULTILINE)
    ffibuilder.cdef(contents)

with Path(header_definitions_file).open("r") as f:
    contents = f.read()
    # Sanitize the output due to `pycparser` limitations
    # Remove defines not starting with `ITC_`
    contents = re.sub(r"^(?!#define\s+ITC).*\n", "", contents, flags=re.MULTILINE)
    # Remove defines without value (i.e. `#define SOMETHING`)
    contents = re.sub(r"^#define\s+\w+\s*\n", "", contents, flags=re.MULTILINE)
    # Remove suffixes from integer literals (`1U` -> `1`, `0xAFuLL` -> `0xAF`)
    contents = re.sub(
        r"(\b(?:0[xXbB])?[\da-fA-F]+)[UulL]+\b", r"\1", contents, flags=re.MULTILINE
    )
    # Remove brackets
    contents = re.sub(r"[\(\)]", "", contents, flags=re.MULTILINE)

    ffibuilder.cdef(contents)

ffibuilder.set_source(
    module_name,
    '#include "ITC.h"',
)

if __name__ == "__main__":
    ffibuilder.distutils_extension(".")
