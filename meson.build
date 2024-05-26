project('pyitc', 'c',
    version : '0.1.0',
    license: ['AGPL-3.0'],
    license_files: ['LICENSE'],
    meson_version: '>=1.4.0',
    subproject_dir: 'vendor',
    default_options : [
        'prefix=' + meson.current_build_dir(),
        'c_std=c99',
        'python.allow_limited_api=false',
        'werror=true',
    ]
)

pyitc_pyext_name = '_@0@'.format(meson.project_name())

c_compiler = meson.get_compiler('c')
python = import('python').find_installation(pure: false)
ffi_generator_script = files('ffi_generator.py')

libitc_proj = subproject(
    'libitc',
    required: true,
    default_options: {
        'default_library': 'static'
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
        '-E',
        libitc_header,
    ],
    output: '@0@.h'.format(pyitc_pyext_name),
    capture: true,
)

# Generate the pyext implementation using CFFI
pyitc_src = configure_file(
    command: [
        python,
        ffi_generator_script,
        '@INPUT@',
        pyitc_pyext_name
    ],
    input: pyitc_pp,
    output: '@0@.c'.format(pyitc_pyext_name)
)

# Compile the pyext
python.extension_module(
    pyitc_pyext_name,
    pyitc_src,
    pyitc_pp,
    dependencies: [
        libitc_dep,
    ],
    subdir: meson.project_name(),
    install: true,
)
