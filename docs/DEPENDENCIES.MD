# GeoPeriX_CPP Dependencies

This project requires two external C++ dependencies.

## Eigen3
Purpose: Linear algebra (matrices, vectors, SVD)  
Type: Header-only  
vcpkg name: eigen3

## HDF5 (with C++ API)
Purpose: Reading and writing HDF5 files  
Type: Shared library  
vcpkg name: hdf5

# Cross-Platform Installation Using vcpkg

Install vcpkg:

```bash
git clone https://github.com/microsoft/vcpkg
cd vcpkg
./bootstrap-vcpkg.sh        # Linux/macOS
.\bootstrap-vcpkg.bat       # Windows