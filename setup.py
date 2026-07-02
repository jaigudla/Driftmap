from pathlib import Path
import platform
import shutil
import subprocess
import sys

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name: str, sourcedir: str = "") -> None:
        super().__init__(name, sources=[])
        self.sourcedir = str(Path(sourcedir).resolve())


def _cmake_executable() -> str:
    cmake = shutil.which("cmake")
    if cmake is not None:
        return cmake

    try:
        import cmake as cmake_pkg
    except ImportError as exc:
        raise RuntimeError(
            "CMake is required to build driftmap_core. "
            "Install it from https://cmake.org or `pip install cmake`."
        ) from exc

    for candidate in (
        Path(cmake_pkg.CMAKE_BIN_DIR) / "cmake",
        Path(cmake_pkg.CMAKE_BIN_DIR) / "cmake.exe",
    ):
        if candidate.is_file():
            return str(candidate)

    raise RuntimeError(
        "CMake is required to build driftmap_core. "
        "Install it from https://cmake.org or `pip install cmake`."
    )


class CMakeBuild(build_ext):
    def build_extension(self, ext: Extension) -> None:
        import pybind11

        ext_fullpath = Path(self.get_ext_fullpath(ext.name)).resolve()
        extdir = ext_fullpath.parent

        cfg = "Debug" if self.debug else "Release"
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-Dpybind11_DIR={pybind11.get_cmake_dir()}",
            f"-DCMAKE_BUILD_TYPE={cfg}",
        ]
        build_args = ["--config", cfg]

        if platform.system() == "Windows":
            cmake_args += [
                f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}",
                f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}",
            ]
        elif platform.system() == "Darwin":
            cmake_args += ["-DCMAKE_OSX_DEPLOYMENT_TARGET=10.14"]

        build_temp = Path(self.build_temp) / ext.name
        build_temp.mkdir(parents=True, exist_ok=True)

        cmake = _cmake_executable()
        subprocess.check_call(
            [cmake, ext.sourcedir, *cmake_args],
            cwd=build_temp,
        )
        subprocess.check_call(
            [cmake, "--build", ".", *build_args],
            cwd=build_temp,
        )


setup(
    name="driftmap-core",
    version="0.1.0",
    description="Phase 1 C++ statistical core bindings",
    ext_modules=[CMakeExtension("driftmap_core", sourcedir="driftmap/core")],
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
)
