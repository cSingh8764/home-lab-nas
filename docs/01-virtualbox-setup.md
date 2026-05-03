# Phase 1 — VirtualBox VM Setup & TrueNAS SCALE Installation

## Overview
This phase covers creating a virtual machine in VirtualBox to run TrueNAS SCALE
on my existing Windows PC. The goal is to learn the full stack before investing
in dedicated hardware.

## What I Learned
- What a hypervisor is and how virtualization works
- How to configure virtual hardware (RAM, CPU, storage, network)
- How ZFS requires separate OS and storage drives
- How to manually configure a static IP address
- The difference between DHCP and static IP addressing
- How CIDR notation works (/24 = 255.255.255.0)

## Environment
- Host OS: Windows 11
- Virtualization: Oracle VirtualBox
- Guest OS: TrueNAS SCALE 25.04.2.6
- Host CPU: Intel Core i7-1355U (13th Gen)
- Host RAM: 32GB

## Virtual Machine Configuration

| Setting | Value | Reason |
|---|---|---|
| RAM | 8192MB (8GB) | ZFS needs RAM for caching |
| CPU | 2 cores | Sufficient for NAS workloads |
| Storage Controller | AHCI (SATA) | Modern standard, required for TrueNAS |
| EFI/UEFI | Enabled | Required for TrueNAS SCALE 25.x |
| Network | Bridged Adapter | VM needs its own IP on home network |
| Video Memory | 128MB | Proper display in VM window |

## Storage Layout

| Drive | Size | Purpose |
|---|---|---|
| TrueNAS-SCALE_1.vdi | 32GB | TrueNAS OS installation drive |
| TrueNAS-SCALE_2.vdi | 20GB | ZFS storage drive 1 |
| TrueNAS-SCALE_3.vdi | 20GB | ZFS storage drive 2 |
| TrueNAS-SCALE_4.vdi | 20GB | ZFS storage drive 3 |

The OS drive and storage drives are kept completely separate.
TrueNAS itself recommends this — the system drive should never
be part of a storage pool.

## Network Configuration

Bridged WiFi adapter would not get a DHCP address automatically
from the router. Fixed by assigning a static IP manually through
the TrueNAS console.

| Setting | Value |
|---|---|
| Interface | enp0s3 |
| IP Address | 192.168.70.50/24 |
| Gateway | 192.168.70.1 |
| DNS | 8.8.8.8 (Google) |
| DHCP | Disabled |

## Problems Encountered

### Problem 1 — Wrong storage controller
Created VM with IDE controller by default. TrueNAS requires AHCI.
**Fix:** Deleted IDE controller, created new AHCI controller, reattached all drives.

### Problem 2 — Bridged WiFi not getting DHCP address
TrueNAS could not get an IP from the router through the bridged WiFi adapter.
**Fix:** Disabled DHCP on the network interface, assigned a static IP address
manually through the TrueNAS console using CIDR notation (192.168.70.50/24).

### Problem 3 — Wrong password on first login
**Fix:** Used TrueNAS console option 4 "Change local administrator password" to reset it.

## Result
TrueNAS SCALE dashboard accessible at http://192.168.70.50
from any browser on the local network.

## Key Concepts Learned

**Hypervisor:** Software that creates and manages virtual machines by
dividing physical hardware resources between multiple guest operating systems.

**AHCI vs IDE:** AHCI is the modern storage controller standard. IDE is
from the 1990s. TrueNAS requires AHCI for proper disk detection and performance.

**Static vs DHCP IP:** DHCP lets a router automatically assign IP addresses.
Static means you hardcode the address manually. Servers should always use
static IPs so their address never changes.

**CIDR Notation:** /24 means 24 bits are used for the network portion of
the IP address, leaving 8 bits for devices. This equals subnet mask 255.255.255.0
and allows 254 devices on the network.

**EFI/UEFI:** Modern firmware standard that replaced BIOS. TrueNAS SCALE 25.x
requires UEFI to boot correctly.

## Next Phase
Phase 2 — ZFS storage pool configuration and dataset creation.
