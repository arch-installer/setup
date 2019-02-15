#!/usr/bin/python

# ArchInstaller.py
# ----------------
# Author      : JamiKettunen
#               https://github.com/JamiKettunen
# Project     : https://github.com/JamiKettunen/ArchInstaller.py
#
# Description : My personal Arch Linux installer script | Python rewrite
#
# License     : MIT (https://github.com/JamiKettunen/ArchInstaller.py/blob/master/LICENSE)
#
# Reference   : https://wiki.archlinux.org/index.php/Installation_guide
#

# TODO Make localizable

# File IO & OS check
from os import popen,name # WARN: normal variable 'name' used
# Standard write and read
from sys import stdout,argv
# Call commands in a subshell
from subprocess import run,PIPE,STDOUT
# Sleep command
from time import sleep



###############################
# Setup config variables
###############################

# Virtual console font - See vconsole-fonts.txt for all options
# def. 'default'
font = 'Lat2-Terminus16'

# Virtual console keymap - See vconsole-keymaps.txt for all options
# def. 'en'
keymap = 'fi'

# Whether to enable NTP time synchronization
# def. 'True'
ntp_enabled = True

# Other groups & packages to install w/ pacstrap on top of 'base' & 'python'
# NOTICE: 'base-devel' is required for AUR support and will be installed automatically if enabled
# def. ''
base_pkgs = 'vim htop'

# Choose between 'stable' & 'unstable' repositories
# def. 'stable'
repo = 'stable'



###############################
# Constant values
###############################

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

# Updated on script load (if needed)
boot_mode = 'BIOS/CSM'



###############################
# Helper functions
###############################

# Clear the entire screen buffer
def clear_screen():
	cmd.exec('clear')

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
			match = '§%s' % str(f) # e.g. '§2'
			if match not in string: # match not found => check next color
				continue

			fg = '0' # default fg to white (37)
			if f != 0: # update fg to use defined color
				fg = str(29 + f)

			string = string.replace(match, '\033[0;%sm' % fg)

	if reset:
		string += '\033[0m'

	return string

# Writes text to stdout
def write(text):
	stdout.write(text)
	stdout.flush()

# Writes a line of text to stdout
def write_ln(text='', new_line_count=1):
	for _ in range(0, new_line_count):
		text += '\n'
	write(text)

# Clears the screen & prints a *nice* looking header
def print_header(header):
	clear_screen()
	write_ln(color_str('§7%s' % header))                 # e.g. 'A Nice Header'
	write_ln(color_str('§7%s' % ('=' * len(header))), 2) # e.g. '============='

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
		write(color_str('§%d>> [ %s ] ' % (color, status_msg))) # e.g. ''
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
		write_ln(color_str('\r§3>> [ %s ]' % status_msg))
	else:
		color = status_colors.get(error_status)
		status_msg = status_mgs.get(error_status)
		write_ln(color_str('\r§%d>> [ %s ]' % (color, status_msg)))

# Logging

# Log a new line to /tmp/setup.log
# Returns: 0 = Success, 1 = Error
def log(text):
	return io.write_ln('/tmp/setup.log', text)

# File I/O class to read from & write to files

class io:
	# Reads the first line from a file
	# Returns: String on success, None on error
	@staticmethod
	def read_ln(fPath):
		try:
			with open(fPath, 'r') as f:
				tmp_ln = f.readline().rstrip('\n')
		except:
			tmp_ln = None
		return tmp_ln

	# Writes a line to a file
	# Returns: 0 = Success, 1 = Error
	@staticmethod
	def write_ln(fPath, text):
		try:
			with open(fPath, 'a') as f:
				f.write(text + '\n')
			return 0
		except:
			return 1

# Package management

class pkg:
	# TODO Progress reporting messages
	# Refresh local package database cache
	# Quit script execution on error
	@staticmethod
	def refresh_dbs(force_refresh=False, msg='', quit_on_fail=True):
		if msg != '':
			write_msg(msg, 1)

		command = 'pacman -Sy'
		command += 'y' if force_refresh else ''

		ret_val = cmd.log(command)
		if msg != '':
			write_status(ret_val)
		if ret_val != 0 and quit_on_fail:
			write_ln(color_str("§2ERROR: §0Database refreshing failed. Check /tmp/setup.log for details"))
			exit_code = 7 if force_refresh else 6
			exit(exit_code) # 6 = Couldn't synchronize databases, 7 = Force-refresh failed
		return ret_val

	# TODO Progress reporting messages
	# Install packages from the Arch repositories (core, extra, community)
	# Returns: pacman exit code
	@staticmethod
	def install(pkgs, only_needed=True, msg=''):
		if msg != '':
			write_msg(msg, 1)
		pac_args = ' --needed' if only_needed else ''
		ret_val = cmd.log('pacman -S --noconfirm --noprogressbar %s %s' % (pac_args, pkgs))
		if msg != '':
			write_status(ret_val)
		return ret_val

# Command execution

class cmd:
	# Run a command on the shell with an optional stdin stream
	# Returns: command exit code
	@staticmethod
	def exec(command): # , enable_input=False
		res = run(command, shell=True) # , input=enable_input
		return res.returncode # Execute & return exit_code

	# Run a command on the shell while logging all it's output
	# Returns: command exit code
	@staticmethod
	def log(command):
		log('\n# ' + command)
		ret_val = cmd.exec(command + ' >>/tmp/setup.log 2>&1')
		return ret_val # Execute & return exit_code

	# Run a command on the shell supressing all it's output
	# Returns: command exit code
	@staticmethod
	def suppress(command):
		ret_val = cmd.exec(command + ' >/dev/null 2>&1')
		return ret_val # Execute & return exit_code

	# Run a command on the shell while capturing all it's output
	# New lines are seperated with a '\n'
	# Returns: command exit code
	@staticmethod
	def get_output(command):
		res = run(command, shell=True, encoding='utf-8', capture_output=True) # stderr=STDOUT
		return res.stdout


###############################
# Pre-run checks
###############################

# Check if running in Arch Linux installer env & quit if not
def check_env():
	os_compat_msg = 'Please only run this script on the Arch Linux installer environment.\n\nhttps://www.archlinux.org/download/'
	if name == 'posix':
		hostname = io.read_ln('/etc/hostname')
		if hostname != 'archiso':
			print(os_compat_msg)
			exit(3) # 3 = Not running in ArchISO environment
	else:
		print(os_compat_msg)
		input()
		exit(2) # 2 = Non-POSIX systems are incompatible

# Check if running as root
def check_privs():
	user = cmd.get_output("whoami").rstrip('\n')
	if user != 'root':
		write_ln(color_str('§2ERROR: §0Please run this file as root to continue.'))
		exit(4) # 4 = Privilege requirements unmet



###############################
# Functions
###############################

# Use custom installer color definitions
def load_colors():
	# TODO 16 colors
	cmd.exec("echo -en '\\033]P00C0C0C'") # Black
	cmd.exec("echo -en '\\033]P1AF1923'") # Red
	cmd.exec("echo -en '\\033]P269A62A'") # Green
	cmd.exec("echo -en '\\033]P3E68523'") # Yellow
	cmd.exec("echo -en '\\033]P42935B1'") # Blue
	cmd.exec("echo -en '\\033]P57C1FA1'") # Magenta
	cmd.exec("echo -en '\\033]P62397F5'") # Cyan
	cmd.exec("echo -en '\\033]P79E9E9E'") # White
	clear_screen() # Clear screen to avoid coloring artifacts

# Update bootmode to EFI if required
def update_boot_mode():
	ret_val = cmd.log('ls /sys/firmware/efi/efivars')
	if ret_val == 0: # efivars dir exits => booted in UEFI
		boot_mode = 'UEFI'

# Check network connectivity with ping
def check_connectivity():
	write_msg('Checking network connectivity...', 1)
	ret_val = cmd.log('ping -c 1 1.1.1.1') # 'archlinux.org'
	write_status(ret_val)
	if ret_val != 0:
		write_ln(color_str("§2ERROR: §0No network connectivity. Check your connection and try again."))
		exit(5) # 5 = Network connectivity error


# Load console font using 'setfont'
def load_font():
	global font
	if font == '' or font == 'def' or font == 'default':
		font = 'default8x16'
	write_msg("Loading system font '%s'..." % font, 1)
	ret_val = cmd.log('setfont ' + font)
	write_status(ret_val)
	if ret_val != 0:
		write_ln(color_str("§2ERROR: §0Font loading failed. Most likely cause: the specified font was not found."))
		exit(8) # 8 = Font couldn't be loaded!

# Load kb map using 'loadkeys'
def load_kbmap():
	write_msg("Loading system keymap '%s'..." % keymap, 1)
	ret_val = cmd.log('loadkeys ' + keymap)
	write_status(ret_val)
	if ret_val != 0:
		write_ln(color_str("§2ERROR: §0Keymap loading failed. Most likely cause: the specified keymap was not found."))
		exit(9) # 9 = Keymap couldn't be loaded!

# NTP time synchronization
def enable_ntp():
	write_msg('Enabling NTP time synchronization...', 1)
	ret_val = cmd.log('timedatectl set-ntp true')
	write_status(ret_val, 0, 4)

# Disk partitioning

def partition(tool_to_use=''):
	cmd.exec("echo && lsblk | grep -v '^loop' | grep -v '^sr0' && echo")
	if tool_to_use != '':
		write_msg('Device to partition (e.g. ')
	else:
		write_msg(color_str('Partitioning command line (e.g. §4fdisk §7/dev/'))
	write(color_str("§7sda§0) §7>> "))
	in_cmd = input().strip()
	if in_cmd != '':
		if tool_to_use != '':
			cmd.exec("%s /dev/%s" % (tool_to_use, in_cmd))
		else:
			cmd.exec(in_cmd)

def sel_par_tool(hide_guide=False):
	if not hide_guide:
		# TODO Improve this
		# Enter 'G' to partition using cgdisk (recommended for UEFI)
		# Enter 'F' to partition using cfdisk (recommended for BIOS/CSM)
		write_ln(color_str("   Enter '§3%s§0' to partition using §3%s §0(recommended for %s)" % ("G" if boot_mode == "UEFI" else "F", "cgdisk" if boot_mode == "UEFI" else "cfdisk", boot_mode)))
		write_ln(color_str("   Enter '§4%s§0' to partition using §4%s §0(recommended for %s)" % ("F" if boot_mode == "UEFI" else "G", "cfdisk" if boot_mode == "UEFI" else "cgdisk", "BIOS/CSM" if boot_mode == "UEFI" else "UEFI")))

		write_ln(color_str("   Enter '§7O§0' to partition using §7something else"), 2)

	# '>> Selection (C/F/G/O) >> '
	write_msg('Selection (')

	# TODO Improve this
	if boot_mode == 'UEFI':
		write(color_str('§3G§0/§4F'))
	else:
		write(color_str('§3F§0/§4G'))

	write(color_str('/§7O§0) §7>> '))

	sel = input().upper().strip()
	if sel != '':
		if sel == 'G':
			partition('cgdisk')
		elif sel == 'F':
			partition('cfdisk')
		elif sel == 'O':
			partition()
		else:
			sel_par_tool(True)
		partition_menu()

par_menu_visit_counter = 0

def partition_menu():
	global par_menu_visit_counter
	print_header('Disk Partitioning')
	middle = ' anymore' if par_menu_visit_counter > 0 else ''
	write_ln(color_str("   §3Tip: §0If don't need to partition%s, just press ENTER" % middle), 2)
	par_menu_visit_counter += 1
	sel_par_tool()

# Partition mounting & formatting

# Mount a partition
# e.g. 'mount_par('/dev/sda1', '/')'
def mount_par(blk_dev, mount_point='/'):
	cmd.log('mkdir -p /mnt%s' % mount_point)
	return cmd.log('mount %s /mnt%s' % (blk_dev, mount_point))

def par_opt_handler(opt): # , format_par=-1
	# Option validity checks
	# TODO Fully disallow mounted selections to be chosen in mounting menu! (e.g. /,/efi,swap etc)
	if len(opt) != 1:
		list_used_pars(True)
	if opt == 'E' and boot_mode != 'UEFI':
		list_used_pars(True)
	if opt != 'B' and opt != 'R' and opt != 'E' and opt != 'H' and opt != 'S' and opt != 'O':
		list_used_pars(True)

	lsblk = cmd.get_output("lsblk | grep -v '^loop' | grep -v '^sr0' | grep -v '/' | grep -v 'SWAP'")

	# TODO Improve check
	if lsblk.count('\n') <= 2:
		write_ln()
		write_msg('Mounting cancelled since there are no devices to mount.', 4)
		write('\nPress ENTER to continue...')
		input()

	write_ln("\n%s" % lsblk)

	purpose = opt.replace('B', '/boot').replace('R', '/').replace('E', '/efi').replace('H', '/home').replace('S', 'swap').replace('O', 'other')
	end = '' if opt != 'O' else ' purpose'
	write_msg(color_str('What partition would you like to use for §3%s%s §0(e.g. ' % (purpose, end)))
	if opt == 'O':
		write(color_str('§7/dev/'))
	write(color_str('§7sda1§0)? §7>> '))
	par = input().strip() # sda1
	if len(par) < 3: # 4?
		mounting_menu()
	par = ('/dev/' if opt != 'O' else '') + par # '/dev/sda1'

	# e.g. 'Would you like to format /dev/sda1 for / using ext4 (y/N)? >> '
	#      'Would you like to format /dev/sda2 for swap usage (y/N)? >> '
	#      'Would you like to use /dev/sda3 for other purpose (y/N)? >> '
	#if format_par == -1:
	write_msg(color_str('Would you like to §2format §7%s §0(§2y§0/§3N§0)? §7>> ' % par))
	ans = input().upper().replace('YES', 'Y')
	#elif format_par == 1:
	#	ans = 'Y'
	#else:
	#	ans = 'n'

	# TODO Formatting progress
	# TODO Report formatting, mounting etc status, create header 
	# TODO Add RAID support etc.

	pause = False # Pause at end of formatting & mounting?
	fs_type = ''

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
				write_ln(color_str('   §3%s' % fs_type))
			write_ln()

			# '{2}this is in red {0}back to default'
			write(color_str('§7>> §0Which §3filesystem type §0would you like to format §7%s §0with (e.g. §3ext4§0)? §7>> ' % par))
			fs_type = input().lower().strip() # e.g. 'ext4'
			if len(fs_type) < 3 or fs_type not in [x.lower() for x in supported_fs_types]:
				mounting_menu()

			fs_type = fs_type.replace('fat32', 'fat')

		# TODO Use '-n ESP' on fat32 /efi par, '-L Arch Linux' on ext4 / par etc.
		format_cmd = 'mkfs.%s' % fs_type if fs_type != 'swap' else 'mkswap' # e.g. 'mkfs.ext4', 'mkswap'
		if fs_type in format_args:
			format_cmd += ' ' + format_args.get(fs_type)

		write_ln()
		write_msg('Formatting %s using %s...' % (par, fs_type), 1)
		# TODO Add custom labels for / 'Arch Linux', /efi 'ESP' etc
		ret_val = cmd.log("%s %s" % (format_cmd, par)) # e.g. 'mkfs.ext4 /dev/sda1'
		write_status(ret_val)
		if ret_val != 0:
			pause = True
		else:
			write_ln()

		# TODO Btrfs: create subvolume, __snapshot etc.
		# TODO Add LUKS disk encryption support

	if not pause:
		if fs_type != 'swap':
			if opt == 'O':
				write_msg(color_str('Where would you like to mount §7%s §0in the new system (e.g. §3/var§0)? §7>> ' % par))
				mp = input().strip()  # e.g. '/var'
			elif opt == 'R':
				mp = '/'
			elif opt == 'B':
				mp = '/boot'
			elif opt == 'H':
				mp = '/home'
			else:
				mp = '/efi'

			# TODO Prevent mounting to / when using NTFS etc.
			write_ln()
			if len(mp) > 0 and mp.startswith('/'):  # Assume proper path
				write_msg('Mounting %s to %s...' % (par, mp), 1)
				ret_val = mount_par(par, mp) # e.g. 'mount /dev/sda1 /mnt/'
				write_status(ret_val)
				if ret_val != 0:
					pause = True
			else:
				write_msg('Mounting cancelled due to an invalid mountpoint.', 4)
				pause = True
		else:
			write_msg('Enabling swap on %s...' % par, 1)
			ret_val = cmd.log('swapon ' + par) # e.g. 'swapon /dev/sda1'
			write_status(ret_val)
			if ret_val != 0:
				pause = True

	if pause:
		write('\nPress ENTER to continue...')
		input()
	else:
		sleep(0.15)

mounts = ''

def write_par_mount(key='E', mount='/efi', device='/dev/sda1', condition=False, max_len=7, start_space_count=6):
	if key == '':
		key = '    '
	write(' ' * start_space_count)
	write('%s   %s' % (key, mount))
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
				log("WARN: Mountpoint not found for mount '%s' on device '%s', showing /dev/null instead..." % (mount, device))
				log("Mounts: '%s'" % mounts)
		action = 'mounted as' if key != 'S' else 'enabled on'
		write(color_str(' §3(%s §7%s§3)' % (action, device)))
	write_ln()

def list_used_pars(hide_guide=False):
	global mount_menu_visit_counter
	global mounts
	mounts = ''
	other_mounts = ''

	# TODO Improve this
	# WARN Mounting anything to a mount point ending in 'root' is forbidden
	tmp_mounts = cmd.get_output("lsblk -n -o NAME,MOUNTPOINT | grep -v '^loop' | grep -v '^sr0'") #  | grep /
	for line in tmp_mounts.split('\n'):
		dev = line.split(' ')[0][2:]                  # e.g. 'sda2'
		if '[SWAP]' in line:                          # Swap enabled
			mounts += 'swap:/dev/%s,' % dev             # e.g. 'swap:/dev/sda2,'
		elif line.count('/') == 1 and '/mnt' in line: # Root mounted
			mounts += 'root:/dev/%s,' % dev             # e.g. 'root:/dev/sda3,'
		elif line.count('/') > 1:                     # Other mounts
			mount = line.split('/', 1)[1][3:]           # e.g. '/efi'
			entry = ('%s:/dev/%s,' % (mount, dev))      # e.g. '/efi:/dev/sda1,'
			if mount == '/efi' or mount == '/boot' or mount == '/home':
				mounts += entry
			else:
				other_mounts += entry

	if 'root:' not in mounts:
		mount_menu_visit_counter = 0

	if not hide_guide:
		# Debug write mouunts & other_mounts strings
		#if len(mounts) > 0:
		#	mounts = mounts[:-1] # Remove last entry's ','

		#	end = '\n' if len(other_mounts) == 0 else ''
		#	write_ln('\n' + color_str("   Mounts: '§7%s§0'%s" % (mounts, end)))
		#if len(other_mounts) > 0:
		#	other_mounts = other_mounts[:-1] # Remove last entry's ','

		#	start = '\n' if len(mounts) == 0 else ''
		#	write_ln(color_str("%s   Other mounts: '§7%s§0'" % (start, other_mounts)), 2)

		write_ln(color_str('   The following partitions are §2mandatory§0:'), 2)
		if boot_mode == 'UEFI':
			write_par_mount('E', '/efi', '', ('/efi:' in mounts))
		write_par_mount('R', '/', '', ('root:' in mounts))

		write_ln('\n' + color_str('   §4Optional §0partitions include:'), 2)
		write_par_mount('B', '/boot', '', ('/boot:' in mounts))
		write_par_mount('H', '/home', '', ('/home:' in mounts))
		write_par_mount('S', 'swap', '', ('swap:' in mounts))
		write_ln('      O   other')

		# TODO Improve output formatting
		if len(other_mounts) > 0: # Other mounts found => List them
			split_mounts = other_mounts.split(',') # e.g. '/root:/dev/sda2', '/efi:/dev/sda1'
			for entry in split_mounts:             # e.g. '/efi:/dev/sda1'
				if entry != '':
					split_entry = entry.split(':')       # e.g. '/efi', '/dev/sda1'
					try:
						write_par_mount('', split_entry[0], split_entry[1], True, 7, 3)
					except:
						log("WARN: Couldn't display other mount entry '%s'" % entry)

		#start = '\n' if len(other_mounts) != 0 else ''
		# %s % start
		write_ln('\n   In case a partition needs to be further identified:', 2)
		write_ln('      L   lsblk')
		write_ln('      I   blkid')
		write_ln('      F   fdisk -l', 2)

	# '>> Selection (B/E/R/H/S/O/L/I/F) >> '
	write_msg('Selection (')
	if boot_mode == 'UEFI' and not '/efi:' in mounts:
		write('E/')
	if not 'root:' in mounts:
		write('R/')
	if not '/boot:' in mounts:
		write('B/')
	if not '/home:' in mounts:
		write('H/')
	if not 'swap:' in mounts:
		write('S/')
	write(color_str('O/L/I/F) §7>> '))

	sel = input().upper().strip()
	if sel != '':
		# Partition identification
		if sel == 'L' or sel == 'I' or sel == 'F':
			command = "lsblk | grep -v '^loop' | grep -v '^sr0'"
			if sel == 'I':
				command = "blkid | grep -v '^/dev/loop' | grep -v '^/dev/sr0'"
			elif sel == 'F':          # 'DEV    TYPE       SIZE MOUNT'
				# TODO Strip /dev/loop0 entry from 'fdisk -l' ouput
				command = 'fdisk -l' # lsblk -n -o NAME,FSTYPE,SIZE,MOUNTPOINT
			write_ln()
			cmd.exec(command)
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
	if boot_mode == 'UEFI' and not '/efi:' in mounts:
		write_ln()
		write_msg(color_str('Would you like to continue without mounting a §3/efi §7partition §0(§2y§0/§3N§0)? §7>> '))
		ans = input().upper().replace('YES', 'Y')
		if ans != 'Y':
			mounting_menu()

mount_menu_visit_counter = 0

def mounting_menu():
	global mount_menu_visit_counter
	print_header('Mounting Partitions')
	write_ln('   Select an option by pressing the corresponding key.')
	write(color_str("   §3Tip: §0If don't need to mount partitions"))
	if mount_menu_visit_counter > 0:
		write(' anymore')
	mount_menu_visit_counter += 1
	write_ln(color_str(', just press ENTER'), 2)
	list_used_pars()


###############################
# Actual script
###############################

# Run env sanity checks
check_env()

# Check privileges
check_privs()

debug = len(argv) > 1 and argv[1].upper() == '-D'
if debug:
	cmd.suppress('rm /tmp/setup.log') # Remove possible old (ONLY DEBUG?)

# Load color scheme
load_colors()

write_msg(color_str('Arch §7Linux '))
update_boot_mode()
write(color_str('§4%s §0live environment was detected. Press ENTER to continue...' % boot_mode))
if not debug:
	input()
else:
	write_ln()

# Some preparation (ONLY DEBUG?)
cmd.log('umount -R /mnt')

write_ln()
write_msg('Loaded customized color scheme', 2)

# Load font
load_font()

# Load keymap
load_kbmap()

# Check internet
check_connectivity()

# Refresh package databases
pkg.refresh_dbs(False, 'Refreshing pacman package databases, please wait...')

# Update used installer packages
# TODO Check if pacman *actually* needs to be updated
write_msg('Updating pacman...', 1)
ret_val = pkg.install('pacman', False)
write_status(ret_val)

write_msg('Updating the Arch Linux keyring, please wait...', 1)
ret_val = pkg.install('archlinux-keyring', False)
write_status(ret_val)

write_msg('Updating live environment partitioning utilities...', 1)
ret_val = pkg.install('parted btrfs-progs xfsprogs', False)
write_status(ret_val)

# NTP time synchronization
if ntp_enabled:
	enable_ntp()

write_msg('Entering disk partition menu...', 1)
sleep(0.25)
partition_menu()

log('\nBlock device map after partitioning:')
cmd.log('lsblk')

mounting_menu()

# END OF SCRIPT
write_ln('\n' + color_str('§3SCRIPT IS DONE (FOR NOW).'), 2)



# install packages: 'pacman-mirrorlist arch-install-scripts'
# mirrorlist sort...

# TODO Install userspace utilities w/ pacstrap for required filesystems, e.g. 'TYPE="reiserfs"' found in blkid => Install xfsprogs etc.
# (btrfs-progs xfsprogs)

# repo - Switch before install & pacman -Syy
# base_pkgs - 'pacstrap /mnt base python ' + base_pkgs
# locale: Use '.UTF-8' if no '.' in locale definition string
# TODO Boot time improvements
