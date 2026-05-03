# Phase 2 — ZFS Storage Pool & Dataset Configuration

## Overview
This phase covers creating a ZFS storage pool using the virtual drives
attached to the TrueNAS VM, and organizing it into datasets for different
purposes. This is the foundation that Nextcloud and all other services
will store data on.

## What I Learned
- What ZFS is and why it's used for NAS systems
- The difference between a pool, a VDEV, and a dataset
- How RAID mirroring works and what redundancy means
- What ZFS compression does and why it's enabled by default
- Why the OS drive and storage drives must be kept separate
- How datasets differ from regular folders

## ZFS Concepts Explained

### Pool
A pool is the top level storage container in ZFS. It combines one or
more VDEVs into a single unified storage unit. All datasets live inside
a pool. Our pool is named "tank" following Unix convention.

### VDEV (Virtual Device)
A VDEV is a group of drives that work together within a pool. The VDEV
type determines the redundancy level. We used a Mirror VDEV which means
data is written identically to both drives simultaneously.

### Dataset
A dataset is like a smart folder inside a pool. Unlike regular folders,
each dataset has its own settings for compression, encryption, snapshots,
quotas, and permissions. Datasets inherit settings from their parent by
default but can be overridden individually.

### Mirror (RAID 1)
Two drives contain identical data at all times. If one drive completely
fails, the other has a perfect copy of everything. Zero data loss.
The tradeoff is you only get half the total raw capacity as usable space.

### ZFS Compression (LZ4)
LZ4 is a fast compression algorithm built into ZFS. It compresses data
before writing it to disk, meaning you effectively get more usable space.
The compression ratio shown on our pool was 3.72x — meaning data is
compressed to roughly 27% of its original size for typical files.
LZ4 is so fast that enabling it actually improves performance because
less data needs to be written to disk.

## Storage Configuration

### Pool Details
| Setting | Value |
|---|---|
| Pool Name | tank |
| VDEV Type | Mirror |
| Drives | 2 x 20 GiB virtual disks |
| Usable Capacity | 18.89 GiB |
| Encryption | None |
| Compression | LZ4 (3.72x ratio) |
| ZFS Health | Online, 0 errors |

### Dataset Structure

tank/                    (pool root — 18.89 GiB available)

├── nextcloud/           (Nextcloud application data)

├── media/               (movies, music, photos)

└── backups/             (backup destination)

All datasets use Generic preset with LZ4 compression inherited
from the pool root.

## Why These Datasets

### tank/nextcloud
Nextcloud needs its own dedicated dataset so we can:
- Set specific permissions for the Nextcloud Docker container
- Take snapshots independently of other data
- Set quotas if needed in the future
- Easily identify and manage Nextcloud's storage usage

### tank/media
Separate from Nextcloud so media files don't count against
any future Nextcloud quotas and can be managed independently.
Will eventually be used with Jellyfin media server.

### tank/backups
Dedicated backup destination. Keeping backups in their own
dataset makes it easy to see how much space backups consume
and manage them independently.

## Key Decisions Made

### Why Mirror instead of RAID-Z1
RAID-Z1 requires a minimum of 3 drives and TrueNAS SCALE 25.x
has stricter requirements for RAID-Z1 with virtual disks.
A 2-drive mirror provides the same core learning experience
and is appropriate for this storage capacity. The third virtual
drive remains unassigned for future experiments.

### Why "tank"
Tank is the traditional default ZFS pool name in the Unix world.
Using conventional names makes documentation and troubleshooting
easier since community resources universally reference "tank".

## ZFS Health Verification
After pool creation, ZFS Health showed:
- Pool Status: Online
- Total ZFS Errors: 0
- Scheduled Scrub Task: Set (automatic)
- Auto TRIM: Off (not needed for HDD)

## Next Phase
Phase 3 — Nextcloud deployment via Docker containers.
