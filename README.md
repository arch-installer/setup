# ArchInstaller.py
A semi-automatic & configurable Arch Linux installer script written in Python.
DISCLAIMER: This is early software and will definitely change during the course of time.

## Development
* Initial checks added
* Disk partitioning menu done
* Disk mounting & formatting menus (mostly) done
* Base system can be installed
* UEFI & BIOS/CSM support
* Support for base, GNOME & KDE installs

## Screenshots
### Script initialization
![Setup 1](/Images/setup-1.png)
### Disk partitioning
![Setup 2](/Images/setup-2.png)
### Mounting partitions
![Setup 3](/Images/setup-3.png)
### Installation
![Setup 4](/Images/setup-4.png)
### Base system installed
![Setup 5](/Images/setup-5.png)

## TODO
* Make installer script UI localizable
* Add dynamic progress messages e.g. for pacman & pacstrap
* Fully disallow mounted selections to be chosen in mounting menu
* Add support for more filesystem types (notably Btrfs)
* Add support for RAID in mounting & formatting options
* Add support for LUKS encryption in mounting & formatting options
* Prevent mounting to / on a NTFS volume etc.
* Add other makepkg.conf optimizations
* Multi-user setup
* Web server stack setup (LEMP / LAMP)
* Xorg / wayland setup
* Video drivers setup
* Power saving features setup
* Desktop environment setup
* Audio setup (Pulseaudio / ALSA)
* Snap & flatpak setup
* Assistive techologies setup
* Printing & scanning setup
* Post-install boot time improvements?
* ...
