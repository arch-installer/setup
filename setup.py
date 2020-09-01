#!/usr/bin/env python3
#
#  Project     : ArchInstaller.py (https://git.io/fjFL6)
#  Author      : JamiKettunen (https://git.io/fj0wc)
#  License     : MIT (https://git.io/fjdxG)
#  Reference   : The Wiki (https://wiki.archlinux.org/index.php/Installation_guide)
#  Description : My personal Arch Linux installer script
#

# File IO, argv, run, sleep, ...
import os, sys, subprocess, time, re, random

# Import configured user variables
try:
	from config import *
except ModuleNotFoundError: pass



###############################
# Custom setup
###############################

def custom_setup():
	# ------------ Custom system & packages setup goes here...

	# Install custom packages
	write_msg("Installing custom packages & applications...", 1)
	errors = Pkg.install('bash-completion lsof strace psutils gnu-netcat reflector vim htop neofetch lm_sensors rsync tree')
	if enable_aur:
		errors += Pkg.aur_install('c-lolcat downgrade')

	if de != '':
		# Xorg, MIME, cursors, fonts etc
		errors += Pkg.install('xorg-xkill xorg-xprop xorg-xrandr xorg-xauth x11-ssh-askpass xorg-fonts-alias-misc perl-file-mimeinfo perl-net-dbus perl-x11-protocol lsd ctags trash-cli wget capitaine-cursors youtube-dl python-pycryptodome')

		if install_de_apps and vm_env == '':
			errors += Pkg.install('noto-fonts-emoji noto-fonts-cjk code discord')
			hide_app('electron6')

			# Steam
			if enable_multilib and not bat_present:
				errors += Pkg.install('steam wqy-zenhei lib32-libldap')
				IO.replace_ln(f'{apps_path}/steam.desktop', 'Name=', 'Name=Steam')

		# Powerline status for Vim
		# TODO: Install powerline-status from AUR (python-powerline-git) instead to avoid pip package conflicts in the future?
		Pkg.install('python-lazy-object-proxy python-wrapt python-typed-ast python-astroid python-mccabe python-isort python-pylint')
		Cmd.log('python -m pip install -U powerline-status')

	write_status(errors)

	# ------------ Wi-Fi setup

	if vm_env == '':
		wifi_setup = Cmd.suppress('lspci | egrep -i "wireless|wlan|wifi"') == 0
		if wifi_setup:
			write_msg("Setting up Wi-Fi hardware...", 1)
			errors = Pkg.install(f'crda {kernel}-headers')
			errors += IO.uncomment_ln('/etc/conf.d/wireless-regdom', f'WIRELESS_REGDOM="{LC_ALL[3:5]}"') # e.g. "FI"

			bcm_install = Cmd.suppress('lspci | egrep -i "bcm|broadcom"') == 0
			if bcm_install:
				errors += Pkg.install('broadcom-wl-dkms')

				# BCM4352
				if Cmd.suppress('lspci | grep -i bcm4352') == 0:
					errors += Pkg.aur_install('bcm20702a1-firmware')

			write_status(errors, 0, 4)

	# ------------ GRUB theme setup (when multibooting)

	if multibooting:
		write_msg("Configuring custom 'Tela' GRUB theme...", 1)
		errors = IO.replace_ln(grub_conf, '#GRUB_THEME=', 'GRUB_THEME="/usr/share/grub/themes/Tela/theme.txt"')
		errors += Cmd.exec('cd /tmp; git clone --depth 1 https://github.com/vinceliuice/grub2-themes.git &>>/setup.log && sed "/GRUB_THEME/d" -i grub2-themes/install.sh && grub2-themes/install.sh -t &>>/setup.log')
		write_status(errors)

	# ------------ TLP tweaks (TODO Move changes to laptop repo)

	if bat_present:
		file = '/etc/default/tlp'
		IO.replace_ln(file, 'TLP_DEFAULT_MODE=', 'TLP_DEFAULT_MODE=BAT')
		IO.replace_ln(file, '#CPU_SCALING_GOVERNOR_ON_AC=', 'CPU_SCALING_GOVERNOR_ON_AC=performance')
		IO.uncomment_ln(file, 'CPU_SCALING_GOVERNOR_ON_BAT=') # powersave
		IO.replace_ln(file, 'RESTORE_DEVICE_STATE_ON_STARTUP=', 'RESTORE_DEVICE_STATE_ON_STARTUP=1')



###############################
# "Constant" values
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

# Runtime vars
script_path, script_fn = os.path.split(os.path.abspath(sys.argv[0])) # Script filename  e.g. 'setup.py'
script_path += ('/' + script_fn)            # Full script path e.g. '/root/setup.py'
script_root = script_path.rsplit('/', 1)[0] # Directory path of script e.g. '/root'

# Vars updated on script load
args = ''                 # All arguments in one string
boot_mode = 'BIOS/CSM'    # 'BIOS/CSM' / 'UEFI'
mbr_grub_dev = ''         # GRUB install device on MBR systems e.g. '/dev/sda'
kernel = 'linux'          # Used by the script for kernel specific configuration like pkgs; e.g. 'linux-lts', 'linux-hardened'
use_dkms_pkgs = False     # Disabled for vanilla 'linux' kernel
cpu_family = ''           # CPU family number e.g. '6'
cpu_model = ''            # CPU model number e.g. '60'
cpu_identifier = ''       # CPU identifier e.g. 'intel_6-60-4'
in_chroot = False         # Inside chroot?
vm_env = ''               # Virtualized env: '','vbox','vmware','qemu','other'
bat_present = False       # Any battery present?
disc_tray_present = False # Any disc tray present?
bt_present = False        # Any BT device present?
camera_present = False    # Any camera device present?
video_drv = ''            # e.g. 'nvidia','nvidia-340','noveau+mesa','amdgpu+mesa','intel+mesa','bumblebee' etc
use_qt_apps = False       # Get Qt versions of apps
unres_users = []          # List of users with admin rights
aur_cache = ''            # Path of cached AUR packages e.g. '/pkgcache/pkgcache/aur/intel_6-60-4'
pkgcache_enabled = os.path.exists('/pkgcache')

# Other vars
lsblk_cmd = "lsblk | grep -v '^loop' | grep -v '^sr0'"
blkid_cmd = "blkid | grep -v '^/dev/loop' | grep -v '^/dev/sr0'"
apps_path = '/usr/share/applications'
cflags = '-march=native -O2 -pipe -fstack-protector-strong -fno-plt'
mounts = '' # Current mounts e.g. '/efi:/dev/sda1,root:/dev/sda2'
grub_conf = '/etc/default/grub'
outdated_pkgs = ''
menu_visit_counter = 0



###############################
# Helper functions
###############################

# Clear the entire screen buffer
def clear_screen():
	Cmd.exec('clear', '', False)

# Printing text

# Returns a string with parsed terminal output forecolor; usage:
# e.g. color_str("§2red §0reset §5blue")

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
def color_str(string, reset=True):
	if '§' in string: # Possible color definition found
		for f in range(0, 9): # Forecolor only: (0-8)
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

# Writes text to stdout with optional coloring; see color_str()
def write(text):
	if '\\§' in text: text = text.replace('\\§', '§') # '\§' => '§'
	elif '§' in text: text = color_str(text)

	sys.stdout.write(text)
	sys.stdout.flush()

# Writes a line of text to stdout with optional coloring; see color_str()
def write_ln(text='', new_line_count=1):
	for _ in range(0, new_line_count):
		text += '\n'
	write(text)

# Clears the screen & prints a *nice* looking header
def print_header(header):
	ul = ('=' * len(header)) # e.g. '============='
	clear_screen()
	write_ln(f'§7{header}') # e.g. 'A Nice Header'
	write_ln(f'§7{ul}', 2) 

# Writes a status message; see status_mgs & status_colors. Examples:
#   >> Using log engine v2.0
#   >> [ WAIT ] Fetching latest data...
#   >> [  OK  ] Started NetworkManager service
#   >> [ FAIL ] ...
def write_msg(msg, status=0, override_newline=-1):
	if status > 0:
		color = status_colors.get(status)
		status_msg = status_mgs.get(status, 0)
		write(f'§{color}>> [ {status_msg} ] ') # e.g. '>> [ WAIT ] '
	else:
		write('§7>> ') # '>> '

	new_ln = True if override_newline == -1 and status > 1 else False
	new_ln = True if override_newline == 1 else new_ln
	write(msg + ('\n' if new_ln else ''))

# Writes back to the current status message line to update the appearance depending on a command's return value
#   write_status(0, 0)
#   '>> [ DONE ]'
#   write_status(1, 0, 4)
#   '>> [ WARN ]'
def write_status(ret_val=0, expected_val=0, error_status=3):

	if ret_val == expected_val:
		status_msg = status_mgs.get(2)
		write_ln(f'\r§3>> [ {status_msg} ]')
	else:
		color = status_colors.get(error_status)
		status_msg = status_mgs.get(error_status)
		write_ln(f'\r§{color}>> [ {status_msg} ]')

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
			mode = 'a' if append else 'w'
			with open(f_path, f'{mode}+') as f:
				f.write(text)
			return 0
		except:
			return 1

	# Appends text to a file
	# Returns: 0 = Success, 1 = Error
	#@staticmethod
	#def append(f_path, text):
	#	return IO.write(f_path, text, True)

	# Writes a line to a file
	# Returns: 0 = Success, 1 = Error
	@staticmethod
	def write_ln(f_path, text='', append=True):
		return IO.write(f_path, text + '\n', append)

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
	# Refresh local package database cache
	# Quit script execution on error
	@staticmethod
	def refresh_dbs(force_refresh=False, quit_on_fail=True):
		cmd = 'pacman -Sy'
		cmd += 'y' if force_refresh else ''
		ret_val = Cmd.log(cmd)
		if ret_val != 0 and quit_on_fail:
			log_path = 'mnt' if in_chroot else 'tmp'
			write_ln(f'§2ERROR: §0Database refreshing failed. Check /{log_path}/setup.log for details')
			exit_code = 8 if force_refresh else 7
			exit(exit_code) # 7 = Couldn't synchronize databases, 8 = Force-refresh failed
		return ret_val

	# Install packages from the Arch repositories (core, extra, community)
	# or optionally a local package with the absolute path defined
	# Returns: pacman exit code
	@staticmethod
	def install(pkgs, only_needed=True):
		pac_args = '--needed' if only_needed else ''
		local = ('/' in pkgs)
		if pkgcache_enabled and in_chroot and not local:
			pac_args += ' --cachedir /pkgcache/pkgcache'
		if len(pac_args) > 0: pac_args = ' ' + pac_args.strip()
		action = 'U' if local else 'S'
		ret_val = Cmd.log(f'pacman -{action} --noconfirm --noprogressbar{pac_args} {pkgs}')
		return ret_val

	# Install Arch package groups while optionally ignoring some of the members
	# Both 'groups' and 'excluded_pkgs' are space (' ') seperated lists
	# Returns: pacman exit code
	@staticmethod
	def install_group(groups, excluded_pkgs='', only_needed=True):
		tmp_pkgs = ''
		if len(excluded_pkgs) > 0:
			for pkg in excluded_pkgs.split(' '):
				tmp_pkgs += pkg + '|'
			excluded_pkgs = tmp_pkgs[:-1] # Remove last '|'
		pkgs = f'$(pacman -Sg {groups} | cut -d" " -f2'
		pkgs += (f' | egrep -v "{excluded_pkgs}"' if len(excluded_pkgs) > 0 else '') + ')'
		pac_args = '--needed' if only_needed else ''
		if pkgcache_enabled and in_chroot:
			pac_args += ' --cachedir /pkgcache/pkgcache'
		if len(pac_args) > 0: pac_args = ' ' + pac_args.strip()
		ret_val = Cmd.log(f'pacman -S {pkgs} --noconfirm --noprogressbar{pac_args}')
		return ret_val

	# Remove installed packages on a system
	# Returns: pacman exit code
	@staticmethod
	def remove(pkgs, also_deps=False, log_cmd=True):
		pac_args = '-Rn' + ('sc' if also_deps else '') + ' --noconfirm --noprogressbar'
		ret_val = Cmd.log(f'pacman {pac_args} {pkgs}', '', log_cmd)
		return ret_val

	# Install packages from the Arch User Repository (AUR)
	# Returns: pacman exit code
	@staticmethod
	def aur_install(pkgs, only_needed=True):
		if in_chroot:
			if enable_aur:
				yay_args = '--needed' if only_needed else ''
				if len(yay_args) > 0: yay_args = ' ' + yay_args.strip()
				errors = 0
				ccache_args = 'export PATH=/usr/lib/ccache/bin:$PATH USE_CCACHE=1; ' if use_ccache else '' # TODO Optimize, use 'env' instead?
				pkgs = pkgs.strip() # To mitigate user error
				if pkgcache_enabled:
					for pkg in pkgs.split(' '):
						pkg = pkg.strip() # To mitigate user error
						# TODO Check version differently for '-git' packages e.g. 'pulseaudio-modules-bt-git' report old pkg versions on yay query
						ver = Cmd.output(f'$ yay -Si {pkg} | grep Version', 'aurhelper').split(':', 1)[1].strip() # e.g. '3.3.0-1'
						latest_pkg = ''
						try: latest_pkg = str(Cmd.output(f'ls {aur_cache}/ | grep {pkg} | grep {ver}')).split('\n')[0].strip() # e.g. 'polybar-3.3.0-1-x86_64.pkg.tar.xz'
						except: pass
						if len(latest_pkg) > 0: # Up-to-date cached version found => install it instead
							errors += Pkg.install(f'{aur_cache}/{latest_pkg}', only_needed)
						else: # Cached version not found => fetch from the AUR
							ret_val = Cmd.log(f'$ {ccache_args}yay -Sq --noconfirm{yay_args} {pkg}', 'aurhelper')
							if ret_val == 0: # Installed => try caching package
								Cmd.log(f'cp /home/aurhelper/.cache/yay/{pkg}/*.pkg.tar.xz {aur_cache}/')
							errors += ret_val
				else:
					errors = Cmd.log(f'$ {ccache_args}yay -Sq --noconfirm{yay_args} {pkgs}', 'aurhelper')
				return errors
			else:
				log(f"[setup.py:Pkg.aur_install('{pkgs}')] WARN: Ignoring installation since AUR support is not present.")
		else:
			log(f"[setup.py:Pkg.aur_install('{pkgs}')] WARN: Ignoring installation since not in chroot.")
		return 1

# Command execution

class Cmd:
	# Run a command on the shell with an optional io stream
	# io_stream_type: 0 = none, 1 = stdout, 2 = logged, 3 = all_supressed
	# Returns: command exit code / output when io_stream_type=2
	@staticmethod
	def exec(cmd, exec_user='', log_cmd=True, io_stream_type=0):
		user_exec = cmd.startswith('$ ')
		exec_cmd = cmd

		if user_exec:
			if exec_user == '':
				exec_user = users.split(',')[0]
			cmd = cmd[2:] # Remove '$ ' from user_exec commands
			if len(exec_user) > 0:
				exec_cmd = f"sudo -i -u {exec_user} -H bash -c '{cmd}'"
			else:
				log(f"[setup.py:Cmd.exec({str(io_stream_type)})] WARN: Ignoring '{cmd}' execution, since no user was defined.")
				return 1

		use_stdout = (io_stream_type == 1)
		logged = (io_stream_type == 2)
		suppress = (io_stream_type == 3)

		# TODO Still log everything if launched with '-D' flag for debugging purposes
		if log_cmd and io_stream_type % 2 == 0: # Log executed command line ()
			start = '# ' + (f'({exec_user}) $ ' if user_exec else '')
			log(f'\n{start}{cmd}') # e.g. '# pacman -Syu'

		end = ''
		if suppress or logged:
			path = '' if in_chroot else '/tmp'
			log_path = f'{path}/setup.log' # e.g. '/tmp/setup.log' or '/setup.log' in chroot
			#end = ' &>>' + (log_path if (logged and log_cmd) else '/dev/null')
			end = ' ' + f'&>>{log_path}' if logged and log_cmd else '&>/dev/null'

		cmd = exec_cmd + end
		# TODO Log cmd line when debugging
		if use_stdout: res = subprocess.run(cmd, shell=True, encoding='utf-8', capture_output=use_stdout)
		else: res = subprocess.run(cmd, shell=True)

		if log_cmd and io_stream_type % 2 == 0 and res.returncode != 0:
			log(f'\n# Command non-zero exit code: {res.returncode}')

		returns = res.stdout if use_stdout else res.returncode
		return returns

	# Run a command on the shell while capturing all it's output
	# New lines are seperated with a '\n'
	# Returns: command exit code
	@staticmethod
	def output(cmd, exec_user='', log_cmd=True):
		return Cmd.exec(cmd, exec_user, log_cmd, 1)

	# Run a command on the shell while logging all it's output
	# Returns: command exit code
	@staticmethod
	def log(cmd, exec_user='', log_cmd=True):
		return Cmd.exec(cmd, exec_user, log_cmd, 2)

	# Run a command on the shell while supressing all it's output
	# Returns: command exit code
	@staticmethod
	def suppress(cmd, exec_user=''):
		return Cmd.exec(cmd, exec_user, False, 3)

	# Check whether a command e.g. 'nc' is available on a system
	# Returns: boolean
	@staticmethod
	def exists(cmd):
		ret_val = Cmd.suppress(f'type {cmd}') # command -v
		return (ret_val == 0)

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
	global de, users, boot_mode, in_chroot, kernel_type, kernel, use_dkms_pkgs, cpu_family, cpu_model, cpu_identifier, aur_cache, use_qt_apps, unres_users
	os_compat_msg = 'Please only run this script on the Arch Linux installer environment.\n\nhttps://www.archlinux.org/download/'
	file_msg = "It seems that you are missing a '§f' module.\n"
	if os.name == 'posix':
		ret_val = Cmd.suppress('cat /etc/hostname')
		if ret_val == 0:
			host = Cmd.output("grep -v '^#' /etc/hostname | tr -d '\n'")
			if host != 'archiso':
				print(os_compat_msg)
				exit(3) # 3 = Not running in ArchISO environment
		#elif host == hostname:
			# TODO Add post-install script parts => verify here
		else: # Read failed => Assume chroot environment
			# TODO Use a better chroot detection mechanism
			in_chroot = True

		if not in_chroot: in_chroot = os.path.isfile('/chroot')

		if in_chroot: Cmd.suppress('rm -f /chroot')

		# config.py
		try:
			kernel_type = kernel_type.strip().lower()

			if kernel_type == 'stable':
				kernel_type = ''
			else:
				kernel = 'linux-' + kernel_type # e.g. 'linux-lts', 'linux-hardened'
				use_dkms_pkgs = True

		except: # NameError
			print(file_msg.replace('§f', 'config.py'))
			write_msg(f'Would you like to try & §7fetch §0the file from GitHub? (§3Y§0/§2n§0)? §7>> ')
			ans = input().upper().replace('YES', 'Y')
			if len(ans) == 0 or ans == 'Y':
				write_ln()
				write_msg('Downloading latest revision of config.py from https://git.io/fjFmg...', 1)
				ret_val = Cmd.suppress(f'curl https://git.io/fjFmg -Lso {script_root}/config.py')
				write_status(ret_val)

			print()
			exit(4) # 4 = config.py not loaded

		# CPU type needed for ucode
		cpu_type = 'intel' if Cmd.suppress('cat /proc/cpuinfo | grep -i intel') == 0 else 'amd'
		cpu_family = Cmd.output("cat /proc/cpuinfo | grep -i family | uniq").split(':', 1)[1].strip() # e.g. '6'
		cpu_model = Cmd.output("cat /proc/cpuinfo | grep -i model | grep -vi '^model name' | uniq").split(':', 1)[1].strip() # e.g. '60'
		cpu_cores = Cmd.output("cat /proc/cpuinfo | grep -i processor | wc -l").strip() # e.g. '4'
		cpu_identifier = f'{cpu_type}_{cpu_family}-{cpu_model}-{cpu_cores}' # e.g. 'intel_6-60-4'
		aur_cache = f'/pkgcache/pkgcache/aur' + (f'/{cpu_identifier}' if optimize_compilation and optimize_cached_pkgs else '')

		de = de.lower().replace('deepin', 'dde').replace('none', '')
		use_qt_apps = (de == 'kde' or de == 'lxqt')

		users = users.replace(' ', '').lower().strip()
		unres_users = User.get_unrestricted_users()

		# Update bootmode to EFI if required
		ret_val = Cmd.suppress('ls /sys/firmware/efi/efivars')
		if ret_val == 0: boot_mode = 'UEFI' # efivars dir exits => booted in UEFI
	else:
		print(os_compat_msg)
		input()
		exit(2) # 2 = Non-POSIX systems are incompatible

# TODO Load phrases.txt for preferred language & transform all phrases in 
def load_localization():
	pass

# Check if running as root
def check_privs():
	user = Cmd.output('whoami').rstrip('\n')
	if user != 'root':
		write_ln('§2ERROR: §0Please run this script as root to continue.')
		exit(5) # 5 = Privilege requirements unmet



###############################
# Functions
###############################

# Use custom installer color definitions
def load_colors():
	Cmd.exec("echo -en '\\033]P0101010'", '', False) # Black
	Cmd.exec("echo -en '\\033]P1AF1923'", '', False) # Dark Red
	Cmd.exec("echo -en '\\033]P269A62A'", '', False) # Dark Green
	Cmd.exec("echo -en '\\033]P3E68523'", '', False) # Dark Yellow
	Cmd.exec("echo -en '\\033]P42935B1'", '', False) # Dark Blue
	Cmd.exec("echo -en '\\033]P57C1FA1'", '', False) # Dark Magenta
	Cmd.exec("echo -en '\\033]P62397F5'", '', False) # Dark Cyan
	Cmd.exec("echo -en '\\033]P7A4A4A4'", '', False) # Light Gray
	Cmd.exec("echo -en '\\033]P8303030'", '', False) # Dark Gray
	Cmd.exec("echo -en '\\033]P9FF0000'", '', False) # Red
	Cmd.exec("echo -en '\\033]PA4CFF00'", '', False) # Green
	Cmd.exec("echo -en '\\033]PBFFD800'", '', False) # Yellow
	Cmd.exec("echo -en '\\033]PC0026FF'", '', False) # Blue
	Cmd.exec("echo -en '\\033]PDFF00FF'", '', False) # Magenta
	Cmd.exec("echo -en '\\033]PE00FFFF'", '', False) # Cyan
	Cmd.exec("echo -en '\\033]PFF5F5F5'", '', False) # White
	clear_screen() # For avoiding coloring artifacts

# Check network connectivity with ping
def check_connectivity():
	write_msg('Checking network connectivity...', 1)
	ret_val = Cmd.log('curl -s 1.1.1.1')
	if ret_val != 0:
		write_status(1)
		write_ln("\n§2ERROR: §0No network connectivity. Check your connection and try again.", 2)
		exit(6) # 6 = Network connectivity issue
	elif enable_aur: # Test connection to AUR
		ret_val += Cmd.log('ping -c 1 aur.archlinux.org')
		write_status(ret_val, 0, 4)
		if ret_val != 0:
			write_ln("\n§4WARN: §0Possibly unreliable network connection detected: AUR support could fail to be enabled.")
			write_msg(f'Would you like to continue §2without §0making any changes? (§3y§0/§2N§0)? §7>> ')
			ans = input().upper().replace('YES', 'Y')
			write_ln()
			if ans != 'Y':
				exit(6) # 6 = Network connectivity issue
	else: write_status()

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
		write_ln("§2ERROR: §0Font loading failed. Most likely cause: the specified font was not found.")
		exit(9) # 9 = Font couldn't be loaded!

# Load kb map using 'loadkeys'
def load_kbmap():
	write_msg(f"Loading system keymap '{keymap}'...", 1)
	ret_val = Cmd.log('loadkeys ' + keymap)
	write_status(ret_val)
	if ret_val != 0:
		write_ln("§2ERROR: §0Keymap loading failed. Most likely cause: the specified keymap was not found.")
		exit(10) # 10 = Keymap couldn't be loaded!

# NTP time synchronization
def ntp_setup():
	write_msg('Enabling NTP time synchronization...', 1)
	ret_val = Cmd.log('timedatectl set-ntp true')
	write_status(ret_val, 0, 4)

# Disk partitioning

def partition(tool_to_use=''):
	Cmd.exec(f"echo && {lsblk_cmd} && echo", '', False)
	tool_defined = len(tool_to_use) > 0
	if tool_defined:
		write_msg('Device to partition (e.g. ')
	else:
		write_msg('Partitioning command line (e.g. §4fdisk §7/dev/')
	write("§7sda§0) §7>> ")
	in_cmd = ''
	in_cmd = input().strip().lower()
	if len(in_cmd) > 0:
		if tool_defined: Cmd.exec(f'{tool_to_use} /dev/{in_cmd}')
		else: Cmd.exec(in_cmd)

def sel_par_tool(hide_guide=False):
	if not hide_guide:
		write_ln("   Enter '§3F§0' to partition using §3cfdisk §0(UEFI & BIOS/CSM)")
		write_ln("   Enter '§4G§0' to partition using §4cgdisk §0(UEFI only)")
		write_ln("   Enter '§7O§0' to partition using §7something else", 2)

		write_ln("   Enter '§3L§0' to view partitions using §3lsblk")
		write_ln("   Enter '§2I§0' to view partitions using §2blkid", 2)

		# TODO: Add note to "cfdisk" about choosing UEFI/GPT vs BIOS/DOS!

	# '>> Selection (F/G/O/L/I) >> '
	write_msg('Selection (')
	write('§3F§0/§4G/§7O§0/§3L§0/§2I§0) §7>> ')

	sel = ''
	sel = input().strip().upper()
	if len(sel) > 0:
		if sel == 'F':
			partition('cfdisk')
		elif sel == 'G':
			partition('cgdisk')
		elif sel == 'O':
			partition()
		elif sel == 'L' or sel == 'I':
			cmd = lsblk_cmd if sel == 'L' else blkid_cmd
			write_ln()
			Cmd.exec(cmd, '', False)
			write('\nPress ENTER to continue...')
			input()
		else:
			sel_par_tool(True)
		partitioning_menu()

def partitioning_menu():
	global menu_visit_counter
	print_header('Disk Partitioning')
	middle = ' anymore' if menu_visit_counter > 0 else ''
	# TODO Make user type 'done' instead to continue?
	write_ln(f"   §3Tip: §0If you don't need to partition{middle}, just press ENTER", 2)
	menu_visit_counter += 1
	sel_par_tool()

# Partition mounting & formatting

# Mount a partition
# e.g. 'mount_par('/dev/sda1', '/')'
def mount_par(blk_dev, mount_point='/', opts=''):
	mount_point = f'/mnt{mount_point}' # e.g. '/' -> '/mnt/'
	Cmd.suppress(f'umount -R {mount_point}') # try unmounting existing par
	Cmd.log(f'mkdir -p {mount_point}')
	opts = ' -o ' + opts if len(opts) > 0 else ''
	return Cmd.log(f'mount{opts} {blk_dev} {mount_point}')

def par_opt_handler(opt):
	global mbr_grub_dev, pkgcache_enabled

	# Option validity checks
	# TODO Fully disallow mounted selections to be chosen in mounting menu! (e.g. /,/efi,swap etc)
	if len(opt) != 1:
		list_used_pars(True)
	if opt == 'E' and boot_mode != 'UEFI':
		list_used_pars(True)
	if opt != 'B' and opt != 'R' and opt != 'E' and opt != 'H' and opt != 'S' and opt != 'C' and opt != 'O':
		list_used_pars(True)

	lsblk = Cmd.output(f"{lsblk_cmd} | grep -v '/mnt' | grep -vi 'swap'")

	if lsblk.count('\n') <= 2:
		write_ln()
		# TODO Show question to re-enter partitioning menu!
		write_msg('Mounting cancelled since there are no devices to mount.', 4)
		write('\nPress ENTER to continue...')
		input()
		mounting_menu()

	write_ln(f"\n{lsblk}")

	purpose = opt.replace('B', '/boot').replace('R', '/').replace('E', '/efi').replace('H', '/home').replace('S', 'swap').replace('O', 'other purpose').replace('C', 'package cache')
	write_msg(f'Which partition would you like to use for §3{purpose} §0(e.g. ')
	if opt == 'O':
		write('§7/dev/')
	write('§7sda1§0)? §7>> ')
	par = ''
	par = input().strip().lower() # e.g. 'sda1'
	if len(par) < 4: mounting_menu()
	if '/' not in par: par = '/dev/' + par # Make proper form, e.g. '/dev/sda1'
	ret_val = Cmd.suppress('find ' + par)
	if ret_val != 0: mounting_menu() # TODO msg user ...

	# e.g. 'Would you like to format /dev/sda1 for / using ext4 (y/N)? >> '
	#      'Would you like to format /dev/sda2 for swap usage (y/N)? >> '
	#      'Would you like to use /dev/sda3 for other purpose (y/N)? >> '
	write_ln()
	write_msg(f'Would you like to §2format §7{par} §0(§2y§0/§3N§0)? §7>> ')
	ans = ''
	ans = input().upper().replace('YES', 'Y')

	# TODO Add RAID support etc.

	pause = False # Pause at end of formatting & mounting?
	fs_type = 'swap' if opt == 'S' else ''

	# Format...
	if ans == 'Y':
		# TODO Add other as fs type & custom format commands etc
		format_args = {
				'f2fs':      '-f', # -l label
				'reiserfs': '-f', # -u -l label
				'xfs':      '-f', # -L label
				'fat':      '-F32 -s2', # -n label
				'ntfs':     '-F -Q', # -U -L label
				#'exfat':    '', # -n label
				#'btrfs':    '-f',
		}
		if opt == 'E': # efi
			fs_type = 'fat'
		elif opt == 'S': # swap
			fs_type = 'swap'
		else: # other
			write_ln('\n§7>> §0All available supported §3filesystem types§0:', 2)
			# TODO Add other as fs types (Btrfs) & custom format commands etc
			supported_fs_types = [ 'ext4', 'XFS', 'F2FS', 'ReiserFS' ]
			if opt != 'R':
				supported_fs_types.extend([ 'FAT32', 'exFAT', 'NTFS', 'swap' ])
			for fs_type in supported_fs_types:
				write_ln(f'   §3{fs_type}')
			write_ln()

			write(f'§7>> §0Which §3filesystem type §0would you like to format §7{par} §0with (e.g. §3ext4§0)? §7>> ')
			fs_type = input().strip().lower() # e.g. 'ext4'
			if len(fs_type) < 3 or fs_type not in [x.lower() for x in supported_fs_types]:
				mounting_menu()

			fs_type = fs_type.replace('fat32', 'fat')

		format_cmd = (f'mkfs.{fs_type}') if fs_type != 'swap' else 'mkswap' # e.g. 'mkfs.ext4', 'mkswap'
		if fs_type in format_args:
			format_cmd += ' ' + format_args.get(fs_type)

		write_ln()
		# TODO umount -R before formatting?
		# TODO Use proper stylized version of 'fs_type' e.g. get index & use from supported_fs_types[]
		write_msg(f'Formatting {par} using {fs_type.replace("fat", "fat32")}...', 1)
		#format_cmd += ' -n ESP' if opt == 'E' else ''
		ret_val = Cmd.log(f'{format_cmd} {par}') # e.g. 'mkfs.ext4 /dev/sda1'
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
				write_msg(f'Where would you like to mount §7{par} §0in the new system (e.g. §3/var§0)? §7>> ')
				mp = ''
				mp = input().strip().lower() # e.g. '/var'
				write_ln()
			elif opt == 'R': mp = '/'
			elif opt == 'B': mp = '/boot'
			elif opt == 'H': mp = '/home'
			elif opt == 'C': mp = '/pkgcache'
			elif opt == 'E': mp = '/efi'

			# TODO Prevent mounting to / when using NTFS etc.
			if len(mp) > 0 and mp.startswith('/'): # Assume proper path
				# TODO Don't add new line if not formatted
				write_ln()
				write_msg('Other §4optional §0mount options (e.g. §7noatime,nofail§0) >> ')
				opts = ''
				opts = input().strip().replace(' ', '') # e.g. 'noatime,nofail'
				#opts = 'defaults' if len(opts) == 0 else f'defaults,{opts}'
				write_ln()
				write_msg(f'Mounting {par} to {mp}...', 1)
				ret_val = mount_par(par, mp, opts) # e.g. 'mount /dev/sda1 /mnt/'
				write_status(ret_val)
				if ret_val != 0: pause = True
				elif boot_mode == 'BIOS/CSM' and ((opt == 'R' and mbr_grub_dev == '') or opt == 'B'): # Update MBR GRUB device
					# TODO: Fix NVMe / EMMC MBR installs (don't assume :-1 in par; nvme,emmc,...)
					if par[-1:].isdigit(): par = par[:-1] # e.g. '/dev/sda1' => '/dev/sda'
					mbr_grub_dev = par # e.g. '/dev/sda'
				elif mp == '/pkgcache':
					# TODO Update to support Btrfs
					#write_ln()
					write_msg('Checking partition filesystem compatibility for caching...', 1)
					errors = Cmd.log(f'mkdir -p /mnt/pkgcache/pkgcache/aur/' + (cpu_identifier if optimize_cached_pkgs else ''))
					errors += Cmd.log('touch /mnt/pkgcache/pkgcache/test-1:1.2.3.4-x86-64.pkg.tar.xz.part')
					write_status(errors)
					pkgcache_enabled = (errors == 0)
					if pkgcache_enabled:
						Cmd.log('rm -f /mnt/pkgcache/pkgcache/test-1:1.2.3.4-x86-64.pkg.tar.xz.part')
						Cmd.log('cp /etc/pacman.conf /etc/pacman.conf.bak')
						IO.replace_ln('/etc/pacman.conf', '#CacheDir', 'CacheDir = /mnt/pkgcache/pkgcache') # pkgcache on live env
						write_msg('Enabling package cache on the partition...', 2)
					else:
						pause = True
						Cmd.log('mv /etc/pacman.conf.bak /etc/pacman.conf')
						IO.replace_ln('/etc/pacman.conf', 'CacheDir', '#CacheDir')
						Cmd.log('cd && umount /mnt/pkgcache && rm -rf /mnt/pkgcache')
			else:
				write_ln()
				write_msg('Mounting cancelled due to an invalid mountpoint.', 4)
				pause = True
		else:
			write_ln()
			write_msg(f'Enabling swap on {par}...', 1)
			Cmd.suppress('swapoff ' + par) # try disabling existing swap
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
		write(f' §3({action} §7{device}§3)')
	write_ln()

def list_used_pars(hide_guide=False):
	global mounts, menu_visit_counter
	mounts = ''
	other_mounts = ''

	# TODO Improve this
	# WARN Mounting anything to a mount point ending in 'root' is forbidden
	tmp_mounts = Cmd.output("lsblk -n -o NAME,MOUNTPOINT | grep -v '^loop' | grep -v '^sr0'") # | grep /
	for line in tmp_mounts.split('\n'):
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
		menu_visit_counter = 0

	#write_msg('Mounts: ' + mounts + '\n')
	#write_msg('Other:  ' + other_mounts + '\n\n')

	if not hide_guide:
		write_ln('   The following partitions are §2mandatory§0:', 2)
		write_par_mount('R', '/', '', ('root:' in mounts))
		if 'root:' in mounts:
			if boot_mode == 'UEFI':
				write_ln()
				write_par_mount('E', '/efi', '', ('/efi:' in mounts))

		if 'root:' in mounts:
			write_ln('\n   §4Optional §0partitions include:', 2)
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
							write_par_mount('', split_entry[0], split_entry[1], True, 9, 3)
						except:
							log(f"[setup.py:list_used_pars()] WARN: Couldn't display other mount entry '{entry}'")

		#start = '\n' if len(other_mounts) != 0 else ''
		# %s % start
		write_ln('\n   For further partition §6identification§0:', 2)
		write_ln('      L   lsblk')
		write_ln('      I   blkid')
		write_ln('      F   fdisk -l', 2)
		write_ln('\n   §3Other §0choices:', 2)
		write_ln('      P   back to partitioning', 2)

	# '>> Selection (R/E/B/H/C/S/O/L/I/F/Z) >> '
	write_msg('Selection (R/')
	if 'root:' in mounts:
		if boot_mode == 'UEFI':
			write('E/')
		write('B/H/C/')
	write('S/O/L/I/F/P) §7>> ')

	# TODO Optionally allow to use /boot instead of /efi on UEFI systems

	sel = ''
	sel = input().strip().upper()
	if len(sel) > 0:
		# Partition identification
		if sel == 'L' or sel == 'I' or sel == 'F':
			cmd = lsblk_cmd
			if sel == 'I':
				cmd = blkid_cmd
			elif sel == 'F':       # 'DEV    TYPE       SIZE MOUNT'
				cmd = 'fdisk -l' # lsblk -n -o NAME,FSTYPE,SIZE,MOUNTPOINT
			write_ln()
			Cmd.exec(cmd, '', False)
			write('\nPress ENTER to continue...')
			input()
		else:
			if sel == 'P':
				Cmd.log('umount -R /mnt')
				if 'swap' in mounts:
					swap_par = mounts.split('swap:')[1].split(',')[0] # /dev/sda2
					Cmd.log(f'swapoff {swap_par}')
				partitioning_menu()
			elif 'root:' not in mounts and not (sel == 'R' or sel == 'S' or sel == 'O'):
				write_ln('\n§2ERROR: §0Please mount a root partition before continuing!')
				write('\nPress ENTER to continue...')
				input()
			else:
				par_opt_handler(sel)
		#input()
		mounting_menu()

	if 'root:' not in mounts:
		# TODO Message?
		mounting_menu()

	if boot_mode == 'UEFI' and '/efi:' not in mounts:
		write_ln()
		write_msg('Would you like to continue without mounting a §3/efi §7partition §0(§2y§0/§3N§0)? §7>> ')
		ans = ''
		ans = input().upper().replace('YES', 'Y')
		if ans != 'Y':
			mounting_menu()

def mounting_menu():
	global menu_visit_counter
	print_header('Mounting Partitions')
	write_ln('   Select an option by entering the corresponding key.')
	write("   §3Tip: §0If you don't need to mount partitions")
	if menu_visit_counter > 0:
		write(' anymore')
	menu_visit_counter += 1
	# TODO Make user type 'done' instead to continue?
	write_ln(', just press ENTER', 2)
	list_used_pars()

# Mirrorlist sorting

def sort_mirrors():
	write_msg('Fetching reflector for mirrorlist sorting...', 1)
	ret_val = Pkg.install('reflector')
	write_status(ret_val)

	if ret_val == 0:
		write_msg('Creating a backup of the local mirrorlist file...', 1)
		ret_val = Cmd.log('cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak')
		write_status(ret_val)

		write_msg('Sorting mirrors using reflector, please wait...', 1)
		ret_val = Cmd.log('reflector --verbose --sort rate --number 25 --fastest 10 --age 24 --protocol https --save /etc/pacman.d/mirrorlist')
		write_status(ret_val)

		write_msg('Refreshing pacman package databases...', 1)
		ret_val = Pkg.refresh_dbs()
		write_status(ret_val)

# Base system install

# TODO Use global sys_root variable in the future
# TODO Fix systemd messages appearing on screen about microcode on real hardware
def base_install(sys_root='/mnt/'):
	ps_args, extra_pkgs = ('', '')
	blkid = Cmd.output('blkid').lower()

	if len(users) > 0: extra_pkgs += 'sudo '
	if font.startswith('ter-'): extra_pkgs += 'terminus-font '
	if enable_aur: extra_pkgs += 'pigz '
	if 'ext' in blkid: extra_pkgs += 'e2fsprogs '
	if 'jfs' in blkid: extra_pkgs += 'jfsutils '
	if 'reiser' in blkid: extra_pkgs += 'reiserfsprogs '
	if 'xfs' in blkid: extra_pkgs += 'xfsprogs '
	if 'f2fs' in blkid: extra_pkgs += 'f2fs-tools '
	# TODO: 'cryptsetup lvm2' if use_lvm (/ encryption)
	# TODO: Detect SW raid & get 'mdadm'

	# Userspace utilities for filesystems
	extra_pkgs = f' {extra_pkgs.rstrip()}' if len(extra_pkgs) > 0 else ''

	cache_arg = '-c ' if os.path.exists(sys_root + 'pkgcache') else ''

	# TODO Force installation to not trigger (Updating linux initcpios) to run it seperately at the end (install the kernel & bootloader at the very end instead perhaps?)
	ps_args = f'{cache_arg}{sys_root} openresolv base linux-firmware device-mapper logrotate which less usbutils inetutils diffutils man-db man-pages python{extra_pkgs}'

	write_msg('Installing base system using pacstrap, please wait...', 1)
	ret_val = Cmd.log('pacstrap ' + ps_args)
	write_status(ret_val)
	if ret_val != 0: # Base install failure
		write_ln('§2ERROR: §0Base system install failed. Check /tmp/setup.log for the details.')
		exit(11) # 11 = Base system install failure

	# Umount cache device (most likely external) to avoid adding to fstab
	if os.path.exists(sys_root + 'pkgcache'):
		Cmd.log(f'umount {sys_root}pkgcache') # e.g. 'umount /mnt/pkgcache'

	write_msg('Generating static filesystem table...', 1)
	fstab = f'{sys_root}etc/fstab'
	Cmd.suppress(f'echo >>{fstab}')
	ret_val = Cmd.exec(f'genfstab -U {sys_root} >>{fstab}')
	write_status(ret_val)

	# Remount cache device if specified
	if '/pkgcache:' in mounts:
		cache_dev = mounts.split('/pkgcache:')[1][:-1] # e.g. '/dev/sdb1'
		Cmd.log(f'mount {cache_dev} {sys_root}pkgcache')

# Continue setup in chroot...

# TODO Use global sys_root variable in the future
def start_chroot(sys_root='/mnt/'):
	Cmd.suppress(f'cp /proc/cpuinfo {sys_root}proc/') # For CPU detection in chroot

	#if multibooting:
		#Cmd.log(f'mkdir {sys_root}hostrun')
		#Cmd.log(f'mount --bind /run {sys_root}hostrun')

	ret_val = IO.write(f'{sys_root}etc/vconsole.conf', f'KEYMAP="{keymap}"\nFONT="{font}"')
	if ret_val != 0:
		log(f"[setup.py:start_chroot()] WARN: Couldn't set persistent keymap ({keymap}) & font ({font}) in '{sys_root}etc/vconsole.conf'")

	Cmd.log(f'cp "{script_path}" "{sys_root}root/"')           # e.g. 'cp "/root/setup.py" "/mnt/root/"'
	Cmd.log(f'chmod 755 {sys_root}root/{script_fn}')           # e.g. 'chmod 755 /mnt/root/setup.py'
	Cmd.log(f'cp "{script_root}/config.py" "{sys_root}root/"') # e.g. 'cp "/root/config.py" "/mnt/root/"'

	Cmd.suppress(f'touch {sys_root}chroot') # Add indicator file for chroot

	# TODO Check if log is copied again?
	log('\n#\n# Start of chroot log\n#')
	Cmd.suppress(f'cp /tmp/setup.log {sys_root}') # Copy log over to chroot
	Cmd.suppress(f'ln -sf {sys_root}setup.log /tmp/setup.log')

	write_msg('Chrooting into the new install...', 1)
	ch_args = f' {mbr_grub_dev}' if len(mbr_grub_dev) > 0 else ''  # Pass grub device to script
	# TODO Use https://wiki.archlinux.org/index.php/systemd-nspawn instead to fix some problems?
	Cmd.exec(f'arch-chroot {sys_root} /root/{script_fn}{ch_args}') # e.g. 'arch-chroot /mnt/ /root/setup.py /dev/sda'

# Chroot specific install steps

def load_hw_info():
	global mbr_grub_dev, bat_present, disc_tray_present, camera_present, bt_present, vm_env

	if len(sys.argv) == 2: mbr_grub_dev = sys.argv[1] # Assume MBR grub dev e.g. '/dev/sda'

	# Update battery presence
	ret_val = Cmd.suppress('ls -1 /sys/class/power_supply | grep -i bat')
	bat_present = (ret_val == 0)

	# Update disc tray presence
	blkid = Cmd.output("blkid")
	disc_tray_present = ('/dev/sr' in blkid or '/dev/sg' in blkid)
	if not disc_tray_present: # Try other alternative methods
		ret_val = Cmd.suppress("dmesg | egrep -i 'cdrom|dvd|cd/rw|writer'")
		disc_tray_present = (ret_val == 0)

	# Update camera presence
	ret_val = Cmd.suppress("dmesg | egrep -i 'camera|webcam'")
	camera_present = (ret_val == 0)

	Cmd.log('update-pciids -q')

	# Update Bluetooth device presence
	# TODO Check for false-positives
	bt_present = Cmd.suppress('rfkill list | grep -i blue') == 0
	if not bt_present:
		bt_f1 = Cmd.suppress('dmesg | grep -i blue') == 0
		bt_f2 = Cmd.suppress('lsusb | grep -i blue') == 0 # TODO Improve USB BT adapter detection
		bt_f3 = Cmd.suppress('lspci | grep -i blue') == 0
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
			# QEMU
			elif IO.read_ln('/sys/devices/virtual/dmi/id/chassis_vendor').rstrip() == 'QEMU':
				vm_env = 'qemu'
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
	Cmd.log('timedatectl set-local-rtc ' + ('0' if timescale == 'utc' else '1'))
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
	#errors += Cmd.log('ufw enable')
	#errors += Cmd.log('systemctl enable ufw')
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

	#if enable_sshd:
	#	errors += Cmd.log('ufw limit SSH')

	#if web_server_type > 0:
	#	errors += Cmd.log('ufw allow http')
	#	errors += Cmd.log('ufw allow https')

	# TODO Allow more services once instlalled e.g. 'KTorrent' on KDE DE etc

	#write_status(errors)

def networking_setup():
	global hostname
	# Generate hostname based on board model / virtualization platform
	if hostname == '':
		if vm_env != 'vmware':
			try:
				hostname = IO.read_ln('/sys/devices/virtual/dmi/id/board_name').rstrip().replace(' ', '-') # e.g. 'Z270N-WIFI'
			except:
				if vm_env != '':
					hostname = IO.read_ln('/sys/devices/virtual/dmi/id/chassis_vendor').rstrip() # e.g. 'QEMU'
				else:
					hostname = 'Arch-' + str(random.randint(1000, 9999)) # e.g. 'Arch-3980'
		else:
			hostname = 'VMware'

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
	manager = ('NetworkManager' if use_networkmanager else 'netctl')
	write_msg(f'Setting up {manager}, please wait...', 1)
	errors = Pkg.install('dnsmasq')
	if use_networkmanager:
		errors += Pkg.install('networkmanager modemmanager mobile-broadband-provider-info usbutils usb_modeswitch rp-pppoe')
		errors += Cmd.log('systemctl enable NetworkManager')
		#if not nm_rand_mac_addr:
		#	file = '/etc/NetworkManager/conf.d/00-no-rand-wifi-scan-mac-addr.conf' # /etc/NetworkManager/NetworkManager.conf
		#	ul = '=' * len(file)
		#	contents = '# Disable randomizing Wi-Fi NIC MAC address when scanning to avoid some issues\n[device]\nwifi.scan-rand-mac-address=no'
		#	Cmd.exec(f'echo "{contents}" >' + file, '', False)
		#	log(f'\n{file}\n{ul}\n{contents}\n{ul}\n')
	else:
		# TODO Implement more precise method to only start on select interfaces e.g. 'dhcpcd@enp1s0' etc
		errors += Pkg.install('netctl dhcpcd ifplugd wpa_supplicant dialog')
		errors += Cmd.log('systemctl enable dhcpcd')

	# 1.1.1.1 DNS
	#resolv_conf = '# Generated by ArchInstaller.py (1.1.1.1 DNS)\nnameserver 1.1.1.1\nnameserver 1.0.0.1\nnameserver 2606:4700:4700::1111\nnameserver 2606:4700:4700::1001'
	#IO.write('/etc/resolv.conf', resolv_conf)
	#log(f'\n/etc/resolv.conf\n================\n{resolv_conf}\n================')

	Cmd.log('shopt -s xpg_echo')
	# TODO Turn this to a function
	# TODO Fix warning: directory permissions differ on /usr/share/polkit-1/rules.d/ (fs: 750  pkg: 755)
	#file = '/etc/polkit-1/rules.d/50-org.freedesktop.NetworkManager.rules'
	#ul = '=' * len(file)
	#contents = 'polkit.addRule(function(action, subject) {\n\tif (action.id.indexOf("org.freedesktop.NetworkManager.") == 0 && subject.isInGroup("network")) {\n\t\treturn polkit.Result.YES;\n\t}\n});'
	#Cmd.exec(f'echo "{contents}" >' + file, '', False)
	#log(f'\n{file}\n{ul}\n{contents}\n{ul}\n')

	write_status(errors)

	if enable_firewall:
		ufw_setup()

def aur_setup():
	write_msg('Installing dependencies for AUR support, please wait...', 1)
	# TODO Setup git properly (subversion etc)
	pkgs = 'base-devel git'
	if use_ccache:
		pkgs += ' ccache'
		#file = '/etc/ccache.conf'
		#ul = '=' * len(file)
		#contents = '# Set maximum cache size to 24 GB\nmax_size = 24G'
		#Cmd.exec(f'echo "{contents}" >' + file, '', False)
		#log(f'\n{file}\n{ul}\n{contents}\n{ul}\n')

	ret_val = Pkg.install(pkgs)
	write_status(ret_val)
	if ret_val == 0: # base-devel & git install successfull
		write_msg('Setting up temporary aurhelper user...', 1)
		errors = Cmd.log('useradd -m -g users -G wheel aurhelper')
		errors += Cmd.log('cp /etc/sudoers /etc/sudoers.bak')
		# TODO Create an actual replace by line number function
		# Give wheel group users sudo permission w/o pass
		Cmd.log('chmod 770 /etc/sudoers')
		errors += Cmd.log("sed '85 s/^# //' -i /etc/sudoers")
		write_status(errors)

		# Build & compress on all CPU cores
		file = '/etc/makepkg.conf'
		if optimize_compilation and (not pkgcache_enabled or optimize_cached_pkgs):
			IO.replace_ln(file, 'CFLAGS="', f'CFLAGS="{cflags}"') # 40
		IO.replace_ln(file, 'CXXFLAGS="', 'CXXFLAGS="${CFLAGS}"') # 41
		IO.replace_ln(file,   '#MAKEFLAGS="', 'MAKEFLAGS="-j$(nproc)"') # 44
		IO.replace_ln(file,   'BUILDENV=', f'BUILDENV=(!distcc color {"" if use_ccache else "!"}ccache !check !sign)') # 62
		IO.uncomment_ln(file, 'BUILDDIR=') # 69
		IO.replace_ln(file,   'COMPRESSGZ=(', 'COMPRESSGZ=(pigz -c -f -n)') # 130
		IO.replace_ln(file,   'COMPRESSXZ=(', 'COMPRESSXZ=(xz -c -z - --threads=0)') # 132

		write_msg('Fetching & installing yay from the AUR, please wait...', 1)
		# TODO Cache the package to /pkgcache?
		# TODO Fix "host not resolved" issues on desktop & laptop!!!
		ret_val = Cmd.log('$ cd /tmp; git clone --depth 1 https://aur.archlinux.org/yay-bin.git && cd yay-bin && makepkg -si --skippgpcheck --noconfirm --noprogressbar --needed', 'aurhelper')
		write_status(ret_val)
		Cmd.log('cd && rm -rf /tmp/yay-bin')
		if ret_val != 0: # Yay install failed
			global enable_aur
			enable_aur = False
			Cmd.log('userdel -f -r aurhelper')
			Cmd.log('cp /etc/sudoers.bak /etc/sudoers')

		Cmd.log('chmod 440 /etc/sudoers')

		# TODO Setup ccache w/ 8GB

def user_setup():
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
		Cmd.log('sed "89s/.*/\\n## Allow members of group sudo to execute any commmand without a password\\n%sudo ALL=(ALL) NOPASSWD: ALL\\n/" -i /etc/sudoers')

	for user in users.split(','):
		# TODO Make 'is_restricted()' etc. extended functions of string?
		restricted = User.is_restricted(user)
		passwdless = User.is_passwdless(user)
		add_args = 'restricted' if restricted else 'users -G wheel,storage,disk,rfkill,network,input,log'
		errors += Cmd.log(f'useradd -m -g {add_args} {user}')

		if not restricted: # Add some more groups
			if xorg_install_type != 0: Cmd.log(f'gpasswd -a {user} video')
			# Allow user full access to media (e.g. mounting)
			if disc_tray_present: Cmd.log(f'gpasswd -a {user} optical')
			if web_server_type > 0: Cmd.log(f'gpasswd -a {user} http')
			if enable_printing: Cmd.log(f'usermod -aG scanner,sys {user}')
			if passwdless: Cmd.log(f'gpasswd -a {user} sudo')

		if passwdless: # Allow logging in without password
			pass
			#Cmd.log(f'gpasswd -a {user} nopasswdlogin')

			# TODO Figure out a way to bypass polkit (or use another user for pass; root?)
			# TODO Remove password later (instead of asking for it at the end) using 'sudo passwd -d $passwdless_user'

	write_status(errors)

	Cmd.log("chmod 440 /etc/sudoers")
	Cmd.log('cp /etc/sudoers /etc/sudoers.bak')

# Enables a repo in /etc/pacman.conf & refreshes the package cache
# TODO Allow adding new repos (url='', sigLevel='' etc)
def enable_repo(repo, updateDb=True):
	write_msg(f'Enabling {repo} repo in /etc/pacman.conf...', 1)
	ln = IO.get_ln_number('/etc/pacman.conf', f'#[{repo}]') # e.g. 93
	if ln != -1:
		Cmd.log('cp /etc/pacman.conf /etc/pacman.conf.bak')
		errors = Cmd.log(f'sed "{ln} s/^#//" -i /etc/pacman.conf') # e.g. "[multilib]"
		errors += Cmd.log(f'sed "{ln+1} s/^#//" -i /etc/pacman.conf') #   "Include = ..."
		write_status(errors)
		if errors == 0:
			write_msg('Refreshing pacman package databases...', 1)
			ret_val = Pkg.refresh_dbs()
			write_status(ret_val)
			# TODO Copy package database to '/pkgcache/pkgcache/pkgs.db' etc for possible offline install
		else:
			Cmd.log('cp /etc/pacman.conf.bak /etc/pacman.conf') # Restore backup
	else:
		write_status(1)

def multilib_setup():
	enable_repo('multilib', not enable_testing)

def testing_setup():
	enable_repo('testing', False)
	enable_repo('community-testing', not enable_multilib)
	if enable_multilib:
		enable_repo('multilib-testing')

def ssh_setup():
	write_msg('Setting up OpenSSH ' + ('server' if enable_sshd else 'utils') + '...', 1)
	ret_val = Pkg.install('openssh')
	write_status(ret_val)

	if xorg_install_type > 0:
		Cmd.log("sed 's/^#X11Forwarding.*/X11Forwarding yes/' -i /etc/ssh/sshd_config")

	if enable_sshd:
		Cmd.log('systemctl enable sshd.service')

def kernel_setup():
	global use_dkms_pkgs
	write_msg(f'Setting up the {kernel} kernel, please wait...', 1)
	errors = Pkg.install(f'{kernel} {kernel}-headers dkms')

	# On errors, fallback to stable kernel...
	if errors != 0:
		use_dkms_pkgs = False
		Pkg.install('linux')

	write_status(errors)

def update_grub():
	return Cmd.log('grub-mkconfig -o /boot/grub/grub.cfg')

def bootloader_fail_prompt():
	#write_status()
	write("§7>> §0The bootloader install has §2failed§0! Your system likely won't boot after restarting. Would you like to continue anyway (y/N)?")
	ans = input().upper().replace('YES', 'Y')
	if ans != 'Y':
		exit(12) # 12 = Bootloader install failure

def bootloader_setup():
	# TODO systemd-boot,syslinux etc alternatives to GRUB?
	write_msg('Fetching dependencies for the GRUB bootloader...', 1)
	pkgs = 'grub' # dosfstools
	cpu_type = cpu_identifier.split('_', 1)[0] # e.g. 'intel' / 'amd'
	pkgs += '' if vm_env != '' else f' {cpu_type}-ucode'
	errors = Pkg.install(pkgs)
	write_status(errors)

	write_msg(f'Installing GRUB in {boot_mode} mode, please wait...', 1)
	if boot_mode == 'UEFI':
		errors = Pkg.install('efibootmgr')
		errors += Cmd.log('grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id="Arch-GRUB"')
	else: # BIOS/CSM
		errors = Cmd.log(f'grub-install --recheck {mbr_grub_dev}')
	write_status(errors)
	if errors != 0: bootloader_fail_prompt()

	write_msg('Creating initial GRUB config, please wait...', 1)
	errors = update_grub()

	# Do some GRUB config modifications
	# TODO Uncomment '#GRUB_ENABLE_CRYPTODISK=y' if LUKS encrypted
	# TODO Set GRUB_GFXMODE to monitor res e.g. '1920x1080'

	IO.uncomment_ln(grub_conf, 'GRUB_COLOR_NORMAL=')
	IO.uncomment_ln(grub_conf, 'GRUB_COLOR_HIGHLIGHT=')
	IO.replace_ln(grub_conf, 'GRUB_DEFAULT=', 'GRUB_DEFAULT=saved')
	IO.replace_ln(grub_conf, '#GRUB_SAVEDEFAULT=', 'GRUB_SAVEDEFAULT=true')
	#IO.uncomment_ln(grub_conf, 'GRUB_SAVEDEFAULT=')

	if not multibooting:
		Cmd.log(f'sed "18s/.*/GRUB_FORCE_HIDDEN_MENU=true\\n/" -i {grub_conf}')
		# TODO Add "GRUB_DISABLE_SUBMENU=y" at the end
		IO.replace_ln(grub_conf, 'GRUB_TIMEOUT=', 'GRUB_TIMEOUT=0')
		#IO.replace_ln(grub_conf, '#GRUB_HIDDEN_TIMEOUT=', 'GRUB_HIDDEN_TIMEOUT=0')
		IO.uncomment_ln(grub_conf, 'GRUB_HIDDEN_TIMEOUT_QUIET=true')

		# TODO Allow to show GRUB menu when holding SHIFT on most systems
		#Cmd.log('cd /etc/grub.d/ && curl https://git.io/vMIFi -Lso 31_hold_shift && chmod a+x ./31_hold_shift; cd') # 21_...

		# TODO Update the comment above the line? "Only load GPT module on single-boot machine" etc
		grub_part = 'gpt' if boot_mode == 'UEFI' else 'msdos'
		IO.replace_ln(grub_conf, 'GRUB_PRELOAD_MODULES=', f'GRUB_PRELOAD_MODULES="part_{grub_part}"')
	else:
		IO.replace_ln(grub_conf, 'GRUB_TIMEOUT=', 'GRUB_TIMEOUT=3') # TODO Keep as default 5?

	write_status(errors)
	if errors != 0: bootloader_fail_prompt()

def x_setup():
	mid = 'minimal' if xorg_install_type == 1 else 'the'
	write_msg(f'Installing {mid} X display server components...', 1)
	pkgs = 'xorg' if xorg_install_type == 2 else 'xorg-server xorg-xinit xf86-input-libinput'
	if vm_env == 'vmware': pkgs += ' xf86-input-vmmouse'
	ret_val = Pkg.install(pkgs)
	write_status(ret_val)

def vm_setup():
	write_msg(f'Setting up virtualization tools for {vm_env} guest...', 1)
	errors = Pkg.install('sshfs')

	# TODO Check vbox shares
	# TODO Fix all issues w/ VBox virtualization
	if vm_env == 'vbox':
		pkgs = 'virtualbox-guest-dkms virtualbox-guest-utils' + ('-nox ' if xorg_install_type == 0 else '')
		errors += Pkg.install(pkgs)
		errors += Cmd.log('systemctl enable vboxservice')
		#errors += Cmd.log('modprobe -a vboxguest vboxsf vboxvideo')
		# TODO execute VBoxClient-all when X is enabled?
		# rcvboxdrv

		# TODO Check if path is correct & works?
		#Cmd.log('mkdir -p /media')
		#Cmd.log('chmod 770 /media') # 755
		#Cmd.log('chown root:vboxsf /media')
		# TODO '# mount -t vboxsf -o gid=1000,uid=1000 Shared /media/Shared'
		if len(unres_users) > 0:
			for user in unres_users:
				errors += Cmd.log(f'gpasswd -a {user} vboxsf')
	elif vm_env == 'vmware':
		# TODO Find something that adds to errors without loggin (AUR disabled shows ERROR status)
		IO.replace_ln('/etc/mkinitcpio.conf', 'MODULES=(', 'MODULES=(vmw_balloon vmw_pvscsi vmw_vmci vmwgfx vmxnet3 vsock vmw_vsock_vmci_transport)')
		Cmd.log(f'mkinitcpio -p {kernel}') # TODO Do this for all installed kernels?

		errors += Pkg.install('fuse open-vm-tools' + (' gtkmm3' if xorg_install_type > 0 else ''))
		#errors += Pkg.aur_install('open-vm-tools-dkms')
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
				Cmd.exec("echo '# vmware shared folders' >>/etc/fstab", '', False)
				for share in shares:
					s_share = share.replace('\\040', ' ').strip() # Share w/ spaces
					share = s_share.replace(' ', '\\040') # Share in fstab-friendly format
					if len(share) > 0:
						Cmd.log(f"mkdir '/vmshare/{s_share}'")
						Cmd.log(f"chmod 770 '/vmshare/{s_share}'") # 777
						Cmd.log(f"chown root:users '/vmshare/{s_share}'")
						# e.g. '.host:/VMShare	/vmshare/VMShare	fuse.vmhgfs-fuse	allow_other,auto_unmount,nofail	0	0'
						# TODO Also use 'noatime' mount option?
						Cmd.exec("echo '.host:/§	/vmshare/§	fuse.vmhgfs-fuse	allow_other,auto_unmount,nofail	0	0' >>/etc/fstab".replace('§', share), '', False)
				Cmd.exec("echo >>/etc/fstab", '', False)

	write_status(errors)

def audio_setup():
	# TODO Add plain ALSA support
	write_msg('Setting up audio support via pulseaudio...', 1)
	errors = Pkg.install('pulseaudio pulseaudio-alsa alsa-utils pamixer libpulse') # (lib32-)alsa-oss (lib32-)alsa-plugins (lib32-)jack

	# Media codecs
	errors += Pkg.install('gst-libav gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly dav1d xvidcore realtime-privileges')

	# Event sounds
	errors += Pkg.install('libcanberra libcanberra-pulse libcanberra-gstreamer')
	if enable_multilib:
		errors += Pkg.install('lib32-libcanberra lib32-libcanberra-gstreamer lib32-libcanberra-pulse') # lib32-libsamplerate lib32-speex


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

	# TODO Add ALSA support
	write_msg('Installing BT audio support, please wait...', 1)
	errors = Pkg.install('pulseaudio-bluetooth')

	#errors = 0
	#if enable_aur:
		# Extra codecs
		#Pkg.remove('pulseaudio-bluetooth', False, False) # Just to make sure no conflicts happen
		#errors += Pkg.aur_install('libldac pulseaudio-modules-bt-git')
		# pulseaudio-bluetooth-a2dp-gdm-fix
		# gluez-git 
		# bluetooth.service: "ExecStart=/usr/lib/bluetoothd -E"
	#else:
	#	errors += Pkg.install('pulseaudio-bluetooth')

	# Auto-enable BT on startup (desktops)
	if not bat_present:
		errors += IO.replace_ln('/etc/bluetooth/main.conf', '#AutoEnable=false', 'AutoEnable=true')

	# Switch audio source to new sink on connection
	errors += Cmd.log('sed "22s/.*/\\n# automatically switch to newly-connected devices\\nload-module module-switch-on-connect\\n/" -i /etc/pulse/default.pa')
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
			video_drv = 'nvidia'
			# Card driver detection
			fermi_gpus = [ 'gf100','gf104','gf106','gf108','gf110','gf114','gf116','gf117','gf119' ] # 390xx
			kepler_gpus = [ 'gk104','gk106','gk107','gk110','gk208','gk210','gk20a' ] # 390xx
			tesla_gpus = [ 'g80','g84','g86','g92','g94','g96','g98','gt200','gt215','gt216','gt218','mcp77','mcp78','mcp79','mcp7a','mcp89' ] # 340xx
			unsupported_gpus = [ 'nv1a','nv1f','g70','g71','g72','g73','nv44a','c51','mcp61','mcp67','mcp68','mcp73' ] # noveau
			for x in range(10, 45): # nv10-nv44
				unsupported_gpus.append(f'nv{x}')
			card = 'S' # S = supported, F = fermi, K = keppler, T = tesla, U = unsupported
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

			# Remove other vulkan drivers to avoid conflicts
			Pkg.remove('vulkan-intel', False, False)
			Pkg.remove('vulkan-radeon', False, False)

			if card == 'F' or card == 'K':
				# nvidia-390xx, NVIDIA cards from around 2010-2011
				video_drv += '-390'
				errors += Pkg.install(f'nvidia-390xx{("-dkms" if use_dkms_pkgs else "")} nvidia-390xx-utils opencl-nvidia-390xx nvidia-390xx-settings')
				if enable_multilib:
					errors += Pkg.install('lib32-nvidia-390xx-utils lib32-opencl-nvidia-390xx')
			elif card == 'T':
				# nvidia-340xx, NVIDIA cards from around 2006-2010
				video_drv += '-340'
				Pkg.remove('libglvnd') # To avoid conflicts
				errors += Pkg.install(f'nvidia-340xx{("-dkms" if use_dkms_pkgs else "")} nvidia-340xx-utils opencl-nvidia-340xx')
				if enable_multilib:
					errors += Pkg.install('lib32-nvidia-340xx-utils lib32-opencl-nvidia-340xx')
			elif card == 'U':
				# use noveau, NVIDIA cards from <= 2006
				mesa_install_type = 2
				video_drv += '-noveau'
				errors += Pkg.install('xf86-video-nouveau')
			else:
				# Expect current NVIDIA cards from around 2010 onwards
				errors += Pkg.install(f'nvidia{("-dkms" if use_dkms_pkgs else "")} nvidia-utils opencl-nvidia nvidia-settings')
				if enable_multilib:
					errors += Pkg.install('lib32-nvidia-utils lib32-opencl-nvidia')

			# TODO Remove /etc/X11/xorg.conf and other discrete configs?

			# Switching NVIDIA graphics with Intel iGPU
			if gpu_has_switchable_gfx and 'intel' in vga_out:
				mesa_install_type = 1
				errors += Pkg.install('bbswitch')

				# Bumblebee driver for older NVIDIA Optimus systems
				if card != 'S':
					video_drv += '/bumblebee'
					errors += Pkg.install('primus xf86-video-intel')
					if enable_multilib:
						errors += Pkg.install('lib32-virtualgl lib32-primus')

					if len(unres_users) > 0:
						for user in unres_users:
							errors += Cmd.log(f'gpasswd -a {user} bumblebee')

					errors += Cmd.log('systemctl enable bumblebeed')
				# Official driver + optimus-manager for newer systems
				else:
					video_drv += '/optimus'
					errors += Pkg.aur_install('optimus-manager')
					errors += Cmd.exec('systemctl enable optimus-manager')

					# For GPU switch control tray icon on DEs
					if de != '':
						errors += Pkg.aur_install('optimus-manager-qt')

			if mesa_install_type < 2:
				errors += Pkg.install('libvdpau')
				if enable_multilib:
					errors += Pkg.install('lib32-libvdpau')

				if mesa_install_type == 0:
					errors += Pkg.install('xorg-server-devel')
					# Generate X.org config
					errors += Cmd.log('nvidia-xconfig')

			# Setup kernel options only on compatible NVIDIA proprietary drivers
			if '340' not in video_drv and 'nouveau' not in video_drv and 'bumblebee' not in video_drv:
				# TODO kernel options: "nvidia-drm.modeset=1"
				# Use '?' in order to avoid issues without proprietary drivers in the future
				# 'MODULES=(... nvidia? nvidia_modeset? nvidia_uvm? nvidia_drm?)' in '/etc/mkinitcpio.conf' (https://wiki.archlinux.org/index.php/Mkinitcpio#MODULES)
				# TODO Setup https://wiki.archlinux.org/index.php/NVIDIA#Pacman_hook
				pass

		# e.g. ''
		elif 'amd' in vga_out or 'radeon' in vga_out or ' ati ' in vga_out:
			video_drv = 'amdgpu'
			mesa_install_type = 2
			errors += Pkg.install('xf86-video-amdgpu vulkan-radeon opencl-mesa')
			# TODO Only install on Vulkan capable GPUs
			if enable_multilib:
				errors += Pkg.install('lib32-vulkan-radeon')

			# TODO Add switchable AMD GPU support
			# ref: https://wiki.archlinux.org/index.php/PRIME
			#if gpu_has_switchable_gfx:
				#add_kernel_par('radeon.dpm=1')

			# libva-mesa-driver vulkan-radeon
			# TODO 'amdgpu.dc=1' as kernel/module option

			# also 'radeon.cik_support=0 amdgpu.cik_support=1' etc depending on card GCN version
			# 'MODULES=(amdgpu radeon)' in /etc/mkinitcpio.conf

		# e.g. 'intel corporation hasswell-ult integrated graphics'
		elif 'intel' in vga_out:
			video_drv = 'intel'
			mesa_install_type = 2
			# TODO VDPAU driver?

			if int(cpu_family) == 6 or int(cpu_family) == 5:
				vaapi_installed = False
				if int(cpu_model) > 57: # >= IvyBridge
					# Vulkan
					errors += Pkg.install('vulkan-intel')
					if enable_multilib:
						errors += Pkg.install('lib32-vulkan-intel')

					# VA-API
					if int(cpu_model) > 59 and int(cpu_model) < 95 and enable_aur: # Haswell => Skylake
						errors += Pkg.aur_install('libva-intel-driver-hybrid intel-hybrid-codec-driver')
						vaapi_installed = True

					# OpenCL
					if int(cpu_model) < 71: # IvyBridge & Haswell iGPUs
						errors += Pkg.install('beignet')

				if int(cpu_model) > 70: # Broadwell and beyond
					# VA-API
					errors += Pkg.install('intel-media-driver')
					vaapi_installed = True

					# OpenCL
					errors += Pkg.install('intel-compute-runtime')

				# VA-API
				if not vaapi_installed: # < Coffee Lake
					errors += Pkg.install('libva-intel-driver')
					if enable_multilib:
						errors += Pkg.install('lib32-libva-intel-driver')

			errors += Pkg.install('xf86-video-intel')

			# TODO Default to DRI3 (/etc/X11/xorg.conf.d/20-intel.conf)
			# TODO Fall back to modesetting on >= Haswell instead of using 'xf86-video-intel' pkg

		if not video_drv.startswith('intel'): # AMD & NVIDIA
			# Video acceleration
			if enable_aur:
				errors += Pkg.aur_install('libva-vdpau-driver-chromium')
			else:
				errors += Pkg.install('libva-vdpau-driver')

			if enable_multilib:
				Pkg.install('lib32-libva-vdpau-driver')

	else: # Virtualized
		mesa_install_type = 2
		Cmd.exec('echo needs_root_rights=yes >/etc/X11/Xwrapper.config')
		if 'vmware' in vga_out:
			video_drv = 'vmware'
			errors += Pkg.install('xf86-video-vmware')
		else:
			video_drv = 'fbdev/vesa'
			errors += Pkg.install('xf86-video-fbdev xf86-video-vesa')

	if '340' not in video_drv:
		errors = Pkg.install('libglvnd')
		if enable_multilib: errors += Pkg.install('lib32-libglvnd')

	if mesa_install_type > 0:
		video_drv += '+mesa'
		errors += Pkg.install('mesa') # all here?
		if 'intel' not in video_drv:
			errors += Pkg.install('libva-mesa-driver mesa-vdpau')
		if enable_multilib:
			errors += Pkg.install('lib32-mesa') # all here?
			if 'intel' not in video_drv:
				errors += Pkg.install('lib32-mesa lib32-libva-mesa-driver lib32-mesa-vdpau')

	# TODO Only install on Vulkan & OpenCL capable GPUs
	errors += Pkg.install('vulkan-icd-loader ocl-icd') # opencl-driver
	if enable_multilib:
		errors += Pkg.install('lib32-vulkan-icd-loader lib32-ocl-icd') # lib32-opencl-driver

	log(f"\n[setup.py:vga_setup()] Video driver: '{video_drv}'")

	write_status(errors)

def lightdm_setup():
	# TODO 'Setting up LightDM...' message, errors etc.
	# TODO DE-specific customizations like Deepin-greeter, backgrounds etc
	# TODO Use webkit theme? (lightdm-webkit2-greeter lightdm-webkit-theme-litarvan in normal repos)
	errors = Pkg.install('lightdm accountsservice xorg-server-xephyr') # light-locker
	errors += Cmd.log('systemctl enable lightdm')

	lightdm_cfg = '/etc/lightdm/lightdm.conf'
	ldm_greeter = 'gtk'

	if de != 'xfce' and de != 'lxde': # Use GTK+ greeter
		if de != 'dde':
			if enable_aur:
				if de != 'pantheon':
					# TODO Configure slick greeter to actually look slick
					errors += Pkg.aur_install('lightdm-slick-greeter lightdm-settings')
					if errors == 0: ldm_greeter = 'slick'
				else:
					errors += Pkg.aur_install('lightdm-pantheon-greeter')
					if errors == 0: ldm_greeter = 'pantheon'
		else:
			ldm_greeter = 'deepin'

	# TODO Install other greeters here too
	if ldm_greeter == 'gtk' or errors != 0:
		# TODO Setup proper config
		errors += Pkg.install('lightdm-gtk-greeter lightdm-gtk-greeter-settings')

	# Set session greeter
	errors += IO.replace_ln(lightdm_cfg, '#greeter-session=', f'greeter-session=lightdm-{ldm_greeter}-greeter')

	return errors

# TODO Extent to support pre-chroot as well
def found_in_log(to_find=''):
	if os.path.isfile('/setup.log'):
		ret_val = Cmd.suppress(f'cat /setup.log | grep "{to_find}"') # '| grep -v "^[installed]"'?
		return (ret_val == 0)
	else: return False

def hide_app(app_name=''):
	# TODO Add supports for multiple .desktop files (separated by spaces)
	Cmd.exec(f"echo 'NoDisplay=true' >>{apps_path}/{app_name}.desktop")

# Add new kernel parameters to GRUB's 'GRUB_CMDLINE_LINUX(_DEFAULT)' config line
# TODO Add compat with systemd-boot on more minimal UEFI systems
def add_kernel_par(parameters='', only_default=True):
	parameters = parameters.strip()

	# TODO Support ' and " quote styles separately
	# TODO Turn into a function
	def_ln = IO.get_ln_number('/etc/default/grub', 'GRUB_CMDLINE_LINUX_DEFAULT="') # 6
	def_pars = str(Cmd.output(f'sed -n {def_ln}p /etc/default/grub')).strip() # GRUB_CMDLINE_LINUX_DEFAULT="quiet"
	def_pars = def_pars[:-1] + ' ' + parameters + '"' # GRUB_CMDLINE_LINUX_DEFAULT="... {x}"
	Cmd.log(f'sed \'{def_ln}s/.*/{def_pars}/\' -i /etc/default/grub')

	if not only_default:
		all_ln = IO.get_ln_number('/etc/default/grub', 'GRUB_CMDLINE_LINUX="') # 7
		all_pars = str(Cmd.output(f'sed -n {def_ln}p /etc/default/grub')).strip() # GRUB_CMDLINE_LINUX=""
		all_pars = all_pars[:-1] + ' ' + parameters + '"' # GRUB_CMDLINE_LINUX="... {x}"
		Cmd.log(f'sed \'{all_ln}s/.*/{all_pars}/\' -i /etc/default/grub')

def get_configs(repo):
	if not fetch_configs:
		log(f"\n[setup.py:get_configs('{repo}')] WARN: Ignoring since fetch_configs wasn't enabled.")
		return 1

	# TODO Put working stuff in /tmp?
	# Fetch config archive
	errors = Cmd.log(f'curl https://github.com/arch-installer/{repo}/archive/master.zip -Lso /configs-master.zip')
	if errors == 0:
		# Get files ready
		Cmd.log('unzip /configs-master.zip -d /')
		Cmd.log('find /*-master/ -path "*/.keep" -delete')
		Cmd.suppress('shopt -s dotglob && cp -rpT /*-master/ /')

		# User configs
		if os.path.isdir('/home/USER/'):
			cmd = 'cd /home'
			for user in unres_users:
				cmd += f'; cp -a ./USER/. {user}/'
			Cmd.log(cmd + '; rm -rf ./USER/; cd')

		# Clean up
		Cmd.log('rm -rf /*-master*') # {...,README.md}
	return errors

def de_setup():
	if fetch_configs:
		# DE configs (common DE)
		write_msg("Setting up DE specific configs...", 1)
		errors = get_configs('common')
		errors += get_configs(de) # e.g. 'cinnamon'
		#if not bat_present: Cmd.log('cd /etc/xdg/autostart/ && mv numlockx.desktop.bak numlockx.desktop; cd')
		write_status(errors)

	# Components
	de_dislay = de.upper().replace('XFCE', 'Xfce').replace('CINNAMON', 'Cinnamon').replace('BUDGIE', 'Budgie').replace('LXQT', 'LXQt').replace('I3', 'i3')
	# TODO If not dummy ... ?
	write_msg(f'Configuring the {de_dislay} desktop environment, please wait...', 1)
	installed = True
	errors = 0

	# TODO https://wiki.archlinux.org/index.php/Pantheon

	# TODO Auto-login support for 'passwdless_users' in all DEs?

	# Create user directories
	errors = Pkg.install('xdg-user-dirs-gtk')
	for user in unres_users:
		if enable_assistive_tech:
			Cmd.log(f'rm /home/{user}/.config/autostart/disable-nbsp.desktop')

		# TODO Use move everything over to 'kde' configs repo
		if de == 'kde':
			# TODO Make more KDE theme folders etc.
			Cmd.log('mkdir -p ~/.local/share/plasma/ ~/.local/share/templates/ && cd ~/.local/share/plasma/ && mkdir look-and-feel desktopthemes ', user)
			# TODO Don't create Public & Templates dirs w/ xdg-user-dirs (global KDE configs from GitHub)

	if enable_multilib:
		Pkg.install('lib32-gtk3')

	# TODO Force installation to not trigger (Updating linux initcpios) to run it seperately at the end
	# => Remove pacman hook for mkinitcpio

	if de == 'gnome':
		# TODO: Use new group install stuff etc.

		# Setup patched GDM for PRIME enabled GPUs
		if gpu_has_switchable_gfx and 'optimus' in video_drv:
			errors += Pkg.aur_install('gdm-prime')
		else:
			errors += Pkg.install('gdm')
		errors += Cmd.log('systemctl enable gdm')

		errors += Pkg.install('gnome-control-center folks gnome-keyring gnome-backgrounds gnome-menus gnome-user-share sushi nautilus-image-converter nautilus-share seahorse-nautilus rygel gnome-icon-theme-extras gnome-shell-extensions chrome-gnome-shell highlight evolution-bogofilter ibus-libpinyin ostree gtk-engines gnome-terminal') # Base; telepathy gnome-session mailnag-gnome-shell mailnag-goa-plugin libgit2-glib razor gnome-remote-desktop
		# TODO gnome-getting-started-docs after working on initial setup phase

		if install_de_apps:
			errors += Pkg.install('eog file-roller gedit gnome-calculator gnome-calendar gnome-clocks gnome-disk-utility gnome-font-viewer gnome-logs gnome-music gnome-photos gnome-screenshot gnome-system-monitor gnome-todo gnome-weather gnome-documents gnome-contacts gnome-tweaks seahorse evince vinagre') # Main apps; rhythmbox gnome-weather gnome-contacts gnome-sound-recorder epiphany polari
			#errors += Pkg.install('') # Misc apps
			#errors += Pkg.install('') # App opt-deps; gedit-code-assistance gedit-plugins eog-plugins

		#hide_app('org.gnome.Evince')

		# TODO Install & enable chromium/firefox extension automatically?

		"""
		if len(users) > 0:
			# TODO Replace with proper keymap parsing from vconsole to xkbmap format

			# TODO Wayland keymap

			# X keymap
			# TODO Seperate this to a function
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

			# TODO Check if §locale needs to be full 'en_US.UTF-8' form instead of 'en_US'
			dconf = Cmd.output('curl https://git.io/gnome-dconf.ini -Ls').strip().replace('§locale', LC_ALL).replace('§xkb', kbmap)
			ret_val = IO.write('/dconf.ini', dconf) # /tmp/dconf.ini
			#for user in users.split(','):
			#	Cmd.log('$ dbus-launch --exit-with-session dconf load / < /dconf.ini', user)

			#if ret_val == 0:
				#for user in users.split(','):
					#restricted = User.is_restricted(user)
					#group = ('restricted' if restricted else 'users')
					#Cmd.log(f'chown {user}:{group} /tmp/dconf.ini')
					# '$ (dbus-launch --exit-with-session) dconf load / < /tmp/dconf.ini'

				#Cmd.log('rm -f /tmp/dconf')
		"""

		# Add some extensions
		if enable_aur:
			Pkg.install('python-nautilus libcanberra gsound') # libappindicator-gtk2 libappindicator-gtk3

			# Activities Configurator; Status Area Horizontal Spacing; KStatusNotifierItem/AppIndicator Support; Clipboard Indicator; Remove Dropdown Arrows; WindowOverlay Icons; Caffeine; GSConnect; OpenWeather; Screenshot Tool; Dash to Dock; Suspend Button; Night Light Slider
			Pkg.aur_install('gnome-shell-extension-activities-config gnome-shell-extension-status-area-horizontal-spacing gnome-shell-extension-appindicator-git gnome-shell-extension-clipboard-indicator-git gnome-shell-extension-remove-dropdown-arrows-git gnome-shell-extension-windowoverlay-icons gnome-shell-extension-caffeine-git gnome-shell-extension-gsconnect-git gnome-shell-extension-openweather-git gnome-shell-extension-screenshot-git gnome-shell-extension-dash-to-dock-git gnome-shell-extension-suspend-button-git gnome-shell-extension-night-light-slider-git')

			# For showing lock keys' status in panel
			if bat_present:
				Pkg.aur_install('gnome-shell-extension-lockkeys-git')

			# Missing: NoAnnoyance; Remove Alt+Tab Delay
			# Other: gnome-shell-extension-audio-output-switcher-git gnome-shell-extension-desktop-icons-git gnome-shell-extension-dash-to-panel-git

			if 'bumblebee' in video_drv:
				Pkg.aur_install('gnome-shell-extension-bumblebee-status-git')
			#elif 'prime' in video_drv: # https://github.com/fffilo/prime-indicator
		
		# Start Xorg session by default (for now: https://bugs.archlinux.org/task/53284)
		if 'nvidia' in video_drv and 'noveau' not in video_drv:
			file = '/etc/gdm/custom.conf'
			IO.uncomment_ln(file, 'WaylandEnable=false')

			for user in users.split(','):
				IO.replace_ln(f'/var/lib/AccountsService/users/{user}', 'XSession=', 'XSession=gnome-xorg')

		# TODO Fix nautilus 'Folder name is too long' allowing only 1 character file & dir names (vmware shares)?

		# Make automatic login possible
		# NOTE Session type cannot be changed if in 'nopasswdlogin' group
		#IO.write('/etc/pam.d/gdm-password', 'auth sufficient pam_succeed_if.so user ingroup nopasswdlogin')

	# TODO Get packages from mate.txt
	elif de == 'mate':
		# Packages
		errors += Pkg.install('mate mate-extra')
		#errors += Pkg.install('')

		errors += lightdm_setup() # Uses slick greeter, TODO Set wallpaper to one of the MATE ones

	# TODO Setup packages properly
	elif de == 'kde':
		# TODO Remove every useless stuff
		errors += Pkg.install('phonon-qt5-vlc qt5-translations kdialog qt5-graphicaleffects redshift') # phonon-qt5-gstreamer
		# TODO Only install translations if something else than en_US (also) detected in locales
		errors += Pkg.install_group('sddm plasma plasma-wayland-session qt5-wayland kde-applications', 'kdevelop kdenlive umbrello kimagemapeditor cervisia kcachegrind kmix lokalize akonadi akonadiconsole okular ktimer kruler kget akregator kde-dev-utils juk sweeper kgpg filelight kmailtransport kirigami-gallery plasma-sdk kapptemplate kwordquiz khangman kiten klettres parley kanagram kbruch cantor kalgebra kig kmplot rocs artikulate kturtle kgeography step blinken minuet ktouch kalzium marble libkdegames kolourpaint kwave dragon konqueror kcharselect kteatime kate kdf kbackup kopete telepathy-qt elisa gwenview') # qt5-tools
		#if enable_aur and install_pamac: errors += Pkg.aur_install('pamac-tray-appindicator')

		# wayland: export GDK_BACKEND=wayland QT_QPA_PLATFORM=wayland-egl SDL_VIDEODRIVER=wayland CLUTTER_BACKEND=wayland
		# pkg: glew-wayland glfw-wayland

		if install_de_apps:
			Pkg.install('gwenview elisa trojita') # Basic programs
			if camera_present: Pkg.install('kamoso')

		errors += Pkg.install('pkcs11-helper botan encfs cryfs kdeconnect ruby kipi-plugins kimageformats libnma qt5-imageformats qt5-virtualkeyboard qt5-networkauth qt5-websockets qt5-connectivity packagekit-qt5') # scim kdepim-addons

		errors += Cmd.exec('cd /tmp; git clone --depth 1 https://github.com/MarianArlt/kde-plasma-chili.git &>>/setup.log && mv /tmp/kde-plasma-chili /usr/share/sddm/themes/')
		# TODO Single-user autologin from /etc/sddm.conf
		errors += Cmd.log('cp /usr/lib/sddm/sddm.conf.d/default.conf /etc/sddm.conf')
		errors += IO.replace_ln('/etc/sddm.conf', 'Current=', 'Current=kde-plasma-chili')
		if enable_aur:
			errors += IO.replace_ln('/etc/sddm.conf', 'CursorTheme=', 'CursorTheme=capitaine-cursors')
		else:
			errors += IO.replace_ln('/etc/sddm.conf', 'CursorTheme=', 'CursorTheme=Breeze_Snow')
		errors += Cmd.log('systemctl enable sddm')

		# TODO Hide apps: Qt Assistant, Qt Linguist, Qt QDbusViewer, KUIViewer

		# TODO Make directory skeleton for KDE applet, plasma-themes etc themes in ~/.local for all users
		# TODO Setup settings for Plasma & other apps
		# TODO Set cursor, dark theme w/ blur etc

	elif de == 'xfce':
		exclude_list = 'xfce4-eyes-plugin xfce4-dict parole' # xfce4-mpc-plugin

		if not bat_present:
			exclude_list += ' xfce4-battery-plugin'
		if not disc_tray_present:
			exclude_list += ' xfburn'
		# TODO: NVIDIA & xfce4-sensors-plugin implementation

		errors += Pkg.install_group('xfce4 xfce4-goodies', exclude_list)
		Pkg.install('light-locker gnome-screensaver gnome-keyring ffmpegthumbnailer libgsf libopenraw gtk-engines hddtemp ttf-droid') # Opt-depends

		#errors += Pkg.install('xorg-xkill xorg-xprop xbindkeys')

		if install_de_apps:
			Pkg.install('arandr sylpheed xarchiver')
			#Pkg.install('') # Apps (gucharmap)

			if enable_aur:
				errors += Pkg.aur_install('menulibre')

		# Hide some app icons
		hide_app('globaltime')
		hide_app('xfce4-sensors')
		# hide_apps('globaltime xfce4-sensors')

		errors += lightdm_setup() # Uses slick greeter, TODO Set wallpaper to one of the XFCE4 ones

	elif de == 'dde':
		# TODO https://wiki.archlinux.org/index.php/Deepin_Desktop_Environment#Customize_touchpad_gesture_behavior
		errors += Pkg.install(f'deepin-anything-{("dkms" if use_dkms_pkgs else "arch")} deepin-session-ui deepin-community-wallpapers deepin-turbo dtkwm deepin-screensaver-pp deepin-shortcut-viewer deepin-terminal') # deepin-kwin deepin-wallpapers-plasma deepin-topbar
		errors += Pkg.install('qt5-translations zssh python-xdg easy-rsa proxychains-ng iw networkmanager-openconnect networkmanager-openvpn networkmanager-pptp networkmanager-strongswan networkmanager-vpnc network-manager-sstp')
		errors += Pkg.install('redshift file-roller gedit')
		if install_de_apps:
			errors += Pkg.install('deepin-boot-maker deepin-calculator deepin-clone deepin-image-viewer deepin-movie deepin-music deepin-picker deepin-screen-recorder deepin-screenshot deepin-system-monitor deepin-voice-recorder geary') # deepin-manual

		# Hide some app icons
		# hide_apps('redshift-gtk xscreensaver-properties')
		hide_app('redshift-gtk')
		hide_app('xscreensaver-properties')

		# TODO Setup touchpad gestures: /usr/share/dde-daemon/gesture.json
		# Sounds: /usr/share/sounds/deepin/stereo
		# TODO NVIDIA proprietary issue: No background after resuming from standby
		# TODO Utilize deepin-grub2-themes if multibooting? (/boot/grub/themes/deepin/theme.txt)

		errors += lightdm_setup() # Uses deepin greeter

	elif de == 'cinnamon':
		errors += Pkg.install('cinnamon')

		# Opt-depends
		Pkg.install('cinnamon-translations gnome-color-manager gnome-online-accounts gtk-engines gtk3 ffmpegthumbnailer freetype2 libraqm djvulibre libspectre gnome-keyring libdmapsharing grilo-plugins libnotify python-xdg')

		# Other
		Pkg.install('arc-gtk-theme gnome-terminal')

		# Apps
		if install_de_apps:
			errors += Pkg.install('file-roller gnome-calculator gnome-disk-utility nemo seahorse redshift gnome-screenshot xed gnome-logs gnome-system-monitor rhythmbox vinagre xreader geary nemo-fileroller nemo-image-converter nemo-seahorse meld') # nemo-preview nemo-share
			# gpasswd -a $USER sambashare

			# KDE Connect
			if enable_aur:
				errors += Pkg.install('breeze-icons kde-cli-tools')
				errors += Pkg.aur_install('indicator-kdeconnect-git')

		# Packages: xplayer(AUR) gparted tomboy

		if bt_present: errors += Pkg.install('blueberry')

		if enable_aur:
			Pkg.install('libgit2-glib')
			errors += Pkg.aur_install('cinnamon-sound-effects mint-sounds mint-themes mint-y-icons mint-backgrounds-sylvia mint-backgrounds-tara mint-backgrounds-tessa xviewer timeshift')
		else:
			errors += Pkg.install('gpicview')

		errors += lightdm_setup() # Uses slick greeter + configure

	# TODO Fix compositing issues...
	elif de == 'budgie':
		errors += Pkg.install('budgie-desktop budgie-extras gnome-backgrounds gnome-control-center gnome-screensaver network-manager-applet gnome-keyring rygel')
		errors += Pkg.install('gtk-engines sushi highlight evolution-bogofilter') # polkit-gnome
		errors += Pkg.install('nautilus eog file-roller gedit gnome-calculator gnome-disk-utility gnome-maps gnome-screenshot gnome-system-monitor gnome-terminal gnome-weather rhythmbox grilo-plugins gnome-calendar') # gnome-sound-recorder dconf-editor gnome-tweaks

		# TODO Other theming packages?

		if enable_aur:
			Pkg.aur_install('matcha-gtk-theme') # TODO Use 'Matcha-dark-azul' GTK theme

		# TODO dconf restore for proper setting & themes etc

		errors += lightdm_setup() # Uses slick greeter, TODO Set wallpaper to one of the Budgie ones?

	elif de == 'lxde':
		errors += Pkg.install_group('lxde', 'lxdm')
		errors += Pkg.install('xorg-xwininfo xorg-xprop xorg-xkill picom gnome-themes-standard ttf-droid python-xdg python2-xdg fluidsynth libmad opusfile wireless_tools gtk-engines gpart mtools network-manager-applet libnotify notify-osd pasystray paprefs xfce4-power-manager feh')
		errors += Pkg.install('sylpheed xarchiver galculator leafpad xpad xfce4-screenshooter nm-connection-editor obconf rofi redshift')

		Cmd.log('cp /usr/bin/lxde-logout /usr/bin/lxde-logout.bak')
		IO.replace_ln(f'{apps_path}/lxde-logout.desktop', 'Icon=', 'Icon=system-shutdown')
		IO.replace_ln(f'{apps_path}/lxde-logout.desktop', 'Exec=', 'Exec=arch-logout')
		IO.replace_ln(f'{apps_path}/xpad.desktop', 'Icon=', 'Icon=gnote')
		hide_app('pasystray')

		# TODO Arch profile icon
		# TODO More complete mimeapps list for less frustration
		# TODO Fix black on rounded corners in GTK
		# TODO Language manager package?
		# TODO lxmusic => 'LXMusic'

		ret_val = Cmd.suppress('find /sys/class/backlight/*')
		if ret_val == 0:
			errors += Pkg.install('xorg-xbacklight')

		if bt_present:
			errors += Pkg.install('blueman') # net-tools
			# TODO Setup autostart?

		if camera_present:
			errors += Pkg.install('guvcview')

		if enable_aur:
			errors += Pkg.aur_install('menulibre') # ob-autostart
			# TODO Create desktop icon for ob-autostart & use some autostart icon

		lightdm_setup()

	elif de == 'lxqt':
		errors += Pkg.install('--asexplicit libstatgrab libsysstat lm_sensors') # Opt-deps
		errors += Pkg.install('sddm obconf-qt lxqt-themes lxqt-session lxqt-qtplugin lxqt-runner lxqt-panel lxqt-powermanagement lxqt-openssh-askpass lxqt-policykit lxqt-notificationd lxqt-config lxqt-admin lxqt-about lxqt-sudo pcmanfm-qt qterminal breeze-icons picom') # lxqt

		if bt_present:
			errors += Pkg.install('bluedevil')

		if install_de_apps:
			errors += Pkg.install('lximage-qt trojita elisa screengrab ark kcalc qtpass partitionmanager')
			if enable_aur:
				pkgs = 'featherpad qlipper compton-conf'
				if install_pamac: pkgs += ' pamac-tray-appindicator'
				errors += Pkg.aur_install(pkgs)
		#errors += Pkg.install('')

		# TODO SDDM theme
		# TODO Screenlock

		if enable_aur:
			Pkg.aur_install('nm-tray-git xscreensaver-arch-logo-nogdm archlinux-lxqt-theme sand-lxqt-theme lxqt-less-theme-git lxqt-arc-dark-theme-git') # lxqt-connman-applet
		else:
			Pkg.install('xscreensaver network-manager-applet')

		Cmd.log('systemctl enable sddm')

	elif de == 'i3':
		# TODO: Setup and integrate 'betterlockscreen' here at some point ()
		errors += Pkg.install('perl-json-xs perl-anyevent-i3 perl-async-interrupt perl-ev perl-guard perl-net-ssleay xorg-xwininfo xorg-xprop xorg-xev xorg-xkill xorg-xrandr ffmpegthumbnailer gnome-themes-extra libnotify python-gobject python-xdg') # Opt-deps
		errors += Pkg.install('i3-gaps gnome-terminal lxrandr rofi rofimoji dunst nitrogen picom nemo cinnamon-translations lxappearance redshift slop scrot xclip polkit-gnome gnome-keyring playerctl') # Main components

		if fetch_configs:
			# TODO:
			# "/home/USER/.config/i3/scripts/autorun/disabled/restore-lxrandr.sh" -> replace all / with \/
			# sed "s/#display-setup-script.*/display-setup-script = \/usr\/bin\/lightdm-screen-setup/" -i /etc/lightdm/lightdm.conf
			pass

		if enable_aur:
			Pkg.aur_install('rofi-dmenu rofi-greenclip polybar xmousepasteblock xviewer mint-themes') # betterlockscreen
		else:
			Pkg.install('i3block i3status gpicview arc-gtk-theme')

		if install_de_apps:
			# network-manager-applet jpegexiforient nemo-image-converter nemo-preview nemo-share djvulibre libspectre jsoncpp
			errors += Pkg.install('htop arandr nemo-fileroller xed dconf-editor gnome-calculator gnome-clocks gparted nemo-seahorse gucharmap ncdu')

			if enable_aur:
				Pkg.aur_install('gscreenshot')
			else:
				Pkg.install('mate-utils')

		# Bluetooth
		if bt_present: Pkg.install('blueman')

		# Laptops
		if bat_present:
			Pkg.install('xfce4-power-manager xorg-xbacklight xorg-xgamma xorg-xinput')
			# TODO: Touchpad configuration (e.g. tap to click, ...)

		# Desktops
		else:
			Pkg.install('numlockx')

		lightdm_setup()

	elif de == 'dummy': # Dummy desktop
		pass

	else: # Unknown desktop
		errors = 1
		installed = False

	write_status(errors)

	if installed:
		# TODO More descriptive action statuses => no empty blinking prompt for a while

		if boot_mode == 'UEFI':
			Pkg.install('fprint fwupd tpm2-abrmd tpm2-tools')

		if Cmd.exists('v4l2-ctl'):
			# Hide V4L test apps
			# hide_apps('qv4l2 qvidcap')
			hide_app('qv4l2')
			hide_app('qvidcap')

		# TODO Hide cheese if no camera present?
		if Cmd.exists('cheese'):
			if not camera_present:
				hide_app('org.gnome.Cheese')
			else:
				Pkg.install('gnome-video-effects') # For some cheese effects

		# Hide avahi application icons by default
		if Cmd.exists('avahi-discover'):
			# hide_apps('avahi-discover bssh bvnc')
			hide_app('avahi-discover')
			hide_app('bssh')
			hide_app('bvnc')

		if Cmd.exists('picom'):
			hide_app('compton')
			hide_app('picom')

		# TODO Move flatpak, snapd & other stuff outside DE to install on no-DE systems if required
		if enable_flatpak:
			write_msg('Installing support for flatpak packages...', 1)
			errors = 0
			if use_qt_apps: errors += Pkg.install('xdg-desktop-portal-kde')
			else: errors += Pkg.install('xdg-desktop-portal-gtk')
			errors += Pkg.install('flatpak-builder fakeroot fakechroot') # flatpak-builder
			errors += Cmd.log('pacman -D --asexplicit flatpak')
			"""
			Dirs for .desktop files:
			~/.local/share/flatpak/exports/share/applications
			/var/lib/flatpak/exports/share/applications
			"""
			write_status(errors)

		if enable_aur:
			Pkg.aur_install('ananicy')
			Cmd.log('systemctl enable ananicy')

			if enable_snap:
				write_msg('Installing support for snap packages...', 1)
				errors = Pkg.aur_install('snapd')
				errors += Cmd.log('pacman -D --asexplicit snapd')
				errors += Pkg.install('apparmor')
				Cmd.log('systemctl enable snapd.socket apparmor snapd.apparmor')
				Cmd.log('ln -s /var/lib/snapd/snap /snap') # For classic confinement snaps
				# https://wiki.archlinux.org/index.php/AppArmor#Installation
				# TODO: Do snap core setup
				add_kernel_par('apparmor=1 security=apparmor')
				write_status(errors)

			# TODO After additional packages
			if Cmd.exists('gnome-terminal'):
				write_msg('Patching GNOME Terminal to include transparency...', 1)
				Pkg.remove('gnome-terminal')
				errors = Pkg.aur_install('gnome-terminal-transparency')
				write_status(errors)

		if enable_assistive_tech:
			# TODO Setup onboard model M theme
			write_msg('Installing support for assistive technologies...')
			errors = Cmd.log("sed '/a11y/d' -i /etc/lightdm/slick-greeter.conf")
			errors = Pkg.install('festival espeak speech-dispatcher orca mousetweaks onboard flite')
			if de == 'kde':
				errors += Pkg.install('kmag kmousetool kmouth') # TODO More packages here
			if enable_aur:
				if de == 'mate':
					errors += Pkg.aur_install('xzoom') # magnifier
			write_status(errors)

		# TODO Before everything else here?
		# Every desktop optdepends
		write_msg('Installing some additional packages for proper system operation...', 1)
		Cmd.suppress('pacman -Rdd --noconfirm blas')
		errors = Pkg.install('xdotool wmctrl xdg-utils perl-locale-gettext fuse notification-daemon exfat-utils ntfs-3g samba freerdp libgpod ibus libiscsi nfs-utils libnfs zip unrar lrzip p7zip unace libheif poppler-data quota-tools mlocate vorbis-tools libappimage openblas geoclue libwlocate coin-or-mp jpegexiforient sshfs') # unarchiver numlockx

		# TODO: env var "GTK_MODULES=canberra-gtk-module"(?)
		if enable_aur:
			Pkg.aur_install('sound-theme-smooth')
		else:
			Pkg.install('sound-theme-freedesktop')

		if enable_firewall:
			errors += Pkg.install('gufw')

		if found_in_log('gvfs-goa: '):
			errors += Pkg.install('--asexplicit gvfs-goa gvfs-google', False)
		errors += Pkg.install('gvfs gvfs-afc gvfs-smb gvfs-gphoto2 gvfs-mtp gvfs-nfs')
		Cmd.log('pacman -D --asexplicit gvfs gvfs-afc gvfs-smb gvfs-gphoto2 gvfs-mtp gvfs-nfs')

		errors += Pkg.install('python-setuptools python-pip python-dbus python-pystemmer python-pysocks python-brotlipy python-pyopenssl') # python-idna python-cryptography python-h2 python-opengl
		errors += Pkg.install('enchant hunspell-en_US aspell-en libmythes mythes-en') # Spell checking (hspell libvoikko)
		if de != 'i3': # => de == 'kde': ...
			errors += Pkg.install('libdbusmenu-glib libdbusmenu-gtk3 libdbusmenu-gtk2 appmenu-gtk-module')
			ret_val = Cmd.suppress('pacman -Qqs | grep qt4')
			if ret_val == 0: Pkg.install('appmenu-qt4') # TODO Move after custom_setup()?

		if disc_tray_present:
			errors += Pkg.install('libisofs libisoburn libburn libdvdcss libbluray vcdimager libdvdread cdrtools dvd+rw-tools cdrdao transcode cdparanoia dvdauthor udftools emovix')

		# Add IR packages
		ret_val = Cmd.output('dmesg | grep -i " ir "')
		if ret_val == 0: errors += Pkg.install('lirc')

		# Allow simple manual configuration of Qt5 theming with an extra program
		if not use_qt_apps and de != "dde":
			Pkg.install('gtk-engine-murrine')
			if enable_aur:
				Pkg.install('qt5ct')
				Pkg.aur_install('qt5-styleplugins')
				file = '/etc/environment'
				Cmd.exec('echo "QT_QPA_PLATFORMTHEME=qt5ct" >> ' + file) # gtk2
		write_status(errors)

		write_msg('Configuring some additional fonts, please wait...', 1)
		errors = Pkg.install('noto-fonts ttf-dejavu ttf-liberation ttf-inconsolata ttf-bitstream-vera ttf-anonymous-pro ttf-roboto ttf-ubuntu-font-family') # xorg-fonts-misc adobe-source-sans-pro-fonts ttf-droid
		if enable_aur:
			errors += Pkg.aur_install('terminus-font-ll2-td1-otb nerd-fonts-hack nerd-fonts-fira-code')
		else:
			errors += Pkg.install('ttf-fira-code ttf-hack')
		# Infinality fonts
		ft2 = '/etc/profile.d/freetype2.sh'
		IO.replace_ln(ft2, '#export ', 'export FREETYPE_PROPERTIES="truetype:interpreter-version=38"')
		write_status(errors)

		write_msg('Installing some additional applications, please wait...', 1)
		errors = Pkg.install('firefox')
		if install_de_apps:
			errors += Pkg.install('pavucontrol bleachbit')
			IO.replace_ln(f'{apps_path}/pavucontrol.desktop', 'Icon=', 'Icon=gnome-volume-control')

			if install_office:
				errors += Pkg.install('libreoffice-fresh')
				# Try to install language pack
				#Pkg.install(f'libreoffice-fresh-{keymap}')
				Cmd.log(f'sed "37s/.*/NoDisplay=true\\n/" -i {apps_path}/libreoffice-base.desktop')
				Cmd.log(f'sed "38s/.*/NoDisplay=true\\n/" -i {apps_path}/libreoffice-math.desktop')

			if de == 'kde':
				errors += Pkg.install('ktorrent')
			elif de == 'lxqt':
				errors += Pkg.install('transmission-qt')
			else:
				errors += Pkg.install('transmission-gtk')

			if use_qt_apps: # Media player
				errors += Pkg.install('vlc protobuf libmicrodns live-media libgoom2 projectm dav1d qt5-translations krita') # Qt5
			else:
				errors += Pkg.install('gimp')
				if de != 'dde':
					errors += Pkg.install('celluloid')
				if enable_aur:
					errors += Pkg.aur_install('mpv-mpris')

			if enable_printing: # Scanning / printing software
				# For HP printers
				errors += Pkg.install('python-pyqt5 python-reportlab hplip')

				if use_qt_apps:
					errors += Pkg.install('skanlite') # Qt5
				else:
					errors += Pkg.install('simple-scan')

			if disc_tray_present: # Disc burning utility
				if use_qt_apps:
					errors += Pkg.install('k3b') # Qt5
				else:
					if de != 'xfce' and de != 'lxde':
						errors += Pkg.install('brasero')
					else:
						errors += Pkg.install('xfburn')
						IO.replace_ln(f'{apps_path}/xfburn.desktop', 'Icon=', 'Icon=brasero')
			#else: # TODO Hide found apps

			ret_val = Cmd.suppress('pacman -Qq | grep eog')
			if ret_val == 0: errors += Pkg.install('gnome-software-packagekit-plugin')

			if enable_aur and install_pamac: # pamac
				errors += Pkg.install('pacman-contrib')
				errors += Pkg.aur_install('pamac-aur')
				Cmd.log('cp /etc/pamac.conf /etc/pamac.conf.bak')
				IO.uncomment_ln('/etc/pamac.conf', 'EnableDowngrade')
				errors += IO.uncomment_ln('/etc/pamac.conf', 'EnableAUR')
				errors += IO.uncomment_ln('/etc/pamac.conf', 'CheckAURUpdates')
				IO.replace_ln('/etc/pamac.conf', 'KeepNumPackages', 'KeepNumPackages = 2')
				IO.uncomment_ln('/etc/pamac.conf', 'OnlyRmUninstalled')
				categories = 'Categories=GNOME;GTK;System;X-XFCE-SettingsDialog;X-XFCE-SystemSettings;'
				IO.replace_ln(f'{apps_path}/pamac-manager.desktop', 'Categories=', categories)
				IO.replace_ln(f'{apps_path}/pamac-updater.desktop', 'Categories=', categories)

		# Hide from accessories category in XFCE etc.
		if Cmd.exists('lightdm-gtk-greeter-settings'):
			IO.replace_ln(f'{apps_path}/lightdm-gtk-greeter-settings.desktop', 'Categories=', 'Categories=GNOME;GTK;Settings;X-XFCE-SettingsDialog;X-XFCE-SystemSettings;')

		if Cmd.exists('libfm-pref-apps'):
			IO.replace_ln(f'{apps_path}/libfm-pref-apps.desktop', 'Name=', 'Name=Preferred Applications (PCManFM)')

		write_status(errors)

		if len(users) > 0:
			# Install an icon pack
			write_msg("Installing 'Tela' icon theme...", 1)
			ret_val = Pkg.aur_install('tela-icon-theme-git')
			write_status(ret_val)

		write_msg("Installing MTP support...", 1)
		errors = 0
		if enable_aur:
			# jmtpfs
			Pkg.remove('mtpfs', False, False)
			errors += Pkg.aur_install('jmtpfs')
		else:
			# mtpfs
			errors += Pkg.install('mtpfs')
		write_status(errors)
	else:
		write_status('A handler for this DE has not been added yet, no DE installed...', 4)

def printing_setup():
	write_msg('Installing packages for printing & scanning support, please wait...', 1)

	# Avahi
	Cmd.log('systemctl disable systemd-resolved')
	errors = Pkg.install('avahi')
	errors += Cmd.log('systemctl enable avahi-daemon')
	errors += Pkg.install('nss-mdns')
	errors += IO.replace_ln('/etc/nsswitch.conf', 'hosts: ', 'hosts: files mymachines mdns4_minimal [NOTFOUND=return] resolve [!UNAVAIL=return] dns mdns4 myhostname')
	# TODO if UWF, open port 5353/UDP

	# TODO Add printer & scanner auto-detection
	Cmd.log('mkdir -p /etc/samba/')
	Cmd.log('touch /etc/samba/smb.conf')
	# TODO Add users to 'sambashare' group for file sharing access? (Cinnamon)
	errors += Pkg.install('cups cups-pk-helper cups-pdf libcups gutenprint gsfonts foomatic-db foomatic-db-engine foomatic-db-gutenprint-ppds poppler-glib sane net-snmp colord-sane argyllcms system-config-printer samba python-pysmbc') # foomatic-db-nonfree foomatic-db-ppds
	if enable_multilib: errors += Pkg.install('lib32-libcups')
	if bt_present: errors += Pkg.install('bluez-cups')

	errors += Cmd.log('systemctl enable org.cups.cupsd.socket saned.socket')

	for user in unres_users:
		Cmd.log(f'gpasswd -a {user} cups')

	#errors += Pkg.install('python-pysmbc')

	write_status(errors)

def bootloader_extra_setup():
	write_msg('Installing GRUB multiboot support dependencies...', 1)
	ret_val = Pkg.install('ntfs-3g os-prober')
	write_status(ret_val)

	write_msg('Finding other bootloaders to add to GRUB menu...', 1)
	ret_val = update_grub()
	write_status(ret_val)

	#Cmd.log('umount /run/lvm')

def passwd_setup():
	write_ln()
	write_msg('Create a password for the §2root §0user:\n\n')
	for _ in range(3):
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
			write_msg(f"{start}Create a password for the {user_type} user §{('3' if user_type == 'regular' else '4')}'{user}'§0:\n\n")
			for _ in range(3):
				ret_val = Cmd.exec(f'passwd {user}')
				if ret_val == 0:
					break
				else:
					write_ln()
					write_msg('Please try that again:\n\n')
	write_ln() # TODO Indent by 1?

def chroot_setup():
	global hostname

	#if multibooting:
		# LVM 10 sec slow scan temp fix when installing os-prober
		#Cmd.log('mkdir -p /run/lvm && mount --bind /hostrun/lvm /run/lvm')

	# Update defailt about HW e.g. running in VM, cpu type, MBR boot dev etc.
	load_hw_info()

	log('\n[setup.py:chroot_setup()] System details:')
	# TODO Log more details here
	# TODO Show GPU info (seperate to get_gpu_details() func)
	log(f"KERNEL              '{kernel}'")
	log(f"CPU_IDENTIFIER      '{cpu_identifier}'")
	if boot_mode == 'BIOS/CSM':
		log(f"MBR_GRUB_DEV        '{mbr_grub_dev}'")
	if vm_env != '':
		log(f"VM_ENV              '{vm_env}'")
	log(f"BAT_PRESENT         '{bat_present}'")
	log(f"DISC_TRAY_PRESENT   '{disc_tray_present}'")
	log(f"CAMERA_PRESENT      '{camera_present}'")
	log(f"BT_PRESENT          '{bt_present}'")

	write_status(0) # Change 'Chrooting...' status msg to DONE

	if de != '':
		Pkg.install('cronie')
		Cmd.log('systemctl enable cronie')
	ret_val = Cmd.suppress('mount | grep discard')
	if ret_val != 0: Cmd.log('systemctl enable fstrim.timer')
	#IO.write('/etc/sysctl.d/10-vm.conf', 'vm.swappiness=1\nvm.vfs_cache_pressure=50\nzswap.enabled=1')
	timezone_setup()
	locale_setup()
	networking_setup()

	if len(users) > 0: user_setup()
	if enable_aur: aur_setup()
	if enable_multilib: multilib_setup()
	if enable_testing: testing_setup()

	# Enable pacman easter egg & colored output by default
	IO.uncomment_ln('/etc/pacman.conf', 'Color')
	Cmd.log('sed "38s/.*/ILoveCandy\\n/" -i /etc/pacman.conf')

	# TODO /usr on seperate partition => (... usr shutdown) hooks in mkinitcpio.

	ssh_setup()
	kernel_setup()
	bootloader_setup()
	#if web_server_type > 0: ...
	if xorg_install_type > 0: x_setup()
	if vm_env != '': vm_setup()
	if auto_detect_gpu: vga_setup() # else: xf86-video-fbdev xf86-video-vesa
	if use_pulseaudio: audio_setup()
	if bt_present: bt_setup()
	if enable_printing: printing_setup()

	# Configs
	if fetch_configs:
		write_msg("Setting up base system configs...", 1)
		Pkg.install('unzip')
		errors = get_configs('base')
		errors = get_configs('laptop' if bat_present else 'desktop')
		if not use_networkmanager or nm_rand_mac_addr: errors += Cmd.log('rm /etc/NetworkManager/conf.d/00-no-rand-wifi-scan-mac-addr.conf')
		if not use_ccache: errors += Cmd.log('rm /etc/ccache.conf')
		write_status(errors)

	if de != '': de_setup()
	# else: remove "~/.hidden" etc files unused?

	# TODO Use proper keymap globally in ALL DEs
	# TODO Check for other HW too e.g. fingerprint scanner (check lspci etc) & install proper packages
	# TODO Wine setup?

	if bat_present:
		write_msg('Configuring some packages for battery power savings...', 1)
		errors = Pkg.install('ethtool smartmontools x86_energy_perf_policy tlp tlp-rdw')
		errors += Cmd.log('systemctl enable tlp NetworkManager-dispatcher')
		errors += Cmd.log('systemctl mask systemd-rfkill.service systemd-rfkill.socket')
		# TODO Detect ThinkPad
		# TODO Btrfs: 'SATA_LINKPWR_ON_BAT=max_performance' for these systems
		# TODO Bumblebee: 'RUNTIME_PM_BLACKLIST="XX:XX.x"' & use GPU addr from 'lspci'
		# TODO Setup tharmald as well?
		write_status(errors)

	# TODO On KDE make theming direcoties automatically e.g. '~/.local/share/plasma/look-and-feel/' etc

	# TODO Boot time improvements

	if run_custom_setup:
		custom_setup()

	# Make AUR package build optimizations (after all caching)
	if optimize_compilation and not (not pkgcache_enabled or optimize_cached_pkgs):
		IO.replace_ln('/etc/makepkg.conf', 'CFLAGS="', f'CFLAGS="{cflags}"') # 40

	# Log fstab
	fstab = Cmd.output('cat /etc/fstab').rstrip()
	log(f'\n/etc/fstab\n==========\n{fstab}\n==========\n')

	# IO sheculer optimizations
	add_kernel_par('scsi_mod.use_blk_mq=1')
	#IO.write('/etc/udev/rules.d/60-ioschedulers.rules', '# Scheduler for non-rotating disks\nACTION=="add|change", KERNEL=="sd[a-z]|mmcblk[0-9]*|nvme[0-9]*", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="mq-deadline"\n# Scheduler for rotating disks\nACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"')

	# Lower default service timeout values (from 90s)
	IO.replace_ln("/etc/systemd/system.conf", "#DefaultTimeoutStartSec=", "DefaultTimeoutStartSec=15s")
	IO.replace_ln("/etc/systemd/system.conf", "#DefaultTimeoutStopSec=", "DefaultTimeoutStopSec=15s")

	if multibooting: bootloader_extra_setup()
	else:
		write_msg('Updating new kernel parameter for GRUB...', 1)
		ret_val = update_grub()
		write_status(ret_val)

	write_msg('Performing cleanup tasks...', 1)
	errors = 0

	# Clean up LVM os-prober scan fix dirs
	# TODO: Fix "/hostrun" not being removed
	#if multibooting:
		#Cmd.log('umount /run/lvm /hostrun && rm -r /hostrun')

	if sudo_ask_pass:
		Cmd.log('cp /etc/sudoers.bak /etc/sudoers')

		# Give wheel group users sudo permission w/ pass
		Cmd.log("chmod 770 /etc/sudoers")
		Cmd.log("sed '82 s/^# //' -i /etc/sudoers")
		Cmd.log("chmod 440 /etc/sudoers")

	if enable_aur:
		if len(unres_users) > 0:
			user = unres_users[0] # e.g. 'deathmist'

			# Move ccache over to 1st unrestricted user
			if use_ccache:
				dest = f'/home/{user}/.ccache/'
				Cmd.log(f'mkdir -p {dest} && mv /home/aurhelper/.ccache/* {dest}')

			# Move over all cached packages
			dest = f'/home/{user}/.cache/yay/'
			Cmd.log(f'mkdir -p {dest} && mv /home/aurhelper/.cache/yay/* {dest}')

		Cmd.log('userdel -f -r aurhelper')
	elif not sudo_ask_pass:
		# Give wheel group users sudo permission w/o pass
		Cmd.log("chmod 770 /etc/sudoers")
		Cmd.log("sed '85 s/^# //' -i /etc/sudoers")
		Cmd.log("chmod 440 /etc/sudoers")

	# Fix user dir ownerships
	if len(unres_users) > 0:
		for user in unres_users:
			errors += Cmd.log(f'chown -R {user}: /home/{user}/')

	# Clear orphan pkgs
	Cmd.log('pacman -Rns $(pacman -Qdtq) --noconfirm')

	# TEMP: Delete currently unused /README.md file for DEs without proper configs
	if os.path.isfile('/README.md'):
		Cmd.log('rm -f /README.md')

	write_status(errors)

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
# https://wiki.archlinux.org/index.php/Pacman/Restore_local_database

debug = '-d' in args.lower()
if debug: Cmd.suppress('rm /tmp/setup.log') # Remove possible old log

# Load color scheme
load_colors()

write_msg('Arch §7Linux ')
write(f'§4{boot_mode} §0live environment was detected. Press ENTER to continue...')
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

# TODO global outdated_pkgs?
outdated_pkgs = Cmd.output('pacman -Qqu')

# Update used out-of-date installer packages
# TODO Don't do partial updates?
if 'pacman' in outdated_pkgs:
	write_msg('Updating pacman...', 1)
	ret_val = Pkg.install('pacman', False)
	write_status(ret_val)

if 'archlinux-keyring' in outdated_pkgs:
	write_msg('Updating the Arch Linux keyring, please wait...', 1)
	ret_val = Pkg.install('archlinux-keyring', False)
	write_status(ret_val)

# TODO Make detect up-to-date pkgs
# TODO Don't run linux initcpios
write_msg('Updating live environment partitioning utilities...', 1)
ret_val = Pkg.install('parted btrfs-progs xfsprogs f2fs-tools', False) # e2fsprogs efitools
write_status(ret_val)

# NTP time synchronization
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
if 'arch-install-scripts' in outdated_pkgs:
	Pkg.install('arch-install-scripts', False)
write_status()

if '-M' not in args: sort_mirrors()

base_install(sys_root)

start_chroot(sys_root)

# Install done! Cleanup & reboot etc.

# Clean up setup files
Cmd.suppress(f'rm -f {sys_root}root/{{setup,config}}.py')
#Cmd.suppress(f'rm -f {sys_root}root/config.py')

if pkgcache_enabled:
	#Cmd.log('chown -R root:root /pkgcache/pkgcache/aur')

	# TODO Do all this inside chroot?
	# TODO Remove older package versions from the package cache (use modified time)
	# Get package name (rsplit('-', 4)[1] ?)
	# 4ti2-1.6.9-1-x86_64.pkg.tar.xz

	#write_msg('Checking package cache drive package versions...', 1)
	#write_msg(f'Clearing {old_pkg_count} old package versions...', 1)

	Cmd.suppress('cd && umount /mnt/pkgcache && rm -rf /mnt/pkgcache')
	Cmd.suppress('mv /etc/pacman.conf.bak /etc/pacman.conf')

# Move log on new system to '/var/log/setup.log'
Cmd.suppress(f'cp -f {sys_root}var/log/setup.log /tmp/')
#Cmd.suppress(f'cd && umount -R {sys_root[:-1]}') # TODO Fix /mnt being "busy"

# END OF SCRIPT
write_ln('§3>> The install script is done!', 2)
exit(0)
