#################################
## User configurable variables ##
#################################

# Virtual console keymap
# See https://git.io/fjq36 for all options
# def. 'us'
keymap = 'fi'

# Timezone setup e.g. 'Region/City'
# See https://git.io/fjq3i for all options
timezone = 'Europe/Helsinki'

# Locales to be generated for the new system separated by commas (,)
# NOTE: UTF-8 locales will be favored if not explicitly defined otherwise e.g. 'en_US ISO-8859-1,...'
# See https://git.io/fjq3X for all options
# def. 'en_US'
locales = 'en_US,fi_FI'

# Main system locale to be used
# def. 'en_US.UTF-8'
LANG = 'en_US.UTF-8'

# Locale used for other localized UI content e.g. time & date
# This should normally match your primary language
# def. 'en_US.UTF-8'
LC_ALL = 'fi_FI.UTF-8'

# Locale for sorting and regular expressions
# def. 'C'
LC_COLLATE = 'C'

# Fallback language ordered list separated by colons (:)
# def. 'en_US:en_GB:en'
LANGUAGE = 'en_US:en_GB:en'

# Hostname for the computer
# If empty, a dynamic hostname will be generated based on your board name
# def. '' => e.g. 'Z270N-WIFI'
hostname = ''

# List of all users that should be created on the system separated by commas (,)
# NOTE: All required users should be added here
# Single user: e.g. 'user'
# Multi-user:  e.g. 'user1,user2,user3,...'
users = 'user'

# List of users that should not be added to groups other than 'restricted'
# NOTE: These users also won't have 'sudo' access
restricted_users = ''

# List of users that will be left password-less
passwdless_users = ''

# Whether to ask root password when using sudo as a non-restricted user
# def. 'True'
sudo_ask_pass = False

# Should packages for assistive technologies such as an on-screen keyboard be included?
# def. 'False'
enable_assistive_tech = False

# Should the Arch User Repository (AUR) be enabled (install AUR helper 'yay')?
# def. 'True'
enable_aur = True

# Should AUR packages & other source code be compiled with 'march=native' for optimal performance?
# NOTE: Enabling this makes compiled code "tied" to the kind of CPU they were built on
# def. 'False'
optimize_compilation = False

# Should cached AUR packages be optimized as well?
# They will be stored in directories named after the specific CPU model
# NOTE: This is only effective when pkgcache & optimize_compilation are enabled
# def. 'False'
optimize_cached_pkgs = False

# Should parts of built packages be cached so the process will go much faster next time?
# NOTE: Large amounts (configurable, by default up to 24 GB) of storage may be used over time
# def. 'False'
use_ccache = True

# Should the testing repositories be enabled?
# This is useful for running the most bleeding edge software at the cost of system stability
# def. 'False'
enable_testing = False

# Should 32-bit software support be included?
# This is neeed for e.g. Steam and WINE
# def. 'True'
enable_multilib = True

# Should software meant for seamless™ printing & scanning be included?
# def. 'True'
enable_printing = True

# Enable flatpak application distribution platform?
# def. 'False'
enable_flatpak = False

# Enable Canonical's Snap application distribution platform?
# NOTE: This requires AUR support to be enabled
# def. 'False'
enable_snap = False

# Should ufw be setup with some basic rules?
# def. 'False'
enable_firewall = False

# Should an SSH daemon be run on the machine by default?
# def. 'False'
enable_sshd = False

# 0 = Don't setup a web server stack
# 1 = Setup LEMP (NGINX, MariaDB, PHP)
# 2 = Setup LAMP (Apache, MariaDB, PHP)
# def. '0'
web_server_type = 0

# Which Linux kernel should the system use?
# stable   = the default Arch Linux kernel
# hardened = a security-focused Linux kernel
# lts      = long-term support kernel
# zen      = kernel aimed at responsiveness (good for desktops)
# def. 'stable'
kernel_type = 'stable'

# Should GRUB multiboot support be included?
# This will show a boot menu during startup instead of booting straight to Arch
# def. 'False'
multibooting = False

# Should the system use localtime as the timescale instead of UTC?
# NOTE: This should be True only when multi-booting with Windows
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
# NOTE: This setting is only effective when auto_detect_gpu is also enabled
# def. 'False'
gpu_has_switchable_gfx = False

# Desktop environment to install
# none          = Leave as a base install
# cinnamon      = Linux Mint's Cinnamon DE
# xfce          = XFCE 4 DE
# gnome         = The GNOME 3 desktop environment
# mate          = Forked GNOME 2 DE
# budgie        = The Solus project's DE
# pantheon      = Pantheon DE from Elementary OS, coming soon™️
# dde           = Deepin Desktop Environment
# kde           = KDE Plasma 5 DE
# lxqt          = The new upcoming DE to replace LXDE
# lxde          = A lightweight X11 DE
# openbox       = Configurable stacking window manager, coming soon™️
# i3            = A wm that can work as a DE (i3-gaps)
# enlightenment = The classic & light desktop based on EFL libraries, coming soon™️
# dummy         = Install extra packages meant for DE's without one (particularly useful for custom setups)
# def. ''
de = 'cinnamon'

# Should many of the DE's default programs be installed?
# They can be safely omitted for a more minimal or specific setup
# def. 'True'
install_de_apps = True

# Should LibreOffice be installed among other DE apps?
# def. 'True'
install_office = True

# Pamac is a simple GTK+ interface to manage Arch Linux & AUR packages
# NOTE: This requires AUR support to be enabled
# Without this out of the box your only choice to manipulate software would be via the terminal w/ yay & pacman
# def. 'False'
install_pamac = False

# Install pulseaudio with some audio codecs for proper audio support?
# def. 'True'
use_pulseaudio = True

# Virtual console font
# See https://git.io/fjC5s for all options
# def. 'default'
font = 'ter-118n'

# Should NetworkManager be used instead of netctl / dhcpcd?
# NOTE: This makes networking work out of the box™ but is less minimal
# Should be almost always 'False' for installations without a DE
# def. 'True'
use_networkmanager = True

# Should Wi-Fi device MAC address be randomized when scanning for networks using NetworkManager?
# NOTE: Setting to True may cause issues with some Wi-Fi networks
# def. 'False'
nm_rand_mac_addr = False

# Should default system configurations be fetched as per the project repositories?
# def. 'True'
fetch_configs = True

# Should custom_setup() be called near end of the setup?
# This can be used to do extra setup specific to any hardware
# (or by default install some things that I'd get anyway)
# def. 'True'
run_custom_setup = True
