###############################
# User configurable variables
###############################

# TODO Reorder to have most important options at the top

# Virtual console keymap
# NOTE See 'vconsole-keymaps.txt' for all options
# def. 'us'
keymap = 'us'

# Timezone setup e.g. 'Region/City'
# See 'timezones.txt' for all options
timezone = 'Europe/Helsinki'

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
# def. 'en_US.UTF-8'
LANGUAGE = 'en_US'

# Hostname for the computer
# If empty, a dynamic hostname will be generated based on your board name
# def. '' => e.g. 'Arch-Z270N-WIFI'
hostname = ''

# Names of all users that should be created on the system
# NOTE All required users should be added here
# Single user: e.g. 'user'
# Multi-user:  e.g. 'user1,user2,user3,...'
# TODO Remove root user from list if detected
users = 'user'

# List of users that should not be added to groups other than 'restricted'
# NOTE These users also won't have 'sudo' access
# TODO Add these users to sudoers file: 
restricted_users = ''

# List of users that will be left password-less
# TODO Auto-login support in GNOME and other DEs?
passwdless_users = ''

# Whether to ask root password when using sudo as a non-restricted user
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
# TODO Finish up - Is it even possible from chroot?
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
# TODO Implement setup function
web_server_type = 0

# Should 'linux-lts' be used as the kernel instead of 'linux'?
# def. 'False'
use_lts_kernel = False

# Should GRUB multiboot support be included?
# def. 'False'
multibooting = False

# Should the system use localtime as the timescale instead of UTC?
# This should be True when when multi-booting with Windows
# def. 'False'
use_localtime = False

# X.org display server install type
# 0 = Don't install X explicitly
# 1 = "Minimal" install (xorg-server & xorg-xinit + a few other pkgs)
# 2 = Install full xorg package group
# def. '0'
xorg_install_type = 1

# Should the GPU be automatically detected & approperiate driver packages be installed?
# def. 'True'
# TODO Support legacy AMD (< ATI HD 8xxx) GPUs & other Intel iGPUs
auto_detect_gpu = True

# Desktop environment to install
# none  = Leave as a base install
# gnome = The GNOME 3 desktop environment
# def. ''
de = 'gnome'

# TODO DE variants 'full', 'minimal' or 'normal'

# TODO Printer & scanner setup

# TODO Assistive technologies (espeak etc)

# Install pulseaudio with other audio codecs for proper audio support?
# def. 'False'
use_pulseaudio = True

# Install the Adobe Flash plugin
# def. 'False'
use_adobe_flash = False

# Virtual console font
# NOTE See 'vconsole-fonts.txt' for all options
# def. 'default'
font = 'ter-118n'

# Whether to enable Network Time Protocol time synchronization
# def. 'True'
enable_ntp = True

# Other groups & packages to install w/ pacstrap on top of 'base' & 'python'
# NOTE 'base-devel' is required for AUR support and will be installed automatically if enabled
# def. ''
base_pkgs = 'vim htop'
