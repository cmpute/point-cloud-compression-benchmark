# Point Cloud Compression Benchmark
Benchmark of compressing sequential point clouds.

To run the benchmark, you need a Python environment with the following packages: `numpy`, `DracoPy`, `pcl.py`, `laspy[lazrs]`.

You also need a 100-frame sequence of point cloud data.

The tested data used here are generated with the CARLA simulator. Each point in the cloud has a structure of (x, y, z, intensity), all represented by 32-bit floats.

## Results

|                                | Compression Time | Compressed Size | Compression Ratio |
|--------------------------------|------------------|-----------------|-------------------|
| tar.xz (baseline)              | 12.595           | 16.25213        | 17.21638          |
| numpy npz                      | 4.254            | 26.37437        | 27.93917          |
| las + tar.xz                   | 4.877            | 10.0848         | 10.68314          |
| draco (q=14) + tar.xz          | 6.004            | 8.701447        | 9.217706          |
| draco (q=10) + tar.xz          | 4.314            | 5.032021        | 5.330572          |
| pcl + tar.xz                   | 19.434           | 23.67338        | 25.07793          |
| las aggregated                 | 0.405            | 9.952751        | 10.54325          |
| draco (q=14) aggregated        | 37.712           | 8.812826        | 9.335694          |
| draco (q=10) aggregated        | 38.127           | 5.535102        | 5.863501          |
| las aggregated (w/pose)        | 0.378            | 9.86227         | 10.4474           |
| draco (q=14) aggregated w/pose | 38.276           | 7.205489        | 7.632993          |
| draco (q=10) aggregated w/pose | 38.966           | 4.245287        | 4.497161          |

<!--
|                                | Compression Time | Compressed Size | Compression Ratio |
|--------------------------------|------------------|-----------------|-------------------|
| tar.xz (baseline)              | 12.595           | 16.252          | 17.22             |
| numpy npz                      | 4.254            | 26.374          | 27.94             |
| las + tar.xz                   | 4.877            | 10.085          | 10.68             |
| draco (q=14) + tar.xz          | 6.004            | 8.701           | 9.22              |
| draco (q=10) + tar.xz          | 4.314            | 5.032           | 5.33              |
| pcl + tar.xz                   | 19.434           | 23.673          | 25.08             |
| las aggregated                 | 0.405            | 9.953           | 10.54             |
| draco (q=14) aggregated        | 37.712           | 8.813           | 9.34              |
| draco (q=10) aggregated        | 38.127           | 5.535           | 5.86              |
| las aggregated (w/pose)        | 0.378            | 9.862           | 10.45             |
| draco (q=14) aggregated w/pose | 38.276           | 7.205           | 7.63              |
| draco (q=10) aggregated w/pose | 38.966           | 4.245           | 4.50              |
-->

