---
name: parallels-vms
description: >-
  Access Parallels VMs on macOS for Linux and Windows work. Use when building,
  testing, or running commands on linux-vm or windows-vm.
---

# Parallels VMs

Two Parallels VMs on the shared network (`10.211.55.0/24`):

| Alias        | OS      | SSH user    | Code directory |
| ------------ | ------- | ----------- | -------------- |
| `linux-vm`   | Fedora  | `parallels` | `~/Code/`      |
| `windows-vm` | Windows | `sargunv`   | `E:\Code\`     |

SSH aliases and current IPs live in `~/.ssh/config.d/parallels-vms` (generated).
VMs are identified by host key fingerprintn in case Parallels DHCP can reassign
addresses.

## Check if a VM is active

```bash
generate-parallels-ssh-config   # refresh IPs first if SSH fails unexpectedly
ping -c 1 -W 2 linux-vm
nc -z -G 2 linux-vm 22 && echo up
ssh -o BatchMode=yes -o ConnectTimeout=5 linux-vm true && echo ssh ok
```

If `generate-parallels-ssh-config` prints `not found on 10.211.55.0/24`, the VM
is probably stopped or not on the shared network.

## Connect and run commands

```bash
ssh linux-vm 'ls ~/Code'
ssh windows-vm 'powershell -NoProfile -Command "Get-ChildItem E:\\Code"'
```

Prefer non-interactive flags (`-o BatchMode=yes`) when scripting.

## Refresh SSH config

When a VM gets a new IP or a new VM is added:

```bash
generate-parallels-ssh-config
```
