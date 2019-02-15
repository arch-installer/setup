# ArchInstaller.py
A semi-automatic &amp; configurable Arch Linux installer script made in Python.  
DISCLAIMER: This is early software and will definitely change during the course of time.

## Development
* Initial checks added
* Disk partitioning menu done
* Disk mounting & formatting menus (mostly) done

## Screenshots
### Script initialization
![Setup 1](/GitHub/setup-1.png)
### Disk partitioning
![Setup 2](/GitHub/setup-2.png)
### Mounting partitions
![Setup 3](/GitHub/setup-3.png)

## TODO
* Make installer script UI localizable
* Add dynamic progress messages e.g. for pacman & pacstrap
* Fully disallow mounted selections to be chosen in mounting menu
* Add support for more filesystem types (notably Btrfs)
* Add support for RAID in mounting & formatting options
* Add support for LUKS in mounting & formatting options
* Prevent mounting to / on a NTFS volume etc.
* Mirrorlist sorting using reflector
* Install to /mnt using pacstrap w/ selected repos
* Command output formatting improvements
* Improve many parts of the codebase
* Post-install boot time improvements?
* ...
