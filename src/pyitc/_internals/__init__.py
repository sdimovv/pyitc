# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
try:
    from .._pyitc import ffi as _ffi  # noqa: F401
    from .._pyitc import lib as _lib  # noqa: F401
except ImportError:  # pragma: no cover
    raise ImportError("pyitc C extension import failed, cannot use C-API")
