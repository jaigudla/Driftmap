from pathlib import Path
import subprocess
import sys

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name: str, sourcedir: str = "") -> None:
        super().__init__(name, sources=[])
        self.sourcedir = str(Path(sourcedir).resolve())


class CMakeBuild(build_ext):
    def build_extension(self, ext: Extension) -> None:
        ext_fullpath = Path(self.get_ext_fullpath(ext.name)).resolve()
        extdir = ext_fullpath.parent

        cfg = "Debug" if self.debug else "Release"
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-DCMAKE_BUILD_TYPE={cfg}",
        ]
        build_args = ["--config", cfg]

        build_temp = Path(self.build_temp) / ext.name
        build_temp.mkdir(parents=True, exist_ok=True)

        subprocess.check_call(
            ["cmake", ext.sourcedir, *cmake_args], cwd=build_temp
        )
        subprocess.check_call(
            ["cmake", "--build", ".", *build_args], cwd=build_temp
        )


setup(
    name="driftmap-core",
    version="0.1.0",
    description="Phase 1 C++ statistical core bindings",
    ext_modules=[CMakeExtension("driftmap_core", sourcedir="driftmap/core")],
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
)
