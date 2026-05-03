# Home Lab NAS — Self-Hosted Nextcloud Server

A complete, documented build of a self-hosted NAS and private cloud 
storage server using TrueNAS SCALE and Nextcloud. Built from scratch, 
documented every step of the way.

---

## What This Project Is

This is a full home lab build — starting from zero, learning everything, 
and ending up with a private cloud server accessible from anywhere in 
the world. No Google Drive. No iCloud. Full ownership of my data.

**Final result:**
- Private file storage accessible from any device, anywhere
- Photo and video backup from phone automatically
- File sharing with password-protected links
- All running on self-hosted hardware I built and configured myself

---

## Tech Stack

| Layer | Technology |
|---|---|
| Virtualization (Stage 1) | Oracle VirtualBox |
| NAS Operating System | TrueNAS SCALE |
| Filesystem | ZFS |
| Containerization | Docker |
| Cloud Storage App | Nextcloud |
| Remote Access | Tailscale |
| Version Control | Git + GitHub |

---

## Build Phases

- [x] Phase 0 — Project planning and GitHub setup
- [ ] Phase 1 — VirtualBox VM creation and configuration
- [ ] Phase 2 — TrueNAS SCALE installation
- [ ] Phase 3 — ZFS storage pool configuration
- [ ] Phase 4 — Nextcloud deployment via Docker
- [ ] Phase 5 — Remote access via Tailscale
- [ ] Phase 6 — Dedicated hardware build

---

## Repository Structure

home-lab-nas/

├── docs/                    # Step by step documentation per phase

├── configs/                 # Configuration files (sanitized)

├── scripts/                 # Automation scripts

└── README.md                # This file

## Documentation

Each phase has its own detailed doc in the `/docs` folder explaining 
what was done, why each decision was made, what went wrong, and how 
it was fixed.

---

## Security Note

All configuration files in this repository have been sanitized. 
No passwords, IP addresses, API keys, or personal information 
are stored here.

---

## Author

**Akshat Singh** — [@cSingh8764](https://github.com/cSingh8764)

*Built for learning. Documented for the community.*
