# ArchInstaller.py
A semi-automatic & configurable Arch Linux installer script written in Python.

You should already be familiar with [Arch Linux](https://www.archlinux.org) before using this as things may and inevitably **will** go wrong.

Actual script configuration is done in the `config.py` module & `custom_setup()` method found at the top of `setup.py`.

**DISCLAIMER:** This is still `alpha` state software and will keep changing in the future.

## Screenshots
### Script initialization
<img src="/Images/init.png" alt="Script init sequence" width="800" />

### Disk partitioning
<img src="/Images/gdisk.png" alt="Partitioning with gdisk" width="800" />
<img src="/Images/cgdisk.png" alt="Partitioning with cgdisk" width="800" />

### Mounting partitions
<img src="/Images/mounting.png" alt="Disk mounting menu" width="800" />

### Installation
<img src="/Images/install.png" alt="Setup installing compontents 1" width="800" />
<img src="/Images/install-2.png" alt="Setup installing compontents 2" width="800" />

### GRUB boot menu (shown when multibooting)
<img src="/Images/grub.png" alt="Themed GRUB boot menu" width="800" />

### Desktop Environments (DEs)

#### Base system install
<img src="/Images/base.png" alt="Installed base system" width="800" />

#### Cinnamon
<img src="/Images/cinnamon.png" alt="Installed Cinnamon desktop" width="800" />

#### XFCE, GNOME, MATE, Budgie, Pantheon, Deepin, KDE (Plasma), LXQt, LXDE, Openbox, i3
Coming soon™️

## Deployment
This is an example of how I'm used to deploying the scripts remotely to a system running the ArchISO environment via ethernet:
```
TARGET # passwd                –  required to use SSH
TARGET # systemctl start sshd  –  launching the SSH server Daemon
TARGET # ip a                  –  get live system IP for SSH / file transfer (e.g. 192.168.1.105)
```
Then to transfer the scripts via terminal from the current directory to the target system:
```
HOST $ scp *.py root@192.168.1.105:/root/
root@192.168.1.105's password:
config.py                                                         100% 6246     2.3MB/s   00:00
setup.py                                                          100%  111KB  73.3MB/s   00:00
```
Using the script is as simple as running it like any other (Python) executable:
```
TARGET # ./setup.py
```
The rest should be self-explanatory when following the instructions during install :)

## Following progress
To follow the progress and view the commands being run by the script, switch to another TTY / login via SSH and do:
```
TARGET # tail -f /tmp/setup.log
```
**NOTE:** This will need to be ended with `Ctrl` + `C` when entering chroot as the file gets moved, you'll then need to run this the command again.

Once the system is installed the log will be moved to `/var/log/setup.log` on the target system for further investigation / removal.
