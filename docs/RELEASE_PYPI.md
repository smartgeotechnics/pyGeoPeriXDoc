# GeoPeriX PyPI Release Guide

This repository builds the Python extension module `PyGeoPeriX` using CMake and `pybind11`.

For pip-only users, the published wheel must bundle native runtime libraries (HDF5, Qhull, GMP/MPFR) instead of relying on local system package managers.

## 1. Prepare Environment

```bash
python3 -m pip install --upgrade pip
python3 -m pip install build twine scikit-build-core pybind11
```

## 2. Build Wheel and Source Distribution

Run from repository root:

```bash
python3 -m build
```

This generates files under `dist/`.

## 2b. Build and Repair macOS Wheel (Recommended)

Use the bundled script to produce a repaired wheel with vendored `.dylib` runtime dependencies:

```bash
bash scripts/build_wheels_macos.sh
```

This places repaired wheels under `dist/repaired/`.

## 3. Validate Distributions

```bash
python3 -m twine check dist/*.tar.gz dist/*.whl dist/repaired/*.whl
```

## 4. Upload to TestPyPI (Recommended First)

```bash
python3 -m twine upload --repository testpypi dist/repaired/*.whl dist/*.tar.gz
```

## 5. Upload to PyPI

```bash
python3 -m twine upload dist/repaired/*.whl dist/*.tar.gz
```

## 6. Versioning

Update both files before release:
- `VERSION.txt`
- `pyproject.toml` (`project.version`)

CMake reads `VERSION` via `cmake/CMakeLists.txt` for native build versioning.

## 6b. GitHub Actions Release

Workflow file: `.github/workflows/wheels.yml`

- Builds wheels for Linux, macOS, and Windows via `cibuildwheel`
- Current matrix targets:
	- Linux: x86_64, aarch64
	- macOS: x86_64, arm64
	- Windows: AMD64
- Repairs wheels per platform:
	- Linux: `auditwheel`
	- macOS: `delocate`
	- Windows: `delvewheel`
- Builds sdist
- Runs `twine check`
- Publishes on `v*` tags

### Dependency Bootstrap in CI

The workflow uses vcpkg bootstrap scripts before wheel builds:

- `scripts/cibw/setup_vcpkg_linux.sh`
- `scripts/cibw/setup_vcpkg_macos.sh`
- `scripts/cibw/setup_vcpkg_windows.ps1`

These scripts install required native dependencies used by CMake find-package logic.

## 7. Notes

- Packaging config is in `pyproject.toml`.
- CMake source root for wheel builds is `cmake/`.
- Examples are disabled for wheel builds through CMake defines in `pyproject.toml`.
- For easiest end-user install, distribute repaired wheels from `dist/repaired`.
