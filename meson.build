project('pyitc', 'c',
    version : '0.1.0',
    license: ['AGPL-3.0'],
    license_files: ['LICENSE'],
    meson_version: '>=1.4.0',
    subproject_dir: 'vendor',
    default_options : [
        'prefix=' + meson.current_build_dir(),
        'c_std=c99',
        'werror=true',
        # Do not respect the `limited_api` arg of the
        # `extension_module` call by default
        'python.allow_limited_api=false',
    ]
)

libitc_c_args = [
    '-DITC_CONFIG_ENABLE_EXTENDED_API=1',
    '-DITC_CONFIG_USE_64BIT_EVENT_COUNTERS=1',
    '-DITC_CONFIG_ENABLE_SERIALISE_TO_STRING_API=1',
]

# A set of defines to pass to the preprocessor when generating the pyitc C ext
# code with CFFI. These are used to fool the preprocessor that certain system
# headers have already been included and preprocessed (when in fact they haven't).
#
# The goal is to reduce the unrelevant noise present in the outputted headers
# coming from the expansion of system includes in the source libitc headers.
# Otherwise `pycparser` can get confused and fail.
libitc_pyext_preproccessing_c_args = [
    '-D_GCC_WRAP_STDINT_H', # Define for stdint.h on mingw64
    '-D__CLANG_STDINT_H', # Define for stdint.h on Xcode clang-15
]

pyitc_pyext_name = '_@0@'.format(meson.project_name())

c_compiler = meson.get_compiler('c')
python = import('python').find_installation(pure: false)
ffi_generator_script = files('ffi_generator.py')

add_global_arguments(libitc_c_args, language: 'c')

libitc_proj = subproject(
    'libitc',
    required: true,
    default_options: {
        'default_library': 'static',
        'tests': false
    },
)
libitc_dep = libitc_proj.get_variable('libitc_dep')

libitc_inc_dir = meson.current_source_dir() / 'vendor' / 'libitc' / 'libitc' / 'include'
libitc_header =  libitc_inc_dir / 'ITC.h'

# Generate the pyext interface (i.e. preprocess the underlying C lib header)
pyitc_pp = configure_file(
    command: [
        c_compiler,
        '-I@0@'.format(libitc_inc_dir),
        libitc_c_args,
        '-E',
        libitc_pyext_preproccessing_c_args,
        libitc_header,
    ],
    output: '@0@.h'.format(pyitc_pyext_name),
    capture: true,
)

# Generate the pyext preprocessor definitions (from the underlying C lib header)
# Used to turn the `ITC_*` preprocessor definitions into global consts in the
# python module
pyitc_defs_pp = configure_file(
    command: [
        c_compiler,
        '-I@0@'.format(libitc_inc_dir),
        libitc_c_args,
        '-dM',
        '-E',
        libitc_pyext_preproccessing_c_args,
        libitc_header,
    ],
    output: '@0@_definitions.h'.format(pyitc_pyext_name),
    capture: true,
)

# Generate the pyext implementation using CFFI
pyitc_src = configure_file(
    command: [
        python,
        ffi_generator_script,
        '@INPUT@',
        pyitc_pyext_name,
    ],
    input: [pyitc_pp, pyitc_defs_pp],
    output: '@0@.c'.format(pyitc_pyext_name)
)

# Compile the pyext
python.extension_module(
    pyitc_pyext_name,
    pyitc_src,
    dependencies: [
        libitc_dep,
    ],
    subdir: meson.project_name(),
    install: true,
    # CFFI uses the limited API when possible.
    # The exact rules for when this happens are a little muddy and depend
    # on both python and C preprocessor logic.
    # Define what the minimum supported limited API version is here, but toggle
    # whether it should be respected or ignored via the `python.allow_limited_api`
    # option.
    #
    # CFFI docs state 3.5+, but this module targets 3.7+.
    limited_api: '3.7',
)

python.install_sources(
    files([
        'src' / 'pyitc' / '__init__.py',
        'src' / 'pyitc' / 'extended_api.py',
        'src' / 'pyitc' / 'pyitc.py',
        'src' / 'pyitc' / 'exceptions.py',
    ]),
    subdir: meson.project_name(),
)

python.install_sources(
    files([
        'src' / 'pyitc' / '_internals' / '__init__.py',
        'src' / 'pyitc' / '_internals' / 'wrappers.py',
    ]),
    subdir: meson.project_name() / '_internals',
)
