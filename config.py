###############################
# User configurable variables
###############################

# Virtual console keymap
# NOTE See 'vconsole-keymaps.txt' for all options
# def. 'us'
keymap = 'fi'

# Virtual console font
# NOTE See 'vconsole-fonts.txt' for all options
# def. 'default'
font = 'ter-118n' # ter-118n

# Other groups & packages to install w/ pacstrap on top of 'base' & 'python'
# NOTE 'base-devel' is required for AUR support and will be installed automatically if enabled
# def. ''
# TODO Add pacman cache support (e.g. USB drive)
# TODO Fix systemd messages appearing on screen about microcode on real hardware
base_pkgs = 'vim htop unzip p7zip unrar'

# Whether to enable Network Time Protocol time synchronization
# def. 'True'
enable_ntp = True

# Should the system use localtime as the timescale instead of UTC?
# This should be True when when multi-booting with Windows
# def. 'False'
use_localtime = False

# Timezone setup e.g. 'Region/City'
# See 'timezones.txt' for all options
timezone = 'Europe/Helsinki'

# Locales to be generated for the new system seperated by commas (,)
# NOTE UTF-8 locales will be favored if not explicitly defined otherwise e.g. 'en_US ISO-8859-1,...'
# def. 'en_US'
locales = 'en_US,fi_FI'

# Main system locale used
# LANG setting under /etc/locale.conf
# def. 'en_US.UTF-8'
LANG = 'en_US.UTF-8'

# Fallback language ordered list e.g. 'en_AU:en_GB:en'
# LANGUAGE setting under /etc/locale.conf
# def. 'en_US.UTF-8'
LANGUAGE = 'en_US'

# Locale for sorting and regular expressions
# LC_COLLATE setting under /etc/locale.conf
# def. 'C'
LC_COLLATE = 'C'

# Locale used for other localized UI content
# Other LC_* settings under /etc/locale.conf
# def. 'en_US.UTF-8'
LC_ALL = 'fi_FI.UTF-8'

# Hostname for the computer
# If empty, a dynamic hostname will be generated based on your board name
# def. '' => e.g. 'Arch-Z270N-WIFI'
hostname = ''

# Name for the non-privileged user (if one should be created)
# NOTE AUR support requires a normal user
# TODO Multi-user creation support, users seperated by ','
# TODO Auto-login support?
user = 'user' # user

# Whether to ask root password when using sudo as the normal user
# def. 'True'
sudo_ask_pass = False

# Should the Arch User Repository (AUR) be enabled (install AUR helper 'yay')?
# def. 'False'
enable_aur = True

# Should 32-bit software support be included?
# def. 'True'
enable_multilib = True

# Should ufw be setup with some basic rules?
# def. 'False'
# TODO Finish up
enable_firewall = False

# 0 = Don't enable OpenSSH server
# 1 = Spawn SSH daemon on connections (recommended)
# 2 = Run SSH daemon permanently (large SSH traffic)
# def. '0'
ssh_server_type = 1

# 0 = Don't setup a web server stack
# 1 = Setup LEMP (NGINX, MariaDB, PHP)
# 2 = Setup LAMP (Apache, MariaDB, PHP)
# def. '0'
# TODO Implement setup function
web_server_type = 0

# Should 'linux-lts' be used as the kernel instead of 'linux'?
# def. 'False'
use_lts_kernel = False

# Should GRUB multiboot support be included?
# def. 'False'
multibooting = False

# X.org display server install type
# 0 = Don't install X explicitly
# 1 = "Minimal" install (xorg-server & xorg-xinit + a few other pkgs)
# 2 = Install full xorg package group
# def. '0'
xorg_install_type = 1

# Should the GPU be automatically detected & approperiate driver packages be installed?
# TODO Support legacy AMD (< ATI HD 8xxx) & nVidia GPUs (< GeForce 6xx)
# def. 'True'
auto_detect_gpu = True

# Desktop environment to install
# none          = Leave as a base install
# gnome         = The GNOME 3 desktop environment
# mate          = Forked GNOME 2 DE
# kde           = KDE Plasma 5 DE
# xfce          = XFCE 4 DE
# dde           = Deepin Desktop Environment
# cinnamon      = Linux Mint's Cinnamon DE
# budgie        = The Solus project's DE
# lxde          = A lightweight X11 DE
# lxqt          = The new upcoming DE to replace LXDE
# i3            = A wm that can work as a DE (i3-gaps)
# def. ''
# TODO Replace 'none' with ''
de = ''

# TODO DE variants 'full', 'minimal' or 'normal'

# Install pulseaudio with other audio codecs for proper audio support?
# def. 'False'
use_pulseaudio = True

# TODO Printer & scanner setup
