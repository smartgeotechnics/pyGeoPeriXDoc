# Installation

GeoPeriX can be installed as a pre-built Python wheel from PyPI, or built from source for maximum performance.

---

## Requirements

### Runtime

| Package | Minimum version | Purpose |
|---------|----------------|---------|
| Python  | 3.9            | Python API |
| h5py    | 3.8            | HDF5 post-processing |
| numpy   | 1.23           | Numerical post-processing |
| openpyxl | 3.1           | Excel export |

The `h5py`, `numpy`, and `openpyxl` packages are only required when using the post-processing tools in `tools/gpx_reader/`. The core `PyGeoPeriX` module has no Python-level dependencies.

### Build from source

| Dependency | Version | Purpose |
|-----------|--------|---------|
| CMake | 3.15+ | Build system |
| C++17 compiler | GCC 8+, Clang 7+, MSVC 2017+ | Core engine |
| Eigen3 | any recent | Linear algebra |
| HDF5 C++ API | 1.10+ | I/O |
| CGAL | 5.x+ | Delaunay / Voronoi volumes |
| Qhull | any recent | Convex hull (CGAL transitive) |
| GMP / MPFR | any recent | Arbitrary precision (CGAL transitive) |
| pybind11 | 2.11.1+ | Python bindings (fetched automatically) |

---

## Install from PyPI (recommended)

The easiest path is to install a pre-built wheel. No compiler or C++ library is needed.

```bash
pip install geoperix
```

Install with post-processing extras (h5py, numpy, openpyxl):

```bash
pip install "geoperix[postprocess]"
```

Verify the installation:

```python
import PyGeoPeriX
print(PyGeoPeriX.__version__)
```

---

## Install from source

### 1. Clone the repository

```bash
git clone https://github.com/smartgeotechnics/GeoPeriX.git
cd GeoPeriX
```

### 2. Install system dependencies

A helper script detects your operating system and installs the required C++ libraries:

```bash
bash scripts/install_deps.sh
```

| Platform | Package manager | Packages installed |
|---------|----------------|-------------------|
| Ubuntu / Debian | apt | build-essential, cmake, libeigen3-dev, libhdf5-dev, libcgal-dev, libqhull-dev, libgmp-dev, libmpfr-dev |
| Fedora / CentOS | dnf | cmake, eigen3-devel, hdf5-devel, CGAL-devel, qhull-devel, gmp-devel, mpfr-devel |
| Arch Linux | pacman | cmake, eigen, hdf5, cgal, qhull, gmp, mpfr |
| macOS | Homebrew | cmake, eigen, hdf5, cgal, qhull, gmp, mpfr, python@3 |
| Windows | vcpkg | eigen3, hdf5[cpp], cgal, qhull, gmp, mpfr |

### 3. Build and install the Python package

```bash
pip install .
```

Or with post-processing extras:

```bash
pip install ".[postprocess]"
```

### 4. Verify

```bash
python -c "import PyGeoPeriX; print('GeoPeriX loaded successfully')"
```

---

## Using vcpkg explicitly

If you prefer to manage dependencies through vcpkg rather than system packages:

```bash
git clone https://github.com/microsoft/vcpkg.git
./vcpkg/bootstrap-vcpkg.sh
export VCPKG_ROOT=$(pwd)/vcpkg

cmake -S cmake -B build \
    -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \
    -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
```

The CMake build system tries vcpkg first, then falls back to system packages.

---

## Build options

| CMake option | Default | Description |
|-------------|---------|-------------|
| `GPX_BUILD_EXAMPLES` | `ON` | Build all C++ example executables |
| `GPX_BUILD_PYTHON_BINDINGS` | `ON` | Build the `PyGeoPeriX` Python extension |
| `CMAKE_BUILD_TYPE` | `Release` | `Release`, `Debug`, or `RelWithDebInfo` |

To build only the Python bindings without the C++ example executables:

```bash
cmake -S cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DGPX_BUILD_EXAMPLES=OFF \
    -DGPX_BUILD_PYTHON_BINDINGS=ON
cmake --build build --parallel
```

---

## Building wheels for distribution

To build a platform-specific wheel:

```bash
python3 -m build
```

On macOS, run the wheel-repair script after building to bundle shared libraries:

```bash
bash scripts/build_wheels_macos.sh
```

The `cibuildwheel` configuration in `pyproject.toml` is used for CI-based multi-platform wheel builds.
