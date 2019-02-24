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
import os, sys, subprocess, time

# Import configured user variables
try:
	from config import *
except ModuleNotFoundError:
	# TODO Move error message here?
	pass

# TODO Create a .gz package to gunzip & include *.py files: # gunzip archinstaller.py.gz
# TODO Check what running from SSH prompt would look like



###############################
# Custom setup 
###############################

# TODO Find a way to seperate to 'custom.py'

def custom_setup():
	#pass

	# Install custom packages
	write_msg("Installing custom packages...", 1)
	errors = pkg.install('bash-completion neofetch')
	errors += pkg.aur_install('c-lolcat')
	write_status(errors)

	# Custom GRUB2 theme
	write_msg("Installing custom 'poly-dark' GRUB2 theme...", 1)
	ret_val = cmd.exec('cd && git clone https://github.com/shvchk/poly-dark.git &>/dev/null && mkdir -p /boot/grub/themes && mv poly-dark /boot/grub/themes && grep "GRUB_THEME=" /etc/default/grub &>/dev/null && sed -i "/GRUB_THEME=/d" /etc/default/grub && echo "GRUB_THEME=/boot/grub/themes/poly-dark/theme.txt" >> /etc/default/grub && grub-mkconfig -o /boot/grub/grub.cfg &>/dev/null')
	write_status(ret_val)

	# TODO Multi-user support

	# Create some directories
	cmd.log('mkdir -p ~/.local/bin ~/.vim/colors') # Root
	if user != '':
		cmd.log('$ mkdir -p ~/.local/bin ~/.vim/colors') # Users

	# Custom ~/.bash_profile
	write_msg("Creating custom '.bash_profile' file for all users...", 1)
	ret_val = cmd.log('curl https://git.io/fhF2b -Lso ~/§f && cd /home/§u/ && cp ~/§f . && chown §u:users §f; cd'.replace('§u', user).replace('§f', '.bash_profile'))
	write_status(ret_val)

	# Custom ~/.bashrc
	write_msg("Creating custom '.bashrc' file for all users...", 1)
	ret_val = cmd.log('curl https://git.io/fhF2p -Lso ~/§f && cd /home/§u/ && cp ~/§f . && chown §u:users §f; cd'.replace('§u', user).replace('§f', '.bashrc'))
	write_status(ret_val)

	# Custom ~/.bashrc.aliases
	write_msg("Creating custom '.bashrc.aliases' file for all users...", 1)
	ret_val = cmd.log('curl https://git.io/fhF2h -Lso ~/§f && cd /home/§u/ && cp ~/§f . && chown §u:users §f; cd'.replace('§u', user).replace('§f', '.bashrc.aliases'))
	write_status(ret_val)

	# Vim custom setup
	write_msg("Creating custom '.vimrc' file for all users...", 1)
	errors = cmd.log('cd ~/.vim/colors/ && curl https://git.io/fhFEE -Lso §f && cd /home/§u/.vim/colors/ && cp ~/.vim/colors/§f . && chown §u:users §f; cd'.replace('§u', user).replace('§f', 'molokai.vim')) # molokai.vim
	errors += cmd.log('curl https://git.io/fhF2j -Lso ~/§f && cd /home/§u/ && cp ~/§f . && chown §u:users §f; cd'.replace('§u', user).replace('§f', '.vimrc'))
	write_status(errors)

	if vm_env == '':
		# TODO /etc/conf.d/wireless-regdom -> uncomment FI (use sed)
		write_msg('Installing proper support for BCM WiFi + BT combo card, please wait...', 1)
		errors = pkg.install('linux%s-headers dkms broadcom-wl-dkms' % ('-lts' if use_lts_kernel else ''))
		errors += pkg.aur_install('bcm20702a1-firmware')
		write_status(errors)

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
script_path += '/%s' % script_fn            # Full script path e.g. '/root/setup.py'
script_root = script_path.rsplit('/', 1)[0] # Directory path of script e.g. '/root'

# Vars updated on script load
boot_mode = 'BIOS/CSM'    # 'BIOS/CSM' / 'UEFI'
cpu_type = ''             # 'intel' / 'amd'
in_chroot = False         # Inside chroot?
vm_env = ''               # Virtualized env e.g. '', 'vbox', 'vmware', 'other'
bat_present = False       # Battery present?
disc_tray_present = False # Disc tray present?
bt_present = False        # BT device present?
args = ''                 # All arguments in one string



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
	sys.stdout.write(text)
	sys.stdout.flush()

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

# Log a new line to /(tmp/)setup.log
# Returns: 0 = Success, 1 = Error
def log(text):
	start = '/' if in_chroot else '/tmp/'
	return io.write_ln('%ssetup.log' % start, text)

# File I/O class to read from & write to files

class io:
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
			with open(f_path, '%s+' % mode) as f:
				f.write(text)
			return 0
		except:
			return 1

	# Appends text to a file
	# Returns: 0 = Success, 1 = Error
	@staticmethod
	def append(f_path, text):
		return io.write(f_path, text, True)

	# Writes a line to a file
	# Returns: 0 = Success, 1 = Error
	@staticmethod
	def write_ln(f_path, text = '', append=True):
		return io.write(f_path, text + '\n', append)

	# TODO Write a get_lines to re-use in other code below

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
					file_lines += '%s\n' % line
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
					file_lines += '%s\n' % line
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

class pkg:
	# TODO Add '--cache-dir' when os.path.exists('/(mnt/)pkgcache')
	# TODO Cache AUR packages too

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
			log_path = 'mnt' if in_chroot else 'tmp'
			write_ln(color_str("§2ERROR: §0Database refreshing failed. Check /%s/setup.log for details" % log_path))
			exit_code = 8 if force_refresh else 7
			exit(exit_code) # 7 = Couldn't synchronize databases, 8 = Force-refresh failed
		return ret_val

	# TODO Progress reporting messages
	# Install packages from the Arch repositories (core, extra, community)
	# Returns: pacman exit code
	@staticmethod
	def install(pkgs, only_needed=True, msg=''):
		if msg != '':
			write_msg(msg, 1)
		pac_args = '--needed' if only_needed else ''
		if in_chroot: pac_args += ' --cachedir /pkgcache/pkgcache' if os.path.exists('/pkgcache') else ''
		if pac_args != '': pac_args = ' ' + pac_args.strip()
		ret_val = cmd.log('pacman -S --noconfirm --noprogressbar%s %s' % (pac_args, pkgs))
		if msg != '':
			write_status(ret_val)
		return ret_val

	# TODO Progress reporting messages
	# Remove installed packages on a system
	# Returns: pacman exit code
	@staticmethod
	def remove(pkgs, msg=''):
		# pacman -Rn --noconfirm --noprogressbar
		if msg != '':
			write_msg(msg, 1)
		ret_val = cmd.log('pacman -Rn --noconfirm --noprogressbar %s' % pkgs)
		if msg != '':
			write_status(ret_val)
		return ret_val

	# TODO Progress reporting messages
	# Install packages from the Arch User Repository (AUR)
	# Returns: pacman exit code
	@staticmethod
	def aur_install(pkgs, only_needed=True, msg=''):
		if in_chroot:
			if enable_aur:
				if msg != '':
					write_msg(msg, 1)
				yay_args = '--needed' if only_needed else ''
				yay_args += ' --builddir /pkgcache/pkgcache/aur' if os.path.exists('/pkgcache') else ''
				if yay_args != '': yay_args = ' ' + yay_args.strip()
				ret_val = cmd.log('$ yay -Sq --noconfirm%s %s' % (yay_args, pkgs))
				if msg != '':
					write_status(ret_val)
				return ret_val
			else:
				log('[setup.py:pkg.aur_install(%s)] WARN: Ignoring installation, since the AUR support is not disabled.' % pkgs)
				return 1
		else:
			log('[setup.py:pkg.aur_install(%s)] WARN: Ignoring installation, since not in chroot.' % pkgs)
			return 1

# Command execution

class cmd:
	# Run a command on the shell with an optional io stream
	# io_stream_type: 0 = none, 1 = stdout, 2 = logged, 3 = all_supressed
	# Returns: command exit code / output when io_stream_type=2
	# TODO Support multiple users
	@staticmethod
	def exec(command, exec_user='', io_stream_type=0):
		user_exec = command.startswith('$ ')
		exec_cmd = command

		if user_exec:
			if exec_user == '':
				exec_user = user
			command = command[2:] # Remove '$ ' from user_exec commands
			if exec_user != '':
				exec_cmd = "sudo -i -u %s -H bash -c '%s'" % (exec_user, command)
			else:
				log('[setup.py:cmd.exec(%s)] WARN: Ignoring "%s" execution, since no user was defined.' % (str(io_stream_type), command))
				return 1

		use_stdout = (io_stream_type == 1)
		logged = (io_stream_type == 2)
		suppress = (io_stream_type == 3)

		end = ''
		if suppress or logged:
			start = '/' if in_chroot else '/tmp/'
			log_path = '%ssetup.log' % start # e.g. '/tmp/setup.log' or '/setup.log' in chroot
			end = ' &>>%s' % log_path if logged else ' &>/dev/null'
			if logged:
				start = ('#' if not user_exec else '#$') + ' '
				log('\n%s%s' % (start, command))
		if use_stdout:
			res = subprocess.run(exec_cmd + end, shell=True, encoding='utf-8', capture_output=use_stdout)
		else:
			res = subprocess.run(exec_cmd + end, shell=True)

		if logged and res.returncode != 0:
			log('\n# Command non-zero exit code: %s\n' % res.returncode)

		returns = res.stdout if use_stdout else res.returncode
		return returns

	# Run a command on the shell while capturing all it's output
	# New lines are seperated with a '\n'
	# Returns: command exit code
	@staticmethod
	def output(command, exec_user=''):
		return cmd.exec(command, exec_user, 1)

	# Run a command on the shell while logging all it's output
	# Returns: command exit code
	@staticmethod
	def log(command, exec_user=''):
		return cmd.exec(command, exec_user, 2)

	# Run a command on the shell while supressing all it's output
	# Returns: command exit code
	@staticmethod
	def suppress(command, exec_user=''):
		return cmd.exec(command, exec_user, 3)



###############################
# Pre-run checks
###############################

# Check if running in Arch Linux installer env & quit if not
# Additionally update details about the device
def check_env():
	os_compat_msg = 'Please only run this script on the Arch Linux installer environment.\n\nhttps://www.archlinux.org/download/'
	file_msg = "It seems that you are missing a '§f' module.\nHere's one way to fix it:\n\n   # §c\n"
	if os.name == 'posix':
		ret_val = cmd.suppress('cat /etc/hostname')
		if ret_val == 0:
			hostname = io.read_ln('/etc/hostname')
			if hostname != 'archiso':
				print(os_compat_msg)
				exit(3) # 3 = Not running in ArchISO environment

			# config.py
			try:
				base_pkgs
			except NameError:
				# TODO Replace with actual URL to config.py
				print(file_msg.replace('§f', 'config.py').replace('§c', 'curl https://git.io/fhbgV -Lso config.py'))
				exit(4) # 4 = config.py not loaded

		else: # Read failed => Assume chroot environment
			global in_chroot
			in_chroot = True

		# Update bootmode to EFI if required
		global boot_mode
		ret_val = cmd.suppress('ls /sys/firmware/efi/efivars')
		if ret_val == 0: boot_mode = 'UEFI' # efivars dir exits => booted in UEFI
	else:
		print(os_compat_msg)
		input()
		exit(2) # 2 = Non-POSIX systems are incompatible

# Check if running as root
def check_privs():
	un = cmd.output("whoami").rstrip('\n')
	if un != 'root':
		write_ln(color_str('§2ERROR: §0Please run this file as root to continue.'))
		exit(5) # 5 = Privilege requirements unmet



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

# Check network connectivity with ping
def check_connectivity():
	write_msg('Checking network connectivity...', 1)
	ret_val = cmd.log('ping -c 1 1.1.1.1') # 'archlinux.org'
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
		ret_val = pkg.install('terminus-font')
		write_status(ret_val)
	write_msg("Loading system font '%s'..." % font, 1)
	ret_val = cmd.log('setfont ' + font)
	write_status(ret_val)
	if ret_val != 0:
		write_ln(color_str("§2ERROR: §0Font loading failed. Most likely cause: the specified font was not found."))
		exit(9) # 9 = Font couldn't be loaded!

# Load kb map using 'loadkeys'
def load_kbmap():
	write_msg("Loading system keymap '%s'..." % keymap, 1)
	ret_val = cmd.log('loadkeys ' + keymap)
	write_status(ret_val)
	if ret_val != 0:
		write_ln(color_str("§2ERROR: §0Keymap loading failed. Most likely cause: the specified keymap was not found."))
		exit(10) # 10 = Keymap couldn't be loaded!

# NTP time synchronization
def ntp_setup():
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
	in_cmd = ''
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

	sel = ''
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
		partitioning_menu()

	# TODO Don't allow to continue without having atleast 1 partition on the disk (check lsblk output lines count)

par_menu_visit_counter = 0

def partitioning_menu():
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

mbr_grub_dev = ''

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

	lsblk = cmd.output("lsblk | grep -v '^loop' | grep -v '^sr0' | grep -v '/' | grep -i -v 'swap'")

	# TODO Improve check
	if lsblk.count('\n') <= 2:
		write_ln()
		write_msg('Mounting cancelled since there are no devices to mount.', 4)
		write('\nPress ENTER to continue...')
		input()
		mounting_menu()

	write_ln("\n%s" % lsblk)

	purpose = opt.replace('B', '/boot').replace('R', '/').replace('E', '/efi').replace('H', '/home').replace('S', 'swap').replace('O', 'other').replace('C', 'package cache')
	end = '' if opt != 'O' else ' purpose'
	write_msg(color_str('Which partition would you like to use for §3%s%s §0(e.g. ' % (purpose, end)))
	if opt == 'O':
		write(color_str('§7/dev/'))
	write(color_str('§7sda1§0)? §7>> '))
	par = ''
	par = input().strip() # sda1
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
	write_msg(color_str('Would you like to §2format §7%s §0(§2y§0/§3N§0)? §7>> ' % par))
	ans = ''
	ans = input().upper().replace('YES', 'Y')
	#elif format_par == 1:
	#	ans = 'Y'
	#else:
	#	ans = 'n'

	# TODO Formatting progress
	# TODO Report formatting, mounting etc status, create header 
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

		# TODO Btrfs: create subvolume, __snapshot etc.
		# TODO Add LUKS disk encryption support

	# Mounting
	if not pause:
		if fs_type != 'swap':
			#if ans != 'Y': write_ln()
			if opt == 'O':
				write_ln()
				write_msg(color_str('Where would you like to mount §7%s §0in the new system (e.g. §3/var§0)? §7>> ' % par))
				mp = ''
				mp = input().strip() # e.g. '/var'
				write_ln()
			elif opt == 'R': mp = '/'
			elif opt == 'B': mp = '/boot'
			elif opt == 'H': mp = '/home'
			elif opt == 'C':
				mp = '/pkgcache'
			else: mp = '/efi'

			# TODO Prevent mounting to / when using NTFS etc.
			if len(mp) > 0 and mp.startswith('/'): # Assume proper path
				write_msg('Mounting %s to %s...' % (par, mp), 1)
				# TODO Add custom optional mounting options
				ret_val = mount_par(par, mp) # e.g. 'mount /dev/sda1 /mnt/'
				write_status(ret_val)
				if ret_val != 0: pause = True
				elif boot_mode == 'BIOS/CSM' and ((opt == 'R' and mbr_grub_dev == '') or opt == 'B'): # Update MBR GRUB device
					if par[-1:].isdigit():
						par = par[:-1]
					mbr_grub_dev = par # e.g. '/dev/sda'
				elif mp == '/pkgcache':
					# TODO Update to support Btrfs
					write_msg('Checking partition filesystem compatability for caching...', 1)
					ret_val = cmd.log('mkdir -p /mnt/pkgcache/pkgcache/aur')
					ret_val += cmd.log('touch /mnt/pkgcache/pkgcache/test-1:1.2.3.4-x86-64.pkg.tar.xz.part')
					write_status(ret_val)
					if ret_val == 0:
						cmd.log('rm -f /mnt/pkgcache/pkgcache/test-1:1.2.3.4-x86-64.pkg.tar.xz.part')
						cmd.log('cp /etc/pacman.conf /etc/pacman.conf.bak')
						write_msg('Enabling package cache on the partition...', 1)
						ret_val = io.replace_ln('/etc/pacman.conf', '#CacheDir', 'CacheDir = /mnt/pkgcache/pkgcache')
						write_status(ret_val)

					if ret_val != 0:
						pause = True
						cmd.log('mv /etc/pacman.conf.bak /etc/pacman.conf')
						cmd.log('rm -rf /mnt/pkgcache')
						cmd.log('umount /mnt/pkgcache')
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
		time.sleep(0.15)

mounts = ''

def write_par_mount(key='E', mount='/efi', device='/dev/sda1', condition=False, max_len=9, start_space_count=6):
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
				log("[setup.py:write_par_mount()] WARN: Mountpoint not found for mount '%s' on device '%s', showing /dev/null instead..." % (mount, device))
				log("Mounts: '%s'" % mounts)
		action = 'mounted as' if key != 'S' else 'enabled on'
		write(color_str(' §3(%s §7%s§3)' % (action, device)))
	write_ln()

def list_used_pars(hide_guide=False):
	global mounts, mount_menu_visit_counter
	mounts = ''
	other_mounts = ''

	# TODO Improve this
	# WARN Mounting anything to a mount point ending in 'root' is forbidden
	tmp_mounts = cmd.output("lsblk -n -o NAME,MOUNTPOINT | grep -v '^loop' | grep -v '^sr0'") #  | grep /
	for line in tmp_mounts.split('\n'):
		# TODO Only do if not starting with an alphabet char
		dev = line.split(' ')[0][2:]               # e.g. 'sda2'
		if '[SWAP]' in line:                       # Swap enabled
			mounts += 'swap:/dev/%s,' % dev          # e.g. 'swap:/dev/sda2,'
		elif '/mnt' in line:
			if line.count('/') == 1:                 # Root mounted
				mounts += 'root:/dev/%s,' % dev        # e.g. 'root:/dev/sda3,'
			elif line.count('/') > 1:                # Other mounts
				mount = line.split('/', 1)[1][3:]      # e.g. '/efi'
				entry = ('%s:/dev/%s,' % (mount, dev)) # e.g. '/efi:/dev/sda1,'
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
				if entry != '':
					split_entry = entry.split(':')     # e.g. '/efi', '/dev/sda1'
					try:
						write_par_mount('', split_entry[0], split_entry[1], True, 7, 3)
					except:
						log("[setup.py:list_used_pars()] WARN: Couldn't display other mount entry '%s'" % entry)

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
	if not '/pkgcache:' in mounts:
		write('C/')
	if not 'swap:' in mounts:
		write('S/')
	write(color_str('O/L/I/F) §7>> '))

	# TODO Optionally allow to use /boot instead of /efi on UEFI systems

	sel = ''
	sel = input().upper().strip()
	if sel != '':
		# Partition identification
		if sel == 'L' or sel == 'I' or sel == 'F':
			command = "lsblk | grep -v '^loop' | grep -v '^sr0'"
			if sel == 'I':
				command = "blkid | grep -v '^/dev/loop' | grep -v '^/dev/sr0'"
			elif sel == 'F':       # 'DEV    TYPE       SIZE MOUNT'
				# TODO Strip /dev/loop0 entry from 'fdisk -l' ouput
				command = 'fdisk -l' # lsblk -n -o NAME,FSTYPE,SIZE,MOUNTPOINT
			write_ln()
			cmd.exec(command)
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
	if boot_mode == 'UEFI' and not '/efi:' in mounts:
		write_ln()
		write_msg(color_str('Would you like to continue without mounting a §3/efi §7partition §0(§2y§0/§3N§0)? §7>> '))
		ans = ''
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

# Mirrorlist sorting

def sort_mirrors():
	write_msg('Fetching reflector for mirrorlist sorting...', 1)
	ret_val = pkg.install('reflector')
	write_status(ret_val)

	if ret_val == 0:
		write_msg('Creating a backup of the local mirrorlist file...', 1)
		ret_val = cmd.log('mv /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak')
		write_status(ret_val)

		write_msg('Sorting mirrors using reflector, please wait...', 1)
		ret_val = cmd.log('reflector --verbose --sort rate --number 25 --fastest 10 --age 24 --protocol https --save /etc/pacman.d/mirrorlist')
		write_status(ret_val)

		# TODO Setup pacman hook to update later in chroot
		cmd.log('cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.reflector')

		pkg.refresh_dbs(True, 'Refreshing pacman package databases...')
		time.sleep(0.25)
	# else: TODO Update 'pacman-mirrorlist' pkg instead

# Base system install

# TODO Use global sys_root variable in the future
def base_install(sys_root = '/mnt/'):
	ps_args, extra_pkgs = ('', '')

	extra_pkgs += 'sudo ' if user != '' else ''
	extra_pkgs += '%s ' % base_pkgs if base_pkgs != '' else ''
	extra_pkgs += 'terminus-font ' if font.startswith('ter-') else ''
	# Userspace utilities for filesystems
	blkid = cmd.output("blkid | grep -v '^/dev/loop' | grep -v '^/dev/sr0'")
	extra_pkgs += 'btrfs-progs ' if '"btrfs"' in blkid else ''
	extra_pkgs += 'exfat-utils ' if '"exfat"' in blkid else ''
	extra_pkgs += 'ntfs-3g ' if '"ntfs"' in blkid else ''
	extra_pkgs += 'reiserfsprogs progsreiserfs ' if '"reiserfs"' in blkid else ''
	extra_pkgs += 'xfsprogs ' if '"xfs"' in blkid else ''
	extra_pkgs = ' %s' % extra_pkgs.rstrip() if extra_pkgs != '' else ''

	ps_args = '%s%s base python%s' % (('-c ' if os.path.exists(sys_root + 'pkgcache') else ''), sys_root, extra_pkgs)

	write_msg('Installing base system using pacstrap, please wait...', 1)
	# TODO Report on progress
	ret_val = cmd.log('pacstrap ' + ps_args)
	write_status(ret_val)
	if ret_val != 0: # Base install failure
		write_ln(color_str('§2ERROR: §0Base system install failed. Check /tmp/setup.log for the details.'))
		exit(11) # 11 = Base system install failure

	write_msg('Generating static filesystem table...', 1)
	ret_val = cmd.exec('genfstab -U %s >>%setc/fstab' % (sys_root, sys_root))
	write_status(ret_val)

# Continue setup in chroot...

# TODO Use global sys_root variable in the future
def start_chroot(sys_root = '/mnt/'):
	cmd.suppress('cp /proc/cpuinfo %sproc/' % sys_root) # For CPU detection in chroot

	if multibooting:
		cmd.suppress('mkdir %shostrun' % sys_root)
		cmd.suppress('mount --bind /run %shostrun' % sys_root)

	ret_val = io.write('%setc/vconsole.conf' % sys_root, 'KEYMAP="%s"\nFONT="%s"' % (keymap, font))
	if ret_val != 0:
		log("[setup.py:start_chroot()] WARN: Couldn't set persistent keymap (%s) & font (%s) in '%setc/vconsole.conf'" % (keymap, font, sys_root))

	cmd.log('cp "%s" "%sroot/"' % (script_path, sys_root))             # e.g. 'cp "/root/setup.py" "/mnt/root/"'
	cmd.log('chmod 755 %sroot/%s' % (sys_root, script_fn))             # e.g. 'chmod 755 /mnt/root/setup.py'
	cmd.log('cp "%s/config.py" "%sroot/"' % (script_root, sys_root))   # e.g. 'cp "/root/config.py" "/mnt/root/"'

	log("\n#\n# Start of chroot log\n#")
	cmd.suppress('cp /tmp/setup.log %s' % sys_root) # Copy log over to chroot

	write_msg('Chrooting into the new install...', 1)
	ch_args = ' %s' % mbr_grub_dev if mbr_grub_dev != '' else '' # Pass grub device to script
	cmd.exec('arch-chroot %s /root/%s%s' % (sys_root, script_fn, ch_args)) # e.g. 'arch-chroot /mnt/ /root/setup.py'

# Chroot specific install steps

def load_hw_info():
	global cpu_type, mbr_grub_dev, bat_present, disc_tray_present, bt_present, vm_env

	# CPU type needed for ucode
	cpu_type = 'intel' if cmd.suppress('cat /proc/cpuinfo | grep -i GenuineIntel') == 0 else 'amd'

	if len(sys.argv) == 2: # Assume MBR grub dev e.g. '/dev/sda4'
		mbr_grub_dev = sys.argv[1]

	# Update battery presence
	# TODO Check if needed to copy dir /sys/class/power_supply
	ret_val = cmd.log('ls /sys/class/power_supply | grep -i bat')
	bat_present = (ret_val == 0)

	# Update disc tray presence
	ret_val = cmd.log("dmesg | egrep -i 'cdrom|dvd|cd/rw|writer'")
	disc_tray_present = (ret_val == 0)

	cmd.log('update-pciids')

	# Update Bluetooth device presence
	# TODO Check for false-positives
	bt_f1 = cmd.log('rfkill list | grep -i blue') == 0
	bt_f2 = cmd.log('lsusb | grep -i blue') == 0 # TODO Improve USB BT adapter detection
	bt_f3 = cmd.log('lspci | grep -i blue') == 0
	bt_f4 = cmd.log('dmesg | grep -i blue') == 0
	bt_present = bt_f1 or bt_f2 or bt_f3 or bt_f4

	# Update virtualized state
	ret_val = cmd.log('cat /proc/cpuinfo | grep hypervisor')
	if ret_val == 0:
		vm_env = 'other'
		# Try & identify the VM platform
		board_name = io.read_ln('/sys/devices/virtual/dmi/id/board_name').rstrip() # e.g. 'VirtualBox'
		if board_name == 'VirtualBox':
			vm_env = 'vbox'
		else:
			prod_name = io.read_ln('/sys/devices/virtual/dmi/id/product_name').rstrip() # e.g. 'VMware7,1'
			if prod_name.startswith('VMware'):
				vm_env = 'vmware'

def timezone_setup():
	write_msg('Settings datetime & timezone settings...', 1)
	ret_val = cmd.log('ln -sf /usr/share/zoneinfo/%s /etc/localtime' % timezone)
	timescale = 'localtime' if use_localtime else 'utc'
	cmd.log('hwclock --systohc --%s' % timescale)
	cmd.log('timedatectl set-local-rtc ' + '0' if timescale == 'utc' else '1')
	write_status(ret_val)
	if ret_val != 0:
		log("[setup.py:timezone_setup()] ERROR: Couldn't set timezone as '%s'. Most likely cause: invalid timezone" % timezone)

def locale_setup():
	cmd.log('cp /etc/locale.gen /etc/locale.gen.bak')

	# /etc/locale.conf
	for locale in locales.split(','): # e.g. ' en_US ','fi_FI'
		locale = locale.strip() # e.g. ' en_US ' => 'en_US'
		found = False
		# Assume UTF-8 locale
		if '.' not in locale or ' ' not in locale or '-' not in locale:
			write_msg("Finding matching UTF-8 locale for '%s' in /etc/locale.gen..." % locale, 1)
			list = [ '%s.UTF-8' % locale, '%s UTF-8' % locale ]
			for opt in list:
				ret_val = io.uncomment_ln('/etc/locale.gen', '%s' % opt)
				if ret_val == 0:
					found = True
					break
			write_status(0 if found else 1)

		# UTF-8 locale not found OR full locale definition
		if not found:
			write_msg("Finding any matching locale for '%s' in /etc/locale.gen..." % locale, 1)
			# TODO Return uncommented line & use for future purposes
			ret_val = io.uncomment_ln('/etc/locale.gen', '%s' % locale)
			write_status(ret_val)
			if ret_val != 0:
				log("[setup.py:locale_setup()] WARN: Couldn't find locale '%s' in /etc/locale.gen" % locale)

	write_msg('Generating chosen locales, please wait...', 1)
	ret_val = cmd.log('locale-gen')
	write_status(ret_val)

	write_msg('Creating /etc/locale.conf...', 1)

	# TODO Expect '.UTF-8' locale IF no '.' in locale definition string

	# /etc/locale.conf
	locale_conf = ''
	if LANG != '':       # Main system locale used e.g. 'en_US.UTF-8'
		locale_conf += 'LANG=%s\n' % LANG
	if LANGUAGE != '':   # Fallback language ordered list e.g. 'en_AU:en_GB:en'
		locale_conf += 'LANGUAGE=%s\n' % LANGUAGE
	if locale_conf != '':
		locale_conf += '\n'
	if LC_COLLATE != '': # Locale for sorting and regular expressions e.g. 'C'
		locale_conf += 'LC_COLLATE=%s\n' % LC_COLLATE
	if LC_ALL != '':     # Locale used for other localized UI content e.g. 'en_US.UTF-8'
		locale_conf += 'LC_ADDRESS=§\nLC_IDENTIFICATION=§\nLC_MEASUREMENT=§\nLC_MONETARY=§\nLC_NAME=§\nLC_NUMERIC=§\nLC_PAPER=§\nLC_TELEPHONE=§\nLC_TIME=§'.replace('§', LC_ALL)

	log("\n/etc/locale.conf\n================\n%s\n================\n" % locale_conf)

	if locale_conf != '':
		ret_val = io.write('/etc/locale.conf', locale_conf)
		write_status(ret_val)
		if ret_val != 0:
			log("[setup.py:locale_setup()] ERROR: Locale conf couldn't be written!")

# TODO Finish up, find workaround for adding rules
def ufw_setup():
	write_msg("Setting up uncomplicated firewall...", 1)
	errors = pkg.install('ufw')
	#errors += cmd.log('systemctl enable ufw')
	# TODO Need to run '# ufw enable' as well
	write_status(errors)

	#write_msg("Setting up basic ufw rules...", 1)
	#errors = cmd.log('ufw default deny')

	# TODO Cannot add rules in chroot: find a workaround?

	# TODO Make work for IPv6 too? '2001:db8::/32'
	#ipv6 = ':' in out
	#out = cmd.output('ip a | grep global').split('\n')[0].split(' ')[5] # e.g. '192.168.1.108/24'
	#start = out.rsplit('.', 1)[0] # e.g. '192.168.1'
	#mask = out.rsplit('/', 1)[1]  # e.g. '24'
	#cidr = '%s.0/%s' % (start, mask) # e.g. '192.168.1.0/24'
	#errors += cmd.log('ufw allow from %s' % cidr)

	#if ssh_server_type > 0:
	#	errors += cmd.log('ufw limit SSH')

	#if web_server_type > 0:
	#	errors += cmd.log('ufw allow HTTP')
	#	errors += cmd.log('ufw allow HTTPS')

	# TODO Allow more services once instlalled e.g. 'KTorrent' on KDE DE etc

	#write_status(errors)

def networking_setup():
	global hostname
	# Generate hostname based on motherboard model
	if hostname == '':
		hostname = 'Arch-'
		if vm_env != 'vmware':
			hostname += io.read_ln('/sys/devices/virtual/dmi/id/board_name').rstrip() # e.g. 'Z270N-WIFI'
		else:
			hostname += 'VMware'

	# /etc/hostname
	write_msg("Setting hostname as '%s'..." % hostname, 1)
	ret_val = io.write('/etc/hostname', hostname)
	log("[setup.py:networking_setup()] INFO: Hostname is '%s'" % hostname)
	write_status(ret_val)

	# /etc/hosts
	write_msg("Generating hosts file...", 1)
	hosts = '# hosts - static table lookup for hostnames\n127.0.0.1	localhost\n::1		localhost\n127.0.1.1	§.localdomain	§'.replace('§', hostname)
	ret_val = io.write('/etc/hosts', hosts)
	log("\n/etc/hosts\n==========\n%s\n==========\n" % hosts)
	write_status(ret_val)

	# NetworkManager
	write_msg("Setting up NetworkManager, please wait...", 1)
	ret_val = pkg.install('networkmanager')
	ret_val += cmd.log('systemctl enable NetworkManager')
	write_status(ret_val)

	if enable_firewall:
		ufw_setup()

def aur_setup():
	write_msg('Installing dependencies for AUR support, please wait...', 1)
	ret_val = pkg.install('base-devel git')
	write_status(ret_val)
	if ret_val == 0: # Git install successfull
		write_msg('Fetching & installing yay from the AUR, please wait...', 1)
		# TODO Cache yay build if cachedir found?
		ret_val = cmd.log('$ cd && git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin && makepkg -sric --skippgpcheck --noconfirm --needed')
		write_status(ret_val)
		if ret_val == 0: # Yay install successfull
			cmd.log('rm -rf /home/%s/yay-bin' % user) # Delete old build folder

			# Allow access to pkgcache AUR builddir
			if os.path.exists('/pkgcache'):
				cmd.log('chown %s:users /pkgcache/pkgcache/aur/' % user)
				# TODO Maybe needs chmod?

			# Optimize makepkg for building on all CPU cores
			# TODO Other makepkg.conf optimizations
			io.replace_ln('/etc/makepkg.conf', '#MAKEFLAGS="', 'MAKEFLAGS="-j$(nproc)"')

def user_setup():
	# TODO Setup other users too
	write_msg("Setting up regular user '%s'..." % user, 1)
	errors = cmd.log('useradd -m -g users -G wheel,storage,input %s' % user)
	errors += cmd.suppress('cp /etc/sudoers /etc/sudoers.bak')

	# TODO Create an actual replace by line number function
	# Give wheel group users sudo permission w/o pass
	errors += cmd.exec("sed '85 s/^# //' /etc/sudoers > /etc/sudoers.tmp")
	errors += cmd.suppress("mv /etc/sudoers.tmp /etc/sudoers")
	errors += cmd.suppress("chmod 440 /etc/sudoers")
	write_status(errors)

	if enable_aur:
		aur_setup()

def multilib_setup():
	write_msg('Including multilib repo in /etc/pacman.conf...', 1)
	cmd.suppress('cp /etc/pacman.conf /etc/pacman.conf.bak')
	ln = io.get_ln_number('/etc/pacman.conf', '#[multilib]') # should be 93
	if ln != -1:
		# "[multilib]"
		errors = cmd.exec('sed "%s s/^#//" /etc/pacman.conf > /etc/pacman.conf.tmp' % str(ln))
		errors += cmd.suppress('mv /etc/pacman.conf.tmp /etc/pacman.conf')
		# "Include = /etc/pacman.conf.d/mirrorlist"
		errors += cmd.exec('sed "%s s/^#//" /etc/pacman.conf > /etc/pacman.conf.tmp' % str(ln + 1))
		errors += cmd.suppress('mv /etc/pacman.conf.tmp /etc/pacman.conf')

		write_status(errors)
		if errors == 0:
			pkg.refresh_dbs(False, 'Refreshing pacman package databases, please wait...')
	else:
		write_status(1)

def sshd_setup():
	write_msg('Setting up OpenSSH server...', 1)
	ret_val = pkg.install('openssh')
	write_status(ret_val)

	if ssh_server_type == 2:
		cmd.log('systemctl enable sshd.service')
	else:
		cmd.log('systemctl enable sshd.socket')

def lts_kernel_setup():
	write_msg('Switching to the Linux LTS kernel, please wait...')
	ret_val = pkg.remove('linux', "Removing regular 'linux' kernel...")
	write_status(ret_val)
	ret_val = pkg.install('linux-lts', "Installing the 'linux-lts' kernel...")
	write_status(ret_val)

def bootloader_setup():
	# TODO Systemd-boot alternative to GRUB?
	write_msg('Fetching dependencies for the GRUB bootloader...', 1)
	pkgs = 'grub dosfstools'
	pkgs += '' if vm_env != '' else ' %s-ucode' % cpu_type
	ret_val = pkg.install(pkgs)
	write_status(ret_val)

	write_msg('Installing GRUB in %s mode, please wait...' % boot_mode, 1)
	if boot_mode == 'UEFI':
		errors = pkg.install('efibootmgr')
		errors += cmd.log('grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id="GRUB"')
		write_status(errors)
	else: # BIOS/CSM
		ret_val = cmd.log('grub-install --recheck %s' % mbr_grub_dev)
		write_status(ret_val)

	write_msg('Creating initial GRUB config, please wait...', 1)
	ret_val = cmd.log('grub-mkconfig -o /boot/grub/grub.cfg')
	write_status(ret_val)

def x_setup():
	mid = 'minimal' if xorg_install_type == 1 else 'the'
	write_msg('Installing %s X display server components...' % mid, 1)
	pkgs = 'xorg' if xorg_install_type == 2 else 'xorg-server xorg-xinit xf86-input-libinput'
	pkgs += ' xf86-input-vmmouse' if vm_env == 'vmware' else ''
	ret_val = pkg.install(pkgs)
	write_status(ret_val)

	# TODO Multi-user support
	if user != '':
		cmd.log('gpasswd -a %s video' % user)

def vm_setup():
	# TODO Implement setting up VBox additions & VMware
	write_msg('Setting up virtualization tools for %s guest...' % vm_env, 1)
	errors = pkg.install('sshfs')

	if vm_env == 'vbox':
		pkgs = 'virtualbox-guest-modules-arch virtualbox-guest-utils' + '-nox ' if xorg_install_type == 0 else ''
		errors += pkg.install(pkgs)
		errors += cmd.log('systemctl enable vboxservice')
		errors += cmd.log('modprobe -a vboxguest vboxsf vboxvideo')
		# TODO execute VBoxClient-all when X is enabled?
		# TODO Multi-user support
		if user != '':
			errors += cmd.log('gpasswd -a %s vboxsf' % user)
		cmd.log('mkdir -p /media')
		cmd.log('chmod 755 /media')
		if user != '':
			cmd.log('chown %s:vboxsf /media' % user)
	elif vm_env == 'vmware':
		# TODO Use official VMware tools somehow?
		# TODO Make mkinitcpio.conf modifications:
		# /etc/mkinitcpio.conf
		# MODULES="... vmw_balloon vmw_pvscsi vsock vmw_vsock_vmci_transport ..."
		# mkinitcpio -p linux
		errors += pkg.install('linux%s-headers dkms fuse gtkmm3 open-vm-tools' % ('-lts' if use_lts_kernel else ''))
		# TODO Use https://github.com/vmware/open-vm-tools instead & compile since AUR package broken?
		errors += pkg.aur_install('open-vm-tools-dkms')
		errors += cmd.log('systemctl enable vmtoolsd vmware-vmblock-fuse')

	write_status(errors)

def audio_setup():
	# TODO Add plain ALSA support
	write_msg('Setting up audio support via pulseaudio...', 1)
	errors = pkg.install('pulseaudio pulseaudio-alsa pamixer libpulse ')

	# Media codecs
	# TODO Add back after gstreamer 1.15: gst-plugins-bad (broken NVDEC fixed)
	errors += pkg.install('gst-libav gst-plugins-base gst-plugins-good gst-plugins-ugly realtime-privileges')

	# Event sounds
	errors += pkg.install('libcanberra libcanberra-gstreamer libcanberra-pulse')
	if enable_multilib:
		errors += pkg.install('lib32-libcanberra lib32-libcanberra-gstreamer lib32-libcanberra-pulse')

	write_status(errors)

	# TODO Multi-user support
	if user != '':
		cmd.log('gpasswd -a %s realtime' % user)

def bt_setup():
	# NOTE Auto-detect is imperfect => allow overriding
	# NOTE External firmware may be required for proper BT functionality e.g. BCM cards
	write_msg('Installing Bluetooth support, please wait...', 1)
	errors = pkg.install('bluez bluez-libs bluez-utils ell')
	errors += cmd.log('systemctl enable bluetooth')
	write_status(errors)

	# TODO Fix FAIL?
	write_msg('Installing BT audio support, please wait...', 1)
	errors = 0
	# TODO Add ALSA support
	if enable_aur:
		# Extra codecs
		errors += pkg.aur_install('libldac pulseaudio-modules-bt-git')
	else:
		errors += pkg.install('pulseaudio-bluetooth')

	# Auto-enable BT on startup (TODO use tlp config on laptops)
	if not bat_present:
		errors += io.replace_ln('/etc/bluetooth/main.conf', '#AutoEnable=false', 'AutoEnable=true')

	# Switch audio source to new sink on connection
	errors += cmd.log('sed -i "22s/.*/\\n# automatically switch to newly-connected devices\\nload-module module-switch-on-connect\\n/" /etc/pulse/default.pa')
	write_status(errors)

def vga_setup():
	write_msg('Setting up graphics card drivers, please wait...', 1)
	vga_out = cmd.output("lspci -nn | grep '\\[03'").lower()
	log('\n[setup.py:vga_setup()] Found GPUs:\n%s\n' % vga_out)
	mesa_install_type = 0 # Install mesa DRI for 3D acceleration
	errors = pkg.install('libglvnd')
	if enable_multilib:
		errors += pkg.install('lib32-libglvnd')

	if vm_env == '':
		# e.g. 'nvidia corporation gm204 [geforce gtx 970]'
		if 'nvidia' in vga_out:
			# Card driver detection
			fermi_gpus = [ 'gf100','gf104','gf106','gf108','gf110','gf114','gf116','gf117','gf119' ] # 390xx
			kepler_gpus = [ 'gk104','gk106','gk107','gk110','gk208','gk210','gk20a' ] # 390xx
			tesla_gpus = [ 'g80','g84','g86','g92','g94','g96','g98','gt200','gt215','gt216','gt218','mcp77','mcp78','mcp79','mcp7a','mcp89' ] # 340xx
			unsupported_gpus = [ 'nv1a','nv1f','g70','g71','g72','g73','nv44a','c51','mcp61','mcp67','mcp68','mcp73' ] # noveau
			for x in range(10, 45): # nv10-nv44
				unsupported_gpus.append('nv' + x)
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
			log("\n[setup.py:vga_setup()] Detected nVidia card type: '%s'\n" % card)

			# TODO Remove /etc/X11/xorg.conf and other discrete configs?
			# Bumblebee driver for nVidia Optimus systems
			if 'intel' in vga_out:
				mesa_install_type = 1
				errors += pkg.install('bumblebee xf86-video-intel')
				errors += cmd.log('gpasswd -a %s bumblebee' % user)
				errors += cmd.log('systemctl enable bumblebeed')
				if enable_multilib:
					errors += pkg.install('lib32-virtualgl')

			# TODO Check if matching works
			if gpu == 'F' or gpu == 'K':
				# nvidia-390xx, nVidia cards from around 2010-2011
				errors += pkg.install('nvidia-390xx%s nvidia-390xx-utils nvidia-390xx-settings' % ('-lts' if use_lts_kernel else ''))
				if enable_multilib:
					errors += pkg.install('lib32-nvidia-390xx-utils')
			elif gpu == 'T':
				# nvidia-340xx, nVidia cards from around 2006-2010
				errors += pkg.install('nvidia-340xx%s nvidia-340xx-utils nvidia-340xx-settings' % ('-lts' if use_lts_kernel else ''))
				if enable_multilib:
					errors += pkg.install('lib32-nvidia-340xx-utils')
			elif gpu == 'U':
				# use noveau, nVidia cards from <= 2006
				mesa_install_type = 2
				errors += pkg.install('xf86-video-nouveau')
			else:
				# Expect current nVidia cards from around 2010 onwards
				errors += pkg.install('nvidia%s nvidia-utils nvidia-settings' % ('-lts' if use_lts_kernel else ''))
				if enable_multilib:
					errors += pkg.install('lib32-nvidia-utils')

			if mesa_install_type < 2:
				errors += pkg.install('libvdpau')
				if enable_multilib:
					errors += pkg.install('lib32-libvdpau')

				if mesa_install_type == 0:
					errors += pkg.install('xorg-server-devel')
					# Generate X.org config
					errors += cmd.log('nvidia-xconfig')

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
			errors += pkg.install('xf86-video-amdgpu vulkan-radeon')
			# TODO Only install on Vulkan capable GPUs
			if enable_multilib:
				errors += pkg.install('lib32-vulkan-radeon')

			# libva-mesa-driver vulkan-radeon
			# TODO 'amdgpu.dc=1' as kernel/module option
			# also 'radeon.cik_support=0 amdgpu.cik_support=1' etc depending on card GCN version
			# 'MODULES=(amdgpu radeon)' in /etc/mkinitcpio.conf

		# e.g. 'intel corporation hasswell-ult integrated graphics'
		elif 'intel' in vga_out:
			errors += pkg.install('xf86-video-intel vulkan-intel')
			# TODO Only install on Vulkan capable GPUs
			if enable_multilib:
				errors += pkg.install('lib32-vulkan-intel')

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
		if 'vmware' in vga_out:
			errors += pkg.install('xf86-video-vmware')
		else:
			errors += pkg.install('xf86-video-fbdev')

	if mesa_install_type > 0:
		errors += pkg.install('mesa libva-mesa-driver mesa-vdpau')
		if enable_multilib:
			errors += pkg.install('lib32-mesa lib32-libva-mesa-driver lib32-mesa-vdpau')
		pass # TODO libva-mesa-driver mesa lib32-mesa ...

	# TODO Only install on Vulkan capable GPUs
	errors += pkg.install('vulkan-icd-loader')
	if enable_multilib:
		errors += pkg.install('lib32-vulkan-icd-loader')

	# Video acceleration
	if enable_aur:
		errors += pkg.aur_install('libva-vdpau-driver-chromium')
	#else: errors += pkg.install('libva-vdpau-driver')

	write_status(errors)

# TODO Install DE
def de_setup():
	pass



def bootloader_extra_setup():
	write_msg('Installing GRUB multiboot support dependencies...', 1)
	ret_val = pkg.install('ntfs-3g os-prober')
	write_status(ret_val)

	write_msg('Finding other bootloaders to add to GRUB menu...', 1)
	# TODO Figure out lvme_tad slowdown if running grub-mkconfig after installing os-prober...
	ret_val = cmd.log('grub-mkconfig -o /boot/grub/grub.cfg')
	write_status(ret_val)

	cmd.suppress('umount /run/lvm')

def chroot_setup():
	global hostname, mbr_grub_dev, cpu_type

	if multibooting:
		# LVM 10 sec slow scan temp fix when installing os-prober
		cmd.suppress('mkdir -p /run/lvm && mount --bind /hostrun/lvm /run/lvm')

	# Update defailt about HW e.g. running in VM, cpu type, MBR boot dev etc.
	load_hw_info()

	log('[setup.py:chroot_setup()] HW details:')
	log("CPU                 '%s'" % cpu_type)
	log("MBR_GRUB_DEV        '%s'" % mbr_grub_dev)
	log("BAT_PRESENT         '%s'" % bat_present)
	log("DISC_TRAY_PRESENT   '%s'" % disc_tray_present)
	log("BT_PRESENT          '%s'" % bt_present)
	log("VM_ENV              '%s'" % vm_env)

	write_status(0) # Change 'Chrooting...' status msg to DONE

	timezone_setup()
	locale_setup()
	networking_setup()
	if user != '': user_setup()
	if enable_multilib: multilib_setup()
	if ssh_server_type > 0: sshd_setup()
	if use_lts_kernel: lts_kernel_setup()
	bootloader_setup()
	# TODO Web server stack setup, user groups: 'http'
	#if web_server_type > 0: ...
	if xorg_install_type > 0: x_setup()
	if vm_env != '': vm_setup()
	if use_pulseaudio: audio_setup()
	if bt_present: bt_setup()
	if auto_detect_gpu: vga_setup()
	if de.replace('none', '') != '': de_setup()

	# TODO DE Setup
	# TODO Snapd & flatpak support?
	# TODO Assistive techologies setup
	# TODO Printing & scanning setup, user groups: 'scanner, sys, lp'
	# TODO Wine setup?

	# TODO Use proper keymap in ALL DEs

	# TODO Check for other HW too e.g. fingerprint scanner (check lspci etc) & install proper packages
	# TODO TLP power saving setup (BAT found)
	# TODO Query for BATTERY to install TLP etc (bat_present)
	# TODO Detect laptop by checking battery to install tlp etc
	# TODO Query for DVD/CD drive to install bluray etc support (disc_tray_present)

	# TODO Boot time improvements

	# TODO On KDE make theming direcoties automatically e.g. '~/.local/share/plasma/look-and-feel/' etc
	# TODO Create ~/.local/share/(fonts|icons|themes) etc

	custom_setup()
	if multibooting: bootloader_extra_setup()

	write_ln()
	write_msg(color_str('Create a password for the §2root §0user:\n\n'))
	cmd.exec('passwd')
	write_ln()
	if user != '':
		# TODO Do the same for other accounts
		write_msg(color_str('Create a password for the regular user §3%s§0:\n\n' % user))
		cmd.exec('passwd %s' % user)
		write_ln()

	if sudo_ask_pass:
		cmd.suppress('cp /etc/sudoers.bak /etc/sudoers')

		# TODO Create an actual replace by line number function
		# Give wheel group users sudo permission w/ pass
		cmd.exec("sed '82 s/^# //' /etc/sudoers > /etc/sudoers.tmp")
		cmd.suppress("mv /etc/sudoers.tmp /etc/sudoers")
		cmd.suppress("chmod 440 /etc/sudoers")

	log("\n#\n# End of chroot log\n#")

	# Move log to /var/log/
	cmd.log('mv /setup.log /var/log/')




###############################
# Actual script
###############################

# Run env sanity checks
check_env()

# Check privileges
check_privs()

args = ' '.join(sys.argv[1:]) # e.g. '-v --test'
if args != '':
	log("[setup.py] Script start arguments: '%s'" % args)

# Continue install if in chroot
if in_chroot == 1:
	chroot_setup()
	exit(0)

log("[setup.py] Device boot mode: '%s'" % boot_mode)


# TODO Add -R arg flag for chroot repair operations menu etc

debug = '-d' in args
if debug:
	cmd.suppress('rm /tmp/setup.log') # Remove possible old (ONLY DEBUG?)

# Load color scheme
load_colors()

write_msg(color_str('Arch §7Linux '))
write(color_str('§4%s §0live environment was detected. Press ENTER to continue...' % boot_mode))
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
pkg.refresh_dbs(False, 'Refreshing pacman package databases, please wait...')

# Load font
load_font()

# Update used installer packages
# TODO Check if the packages *actually* need to be updated (with pacman -Qs pkg?)
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
if enable_ntp:
	ntp_setup()

write_msg('Entering disk partitioning menu...', 1)
time.sleep(0.25)
partitioning_menu()

log('\n[setup.py] Block device map after partitioning:\n')
cmd.log("lsblk | grep -v '^loop' | grep -v '^sr0'; echo")
cmd.log("blkid | grep -v '^/dev/loop' | grep -v '^/dev/sr0'; echo")

mounting_menu()

sys_root = '/' # TODO Change for Btrfs volumes
sys_root = '/mnt%s' % sys_root

print_header('Installing Arch Linux')
write_msg('Starting Arch Linux install process...', 1)
ret_val = pkg.install('arch-install-scripts', False)
write_status(ret_val)

if not '-M' in args: sort_mirrors()

base_install(sys_root)

start_chroot(sys_root)

# Install done! Cleanup & reboot etc.
cmd.suppress('cp %svar/log/setup.log /tmp/' % sys_root)

# Clean up setup files
cmd.suppress('rm -f %sroot/setup.py' % sys_root)
cmd.suppress('rm -f %sroot/config.py' % sys_root)

if os.path.exists('/mnt/pkgcache'):
	cmd.suppress('chown root:root /pkgcache/pkgcache/aur/')
	cmd.suppress('umount /mnt/pkgcache; cd')
	cmd.suppress('rm -rf /mnt/pkgcache')
	cmd.suppress('mv /etc/pacman.conf.bak /etc/pacman.conf')

# END OF SCRIPT
write_ln(color_str('§3>> The install script is done!'), 2)
exit(0)

# TODO '# umount -R /mnt'
# TODO '# reboot'
