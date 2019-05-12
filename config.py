#################################
## User configurable variables ##
#################################

# Virtual console keymap
# See https://git.io/fjq36 for all options
# def. 'us'
keymap = 'us'

# Timezone setup e.g. 'Region/City'
# See https://git.io/fjq3i for all options
timezone = 'Europe/Helsinki'

# NOTE See https://git.io/fjq3X for all locale options

# Language used by the setup interface
# See https://git.io/x for all options
# NOTE This won't affect tools the installer uses like cgdisk, parted etc
# def. 'en'
setup_language = 'en'

# Locales to be generated for the new system seperated by commas (,)
# NOTE UTF-8 locales will be favored if not explicitly defined otherwise e.g. 'en_US ISO-8859-1,...'
# def. 'en_US'
locales = 'en_US'

# Main system locale used
# LANG setting under /etc/locale.conf
# def. 'en_US.UTF-8'
LANG = 'en_US.UTF-8'

# Locale used for other localized UI content
# Other LC_* settings under /etc/locale.conf
# def. 'en_US.UTF-8'
LC_ALL = 'en_US.UTF-8'

# Locale for sorting and regular expressions
# LC_COLLATE setting under /etc/locale.conf
# def. 'C'
LC_COLLATE = 'C'

# Fallback language ordered list e.g. 'en_AU:en_GB:en'
# LANGUAGE setting under /etc/locale.conf
# def. 'en_US'
LANGUAGE = 'en_US'

# Hostname for the computer
# If empty, a dynamic hostname will be generated based on your board name
# def. '' => e.g. 'Arch-Z270N-WIFI'
hostname = ''

# Names of all users that should be created on the system
# NOTE All required users should be added here
# Single user: e.g. 'user'
# Multi-user:  e.g. 'user1,user2,user3,...'
users = 'username'

# List of users that should not be added to groups other than 'restricted'
# NOTE These users also won't have 'sudo' access
restricted_users = ''

# List of users that will be left password-less
passwdless_users = ''

# Whether to ask root password when using sudo as a non-restricted user
# def. 'True'
sudo_ask_pass = True

# Should packages for assistive technologies such as an on-screen keyboard be included?
# def. 'False'
enable_assistive_tech = False

# Should the Arch User Repository (AUR) be enabled (install AUR helper 'yay')?
# def. 'True'
enable_aur = True

# Should AUR packages be built with 'march=native' for more optimal performance?
# NOTE Enabling this makes AUR packages (by default) "tied" to the kind of CPU they were built on
# def. 'True'
optimize_aur_packages = True

# Should cached AUR packages be optimized as well?
# They will be stored in directories named after the specific CPU model
# NOTE This is only effective when pkgcache & optimize_aur_packages are enabled
# def. 'False'
optimize_cached_pkgs = False

# Should parts of built packages be cached so the process will go much faster next time?
# NOTE Large amounts (configurable, by default up to 24 GB) of storage may be used over time
# def. 'False'
use_ccache = False

# Should 32-bit software support be included?
# def. 'True'
enable_multilib = True

# Should software meant for seamless™ printing & scanning be included?
# def. 'True'
enable_printing = True

# Enable flatpak application distribution platform?
# def. 'False'
enable_flatpak = False

# Enable Canonical's Snap application distribution platform?
# NOTE Requires AUR support
# def. 'False'
enable_snap = False

# Should ufw be setup with some basic rules?
# def. 'False'
enable_firewall = False

# 0 = Don't enable OpenSSH server
# 1 = Spawn SSH daemon on connections (recommended)
# 2 = Run SSH daemon permanently (large SSH traffic)
# def. '0'
ssh_server_type = 0

# 0 = Don't setup a web server stack
# 1 = Setup LEMP (NGINX, MariaDB, PHP)
# 2 = Setup LAMP (Apache, MariaDB, PHP)
# def. '0'
web_server_type = 0

# Should 'linux-lts' be used as the kernel instead of 'linux'?
# def. 'False'
use_lts_kernel = False

# Should GRUB multiboot support be included?
# def. 'False'
multibooting = False

# Should the system use localtime as the timescale instead of UTC?
# NOTE This should be True when when multi-booting with Windows
# def. 'False'
use_localtime = False

# X.org display server install type
# 0 = Don't install X explicitly
# 1 = "Minimal" install (xorg-server & xorg-xinit + a few other pkgs)
# 2 = Install full xorg package group
# def. '1'
xorg_install_type = 1

# Should the GPU be automatically detected & approperiate driver packages be installed?
# def. 'True'
auto_detect_gpu = True

# Does the device have switchable graphics like NVIDIA PRIME on laptops?
# NOTE This setting is only effective when auto_detect_gpu is also enabled
# def. 'False'
gpu_has_switchable_gfx = False

# Desktop environment to install
# none     = Leave as a base install
# gnome    = The GNOME 3 desktop environment
# mate     = Forked GNOME 2 DE
# kde      = KDE Plasma 5 DE
# xfce     = XFCE 4 DE
# dde      = Deepin Desktop Environment
# cinnamon = Linux Mint's Cinnamon DE
# budgie   = The Solus project's DE
# lxde     = A lightweight X11 DE
# lxqt     = The new upcoming DE to replace LXDE
# i3       = A wm that can work as a DE (i3-gaps)
# dummy    = Install extra packages meant for DE's without one (particularly useful for custom setups)
# def. ''
de = 'none'

# Should many of the DE's default programs be installed?
# They can be safely omitted for a more minimal or specific setup
# def. 'True'
install_de_apps = True

# Install pulseaudio with some audio codecs for proper audio support?
# def. 'True'
use_pulseaudio = True

# Install the Adobe Flash plugin
# def. 'False'
use_adobe_flash = False

# Virtual console font
# See https://git.io/fjC5s for all options
# def. 'default'
font = 'default'

# Should NetworkManager be used instead of dhcpcd?
# NOTE This makes networking easier to set up but will bring some packages with it to the system
# Should be almost always 'False' for installations without a DE
# def. 'True'
use_networkmanager = True

# Should Wi-Fi device MAC address be randomized when scanning for networks using NetworkManager?
# 
nm_rand_mac_addr = False

# Whether to enable Network Time Protocol time synchronization
# def. 'True'
enable_ntp = True

# Other groups & packages to install w/ pacstrap on top of 'base' & 'python'
# NOTE 'base-devel' is required for AUR support and will be installed automatically if enabled
# def. ''
base_pkgs = 'reflector vim htop'