# Local Build and Example Authoring Guide

This guide is for users working directly from the repository source.

## 1. Prerequisites

From the repository root, install dependencies:

```bash
bash scripts/install_deps.sh
```

You should have:
- CMake
- A C++17 compiler
- Python 3.9+
- vcpkg dependencies from `vcpkg.json`

## 2. Local Build Modes

### Full Release Build (C++ core + examples + Python bindings)

```bash
bash scripts/build_release.sh
```

This uses the optimized flag set:
- `-O3 -march=native -mtune=native -ffast-math -funroll-loops -fstrict-aliasing -flto -DNDEBUG`

### Python Bindings Only

```bash
bash scripts/generate_bindings.sh
```

This now uses the same optimized flag set as release build.

### Build macOS Wheels Locally

```bash
bash scripts/build_wheels_macos.sh
```

This now exports the same optimization flags through `CXXFLAGS`.

## 3. Run Existing Examples

Each example folder has a `run.sh` wrapper. Example:

```bash
bash examples/5_trial_2d/run.sh
```

What this does:
1. Configures CMake in Release mode with examples and Python bindings enabled.
2. Builds the target mapped from the folder name.
3. Runs the C++ binary in the example `output` folder.
4. Runs the Python model if it exists and is non-empty.
5. Runs `process.py` for post-processing (if present).

## 4. Create a New Example (C++ + Python)

### Folder naming contract

Create a folder under `examples` using:
- `<number>_<suffix>`

Example:
- `examples/13_my_new_case/`

### Required files

Inside the new folder:
- `<suffix>.cpp` (example: `my_new_case.cpp`)
- `<suffix>.py` (example: `my_new_case.py`, can be empty initially)
- `run.sh`
- `process.py`
- `output/` directory (optional, created at runtime if missing)

You can copy `run.sh` and `process.py` from an existing folder like:
- `examples/5_trial_2d/`

### CMake target naming

CMake auto-discovers sources matching:
- `examples/[0-9]*_*/*.cpp`

Target name is auto-generated from folder suffix:
- folder `13_my_new_case` -> target `gpx_example_my_new_case`

You usually do not need to edit CMake files when adding a new example that follows this structure.

## 5. CMake Options You Can Toggle

Common CMake options:
- `-DGPX_BUILD_EXAMPLES=ON|OFF`
- `-DGPX_BUILD_PYTHON_BINDINGS=ON|OFF`
- `-DCMAKE_BUILD_TYPE=Release|Debug|RelWithDebInfo`

The main CMake entrypoint used by scripts is:
- `cmake/CMakeLists.txt`

## 6. Run a Specific Example Target Manually

From repo root:

```bash
cmake -S cmake -B build -DCMAKE_BUILD_TYPE=Release -DGPX_BUILD_EXAMPLES=ON -DGPX_BUILD_PYTHON_BINDINGS=ON
cmake --build build --target gpx_example_trial_2d --parallel
./build/examples/5_trial_2d/gpx_example_trial_2d
```

## 7. GitHub Release Tag for 0.1.0

After your branch is merged and CI is green:

```bash
git checkout main
git pull
git tag v0.1.0
git push origin v0.1.0
```

The wheels workflow is configured to publish on tags matching `v*`.
