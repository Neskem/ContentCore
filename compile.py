from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools import setup
from setuptools.extension import Extension

setup(
    ext_modules=cythonize(
        [
            Extension("breakcontent.*", ["breakcontent/*.py"]),
            Extension("breakcontent.api.*", ["breakcontent/api/*.py"]),
            Extension("breakcontent.api.v1.*", ["breakcontent/api/v1/*.py"])
        ],
        build_dir='build',
        compiler_directives=dict(
            always_allow_keywords=True, language_level=3
        )
    ),
    cmdclass=dict(
        build_ext=build_ext
    )
)
