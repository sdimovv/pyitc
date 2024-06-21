# Copyright (c) 2024 pyitc project. Released under AGPL-3.0
# license. Refer to the LICENSE file for details or visit:
# https://www.gnu.org/licenses/agpl-3.0.en.html
try:
    from pyitc._pyitc import ffi as _ffi  # type: ignore[import-untyped] # noqa: F401
    from pyitc._pyitc import lib as _lib  # type: ignore[import-untyped] # noqa: F401
except ImportError:  # pragma: no cover
    msg = "pyitc C extension import failed, cannot use C-API"
    raise ImportError(msg) from None
