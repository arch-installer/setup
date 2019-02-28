#!/usr/bin/python

# ArchInstaller.py
# ----------------
# Author      : JamiKettunen
#               https://github.com/JamiKettunen
# Project     : https://github.com/JamiKettunen/ArchInstaller.py
#
# Description : My personal Arch Linux installer script | Python rewrite
#
# License     : MIT (https://git.io/fhF8b)
#
# Reference   : https://wiki.archlinux.org/index.php/Installation_guide
#

# File IO, argv, run, sleep, ...
import os, sys, subprocess, time, re, random

# Import configured user variables
try:
	from config import *
except ModuleNotFoundError:
	# TODO Move error message here?
	pass

# TODO Create a .gz package to gunzip & include *.py files: # gunzip archinstaller.py.gz
# TODO Report device formatting, package installing, pacstrap etc progress



###############################
# Custom setup 
###############################

# TODO Find a way to seperate to 'custom.py'

def custom_setup():
	#pass

	# Install custom packages
	write_msg("Installing custom packages...", 1)
	errors = Pkg.install('bash-completion neofetch')
	errors += Pkg.aur_install('c-lolcat')
	write_status(errors)

	# Custom GRUB2 theme
	write_msg("Installing custom 'poly-dark' GRUB2 theme...", 1)
	ret_val = Cmd.exec('cd /tmp && git clone https://github.com/shvchk/poly-dark.git &>/dev/null && mkdir -p /boot/grub/themes && mv poly-dark /boot/grub/themes && grep "GRUB_THEME=" /etc/default/grub &>/dev/null && sed -i "/GRUB_THEME=/d" /etc/default/grub && echo "GRUB_THEME=/boot/grub/themes/poly-dark/theme.txt" >>/etc/default/grub && grub-mkconfig -o /boot/grub/grub.cfg &>/dev/null')
	write_status(ret_val)

	user_cmds = '' # §u = User, §t = TargetUserHomePath, §s = SourcePath, §g = UserGroup, §f = FileName

	# Create some directories
	Cmd.log('mkdir -p ~/.local/bin ~/.vim/colors') # Root
	if len(users) > 0:
		for user in users.split(','):
			Cmd.log('$ mkdir -p ~/.local/bin ~/.vim/colors', user) # Users
			restricted = User.is_restricted(user)
			group = ('restricted' if restricted else 'users')
			# TODO Use '&&' again (probably need some sort of brackets)
			user_cmds += '; cd /home/§u/§t; cp §s .; chown §u:§g §f'.replace('§u', user).replace('§g', group)
	#write_status(ret_val)

	# TODO Use global config files instead after making backups?

	# Custom ~/.bash_profile
	write_msg("Creating custom '.bash_profile' file for all users...", 1)
	ret_val = Cmd.log(f'cd && curl https://git.io/fhNsR -Lso §s{user_cmds}; cd'.replace('§t', '').replace('§s', '~/§f').replace('§f', '.bash_profile'))
	write_status(ret_val)

	# Custom ~/.bashrc
	write_msg("Creating custom '.bashrc' file for all users...", 1)
	ret_val = Cmd.log(f'curl https://git.io/fhNsu -Lso §s{user_cmds}; cd'.replace('§t', '').replace('§s', '~/§f').replace('§f', '.bashrc'))
	write_status(ret_val)

	# Custom ~/.bashrc.aliases
	write_msg("Creating custom '.bashrc.aliases' file for all users...", 1)
	ret_val = Cmd.log(f'curl https://git.io/fhNsg -Lso §s{user_cmds}; cd'.replace('§t', '').replace('§s', '~/§f').replace('§f', '.bashrc.aliases'))
	write_status(ret_val)

	# Vim custom setup
	write_msg("Creating custom '.vimrc' file for all users...", 1)
	errors = Cmd.log(f'curl https://git.io/fhNs2 -Lso §s{user_cmds}; cd'.replace('§t', '').replace('§s', '~/§f').replace('§f', '.vimrc'))
	errors += Cmd.log(f'curl https://git.io/fhNs6 -Lso §s{user_cmds}; cd'.replace('§t', '.vim/colors/').replace('§s', '~/.vim/colors/§f').replace('§f', 'molokai.vim'))
	write_status(errors)

	# TODO Add proton config options & system file mofidications
	# https://github.com/ValveSoftware/Proton#runtime-config-options

	# TODO Also check if BCM or Broadcom in dmesg etc. to further identify system hw
	#if vm_env == '':
		#write_msg('Installing proper support for BCM WiFi + BT combo card, please wait...', 1)
		#errors = Pkg.install(f'linux{kernel_suffix}-headers dkms crda broadcom-wl-dkms')
		#write_msg('Installing proper support for RTL 8192 WiFi card, please wait...', 1)
		#errors = Pkg.install(f'linux{kernel_suffix}-headers dkms crda')
		#IO.uncomment_ln('/etc/conf.d/wireless-regdom', 'WIRELESS_REGDOM="FI"')
		#errors += Pkg.aur_install('bcm20702a1-firmware')
		#write_status(errors)

	# TODO Custom tlp config?



###############################
# "Constant" values
###############################

# TODO Make localizable (add overrideable localized variables)

status_colors = {
	0: 1,
	1: 4,
	2: 3,
	3: 2,
	4: 4,
	5: 7
}

status_mgs = {
	0: '    ',
	1: 'WAIT',
	2: 'DONE',
	3: 'FAIL',
	4: 'WARN',
	5: 'INFO'
}

script_path, script_fn = os.path.split(os.path.abspath(sys.argv[0])) # Script filename  e.g. 'setup.py'
script_path += ('/' + script_fn)            # Full script path e.g. '/root/setup.py'
script_root = script_path.rsplit('/', 1)[0] # Directory path of script e.g. '/root'
lsblk_cmd = "lsblk | grep -v '^loop' | grep -v '^sr0'"
blkid_cmd = "blkid | grep -v '^/dev/loop' | grep -v '^/dev/sr0'"

# Vars updated on script load
boot_mode = 'BIOS/CSM'    # 'BIOS/CSM' / 'UEFI'
cpu_type = ''             # 'intel' / 'amd'
in_chroot = False         # Inside chroot?
vm_env = ''               # Virtualized env: '','vbox','vmware','other'
bat_present = False       # Any battery present?
disc_tray_present = False # Any disc tray present?
bt_present = False        # Any BT device present?
fdd_present = False       # Any floppy disk drive present?
args = ''                 # All arguments in one string
mbr_grub_dev = ''         # GRUB install device on MBR systems e.g. '/dev/sda'
mounts = ''               # Current mounts e.g. '/efi:/dev/sda1,root:/dev/sda2'
video_drv = ''            # e.g. 'nvidia','nvidia-340','noveau+mesa','amdgpu+mesa','intel+mesa','bumblebee' etc
kernel_suffix = ('-lts' if use_lts_kernel else '')
par_menu_visit_counter = 0
mount_menu_visit_counter = 0



###############################
# Helper functions
###############################

# Clear the entire screen buffer
def clear_screen():
	Cmd.exec('clear')

# Printing text

# Returns a string with parsed terminal output forecolor; usage:
# e.g. 'color_str(§2red §0reset §5blue)'
#
# Colors:
# 0 = Default (white fg, black bg)
# 1 = Black
# 2 = Red
# 3 = Green
# 4 = Yellow
# 5 = Blue
# 6 = Magenta
# 7 = Cyan
# 8 = White
#
def color_str(string, reset=True):
	if '§' in string: # Possible color definition found
		for f in range(0, 9): # Fore color only: (0-8)
			match = f'§{str(f)}' # e.g. '§2'
			if match not in string: # match not found => check next color
				continue

			fg = '0' # default fg to white (37)
			if f != 0: # update fg to use defined color
				fg = str(29 + f)

			string = string.replace(match, f'\033[0;{fg}m') # e.g. '\e[0;32m'

	if reset:
		string += '\033[0m'

	return string

# Writes text to stdout
def write(text):
	sys.stdout.write(text)
	sys.stdout.flush()

# Writes a line of text to stdout
def write_ln(text='', new_line_count=1):
	for _ in range(0, new_line_count):
		text += '\n'
	write(text)

# Clears the screen & prints a *nice* looking header
def print_header(header):
	ul = ('=' * len(header)) # e.g. '============='
	clear_screen()
	write_ln(color_str(f'§7{header}')) # e.g. 'A Nice Header'
	write_ln(color_str(f'§7{ul}'), 2) 

# Status messages

# Writes a status message
# e.g. '>> Using log engine v2.0'
#      '>> [ WAIT ] Fetching latest data...'
#      '>> [  OK  ] Started NetworkManager service'
#      '>> [ FAIL ] ...'
# TODO Dynamic messages (e.g. changes on success/fail etc)
# TODO Progress reporting commands (e.g. 'Updating sources... 34%')
def write_msg(msg, status=0, override_newline=-1):
	if status > 0:
		color = status_colors.get(status)
		status_msg = status_mgs.get(status, 0)
		write(color_str(f'§{color}>> [ {status_msg} ] ')) # e.g. '>> [ WAIT ] '
	else:
		write(color_str('§7>> ')) # '>> '

	# TODO msg = color_str(msg) ?

	# TODO Improve this
	if override_newline == -1:
		if status > 1:
			write_ln(msg)
		else:
			write(msg)
	elif override_newline == 1:
		write_ln(msg)
	else:
		write(msg)

# Writes back to the current status message line to update the appearance depending on a command's return value
# e.g. write_status(0, 0)
#      '>> [ DONE ]'
#      write_status(1, 0, 4)
#      '>> [ WARN ]'
def write_status(ret_val, expected_val=0, error_status=3):
	if ret_val == expected_val:
		status_msg = status_mgs.get(2)
		write_ln(color_str(f'\r§3>> [ {status_msg} ]'))
	else:
		color = status_colors.get(error_status)
		status_msg = status_mgs.get(error_status)
		write_ln(color_str(f'\r§{color}>> [ {status_msg} ]'))

# Logging

# Log a new line to /(tmp/)setup.log
# Returns: 0 = Success, 1 = Error
def log(text):
	path = '' if in_chroot else '/tmp'
	return IO.write_ln(f'{path}/setup.log', text)

# File I/O class to read from & write to files

class IO:
	# Reads the first line from a file
	# Returns: String on success, None on error
	@staticmethod
	def read_ln(f_path):
		try:
			with open(f_path, 'r') as f:
				tmp_ln = f.readline().rstrip('\n')
		except:
			tmp_ln = None
		return tmp_ln

	# Writes text to a file
	# Returns: 0 = Success, 1 = Error
	@staticmethod
	def write(f_path, text, append=False):
		try:
			# TODO Fix append mode??
			mode = 'a' if append else 'w'
			with open(f_path, f'{mode}+') as f:
				f.write(text)
			return 0
		except:
			return 1

	# Appends text to a file
	# Returns: 0 = Success, 1 = Error
	@staticmethod
	def append(f_path, text):
		return IO.write(f_path, text, True)

	# Writes a line to a file
	# Returns: 0 = Success, 1 = Error
	@staticmethod
	def write_ln(f_path, text = '', append=True):
		return IO.write(f_path, text + '\n', append)

	# TODO Write a function returning tuples about a found line (e.g. ln_num, ln_str, ...)

	# Replace a line with another in a file
	# Returns: 0 = Replaced, 1 = Line not found, 2 = Error
	@staticmethod
	def replace_ln(file_path, search_ln, replace_ln, only_first_match=True):
		try:
			found = False
			file_lines = ''
			with open(file_path) as lines:
				for line in lines:
					line = line.rstrip() # e.g. 'line\n' => 'line'
					if not only_first_match or (only_first_match and not found):
						if line.startswith(search_ln):
							found = True
							line = replace_ln
					file_lines += f'{line}\n'
			if found:
				with open(file_path, 'w') as f:
					f.write(file_lines.rstrip())
				return 0
			else:
				return 1
		except:
			return 2

	# Uncomments a line in a file
	# Returns: 0 = Uncommented, 1 = Line not found, 2 = Error
	# TODO Return uncommented line & use for future purposes
	@staticmethod
	def uncomment_ln(file_path, search_ln, comment_prefix='#'):
		try:
			found = False
			file_lines = ''
			with open(file_path) as lines:
				for line in lines:
					line = line.rstrip() # e.g. 'line\n' => 'line'
					if not found and line.startswith(comment_prefix + search_ln):
						found = True
						line = line[len(comment_prefix):]
					file_lines += f'{line}\n'
			if found:
				with open(file_path, 'w') as f:
					f.write(file_lines.rstrip())
				return 0
			else:
				return 1
		except:
			return 2

	# Returns: line number of found line, -1 when not found
	@staticmethod
	def get_ln_number(file_path, search_ln):
		try:
			line_num = -1
			with open(file_path) as lines:
				ln = 1
				for line in lines:
					line = line.rstrip() # e.g. 'line\n' => 'line'
					if line.startswith(search_ln):
						line_num = ln
						break
					ln += 1
			return line_num
		except:
			return -2

# Package management

class Pkg:
	# TODO Progress reporting messages
	# Refresh local package database cache
	# Quit script execution on error
	@staticmethod
	def refresh_dbs(force_refresh=False, quit_on_fail=True):
		command = 'pacman -Sy'
		command += 'y' if force_refresh else ''
		ret_val = Cmd.log(command)
		if ret_val != 0 and quit_on_fail:
			log_path = 'mnt' if in_chroot else 'tmp'
			write_ln(color_str(f'§2ERROR: §0Database refreshing failed. Check /{log_path}/setup.log for details'))
			exit_code = 8 if force_refresh else 7
			exit(exit_code) # 7 = Couldn't synchronize databases, 8 = Force-refresh failed
		return ret_val

	# TODO Progress reporting messages
	# Install packages from the Arch repositories (core, extra, community)
	# Returns: pacman exit code
	@staticmethod
	def install(pkgs, only_needed=True):
		pac_args = '--needed' if only_needed else ''
		if in_chroot: pac_args += ' --cachedir /pkgcache/pkgcache' if os.path.exists('/pkgcache') else ''
		if len(pac_args) > 0: pac_args = ' ' + pac_args.strip()
		ret_val = Cmd.log(f'pacman -S --noconfirm --noprogressbar{pac_args} {pkgs}')
		return ret_val

	# TODO Progress reporting messages
	# Remove installed packages on a system
	# Returns: pacman exit code
	@staticmethod
	def remove(pkgs, also_deps=False):
		pac_args = '-Rn' + ('sc' if also_deps else '') + ' --noconfirm --noprogressbar'
		ret_val = Cmd.log(f'pacman {pac_args} {pkgs}')
		return ret_val

	# TODO Progress reporting messages
	# Install packages from the Arch User Repository (AUR)
	# Returns: pacman exit code
	@staticmethod
	def aur_install(pkgs, only_needed=True):
		if in_chroot:
			if enable_aur:
				yay_args = '--needed' if only_needed else ''
				# TODO Add caching back once issues are resolved
				#yay_args += ' --builddir /pkgcache/pkgcache/aur' if os.path.exists('/pkgcache') else ''
				if len(yay_args) > 0: yay_args = ' ' + yay_args.strip()
				ret_val = Cmd.log(f'$ yay -Sq --noconfirm{yay_args} {pkgs}', 'aurhelper')
				return ret_val
			else:
				log(f'[setup.py:Pkg.aur_install({pkgs})] WARN: Ignoring installation, since the AUR support is not disabled.')
				return 1
		else:
			log(f'[setup.py:Pkg.aur_install({pkgs})] WARN: Ignoring installation, since not in chroot.')
			return 1

# Command execution

class Cmd:
	# Run a command on the shell with an optional io stream
	# io_stream_type: 0 = none, 1 = stdout, 2 = logged, 3 = all_supressed
	# Returns: command exit code / output when io_stream_type=2
	@staticmethod
	def exec(command, exec_user='', io_stream_type=0):
		user_exec = command.startswith('$ ')
		exec_cmd = command

		if user_exec:
			if exec_user == '':
				# TODO Use first NON-RESTRICTED user instead if not defined?
				exec_user = users.split(',')[0]
			command = command[2:] # Remove '$ ' from user_exec commands
			if len(exec_user) > 0:
				exec_cmd = f"sudo -i -u {exec_user} -H bash -c '{command}'"
			else:
				log(f'[setup.py:Cmd.exec({str(io_stream_type)})] WARN: Ignoring "{command}" execution, since no user was defined.')
				return 1

		use_stdout = (io_stream_type == 1)
		logged = (io_stream_type == 2)
		suppress = (io_stream_type == 3)

		end = ''
		if suppress or logged:
			path = '' if in_chroot else '/tmp'
			log_path = f'{path}/setup.log' # e.g. '/tmp/setup.log' or '/setup.log' in chroot
			end = ' ' + f'&>>{log_path}' if logged else '&>/dev/null'
			if logged:
				start = (f'# ({exec_user}) $' if user_exec else '#') + ' '
				log(f'\n{start}{command}') # e.g. '# pacman -Syu'
		if use_stdout:
			res = subprocess.run(exec_cmd + end, shell=True, encoding='utf-8', capture_output=use_stdout)
		else:
			res = subprocess.run(exec_cmd + end, shell=True)

		if logged and res.returncode != 0:
			log(f'\n# Command non-zero exit code: {res.returncode}')

		returns = res.stdout if use_stdout else res.returncode
		return returns

	# Run a command on the shell while capturing all it's output
	# New lines are seperated with a '\n'
	# Returns: command exit code
	@staticmethod
	def output(command, exec_user=''):
		return Cmd.exec(command, exec_user, 1)

	# Run a command on the shell while logging all it's output
	# Returns: command exit code
	@staticmethod
	def log(command, exec_user=''):
		return Cmd.exec(command, exec_user, 2)

	# Run a command on the shell while supressing all it's output
	# Returns: command exit code
	@staticmethod
	def suppress(command, exec_user=''):
		return Cmd.exec(command, exec_user, 3)

# Checking user details

class User:
	# Returns: Boolean representing the user's restricted status
	@staticmethod
	def is_restricted(user=''):
		if len(users) == 0: return False # No users => can't be restricted
		# TODO Add proper checking (against users list)
		return user in restricted_users.split(',')

	# Returns: Restricted users in a list
	@staticmethod
	def get_restricted_users():
		if len(users) == 0: return [] # No users => can't be restricted
		# TODO Add proper checking (against users list)
		return restricted_users.split(',')

	# Returns: Boolean representing the user's passwordless status
	@staticmethod
	def is_passwdless(user=''):
		if len(users) == 0: return False # No users => can't be passwdless
		# TODO Add proper checking (against users list)
		return user in passwdless_users.split(',')

	# Returns: Passwordless users in a list
	@staticmethod
	def get_passwdless_users():
		if len(users) == 0: return [] # No users => can't be unrestricted
		# TODO Add proper checking (against users list)
		return passwdless_users.split(',')

	# Returns: Unrestricted users in a list
	@staticmethod
	def get_unrestricted_users():
		if len(users) == 0: return [] # No users => can't be unrestricted

		users_lst = users.split(',')
		res_users_lst = User.get_restricted_users()
		unres_users_lst = []

		for user in users_lst:
			if user not in res_users_lst:
				unres_users_lst.append(user)

		return unres_users_lst



###############################
# Pre-run checks
###############################

# Check if running in Arch Linux installer env & quit if not
# Additionally update details about the device
def check_env():
	global de, users, boot_mode, in_chroot
	os_compat_msg = 'Please only run this script on the Arch Linux installer environment.\n\nhttps://www.archlinux.org/download/'
	file_msg = "It seems that you are missing a '§f' module.\nHere's one way to fix it:\n\n   # §c\n"
	if os.name == 'posix':
		ret_val = Cmd.suppress('cat /etc/hostname')
		if ret_val == 0:
			host = IO.read_ln('/etc/hostname')
			if host != 'archiso':
				print(os_compat_msg)
				exit(3) # 3 = Not running in ArchISO environment

			# config.py
			try:
				base_pkgs
			except NameError:
				# TODO Give an option to download the script instead of only giving instructions
				print(file_msg.replace('§f', 'config.py').replace('§c', 'curl https://git.io/fhbgV -Lso config.py'))
				exit(4) # 4 = config.py not loaded
		#elif host == hostname:
			# TODO Add post-install script parts => verify here
		else: # Read failed => Assume chroot environment
			in_chroot = True

		de = de.lower().replace('none', '')
		# TODO Add a regex to disregard everything except accepted chars
		users = users.lower().strip().replace(' ', '') # '-'

		# Update bootmode to EFI if required
		ret_val = Cmd.suppress('ls /sys/firmware/efi/efivars')
		if ret_val == 0: boot_mode = 'UEFI' # efivars dir exits => booted in UEFI
	else:
		print(os_compat_msg)
		input()
		exit(2) # 2 = Non-POSIX systems are incompatible

# Check if running as root
def check_privs():
	user = Cmd.output("whoami").rstrip('\n')
	if user != 'root':
		write_ln(color_str('§2ERROR: §0Please run this file as root to continue.'))
		exit(5) # 5 = Privilege requirements unmet



###############################
# Functions
###############################

# Use custom installer color definitions
def load_colors():
	# TODO 16 colors
	Cmd.exec("echo -en '\\033]P00C0C0C'") # Black
	Cmd.exec("echo -en '\\033]P1AF1923'") # Red
	Cmd.exec("echo -en '\\033]P269A62A'") # Green
	Cmd.exec("echo -en '\\033]P3E68523'") # Yellow
	Cmd.exec("echo -en '\\033]P42935B1'") # Blue
	Cmd.exec("echo -en '\\033]P57C1FA1'") # Magenta
	Cmd.exec("echo -en '\\033]P62397F5'") # Cyan
	Cmd.exec("echo -en '\\033]P79E9E9E'") # White
	clear_screen() # Clear screen to avoid coloring artifacts

# Check network connectivity with ping
def check_connectivity():
	write_msg('Checking network connectivity...', 1)
	ret_val = Cmd.log('curl 1.1.1.1')
	write_status(ret_val)
	if ret_val != 0:
		write_ln(color_str("§2ERROR: §0No network connectivity. Check your connection and try again."))
		exit(6) # 6 = Network connectivity error

# Load console font using 'setfont'
def load_font():
	global font
	if font == '' or font == 'def' or font == 'default':
		font = 'default8x16'
	if font.startswith('ter-'):
		write_msg('Installing the terminus-font package, please wait...', 1)
		ret_val = Pkg.install('terminus-font')
		write_status(ret_val)
	write_msg(f"Loading system font '{font}'...", 1)
	ret_val = Cmd.log('setfont ' + font)
	write_status(ret_val)
	if ret_val != 0:
		write_ln(color_str("§2ERROR: §0Font loading failed. Most likely cause: the specified font was not found."))
		exit(9) # 9 = Font couldn't be loaded!

# Load kb map using 'loadkeys'
def load_kbmap():
	write_msg(f"Loading system keymap '{keymap}'...", 1)
	ret_val = Cmd.log('loadkeys ' + keymap)
	write_status(ret_val)
	if ret_val != 0:
		write_ln(color_str("§2ERROR: §0Keymap loading failed. Most likely cause: the specified keymap was not found."))
		exit(10) # 10 = Keymap couldn't be loaded!

# NTP time synchronization
def ntp_setup():
	write_msg('Enabling NTP time synchronization...', 1)
	ret_val = Cmd.log('timedatectl set-ntp true')
	write_status(ret_val, 0, 4)

# Disk partitioning

def partition(tool_to_use=''):
	Cmd.exec(f"echo && {lsblk_cmd} && echo")
	tool_defined = len(tool_to_use) > 0
	if tool_defined:
		write_msg('Device to partition (e.g. ')
	else:
		write_msg(color_str('Partitioning command line (e.g. §4fdisk §7/dev/'))
	write(color_str("§7sda§0) §7>> "))
	in_cmd = ''
	in_cmd = input().strip().lower()
	if len(in_cmd) > 0:
		if tool_defined:
			Cmd.exec(f"{tool_to_use} /dev/{in_cmd}")
		else:
			Cmd.exec(in_cmd)

def sel_par_tool(hide_guide=False):
	if not hide_guide:
		# TODO Improve this
		# Enter 'G' to partition using cgdisk (recommended for UEFI)
		# Enter 'F' to partition using cfdisk (recommended for BIOS/CSM)
		write_ln(color_str("   Enter '§3%s§0' to partition using §3%s §0(recommended for %s)" % ("G" if boot_mode == "UEFI" else "F", "cgdisk" if boot_mode == "UEFI" else "cfdisk", boot_mode)))
		write_ln(color_str("   Enter '§4%s§0' to partition using §4%s §0(recommended for %s)" % ("F" if boot_mode == "UEFI" else "G", "cfdisk" if boot_mode == "UEFI" else "cgdisk", "BIOS/CSM" if boot_mode == "UEFI" else "UEFI")))
		# TODO Add partition listing options e.g. lsblk, blkid, fdisk -l
		write_ln(color_str("   Enter '§7O§0' to partition using §7something else"), 2)

	# '>> Selection (C/F/G/O) >> '
	write_msg('Selection (')

	# TODO Improve this
	if boot_mode == 'UEFI':
		write(color_str('§3G§0/§4F'))
	else:
		write(color_str('§3F§0/§4G'))

	write(color_str('/§7O§0) §7>> '))

	# TODO Fix output showing lsblk when empty (running partition() somehow)?
	sel = ''
	sel = input().strip().upper()
	if len(sel) > 0:
		if sel == 'G':
			partition('cgdisk')
		elif sel == 'F':
			partition('cfdisk')
		elif sel == 'O':
			partition()
		else:
			sel_par_tool(True)
		partitioning_menu()

	# TODO Don't allow to continue without having atleast 1 partition on the disk (check lsblk output lines count)

def partitioning_menu():
	global par_menu_visit_counter
	print_header('Disk Partitioning')
	middle = ' anymore' if par_menu_visit_counter > 0 else ''
	# TODO Make user type 'done' instead to continue?
	write_ln(color_str(f"   §3Tip: §0If you don't need to partition{middle}, just press ENTER"), 2)
	par_menu_visit_counter += 1
	sel_par_tool()

# Partition mounting & formatting

# Mount a partition
# e.g. 'mount_par('/dev/sda1', '/')'
def mount_par(blk_dev, mount_point='/', opts=''):
	Cmd.log(f'mkdir -p /mnt{mount_point}')
	opts = ' -o ' + opts if len(opts) > 0 else ''
	return Cmd.log(f'mount{opts} {blk_dev} /mnt{mount_point}')

def par_opt_handler(opt):
	global mbr_grub_dev

	# Option validity checks
	# TODO Fully disallow mounted selections to be chosen in mounting menu! (e.g. /,/efi,swap etc)
	if len(opt) != 1:
		list_used_pars(True)
	if opt == 'E' and boot_mode != 'UEFI':
		list_used_pars(True)
	if opt != 'B' and opt != 'R' and opt != 'E' and opt != 'H' and opt != 'S' and opt != 'C' and opt != 'O':
		list_used_pars(True)

	lsblk = Cmd.output(f"{lsblk_cmd} | grep -v '/' | grep -i -v 'swap'")

	# TODO Improve check
	if lsblk.count('\n') <= 2:
		write_ln()
		write_msg('Mounting cancelled since there are no devices to mount.', 4)
		write('\nPress ENTER to continue...')
		input()
		mounting_menu()

	write_ln(f"\n{lsblk}")

	purpose = opt.replace('B', '/boot').replace('R', '/').replace('E', '/efi').replace('H', '/home').replace('S', 'swap').replace('O', 'other purpose').replace('C', 'package cache')
	write_msg(color_str(f'Which partition would you like to use for §3{purpose} §0(e.g. '))
	if opt == 'O':
		write(color_str('§7/dev/'))
	write(color_str('§7sda1§0)? §7>> '))
	par = ''
	par = input().strip().lower() # sda1
	# TODO Check if input device is ACTUALLY valid
	if len(par) < 3: # 4?
		mounting_menu()
	if '/' not in par:
		par = '/dev/' + par # Make proper form, e.g. '/dev/sda1'

	# TODO Improve formatting in this function

	# e.g. 'Would you like to format /dev/sda1 for / using ext4 (y/N)? >> '
	#      'Would you like to format /dev/sda2 for swap usage (y/N)? >> '
	#      'Would you like to use /dev/sda3 for other purpose (y/N)? >> '
	#if format_par == -1:
	write_msg(color_str(f'Would you like to §2format §7{par} §0(§2y§0/§3N§0)? §7>> '))
	ans = ''
	ans = input().upper().replace('YES', 'Y')
	#elif format_par == 1:
	#	ans = 'Y'
	#else:
	#	ans = 'n'

	# TODO Add RAID support etc.

	pause = False # Pause at end of formatting & mounting?
	fs_type = 'swap' if opt == 'S' else ''

	# Format...
	if ans == 'Y':
		# TODO Add other as fs type & custom format commands etc
		format_args = {
				#'btrfs':    '-f',
				#'exfat':    '-i', # -i id -n label
				'fat':      '-F32 -s2', # -i -n label
				'reiserfs': '-f', # -u -l label
				'ntfs':     '-F -Q', # -U -L label
				'xfs':      '-f', # -L label
		}
		if opt == 'E': # efi
			fs_type = 'fat'
		elif opt == 'S': # swap
			fs_type = 'swap'
		else: # other
			write_ln(color_str('§7>> §0All available supported §3filesystem types§0:'), 2)
			# TODO Add other as fs type & custom format commands etc
			# [ 'Btrfs', ...
			supported_fs_types = [ 'ext4', 'exFAT', 'FAT32', 'NTFS', 'ReiserFS', 'swap', 'XFS' ]
			for fs_type in supported_fs_types:
				write_ln(color_str(f'   §3{fs_type}'))
			write_ln()

			# '{2}this is in red {0}back to default'
			write(color_str(f'§7>> §0Which §3filesystem type §0would you like to format §7{par} §0with (e.g. §3ext4§0)? §7>> '))
			fs_type = input().strip().lower() # e.g. 'ext4'
			if len(fs_type) < 3 or fs_type not in [x.lower() for x in supported_fs_types]:
				mounting_menu()

			fs_type = fs_type.replace('fat32', 'fat')

		# TODO Use '-L Arch Linux' on ext4 / par etc.
		format_cmd = (f'mkfs.{fs_type}') if fs_type != 'swap' else 'mkswap' # e.g. 'mkfs.ext4', 'mkswap'
		if fs_type in format_args:
			format_cmd += ' ' + format_args.get(fs_type)

		write_ln()
		write_msg(f'Formatting {par} using {fs_type}...', 1)
		# TODO Add custom labels for / 'Arch Linux' etc
		format_cmd += ' -n ESP' if opt == 'E' else ''
		ret_val = Cmd.log(f"{format_cmd} {par}") # e.g. 'mkfs.ext4 /dev/sda1'
		write_status(ret_val)
		if ret_val != 0:
			pause = True

		# TODO Btrfs: create subvolume, __snapshot etc.
		# TODO Add LUKS disk encryption support

	# Mounting
	if not pause:
		if fs_type != 'swap':
			#if ans != 'Y': write_ln()
			if opt == 'O':
				write_ln()
				write_msg(color_str(f'Where would you like to mount §7{par} §0in the new system (e.g. §3/var§0)? §7>> '))
				mp = ''
				mp = input().strip().lower() # e.g. '/var'
				write_ln()
			elif opt == 'R': mp = '/'
			elif opt == 'B': mp = '/boot'
			elif opt == 'H': mp = '/home'
			elif opt == 'C':
				mp = '/pkgcache'
			else: mp = '/efi'

			# TODO Prevent mounting to / when using NTFS etc.
			if len(mp) > 0 and mp.startswith('/'): # Assume proper path
				# TODO Don't add new line if not formatted
				write_ln()
				write_msg(color_str('Other §4optional §0mount options (e.g. §7noatime,nofail§0) >> '))
				opts = ''
				opts = input().strip().replace(' ', '') # e.g. 'noatime,nofail'
				write_ln()
				write_msg(f'Mounting {par} to {mp}...', 1)
				ret_val = mount_par(par, mp, opts) # e.g. 'mount /dev/sda1 /mnt/'
				write_status(ret_val)
				if ret_val != 0: pause = True
				elif boot_mode == 'BIOS/CSM' and ((opt == 'R' and mbr_grub_dev == '') or opt == 'B'): # Update MBR GRUB device
					if par[-1:].isdigit():
						par = par[:-1]
					mbr_grub_dev = par # e.g. '/dev/sda'
				elif mp == '/pkgcache':
					# TODO Update to support Btrfs
					write_msg('Checking partition filesystem compatability for caching...', 1)
					errors = Cmd.log('mkdir -p /mnt/pkgcache/pkgcache') # /aur
					errors += Cmd.log('touch /mnt/pkgcache/pkgcache/test-1:1.2.3.4-x86-64.pkg.tar.xz.part')
					write_status(errors)
					if errors == 0:
						Cmd.log('rm -f /mnt/pkgcache/pkgcache/test-1:1.2.3.4-x86-64.pkg.tar.xz.part')
						Cmd.log('cp /etc/pacman.conf /etc/pacman.conf.bak')
						write_msg('Enabling package cache on the partition...', 1)
						ret_val = IO.replace_ln('/etc/pacman.conf', '#CacheDir', 'CacheDir = /mnt/pkgcache/pkgcache')
						write_status(ret_val)

					if ret_val != 0:
						pause = True
						Cmd.log('mv /etc/pacman.conf.bak /etc/pacman.conf')
						Cmd.log('rm -rf /mnt/pkgcache')
						Cmd.log('umount /mnt/pkgcache')
			else:
				write_msg('Mounting cancelled due to an invalid mountpoint.', 4)
				pause = True
		else:
			write_msg(f'Enabling swap on {par}...', 1)
			ret_val = Cmd.log('swapon ' + par) # e.g. 'swapon /dev/sda1'
			write_status(ret_val)
			if ret_val != 0:
				pause = True

	if pause:
		write('\nPress ENTER to continue...')
		input()
	else:
		time.sleep(0.15)

def write_par_mount(key='E', mount='/efi', device='/dev/sda1', condition=False, max_len=9, start_space_count=6):
	if key == '':
		key = '    '
	write(' ' * start_space_count)
	write(f'{key}   {mount}')
	if condition:
		mount_len = len(mount)
		if mount_len < max_len:
			write(' ' * (max_len - mount_len))
		if device == '' and len(mounts) > 0:
			split_mounts = mounts.split(',')
			for entry in split_mounts:       # e.g. '/efi:/dev/sda1'
				split_entry = entry.split(':') # e.g. '/efi', '/dev/sda1'
				mount_compare = split_entry[0] # eg. '/efi'
				if mount_compare == 'root':
					mount_compare = '/'

				if mount == mount_compare:
					device = split_entry[1]
					break
			if device == '':
				device = '/dev/null'
				log(f"[setup.py:write_par_mount()] WARN: Mountpoint not found for mount '{mount}' on device '{device}', showing /dev/null instead...")
				log(f"Mounts: '{mounts}'")
		action = 'mounted as' if key != 'S' else 'enabled on'
		write(color_str(f' §3({action} §7{device}§3)'))
	write_ln()

def list_used_pars(hide_guide=False):
	global mounts, mount_menu_visit_counter
	mounts = ''
	other_mounts = ''

	# TODO Improve this
	# WARN Mounting anything to a mount point ending in 'root' is forbidden
	tmp_mounts = Cmd.output("lsblk -n -o NAME,MOUNTPOINT | grep -v '^loop' | grep -v '^sr0'") # | grep /
	for line in tmp_mounts.split('\n'):
		# TODO Only do if not starting with an alphabet char
		dev = line.split(' ')[0][2:]          # e.g. 'sda2'
		if '[SWAP]' in line:                  # Swap enabled
			mounts += f'swap:/dev/{dev},'       # e.g. 'swap:/dev/sda2,'
		elif '/mnt' in line:
			if line.count('/') == 1:            # Root mounted
				mounts += f'root:/dev/{dev},'     # e.g. 'root:/dev/sda3,'
			elif line.count('/') > 1:           # Other mounts
				mount = line.split('/', 1)[1][3:] # e.g. '/efi'
				entry = (f'{mount}:/dev/{dev},')  # e.g. '/efi:/dev/sda1,'
				if mount == '/efi' or mount == '/boot' or mount == '/home' or mount == '/pkgcache':
					mounts += entry
				else:
					other_mounts += entry

	if 'root:' not in mounts:
		mount_menu_visit_counter = 0

	#write_msg('Mounts: ' + mounts + '\n')
	#write_msg('Other:  ' + other_mounts + '\n\n')

	if not hide_guide:
		write_ln(color_str('   The following partitions are §2mandatory§0:'), 2)
		write_par_mount('R', '/', '', ('root:' in mounts))
		if boot_mode == 'UEFI':
			write_par_mount('E', '/efi', '', ('/efi:' in mounts))

		write_ln('\n' + color_str('   §4Optional §0partitions include:'), 2)
		write_par_mount('B', '/boot', '', ('/boot:' in mounts))
		write_par_mount('H', '/home', '', ('/home:' in mounts))
		write_par_mount('C', '/pkgcache', '', ('/pkgcache:' in mounts))
		write_par_mount('S', 'swap', '', ('swap:' in mounts))
		write_ln('      O   other')
		# TODO Improve output formatting
		if 'root:' in mounts and len(other_mounts) > 0: # Other mounts found => List them
			split_mounts = other_mounts.split(',') # e.g. '/root:/dev/sda2', '/efi:/dev/sda1'
			for entry in split_mounts:             # e.g. '/efi:/dev/sda1'
				if len(entry) > 0:
					split_entry = entry.split(':')     # e.g. '/efi', '/dev/sda1'
					try:
						write_par_mount('', split_entry[0], split_entry[1], True, 7, 3)
					except:
						log(f"[setup.py:list_used_pars()] WARN: Couldn't display other mount entry '{entry}'")

		#start = '\n' if len(other_mounts) != 0 else ''
		# %s % start
		write_ln('\n   In case a partition needs to be further identified:', 2)
		write_ln('      L   lsblk')
		write_ln('      I   blkid')
		write_ln('      F   fdisk -l', 2)

	# '>> Selection (B/E/R/H/S/O/L/I/F) >> '
	write_msg('Selection (')
	if 'root:' not in mounts:
		write('R/')
	if boot_mode == 'UEFI' and '/efi:' not in mounts:
		write('E/')
	if '/boot:' not in mounts:
		write('B/')
	if '/home:' not in mounts:
		write('H/')
	if '/pkgcache:' not in mounts:
		write('C/')
	if 'swap:' not in mounts:
		write('S/')
	write(color_str('O/L/I/F) §7>> '))

	# TODO Optionally allow to use /boot instead of /efi on UEFI systems

	sel = ''
	sel = input().strip().upper()
	if len(sel) > 0:
		# Partition identification
		if sel == 'L' or sel == 'I' or sel == 'F':
			command = lsblk_cmd
			if sel == 'I':
				command = blkid_cmd
			elif sel == 'F':       # 'DEV    TYPE       SIZE MOUNT'
				# TODO Strip /dev/loop0 entry from 'fdisk -l' ouput
				command = 'fdisk -l' # lsblk -n -o NAME,FSTYPE,SIZE,MOUNTPOINT
			write_ln()
			Cmd.exec(command)
			write('\nPress ENTER to continue...')
			input()
		else:
			if 'root:' not in mounts and not (sel == 'R' or sel == 'S' or sel == 'O'):
				write_ln('\n' + color_str('§2ERROR: §0Please mount a root partition before continuing!'))
				write('\nPress ENTER to continue...')
				input()
			else:
				# TODO Don't allow selections that are already mounted!! (e.g. /,/efi,swap etc)
				par_opt_handler(sel)
		#input()
		mounting_menu()

	if 'root:' not in mounts:
		# TODO Message?
		mounting_menu()
	if boot_mode == 'UEFI' and '/efi:' not in mounts:
		write_ln()
		write_msg(color_str('Would you like to continue without mounting a §3/efi §7partition §0(§2y§0/§3N§0)? §7>> '))
		ans = ''
		ans = input().upper().replace('YES', 'Y')
		if ans != 'Y':
			mounting_menu()

def mounting_menu():
	global mount_menu_visit_counter
	print_header('Mounting Partitions')
	write_ln('   Select an option by pressing the corresponding key.')
	write(color_str("   §3Tip: §0If you don't need to mount partitions"))
	if mount_menu_visit_counter > 0:
		write(' anymore')
	mount_menu_visit_counter += 1
	# TODO Make user type 'done' instead to continue?
	write_ln(color_str(', just press ENTER'), 2)
	list_used_pars()

# Mirrorlist sorting

def sort_mirrors():
	write_msg('Fetching reflector for mirrorlist sorting...', 1)
	ret_val = Pkg.install('reflector')
	write_status(ret_val)

	if ret_val == 0:
		write_msg('Creating a backup of the local mirrorlist file...', 1)
		ret_val = Cmd.log('mv /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak')
		write_status(ret_val)

		write_msg('Sorting mirrors using reflector, please wait...', 1)
		ret_val = Cmd.log('reflector --verbose --sort rate --number 25 --fastest 10 --age 24 --protocol https --save /etc/pacman.d/mirrorlist')
		write_status(ret_val)

		# TODO Setup pacman hook to update later in chroot
		Cmd.log('cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.reflector')

		write_msg('Refreshing pacman package databases...', 1)
		ret_val = Pkg.refresh_dbs() # TODO No need for 'True' ?
		write_status(ret_val)
		time.sleep(0.25)
	# else: TODO Update 'pacman-mirrorlist' pkg instead

# Base system install

# TODO Use global sys_root variable in the future
# TODO Fix systemd messages appearing on screen about microcode on real hardware
def base_install(sys_root = '/mnt/'):
	ps_args, extra_pkgs = ('', '')

	extra_pkgs += 'sudo ' if len(users) > 0 else ''
	extra_pkgs += f'{base_pkgs} ' if len(base_pkgs) > 0 else ''
	extra_pkgs += 'terminus-font ' if font.startswith('ter-') else ''
	# Userspace utilities for filesystems
	blkid = Cmd.output(blkid_cmd)
	extra_pkgs += 'exfat-utils ' if '"exfat"' in blkid else ''
	extra_pkgs += 'ntfs-3g ' if '"ntfs"' in blkid else ''
	extra_pkgs = f' {extra_pkgs.rstrip()}' if len(extra_pkgs) > 0 else ''

	# TODO Check pkgcache another way
	cache_arg = '-c ' if os.path.exists(sys_root + 'pkgcache') else ''

	ps_args = f'{cache_arg}{sys_root} base python{extra_pkgs}'

	write_msg('Installing base system using pacstrap, please wait...', 1)
	# TODO Report on progress
	ret_val = Cmd.log('pacstrap ' + ps_args)
	write_status(ret_val)
	if ret_val != 0: # Base install failure
		write_ln(color_str('§2ERROR: §0Base system install failed. Check /tmp/setup.log for the details.'))
		exit(11) # 11 = Base system install failure

	# Umount cache device (most likely external) to avoid adding to fstab
	if os.path.exists(sys_root + 'pkgcache'):
		Cmd.log(f'umount {sys_root}pkgcache') # e.g. 'umount /mnt/pkgcache'

	write_msg('Generating static filesystem table...', 1)
	# TODO Format properly otherwise (no repeating)
	ret_val = Cmd.exec(f'genfstab -U {sys_root} >>{sys_root}etc/fstab')
	write_status(ret_val)

	# Remount cache device if specified
	if '/pkgcache:' in mounts:
		cache_dev = mounts.split('/pkgcache:')[1][:-1] # e.g. '/dev/sdb1'
		Cmd.log(f'mount {cache_dev} {sys_root}pkgcache')

# Continue setup in chroot...

# TODO Use global sys_root variable in the future
def start_chroot(sys_root = '/mnt/'):
	Cmd.suppress(f'cp /proc/cpuinfo {sys_root}proc/') # For CPU detection in chroot

	if multibooting:
		Cmd.suppress(f'mkdir {sys_root}hostrun')
		Cmd.suppress('mount --bind /run {sys_root}hostrun')

	ret_val = IO.write(f'{sys_root}etc/vconsole.conf', f'KEYMAP="{keymap}"\nFONT="{font}"')
	if ret_val != 0:
		log(f"[setup.py:start_chroot()] WARN: Couldn't set persistent keymap ({keymap}) & font ({font}) in '{sys_root}etc/vconsole.conf'")

	Cmd.log(f'cp "{script_path}" "{sys_root}root/"')           # e.g. 'cp "/root/setup.py" "/mnt/root/"'
	Cmd.log(f'chmod 755 {sys_root}root/{script_fn}')           # e.g. 'chmod 755 /mnt/root/setup.py'
	Cmd.log(f'cp "{script_root}/config.py" "{sys_root}root/"') # e.g. 'cp "/root/config.py" "/mnt/root/"'

	log("\n#\n# Start of chroot log\n#")
	Cmd.suppress(f'cp /tmp/setup.log {sys_root}') # Copy log over to chroot
	Cmd.suppress(f'ln -sf {sys_root}setup.log /tmp/setup.log')
	# TODO Check if it works?

	write_msg('Chrooting into the new install...', 1)
	ch_args = f' {mbr_grub_dev}' if len(mbr_grub_dev) > 0 else ''  # Pass grub device to script
	Cmd.exec(f'arch-chroot {sys_root} /root/{script_fn}{ch_args}') # e.g. 'arch-chroot /mnt/ /root/setup.py'

# Chroot specific install steps

def load_hw_info():
	global cpu_type, mbr_grub_dev, bat_present, disc_tray_present, bt_present, vm_env

	# CPU type needed for ucode
	cpu_type = 'intel' if Cmd.suppress('cat /proc/cpuinfo | grep -i GenuineIntel') == 0 else 'amd'

	if len(sys.argv) == 2: # Assume MBR grub dev e.g. '/dev/sda4'
		mbr_grub_dev = sys.argv[1]

	# Update battery presence
	ret_val = Cmd.suppress('ls /sys/class/power_supply | grep -i bat')
	bat_present = (ret_val == 0)

	# Update disc tray presence
	blkid = Cmd.output("blkid")
	disc_tray_present = ('/dev/sr' in blkid or '/dev/sg' in blkid)
	if not disc_tray_present: # Try other alternative methods
		ret_val = Cmd.log("dmesg | egrep -i 'cdrom|dvd|cd/rw|writer'")
		disc_tray_present = (ret_val == 0)
	# Update floppy disk drive presence
	fdd_present = ('/dev/fd' in blkid)

	Cmd.log('update-pciids')

	# Update Bluetooth device presence
	# TODO Check for false-positives
	bt_present = Cmd.log('rfkill list | grep -i blue') == 0
	if not bt_present:
		bt_f1 = Cmd.log('dmesg | grep -i blue') == 0
		bt_f2 = Cmd.log('lsusb | grep -i blue') == 0 # TODO Improve USB BT adapter detection
		bt_f3 = Cmd.log('lspci | grep -i blue') == 0
		bt_present = bt_f1 or bt_f2 or bt_f3

	# Update virtualized state
	ret_val = Cmd.suppress('cat /proc/cpuinfo | grep hypervisor')
	if ret_val == 0:
		vm_env = 'other'
		# Try & identify the VM platform
		try:
			board_name = IO.read_ln('/sys/devices/virtual/dmi/id/board_name').rstrip() # e.g. 'VirtualBox'
			if board_name == 'VirtualBox':
				vm_env = 'vbox'
			else:
				prod_name = IO.read_ln('/sys/devices/virtual/dmi/id/product_name').rstrip() # e.g. 'VMware7,1'
				if prod_name.startswith('VMware'):
					vm_env = 'vmware'
		except:
			pass



def timezone_setup():
	write_msg('Settings datetime & timezone settings...', 1)
	ret_val = Cmd.log(f'ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime')
	# TODO Find a better way to use the variable 'use_localtime'
	timescale = 'localtime' if use_localtime else 'utc'
	Cmd.log(f'hwclock --systohc --{timescale}')
	Cmd.log('timedatectl set-local-rtc ' + '0' if timescale == 'utc' else '1')
	write_status(ret_val)
	if ret_val != 0:
		log(f"[setup.py:timezone_setup()] ERROR: Couldn't set timezone as '{timezone}'. Most likely cause: invalid timezone")

def locale_setup():
	Cmd.log('cp /etc/locale.gen /etc/locale.gen.bak')

	# /etc/locale.conf
	for locale in locales.split(','): # e.g. ' en_US ','fi_FI'
		locale = locale.strip() # e.g. ' en_US ' => 'en_US'
		found = False
		# Assume UTF-8 locale
		if '.' not in locale or ' ' not in locale or '-' not in locale:
			write_msg(f"Finding matching UTF-8 locale for '{locale}' in /etc/locale.gen...", 1)
			list = [ f'{locale}.UTF-8', f'{locale} UTF-8' ]
			for lng in list:
				ret_val = IO.uncomment_ln('/etc/locale.gen', lng)
				if ret_val == 0:
					found = True
					break
			write_status(0 if found else 1)

		# UTF-8 locale not found OR full locale definition
		if not found:
			write_msg(f"Finding any matching locale for '{locale}' in /etc/locale.gen...", 1)
			# TODO Return uncommented line & use for future purposes
			ret_val = IO.uncomment_ln('/etc/locale.gen', locale)
			write_status(ret_val)
			if ret_val != 0:
				log(f"[setup.py:locale_setup()] WARN: Couldn't find locale '{locale}' in /etc/locale.gen")

	write_msg('Generating chosen locales, please wait...', 1)
	ret_val = Cmd.log('locale-gen')
	write_status(ret_val)

	write_msg('Creating /etc/locale.conf...', 1)

	# TODO Expect '.UTF-8' locale IF no '.' in locale definition string

	# /etc/locale.conf
	locale_conf = ''
	if len(LANG) > 0:       # Main system locale used e.g. 'en_US.UTF-8'
		locale_conf += f'LANG={LANG}\n'
	if len(LANGUAGE) > 0:   # Fallback language ordered list e.g. 'en_AU:en_GB:en'
		locale_conf += f'LANGUAGE={LANGUAGE}\n'
	if len(locale_conf) > 0: locale_conf += '\n'
	if len(LC_COLLATE) > 0: # Locale for sorting and regular expressions e.g. 'C'
		locale_conf += f'LC_COLLATE={LC_COLLATE}\n'
	if len(LC_ALL) > 0:     # Locale used for other localized UI content e.g. 'en_US.UTF-8'
		locale_conf += 'LC_ADDRESS=§\nLC_IDENTIFICATION=§\nLC_MEASUREMENT=§\nLC_MONETARY=§\nLC_NAME=§\nLC_NUMERIC=§\nLC_PAPER=§\nLC_TELEPHONE=§\nLC_TIME=§'.replace('§', LC_ALL)

	log(f'\n/etc/locale.conf\n================\n{locale_conf}\n================\n')

	if len(locale_conf) > 0:
		ret_val = IO.write('/etc/locale.conf', locale_conf)
		write_status(ret_val)
		if ret_val != 0:
			log("[setup.py:locale_setup()] ERROR: Locale conf couldn't be written!")

# TODO Finish up, find workaround for adding rules
def ufw_setup():
	write_msg('Setting up uncomplicated firewall...', 1)
	errors = Pkg.install('ufw')
	#errors += Cmd.log('systemctl enable ufw')
	# TODO Need to run '# ufw enable' as well
	write_status(errors)

	#write_msg("Setting up basic ufw rules...", 1)
	#errors = Cmd.log('ufw default deny')

	# TODO Cannot add rules in chroot: find a workaround?

	# TODO Make work for IPv6 too? '2001:db8::/32'
	#ipv6 = ':' in out
	#out = Cmd.output('ip a | grep global').split('\n')[0].split(' ')[5] # e.g. '192.168.1.108/24'
	#start = out.rsplit('.', 1)[0] # e.g. '192.168.1'
	#mask = out.rsplit('/', 1)[1]  # e.g. '24'
	#cidr = '%s.0/%s' % (start, mask) # e.g. '192.168.1.0/24'
	#errors += Cmd.log('ufw allow from %s' % cidr)

	#if ssh_server_type > 0:
	#	errors += Cmd.log('ufw limit SSH')

	#if web_server_type > 0:
	#	errors += Cmd.log('ufw allow HTTP')
	#	errors += Cmd.log('ufw allow HTTPS')

	# TODO Allow more services once instlalled e.g. 'KTorrent' on KDE DE etc

	#write_status(errors)

def networking_setup():
	global hostname
	# Generate hostname based on motherboard model
	if hostname == '':
		hostname = 'Arch-'
		if vm_env != 'vmware':
			try:
				hostname += IO.read_ln('/sys/devices/virtual/dmi/id/board_name').rstrip() # e.g. 'Z270N-WIFI'
			except:
				if len(vm_env) > 0:
					hostname += IO.read_ln('/sys/devices/virtual/dmi/id/chassis_vendor').rstrip() # e.g. 'QEMU'
				else:
					hostname += str(random.randint(1000, 9999)) # e.g. '3980'
		else:
			hostname += 'VMware'

	# /etc/hostname
	write_msg(f"Setting hostname as '{hostname}'...", 1)
	ret_val = IO.write('/etc/hostname', hostname)
	log(f"[setup.py:networking_setup()] INFO: Hostname set as '{hostname}'")
	write_status(ret_val)

	# /etc/hosts
	write_msg("Generating hosts file...", 1)
  # TODO Proper formatting
	hosts = '# hosts - static table lookup for hostnames\n127.0.0.1	localhost\n::1		localhost\n127.0.1.1	§.localdomain	§'.replace('§', hostname)
	ret_val = IO.write('/etc/hosts', hosts)
	log(f'\n/etc/hosts\n==========\n{hosts}\n==========')
	write_status(ret_val)

	# NetworkManager
	write_msg("Setting up NetworkManager, please wait...", 1)
	errors = Pkg.install('networkmanager')
	errors += Cmd.log('systemctl enable NetworkManager')
	Cmd.suppress('shopt -s xpg_echo')
	# TODO Fix
	Cmd.exec('echo "polkit.addRule(function(action, subject) {\n\tif (action.id.indexOf("org.freedesktop.NetworkManager.") == 0 && subject.isInGroup("network")) {\n\t\treturn polkit.Result.YES;\n\t}\n});" >/etc/polkit-1/rules.d/50-org.freedesktop.NetworkManager.rules')
	write_status(errors)

	if enable_firewall:
		ufw_setup()

def aur_setup():
	write_msg('Installing dependencies for AUR support, please wait...', 1)
	ret_val = Pkg.install('base-devel git')
	write_status(ret_val)
	if ret_val == 0: # Git install successfull
		write_msg('Setting up temporary aurhelper user...', 1)
		errors = Cmd.log('useradd -m -g users -G wheel aurhelper')
		errors += Cmd.suppress('cp /etc/sudoers /etc/sudoers.bak')
		# TODO Create an actual replace by line number function
		# Give wheel group users sudo permission w/o pass
		Cmd.suppress("chmod 770 /etc/sudoers")
		errors += Cmd.exec("sed -i '85 s/^# //' /etc/sudoers") # > /etc/sudoers.tmp
		#errors += Cmd.suppress('mv /etc/sudoers.tmp /etc/sudoers')
		errors += Cmd.suppress('chmod 440 /etc/sudoers')
		write_status(errors)

		write_msg('Fetching & installing yay from the AUR, please wait...', 1)
		# TODO Cache yay build if cachedir found?
		ret_val = Cmd.log('$ cd /tmp && git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin && makepkg -sric --skippgpcheck --noconfirm --needed', 'aurhelper')
		write_status(ret_val)
		if ret_val == 0: # Yay install successfull
			Cmd.log('rm -rf /tmp/yay-bin') # Delete old build dir

			# Allow access to pkgcache AUR builddir
			#if os.path.exists('/pkgcache'):
				#Cmd.log('find /pkgcache/pkgcache/aur/ -name "*.lock" -type f -delete')
				#Cmd.log('chown aurhelper:users /pkgcache/pkgcache/aur/')
				#Cmd.log('chmod 777 /pkgcache/pkgcache/aur/') # 770

			# Optimize makepkg for building on all CPU cores
			# TODO Other makepkg.conf optimizations
			IO.replace_ln('/etc/makepkg.conf', '#MAKEFLAGS="', 'MAKEFLAGS="-j$(nproc)"')

def user_setup():
	# TODO https://www.reddit.com/r/openSUSE/comments/5pnaat/is_there_any_way_to_prevent_polkit_from_asking/
	errors = 0
	write_msg("Setting up all local user accounts...", 1)

	Cmd.log('cp /etc/sudoers /etc/sudoers.orig')
	Cmd.log("chmod 770 /etc/sudoers")

	if len(restricted_users) > 0:
		Cmd.log('groupadd -f restricted')

	if len(passwdless_users) > 0:
		#Cmd.log('groupadd -f nopasswdlogin')
		Cmd.log('groupadd -f sudo')
		# TODO Replace with a proper function
		# Give sudo group users sudo permission w/o pass
		# TODO Check if '%' causes issues?
		Cmd.log('sed -i "89s/.*/\\n## Allow members of group sudo to execute any commmand without a password\\n\%sudo ALL=(ALL) NOPASSWD: ALL\\n/" /etc/sudoers')

	for user in users.split(','):
		# TODO Make 'is_restricted()' etc. extended functions of string?
		restricted = User.is_restricted(user)
		passwdless = User.is_passwdless(user)
		add_args = 'restricted' if restricted else 'users -G wheel,storage,log,input,rfkill,network'
		errors += Cmd.log(f'useradd -m -g {add_args} {user}')

		if not restricted: # Add some more groups
			if xorg_install_type != 0: Cmd.log(f'gpasswd -a {user} video')
			# Allow user full access to media (e.g. mounting)
			if disc_tray_present: Cmd.log(f'gpasswd -a {user} optical')
			if fdd_present: Cmd.log(f'gpasswd -a {user} floppy')
			if web_server_type > 0: Cmd.log(f'gpasswd -a {user} http')
			# TODO Printing & scanning setup, user groups: 'scanner sys lp'
			if passwdless:
				Cmd.log(f'gpasswd -a {user} sudo')

		if passwdless: # Allow logging in without password
			pass
			#Cmd.log(f'gpasswd -a {user} nopasswdlogin')

			# TODO Figure out a way to bypass polkit (or use another user for pass; root?)
			# TODO Remove password later (instead of asking for it at the end) using 'sudo passwd -d $passwdless_user'

	write_status(errors)

	Cmd.log("chmod 440 /etc/sudoers")
	Cmd.log('cp /etc/sudoers /etc/sudoers.bak')

def multilib_setup():
	write_msg('Including multilib repo in /etc/pacman.conf...', 1)
	Cmd.suppress('cp /etc/pacman.conf /etc/pacman.conf.bak')
	ln = IO.get_ln_number('/etc/pacman.conf', '#[multilib]') # should be ~93
	if ln != -1:
		# "[multilib]"
		Cmd.log('chmod 770 /etc/pacman.conf')
		errors = Cmd.exec(f'sed -i "{ln} s/^#//" /etc/pacman.conf')
		# "Include = /etc/pacman.conf.d/mirrorlist"
		errors += Cmd.exec(f'sed -i "{ln+1} s/^#//" /etc/pacman.conf')
		Cmd.log('chmod 644 /etc/pacman.conf')
		write_status(errors)

		if errors == 0:
			write_msg('Refreshing pacman package databases...', 1)
			ret_val = Pkg.refresh_dbs()
			write_status(ret_val)
		else:
			Cmd.suppress('cp /etc/pacman.conf.bak /etc/pacman.conf')
	else:
		write_status(1)

def sshd_setup():
	write_msg('Setting up OpenSSH server...', 1)
	ret_val = Pkg.install('openssh')
	write_status(ret_val)

	if ssh_server_type == 2:
		Cmd.log('systemctl enable sshd.service')
	else:
		Cmd.log('systemctl enable sshd.socket')

def lts_kernel_setup():
	write_msg('Switching to the Linux LTS kernel, please wait...', 1)
	# TODO Don't remove 'linux' package?
	errors = Pkg.remove('linux')
	errors += Pkg.install('linux-lts')
	write_status(errors)

def bootloader_setup():
	# TODO Systemd-boot alternative to GRUB?
	write_msg('Fetching dependencies for the GRUB bootloader...', 1)
	pkgs = 'grub dosfstools'
	pkgs += '' if len(vm_env) > 0 else f' {cpu_type}-ucode'
	ret_val = Pkg.install(pkgs)
	write_status(ret_val)

	write_msg(f'Installing GRUB in {boot_mode} mode, please wait...', 1)
	if boot_mode == 'UEFI':
		errors = Pkg.install('efibootmgr')
		errors += Cmd.log('grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id="Arch-GRUB"')
		write_status(errors)
	else: # BIOS/CSM
		ret_val = Cmd.log(f'grub-install --recheck {mbr_grub_dev}')
		write_status(ret_val)

	write_msg('Creating initial GRUB config, please wait...', 1)
	ret_val = Cmd.log('grub-mkconfig -o /boot/grub/grub.cfg')
	write_status(ret_val)

def x_setup():
	mid = 'minimal' if xorg_install_type == 1 else 'the'
	write_msg(f'Installing {mid} X display server components...', 1)
	pkgs = 'xorg' if xorg_install_type == 2 else 'xorg-server xorg-xinit xf86-input-libinput'
	pkgs += ' xf86-input-vmmouse' if vm_env == 'vmware' else ''
	ret_val = Pkg.install(pkgs)
	write_status(ret_val)

def vm_setup():
	write_msg(f'Setting up virtualization tools for {vm_env} guest...', 1)
	errors = Pkg.install('sshfs')

	# TODO Also handle in user_setup() ?
	# TODO Turn into a function, changeable users int to select all,unrestricted etc. users?
	unres_users = User.get_unrestricted_users()

	# TODO Check vbox shares
	if vm_env == 'vbox':
		pkgs = 'virtualbox-guest-modules-arch virtualbox-guest-utils' + ('-nox ' if xorg_install_type == 0 else '')
		errors += Pkg.install(pkgs)
		errors += Cmd.log('systemctl enable vboxservice')
		errors += Cmd.log('modprobe -a vboxguest vboxsf vboxvideo')
		# TODO execute VBoxClient-all when X is enabled?

		# TODO Check if path is correct & works?
		Cmd.log('mkdir -p /media')
		Cmd.log('chmod 770 /media') # 755
		Cmd.log('chown root:vboxsf /media')
		if len(unres_users) > 0:
			for user in unres_users:
				errors += Cmd.log(f'gpasswd -a {user} vboxsf')
	elif vm_env == 'vmware':
		# https://wiki.archlinux.org/index.php/VMware/Installing_Arch_as_a_guest#Performance_Tips
		# TODO Make mkinitcpio.conf modifications:
		# /etc/mkinitcpio.conf
		# MODULES="... vmw_balloon vmw_pvscsi vsock vmw_vsock_vmci_transport ..."
		# mkinitcpio -p linux
		errors += Pkg.install(f'linux{kernel_suffix}-headers dkms fuse gtkmm3 open-vm-tools')
		errors += Pkg.aur_install('open-vm-tools-dkms')
		errors += Cmd.log('systemctl enable vmtoolsd vmware-vmblock-fuse')
		#Cmd.log('systemctl start vmtoolsd vmware-vmblock-fuse') # errors +=
		Cmd.log('vmware-toolbox-cmd timesync enable')
		# TODO Figure out a better way to automount VMware shares
		if errors == 0:
			Cmd.log('mkdir /vmshare')
			# TODO Add a 'update-mounts' alias
			# TODO Setup proper permissions
			Cmd.log('ln -s /vmshare ~/VMShare')
			if len(unres_users) > 0:
				Cmd.log('chmod 770 /vmshare') # 777
				Cmd.log('chown root:users /vmshare')
				for user in unres_users:
					Cmd.log('$ ln -s /vmshare ~/VMShare', user)

			shares = str(Cmd.output('vmware-hgfsclient')).strip().replace(' ', '\\040') # 'VMShare\nOther\040Share'
			log(f"\n[setup.py:vm_setup()] Output of 'vmware-hgfsclient':\n'{shares}'\n")
			if len(shares) > 0:
				shares = shares.split('\n') # 'VMShare','Other\040Share'
				Cmd.exec("echo '# vmware shared folders' >>/etc/fstab")
				for share in shares:
					s_share = share.replace('\\040', ' ').strip() # Share w/ spaces
					share = s_share.replace(' ', '\\040') # Share in fstab-friendly format
					if len(share) > 0:
						Cmd.log(f"mkdir '/vmshare/{s_share}'")
						Cmd.log(f"chmod 770 '/vmshare/{s_share}'") # 777
						Cmd.log(f"chown root:users '/vmshare/{s_share}'")
						# e.g. '.host:/VMShare	/vmshare/VMShare	fuse.vmhgfs-fuse	allow_other,auto_unmount,nofail	0	0'
						Cmd.exec("echo '.host:/§	/vmshare/§	fuse.vmhgfs-fuse	allow_other,auto_unmount,nofail	0	0' >>/etc/fstab".replace('§', share))
				Cmd.exec("echo >>/etc/fstab")

	write_status(errors)

def audio_setup():
	# TODO Add plain ALSA support
	write_msg('Setting up audio support via pulseaudio...', 1)
	errors = Pkg.install('pulseaudio pulseaudio-alsa pamixer libpulse')

	# Media codecs
	# TODO Add back after gstreamer 1.15: gst-plugins-bad (broken NVDEC fixed)
	errors += Pkg.install('gst-libav gst-plugins-base gst-plugins-good gst-plugins-ugly realtime-privileges')

	# Event sounds
	errors += Pkg.install('libcanberra libcanberra-pulse libcanberra-gstreamer')
	if enable_multilib:
		errors += Pkg.install('lib32-libcanberra lib32-libcanberra-gstreamer lib32-libcanberra-pulse')

	write_status(errors)

	# TODO Also handle in user_setup() ?
	if len(users) > 0:
		for user in users.split(','):
			Cmd.log(f'gpasswd -a {user} realtime')

def bt_setup():
	# NOTE Auto-detect is imperfect => allow overriding
	# NOTE External firmware may be required for proper BT functionality e.g. BCM cards
	write_msg('Installing Bluetooth support, please wait...', 1)
	errors = Pkg.install('bluez bluez-libs bluez-utils ell')
	errors += Cmd.log('systemctl enable bluetooth')
	write_status(errors)

	# TODO Fix FAIL?
	write_msg('Installing BT audio support, please wait...', 1)
	errors = 0
	# TODO Add ALSA support
	if enable_aur:
		# Extra codecs
		Pkg.remove('pulseaudio-bluetooth') # Just to make sure no conflicts happen
		errors += Pkg.aur_install('libldac pulseaudio-modules-bt-git')
	else:
		errors += Pkg.install('pulseaudio-bluetooth')

	# Auto-enable BT on startup (TODO use tlp config on laptops)
	if not bat_present:
		errors += IO.replace_ln('/etc/bluetooth/main.conf', '#AutoEnable=false', 'AutoEnable=true')

	# Switch audio source to new sink on connection
	errors += Cmd.log('sed -i "22s/.*/\\n# automatically switch to newly-connected devices\\nload-module module-switch-on-connect\\n/" /etc/pulse/default.pa')
	write_status(errors)

def vga_setup():
	global video_drv
	write_msg('Setting up graphics card drivers, please wait...', 1)
	vga_out = Cmd.output("lspci -nn | grep '\\[03'")
	log(f'\n[setup.py:vga_setup()] Found GPUs:\n{vga_out}')
	vga_out = vga_out.lower()
	mesa_install_type = 0 # Install mesa DRI for 3D acceleration
	errors = 0

	if vm_env == '':
		# e.g. 'nvidia corporation gm204 [geforce gtx 970]'
		if 'nvidia' in vga_out:
			# Card driver detection
			fermi_gpus = [ 'gf100','gf104','gf106','gf108','gf110','gf114','gf116','gf117','gf119' ] # 390xx
			kepler_gpus = [ 'gk104','gk106','gk107','gk110','gk208','gk210','gk20a' ] # 390xx
			tesla_gpus = [ 'g80','g84','g86','g92','g94','g96','g98','gt200','gt215','gt216','gt218','mcp77','mcp78','mcp79','mcp7a','mcp89' ] # 340xx
			unsupported_gpus = [ 'nv1a','nv1f','g70','g71','g72','g73','nv44a','c51','mcp61','mcp67','mcp68','mcp73' ] # noveau
			for x in range(10, 45): # nv10-nv44
				unsupported_gpus.append(f'nv{x}')
			card = 'S' # S = supported, F = fermi, kK = keppler, T = tesla, U = unsupported
			for gpu in fermi_gpus:
				if gpu in vga_out:
					card = 'F'
					break
			if card == 'S':
				for gpu in kepler_gpus:
					if gpu in vga_out:
						card = 'K'
						break
				if card == 'S':
					for gpu in tesla_gpus:
						if gpu in vga_out:
							card = 'T'
							break
					if card == 'S':
						for gpu in unsupported_gpus:
							if gpu in vga_out:
								card = 'U'
								break
			log(f"\n[setup.py:vga_setup()] Detected NVIDIA card type: '{card}'\n")

			# TODO Remove /etc/X11/xorg.conf and other discrete configs?
			# Bumblebee driver for NVIDIA Optimus systems
			if 'intel' in vga_out:
				mesa_install_type = 1
				video_drv = 'bumblebee'
				errors += Pkg.install('bumblebee xf86-video-intel')

				unres_users = User.get_unrestricted_users()
				if len(unres_users) > 0:
					for user in unres_users:
						errors += Cmd.log(f'gpasswd -a {user} bumblebee')

				errors += Cmd.log('systemctl enable bumblebeed')
				if enable_multilib:
					errors += Pkg.install('lib32-virtualgl')

			# TODO Check if matching works
			if card == 'F' or card == 'K':
				# nvidia-390xx, NVIDIA cards from around 2010-2011
				video_drv += ('' if video_drv == '' else '-') + 'nvidia-390'
				errors += Pkg.install(f'nvidia-390xx{kernel_suffix} nvidia-390xx-utils nvidia-390xx-settings')
				if enable_multilib:
					errors += Pkg.install('lib32-nvidia-390xx-utils')
			elif card == 'T':
				# nvidia-340xx, NVIDIA cards from around 2006-2010
				video_drv += ('' if video_drv == '' else '-') + 'nvidia-340'
				Pkg.remove('libglvnd') # To avoid conflicts
				errors += Pkg.install(f'nvidia-340xx{kernel_suffix} nvidia-340xx-utils')
				if enable_multilib:
					errors += Pkg.install('lib32-nvidia-340xx-utils')
			elif card == 'U':
				# use noveau, NVIDIA cards from <= 2006
				mesa_install_type = 2
				video_drv += ('' if video_drv == '' else '-') + 'noveau'
				errors += Pkg.install('xf86-video-nouveau')
			else:
				# Expect current NVIDIA cards from around 2010 onwards
				video_drv += ('' if video_drv == '' else '-') + 'nvidia'
				errors += Pkg.install(f'nvidia{kernel_suffix} nvidia-utils nvidia-settings')
				if enable_multilib:
					errors += Pkg.install('lib32-nvidia-utils')

			if mesa_install_type < 2:
				errors += Pkg.install('libvdpau')
				if enable_multilib:
					errors += Pkg.install('lib32-libvdpau')

				if mesa_install_type == 0:
					errors += Pkg.install('xorg-server-devel')
					# Generate X.org config
					errors += Cmd.log('nvidia-xconfig')

			# TODO
			# kernel options: "nvidia-drm.modeset=1"
			# /etc/mkinitcpio.conf
			# MODULES=(... nvidia nvidia_modeset nvidia_uvm nvidia_drm)
			# https://wiki.archlinux.org/index.php/NVIDIA#Pacman_hook
			# https://wiki.archlinux.org/index.php/GDM#Use_Xorg_backend

			# TODO Make sure vulkan-intel is not installed

		# e.g. ''
		elif 'amd' in vga_out or 'ati' in vga_out:
			mesa_install_type = 2
			video_drv = 'amdgpu'
			errors += Pkg.install('xf86-video-amdgpu vulkan-radeon')
			# TODO Only install on Vulkan capable GPUs
			if enable_multilib:
				errors += Pkg.install('lib32-vulkan-radeon')

			# libva-mesa-driver vulkan-radeon
			# TODO 'amdgpu.dc=1' as kernel/module option
			# also 'radeon.cik_support=0 amdgpu.cik_support=1' etc depending on card GCN version
			# 'MODULES=(amdgpu radeon)' in /etc/mkinitcpio.conf

		# e.g. 'intel corporation hasswell-ult integrated graphics'
		elif 'intel' in vga_out:
			mesa_install_type = 2
			video_drv = 'intel'
			errors += Pkg.install('xf86-video-intel vulkan-intel')
			# TODO Only install on Vulkan capable GPUs
			if enable_multilib:
				errors += Pkg.install('lib32-vulkan-intel')

			# TODO Enable DRI3
			#/etc/X11/xorg.conf.d/20-intel.conf
			#----------------------------------
			#Section "Device"
			#	Identifier  "Intel Graphics"
			#	Driver      "intel"
			#	Option      "DRI"    "3"
			#EndSection
	else: # Virtualized
		mesa_install_type = 2
		Cmd.exec('echo needs_root_rights=yes >/etc/X11/Xwrapper.config')
		if 'vmware' in vga_out:
			video_drv = 'vmware'
			errors += Pkg.install('xf86-video-vmware')
		else:
			video_drv = 'fbdev'
			errors += Pkg.install('xf86-video-fbdev')

	if 'nvidia-340' not in video_drv:
		errors = Pkg.install('libglvnd')
		if enable_multilib:
			errors += Pkg.install('lib32-libglvnd')

	if mesa_install_type > 0:
		video_drv += '+mesa'
		errors += Pkg.install('mesa libva-mesa-driver mesa-vdpau')
		if enable_multilib:
			errors += Pkg.install('lib32-mesa lib32-libva-mesa-driver lib32-mesa-vdpau')
		pass # TODO libva-mesa-driver mesa lib32-mesa ...

	# TODO Only install on Vulkan capable GPUs
	errors += Pkg.install('vulkan-icd-loader')
	if enable_multilib:
		errors += Pkg.install('lib32-vulkan-icd-loader')

	# Video acceleration
	if enable_aur:
		errors += Pkg.aur_install('libva-vdpau-driver-chromium')
	#else: errors += Pkg.install('libva-vdpau-driver')

	log(f"\n[setup.py:vga_setup()] Video driver: '{video_drv}'")

	write_status(errors)

def de_setup():
	# TODO Improve this
	de_dislay = de.upper().replace('XFCE', 'Xfce').replace('CINNAMON', 'Cinnamon').replace('BUDGIE', 'Budgie').replace('LXQT', 'LXQt').replace('I3', 'i3')
	write_msg(f'Installing components for the {de_dislay} desktop environment, please wait...', 1)
	installed = True
	errors = 0

	# TODO Auto-login support for 'passwdless_users' in all DEs?

	if len(users) > 0:
		for user in users.split(','):
			Cmd.log('$ mkdir -p ~/.local/share/ cd ~/.local/share/ && mkdir fonts icons themes; cd', user)

	if de == 'gnome':
		errors += Pkg.install('gnome gnome-extra')
		errors += Cmd.log('systemctl enable gdm')
		# TODO Execute post-instlal ?
		#export DISPLAY=:0
		#Cmd.log('xhost +SI:localuser:gdm')

		# TODO Don't remove gnome-sound-recorder when repo version is >= 3.28.2-2
		# TODO Only install required packages instead of downloading 'gnome-extra' group and removing many
		# TODO Use /tmp/ for temporary downloaded files!
		Pkg.remove('gnome-sound-recorder gnome-dictionary gnome-usage gnome-recipes gnome-boxes gnome-music gnome-nettool gnome-documents gnome-characters gnome-font-viewer yelp accerciser five-or-more four-in-a-row hitori iagno gnome-klotski lightsoff gnome-nibbles quadrapassel gnome-robots swell-foop tali gnome-taquin gnome-tetravex', True)

		# Hide V4L test apps
		Cmd.suppress('cd /usr/share/applications/')
		Cmd.exec("echo 'NoDisplay=true' >>qv4l2.desktop")
		Cmd.exec("echo 'NoDisplay=true' >>qvidcap.desktop")

		Pkg.install('rhythmbox transmission-gtk')

		# GNOME specific optdepends
		Pkg.install('chrome-gnome-shell gnome-icon-theme-extras gtk-engine-murrine gtk-engines highlight evolution-bogofilter eog-plugins festival fwupd gnuchess polkit-gnome fprintd tpm2-abrmd tpm2-tools ibus telepathy mtools libiscsi') # libgit2-glib razor

		if len(users) > 0:
			# Install an icon pack
			log('\n')
			Cmd.exec('cd /tmp && git clone https://github.com/vinceliuice/Tela-icon-theme.git &>>/setup.log && ./Tela-icon-theme/Install &>>/setup.log; rm -rf Tela-icon-theme/')

			# TODO Replace with proper keymap parsing from vconsole to xkbmap format
			kbmap = ''
			if keymap.isalpha():
				kbmap = keymap
			else:
				xkb = re.split('[^a-zA-Z]', keymap) # e.g. 'dvorak','uk'
				for part in xkb:
					part = part.strip()
					if len(part) == 2:
						kbmap = part
						break
			if kbmap == '' and len(kbmap) > 1:
				kbmap = keymap[:2]
			ret_val = Cmd.suppress(f'localectl list-x11-keymap-layouts --no-pager | grep "{kbmap}"')
			if ret_val != 0:
				log(f"\n[setup.py:de_setup()] Ignoring not found kbmap '{kbmap}'")
				kbmap = 'us'
			log(f"\n[setup.py:de_setup()] Set X kbmap: '{kbmap}'")

			dconf = Cmd.output('curl https://git.io/fhNOG -Ls').strip().replace('§locale', LC_ALL).replace('§ntp', str(enable_ntp).lower()).replace('§xkb', kbmap)
			ret_val = IO.write('/dconf.ini', dconf) # /tmp/dconf.ini
			#if ret_val == 0:
				#for user in users.split(','):
					#restricted = User.is_restricted(user)
					#group = ('restricted' if restricted else 'users')
					#Cmd.log(f'chown {user}:{group} /tmp/dconf.ini')
					# '$ (dbus-launch --exit-with-session) dconf load / < /tmp/dconf.ini'

				#Cmd.log('rm -f /tmp/dconf')
		else:
			# TODO dconf for root user?
			pass

		if enable_aur:
			Pkg.install('pacman-contrib')
			Pkg.aur_install('pamac-aur gnome-shell-extension-arch-update gnome-shell-extension-status-area-horizontal-spacing gnome-shell-extension-remove-dropdown-arrows')
			Cmd.log('cp /etc/pamac.conf /etc/pamac.conf.bak')
			IO.uncomment_ln('/etc/pamac.conf', 'EnableDowngrade')
			IO.uncomment_ln('/etc/pamac.conf', 'EnableAUR')
			IO.uncomment_ln('/etc/pamac.conf', 'CheckAURUpdates')
			IO.replace_ln('/etc/pamac.conf', 'KeepNumPackages', 'KeepNumPackages = 2')
			IO.uncomment_ln('/etc/pamac.conf', 'OnlyRmUninstalled')

		# Start Xorg session by default (for now: https://bugs.archlinux.org/task/53284)
		if 'nvidia' in video_drv:
			for user in users.split(','):
				IO.replace_ln(f'/var/lib/AccountsService/users/{user}', 'XSession=', 'XSession=gnome-xorg')

		# TODO Fix nautilus 'Folder name is too long' allowing only 1 character file & dir names (vmware shares)?

		# Make automatic login possible
		# NOTE Session type cannot be changed if in 'nopasswdlogin' group
		#IO.write('/etc/pam.d/gdm-password', 'auth sufficient pam_succeed_if.so user ingroup nopasswdlogin')

		if not disc_tray_present:
			Pkg.remove('brasero', True)

	else: # Unknown desktop
		errors = 1
		installed = False

	write_status(errors)

	# TODO Setup flatpak properly (e.g. sandboxing etc)
	# TODO if enable_flatpak:
	Pkg.install('flatpak flatpak-builder')

	# TODO if enable_snap:
	#Pkg.install('snapd ...')

	# TODO if enable_assistive_tech:
	Pkg.install('festival')

	# Every desktop optdepends
	Pkg.install('ntfs-3g nfs-utils samba libgpod unzip p7zip unrar lrzip unace libheif poppler-data libdbusmenu-glib libdbusmenu-gtk3 libdbusmenu-gtk2 libgit2-glib python-pysocks python-pyopenssl python-brotlipy')

	# Avahi
	Cmd.log('systemctl disable systemd-resolved')
	errors = Cmd.log('systemctl enable avahi-daemon')
	errors += Pkg.install('nss-mdns')
	errors += IO.replace_ln('/etc/nsswitch.conf', 'hosts: ', 'hosts: files mymachines mdns4_minimal [NOTFOUND=return] resolve [!UNAVAIL=return] dns mdns4 myhostname')
	# TODO if UWF, open port 5353/UDP
	#write_status(errors)

	if installed:
		write_msg('Installing some additional packages, please wait...', 1)
		errors = Pkg.install('noto-fonts noto-fonts-emoji noto-fonts-cjk ttf-bitstream-vera ttf-dejavu ttf-liberation chromium libisofs')

		# Use 'mtpfs' with better Android support if AUR is enabled
		if enable_aur:
			Pkg.remove('mtpfs')
			errors += Pkg.aur_install('jmtpfs')
		else:
			errors += Pkg.install('mtpfs')

		write_status(errors)

		# TODO Printer & scanner pkgs: 'sane argyllcms system-config-printer python-pysmbc'

		if use_adobe_flash:
			write_msg('Installing the Adobe Flash plugin...', 1)
			ret_val = Pkg.install('pepper-flash flashplugin')
			write_status(ret_val)
	else:
		write_status('A handler for this DE has not been added yet, no DE installed...', 4)

def bootloader_extra_setup():
	write_msg('Installing GRUB multiboot support dependencies...', 1)
	ret_val = Pkg.install('ntfs-3g os-prober')
	write_status(ret_val)

	write_msg('Finding other bootloaders to add to GRUB menu...', 1)
	# TODO Figure out lvme_tad slowdown if running grub-mkconfig after installing os-prober...
	ret_val = Cmd.log('grub-mkconfig -o /boot/grub/grub.cfg')
	write_status(ret_val)

	Cmd.suppress('umount /run/lvm')

def passwd_setup():
	write_ln()
	write_msg(color_str('Create a password for the §2root §0user:\n\n'))
	for i in range(3):
		ret_val = Cmd.exec('passwd')
		if ret_val == 0:
			break
		else:
			write_ln()
			write_msg('Please try that again:\n\n')

	users_lst = users.split(',')
	if len(users_lst) > 0:
		psl_users_lst = passwdless_users.split(',')
		restricted_lst = User.get_restricted_users()
		passwd_users_lst = [] # TODO Improve
		for user in users_lst:
			if user not in psl_users_lst:
				passwd_users_lst.append(user)

		full_user_count = len(passwd_users_lst)
		user_count = 0
		show_counter = full_user_count > 1
		for user in passwd_users_lst:
			user_count += 1
			user_type = 'restricted' if user in restricted_lst else 'regular'
			write_ln()
			start = (f'§7({user_count}/{full_user_count}) §0') if show_counter else ''
			write_msg(color_str(f'{start}Create a password for the {user_type} user §3{user}§0:\n\n'))
			for i in range(3):
				ret_val = Cmd.exec(f'passwd {user}')
				if ret_val == 0:
					break
				else:
					write_ln()
					write_msg('Please try that again:\n\n')
	write_ln() # TODO Indent by 1?

def chroot_setup():
	global hostname, mbr_grub_dev, cpu_type

	if multibooting:
		# LVM 10 sec slow scan temp fix when installing os-prober
		Cmd.suppress('mkdir -p /run/lvm && mount --bind /hostrun/lvm /run/lvm')

	# Update defailt about HW e.g. running in VM, cpu type, MBR boot dev etc.
	load_hw_info()

	log('[setup.py:chroot_setup()] HW details:')
	# TODO Log more defails here
	log(f"CPU                 '{cpu_type}'")
	log(f"MBR_GRUB_DEV        '{mbr_grub_dev}'")
	log(f"BAT_PRESENT         '{bat_present}'")
	log(f"DISC_TRAY_PRESENT   '{disc_tray_present}'")
	log(f"BT_PRESENT          '{bt_present}'")
	log(f"FLOPPY_PRESENT      '{fdd_present}'")
	log(f"VM_ENV              '{vm_env}'")

	write_status(0) # Change 'Chrooting...' status msg to DONE

	timezone_setup()
	locale_setup()
	networking_setup()
	if len(users) > 0: user_setup()
	if enable_aur: aur_setup()
	if enable_multilib: multilib_setup()

	# Enable pacman eating dots
	Cmd.log('chmod 770 /etc/pacman.conf')
	Cmd.log('sed -i "38s/.*/ILoveCandy\\n/" /etc/pacman.conf')
	Cmd.log('chmod 644 /etc/pacman.conf')

	if ssh_server_type > 0: sshd_setup()
	if use_lts_kernel: lts_kernel_setup()
	bootloader_setup()
	#if web_server_type > 0: ...
	if xorg_install_type > 0: x_setup()
	if len(vm_env) > 0: vm_setup()
	if use_pulseaudio: audio_setup()
	if bt_present: bt_setup()
	if auto_detect_gpu: vga_setup()
	if len(de) > 0: de_setup()

	# TODO Use proper keymap globally in ALL DEs
	# TODO Snapd & flatpak support?
	# TODO Assistive techologies setup
	# TODO Printing & scanning setup, user groups: 'scanner sys lp'
	# TODO Check for other HW too e.g. fingerprint scanner (check lspci etc) & install proper packages
	# TODO Wine setup?

	if bat_present:
		write_msg('Installing some packages for battery power savings...', 1)
		ret_val = Pkg.install('tlp')
		# TODO Setup tharmald as well?
		write_status(ret_val)

	# TODO Query for DVD/CD drive to install bluray etc support (disc_tray_present)
	if disc_tray_present:
		write_msg('Installing some packages for proper disc drive usage...', 1)
		ret_val = Pkg.install('libisofs libdvdcss vcdimager lirc-utils') # dvdauthor
		write_status(ret_val)

	# TODO On KDE make theming direcoties automatically e.g. '~/.local/share/plasma/look-and-feel/' etc

	# TODO Boot time improvements

	custom_setup()
	if multibooting: bootloader_extra_setup()

	if sudo_ask_pass:
		Cmd.suppress('cp /etc/sudoers.bak /etc/sudoers')

		# TODO Create an actual replace by line number function
		# Give wheel group users sudo permission w/ pass
		Cmd.suppress("chmod 770 /etc/sudoers")
		Cmd.exec("sed -i '82 s/^# //' /etc/sudoers") #  > /etc/sudoers.tmp
		#Cmd.suppress("mv /etc/sudoers.tmp /etc/sudoers")
		Cmd.suppress("chmod 440 /etc/sudoers")

	if enable_aur:
		Cmd.log('userdel -f -r aurhelper')
		# TODO Clear AUR package cache (if not cached to drive) ?

	passwd_setup()

	log("\n#\n# End of chroot log\n#")

	# Move log to /var/log/
	Cmd.log('mv /setup.log /var/log/')




###############################
# Actual script
###############################

# Run env sanity checks
check_env()

# Check privileges
check_privs()

args = ' '.join(sys.argv[1:]) # e.g. '-v --test'
if len(args) > 0:
	log(f"[setup.py] Script start arguments: '{args}'")

# Continue install if in chroot
if in_chroot == 1:
	chroot_setup()
	exit(0)

log(f"[setup.py] Device boot mode: '{boot_mode}'")

# TODO Add -R arg flag for chroot repair operations menu etc
# TODO Add -N arg flag to run without internet and use only cached packages (show /pkgcache as mandatory, skip mirrorlist sorting, somehow update package databases / store database on cachedrive & replace system one?)

debug = '-d' in args
if debug:
	Cmd.suppress('rm /tmp/setup.log') # Remove possible old

# Load color scheme
load_colors()

write_msg(color_str('Arch §7Linux '))
write(color_str(f'§4{boot_mode} §0live environment was detected. Press ENTER to continue...'))
if not debug:
	input()
else:
	write_ln()

write_ln()
write_msg('Loaded customized color scheme', 2)

# Load keymap
load_kbmap()

# Check internet
check_connectivity()

# Refresh package databases

write_msg('Refreshing pacman package databases, please wait...', 1)
ret_val = Pkg.refresh_dbs()
write_status(ret_val)

# Load font
load_font()

# Update used installer packages
# TODO Check if the packages *actually* need to be updated (with pacman -Qs pkg?)
write_msg('Updating pacman...', 1)
ret_val = Pkg.install('pacman', False)
write_status(ret_val)

write_msg('Updating the Arch Linux keyring, please wait...', 1)
ret_val = Pkg.install('archlinux-keyring', False)
write_status(ret_val)

write_msg('Updating live environment partitioning utilities...', 1)
ret_val = Pkg.install('parted btrfs-progs xfsprogs', False)
write_status(ret_val)

# NTP time synchronization
if enable_ntp:
	ntp_setup()

write_msg('Entering disk partitioning menu...', 1)
time.sleep(0.25)
partitioning_menu()

log('\n[setup.py] Block device map after partitioning:')
Cmd.log(lsblk_cmd)
#log('\n')
Cmd.log(blkid_cmd)

mounting_menu()

sys_root = '/' # TODO Change for Btrfs volumes
sys_root = f'/mnt{sys_root}'

print_header('Installing Arch Linux')
write_msg('Starting Arch Linux install process...', 1)
ret_val = Pkg.install('arch-install-scripts', False)
write_status(ret_val)

if '-M' not in args: sort_mirrors()

base_install(sys_root)

start_chroot(sys_root)

# Install done! Cleanup & reboot etc.

# Clean up setup files
Cmd.suppress(f'rm -f {sys_root}root/setup.py')
Cmd.suppress(f'rm -f {sys_root}root/config.py')

if os.path.exists('/mnt/pkgcache'):
	#Cmd.suppress('chown root:root /pkgcache/pkgcache/aur/')
	#Cmd.suppress('find /pkgcache/pkgcache/aur/ -name "*.lock" -type f -delete')

	# TODO Remove older package versions from the package cache (use modified time)
	# Get package name (rsplit('-', 4)[1] ?)
	# 4ti2-1.6.9-1-x86_64.pkg.tar.xz

	#write_msg('Checking package cache drive package versions...', 1)
	#write_msg(f'Clearing {old_pkg_count} old package versions...', 1)

	Cmd.suppress('cd && umount /mnt/pkgcache')
	Cmd.suppress('rm -rf /mnt/pkgcache')
	Cmd.suppress('mv /etc/pacman.conf.bak /etc/pacman.conf')

Cmd.suppress(f'cp -f {sys_root}var/log/setup.log /tmp/')
#Cmd.suppress(f'cd && umount -R {sys_root[:-1]}') # TODO Fix causing /mnt to be busy

# END OF SCRIPT
write_ln(color_str('§3>> The install script is done!'), 2)
exit(0)
