import numpy as np
import os.path as osp
import subprocess
import tempfile
import time

import DracoPy
import laspy
import pcl

# This folder contain 0000.npy ~ 0099.npy representing xyzi point clouds,
# with intensity normalized to 0~1. It also contains 0000.loc.npy ~ 0000.loc.npy
# representing (x, y, z, theta) locations per frame.
folder_in = "compression_data"

# This folder contains all the compression outputs
folder_out = "compression_test"

def aggregate_point_clouds(pcs, poses=None):
    if poses is not None:
        transformed = []
        for pc, pose in zip(pcs, poses):
            xyz = pc[:, :3]
            rotmat = np.array([
                [np.cos(pose[3]), np.sin(pose[3])], [-np.sin(pose[3]), np.cos(pose[3])]]
            )
            xyz[:, :2] = xyz[:, :2].dot(rotmat)
            xyz[:, :3] += pose[:3]
            transformed.append(xyz)
        points = np.concatenate(transformed, axis=0)
    else:
        points = np.concatenate([pc[:, :3] for pc in pcs], axis=0)
    intensity = np.concatenate([pc[:, 3] for pc in pcs]) * (2**16 - 1)
    idx = np.concatenate([np.full(len(pc), i, dtype='u2') for i, pc in enumerate(pcs)])
    return points, intensity, idx

def compress_with_npz(pcs, out):
    save = {}
    for idx, pc in enumerate(pcs):
        save[str(idx)] = pc
    np.savez_compressed(osp.join(out, "npz_compress.npz"), **save)

def save_laz(pc, out):
    header = laspy.LasHeader(point_format=0)
    header.offsets = np.zeros(3)
    header.scales = np.full(3, 1e-3)

    with laspy.open(out, mode="w", header=header) as writer:
        point_record = laspy.ScaleAwarePointRecord.zeros(len(pc), header=header)
        point_record.x = pc[:, 0]
        point_record.y = pc[:, 1]
        point_record.z = pc[:, 2]
        point_record.intensity = (pc[:, 3] * (2**16 - 1)).astype('u2')
        writer.write_points(point_record)

def compress_with_las_tar(pcs, out):
    with tempfile.TemporaryDirectory() as tmpd:
        for i, pc in enumerate(pcs):
            save_laz(pc, osp.join(tmpd, "%04d.laz" % i))    
        subprocess.check_call(['tar', '-Ipxz', '-cf', osp.abspath(osp.join(out, "las_tar_compress.txz")), "."], cwd=tmpd)

def compress_with_las_aggr(pcs, out, poses=None):
    xyz, intensity, idx = aggregate_point_clouds(pcs, poses)
    
    header = laspy.LasHeader(point_format=0)
    header.offsets = np.zeros(3)
    header.scales = np.full(3, 1e-3)

    outname = ("las_aggregated_wpose.laz" if poses else "las_aggregated.laz") 
    with laspy.open(osp.join(out, outname), mode="w", header=header) as writer:
        point_record = laspy.ScaleAwarePointRecord.zeros(len(idx), header=header)
        point_record.x, point_record.y, point_record.z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
        point_record.intensity = intensity.astype('u2')

        # use two extra fields to encode index number
        point_record.user_data = idx.view('2u1')[:, 0]
        point_record.point_source_id = idx.view('2u1')[:, 1]
        writer.write_points(point_record)

def save_draco(pc, out, quantization_bits):
    intensity = (pc[:, 3] * (2**16 - 1)).astype('u2').view("2u1")
    with open(out, "wb") as fout:
        fout.write(DracoPy.encode(pc[:, :3], colors=intensity, compression_level=0, quantization_bits=quantization_bits))

def compress_with_draco_tar(pcs, out, q=14):
    with tempfile.TemporaryDirectory() as tmpd:
        for i, pc in enumerate(pcs):
            save_draco(pc, osp.join(tmpd, "%04d.drc" % i), q)    
        subprocess.check_call(['tar', '-Ipxz', '-cf', osp.abspath(osp.join(out, "draco_q%d_tar_compress.txz" % q)), "."], cwd=tmpd)

def compress_with_draco_aggr(pcs, out, poses=None, q=14):
    points, intensity, idx = aggregate_point_clouds(pcs, poses)
    colors = np.concatenate([intensity.astype('u2').view('2u1'), idx.view('2u1')], axis=1)

    outname = ("draco_q%d_aggregated_wpose.drc" if poses else "draco_q%d_aggregated.drc") % q 
    with open(osp.join(out, outname), "wb") as fout:
        fout.write(DracoPy.encode(points, colors=colors, compression_level=0, quantization_bits=q))

def compress_with_pcl_tar(pcs, out):
    with tempfile.TemporaryDirectory() as tmpd:
        for i, pc in enumerate(pcs):
            pcl.save_pcd(osp.join(tmpd, "%04d.pcd" % i), pcl.create_xyzi(pc), binary=True, compressed=True)
        subprocess.check_call(['tar', '-Ipxz', '-cf', osp.abspath(osp.join(out, "pcl_tar_compress.txz")), "."], cwd=tmpd)

def time_func(func, *args, **kwargs):
    tstart = time.time()
    func(*args, **kwargs)
    tend = time.time()
    print("Elapsed %.3f seconds" % (tend - tstart))

if __name__ == "__main__":
    # tar xz as baseline
    print("Compressing with tar.xz..")
    cmd = ['tar', '-Ipxz', '-cf', osp.abspath(osp.join(folder_out, "tar_compress.txz")), folder_in]
    time_func(subprocess.check_call, cmd)

    # test other approaches
    data = [np.load(osp.join(folder_in, "%04d.npy" % i)) for i in range(100)]
    poses = [np.load(osp.join(folder_in, "%04d.loc.npy" % i)) for i in range(100)]
    print("Compressing with npz..")
    time_func(compress_with_npz, data, folder_out)
    print("Compressing with las + tar..")
    time_func(compress_with_las_tar, data, folder_out)
    print("Compressing with draco (q=14) + tar ..")
    time_func(compress_with_draco_tar, data, folder_out)
    print("Compressing with draco (q=10) + tar ..")
    time_func(compress_with_draco_tar, data, folder_out, q=10)
    print("Compressing with pcl + tar ..")
    time_func(compress_with_pcl_tar, data, folder_out)
    print("Compressing with las aggregated ..")
    time_func(compress_with_las_aggr, data, folder_out)
    print("Compressing with draco (q=14) aggregated ..")
    time_func(compress_with_draco_aggr, data, folder_out)
    print("Compressing with draco (q=10) aggregated ..")
    time_func(compress_with_draco_aggr, data, folder_out, q=10)
    print("Compressing with las aggregated with poses ..")
    time_func(compress_with_las_aggr, data, folder_out, poses)
    print("Compressing with draco (q=14) aggregated with poses ..")
    time_func(compress_with_draco_aggr, data, folder_out, poses)
    print("Compressing with draco (q=10) aggregated with poses ..")
    time_func(compress_with_draco_aggr, data, folder_out, poses, q=10)
