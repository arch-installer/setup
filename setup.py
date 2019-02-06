#
#  Arch Installer Script by @JamiKettunen
#     - Python rewrite | 2019/02/06 -
#
#!/usr/bin/python

# File IO & OS check
from os import popen,name # WARN: normal variable 'name' used
# Standard write and read
from sys import stdout
# Call commands in a subshell
from subprocess import call
# Sleep command
from time import sleep

###############################
# Setup config variables
###############################

# Virtual console keymap - See vconsole-keymaps.txt for all options
# def. 'en'
keymap = "fi"

# Whether to enable NTP time synchronization
# def. 'True'
ntp_enabled = True

# Other groups & packages to install w/ pacstrap on top of 'base' & 'python'
# NOTICE: 'base-devel' is required for AUR support
# def. 'base-devel'
base_pkgs = "base-devel vim htop"

# Choose between 'stable' & 'unstable' repositories
# def. 'stable'
repo = "stable"

###############################
# Constant values
###############################

status_indexes = {
	0: 0,
	1: 4,
	2: 3,
	3: 2,
	4: 4,
	5: 7
}

status_mgs = {
	0: "    ",
	1: "WAIT",
	2: "DONE", # " OK "
	3: "FAIL",
	4: "WARN",
	5: "INFO"
}

boot_mode = "BIOS/CSM"

###############################
# Helper functions
###############################

# Screen text manipulation

# Clear the entire screen buffer
def clear_screen():
	shell_exec("clear")

# Writes text to stdout w/ the specified fg & bg colors
def write(text, fg_color=8, bg_color=1):
	stdout.write("\x1b[0;" +
		str(29 + fg_color) + ";" +
		str(39 + bg_color) + "m" +
		text +
		"\x1b[0m")
	stdout.flush()

# Writes a line of text to stdout w/ the specified fg & bg colors
def write_ln(text="", fg_color=8, bg_color=1):
	write(text + "\n", fg_color, bg_color)

# Writes a status message
# eg. ">> Using log engine v2.0"
#     ">> [ WAIT ] Fetching latest data..."
#     ">> [  OK  ] Started NetworkManager service"
#     ">> [ FAIL ] ..."
# TODO Dynamic messages (eg. changes on success/fail etc)
# TODO Progress reporting commands (eg. 'Updating sources... 34%')
def write_msg(status_msg, status=0, override_newline=-1):
	if (status > 0):
		index = status_indexes.get(status)
		write(">> ", index)
		write("[ " + status_mgs.get(status, 0) + " ] ", index)
		if (override_newline == -1):
			if (status > 1):
				write_ln(status_msg)
			else:
				write(status_msg)
		elif (override_newline == 1):
			write_ln(status_msg)
		else:
			write(status_msg)
	else:
		write(">> ", 7)
		if (override_newline == 1):
			write_ln(status_msg)
		else:
			write(status_msg)

# Writes back to the current status message line to update the appearance depending on a command's return value
def write_status(ret_val, expected_val=0, error_status=3):
	if (ret_val == expected_val):
		write("\r>> ", 3)
		write("[ " + status_mgs.get(2) + " ]", 3)
	else:
		index = status_indexes.get(error_status)
		write("\r>> ", index)
		write("[ " + status_mgs.get(error_status) + " ]", index)
	write("\n")

def print_header(header_text):
	clear_screen()
	write_ln(header_text, 7)
	for _ in header_text:
		write("=", 7)
	write_ln()
	write_ln()

# File IO

class io:
	@staticmethod
	def read_ln(fPath):
		try:
			with open(fPath, "r") as f:
				tmp_ln = f.readline().rstrip("\n")
		except:
			tmp_ln = None
		return tmp_ln

	@staticmethod
	def write_ln(fPath, text):
		try:
			with open(fPath, "a") as f:
				f.write(text + "\n")
			return 0
		except:
			return 1

def shell_exec(cmd):
	ret_val = call(cmd, shell=True) # Execute
	return ret_val                  # & return exit_code

# Logging

def log(text):
	io.write_ln("/tmp/setup.log", text)

def log_exec(cmd):
	try:
		log("\n\n# " + cmd)
		ret_val = call(cmd + " >>/tmp/setup.log 2>&1", shell=True)
		return ret_val # Execute & return exit_code
	except:
		return 1  # Return general error code 1

###############################
# Pre-install
###############################

def check_env():
	os_compat_msg = "Please only run this script on the Arch Linux installer environment.\n\nhttps://www.archlinux.org/download/"
	if (name == "posix"):
		hostname = io.read_ln("/etc/hostname")
		if (hostname != "archiso"):
			print(os_compat_msg)
			exit(3) # 3 = Not running in ArchISO environment
	else:
		print(os_compat_msg)
		input()
		exit(2) # 2 = Non-POSIX systems are incompatible

def check_privs():
	user = popen("whoami").read().rstrip("\n")
	if (user != "root"):
		write("Please run this file as root to continue.", 2)
		exit(4) # 4 = Privilege requirements unsatisfied

###############################
# Functions
###############################

# Custom installer color definitions
def load_colors():
	call("echo -en '\\e]P00C0C0C'", shell=True) # Black
	call("echo -en '\\e]P1AF1923'", shell=True) # Red
	call("echo -en '\\e]P269A62A'", shell=True) # Green
	call("echo -en '\\e]P3E68523'", shell=True) # Yellow
	call("echo -en '\\e]P42935B1'", shell=True) # Blue
	call("echo -en '\\e]P57C1FA1'", shell=True) # Magenta
	call("echo -en '\\e]P62397F5'", shell=True) # Cyan
	call("echo -en '\\e]P79E9E9E'", shell=True) # White
	clear_screen() # Clear screen to avoid coloring artifacts

def update_boot_mode():
	ret_val = log_exec("ls /sys/firmware/efi/efivars")
	if (ret_val == 0):
		boot_mode = "UEFI"

def check_connectivity():
	write_msg("Checking network connectivity...", 1)
	ret_val = log_exec("ping -c 1 1.1.1.1") # "archlinux.org"
	write_status(ret_val)
	if (ret_val != 0):
		write("ERROR: ", 2)
		write_ln("No network connectivity. Check your connection and try again.")
		exit(5) # 5 = Network connectivity error

# Pacman functions

# Refresh local package cache
def refresh_pkg_dbs(force_refresh=False):
	write_msg("Refreshing pacman package databases, please wait...", 1)
	cmd = "pacman -Sy"
	if (force_refresh):
		cmd += "y"
	ret_val = log_exec(cmd)
	write_status(ret_val)
	if (ret_val != 0):
		write("ERROR: ", 2)
		write_ln("Database refreshing failed. Check /tmp/setup.log for details")
		exit_code = 6
		if (force_refresh):
			exit_code += 1
		exit(exit_code)  # 6 = Couldn't synchronize databases, 7 = Force-refresh failed

# Install package from the Arch Linux repositories (core, extra, community)
def install_pkg(pkg_name):
	ret_val = log_exec("pacman -S --noconfirm --noprogressbar --needed " + pkg_name)
	return ret_val

# Load kb map using 'loadkeys'
def load_kbmap():
	write_msg("Loading keymap '" + keymap + "'...", 1)
	ret_val = log_exec("loadkeys " + keymap)
	write_status(ret_val)
	if (ret_val != 0):
		write("ERROR: ", 2)
		write_ln("Keymap loading failed. Most likely cause: the specified keymap was not found.")
		exit(8) # 6 = Keymap couldn't be loaded!

# NTP time synchronization
def enable_ntp():
	write_msg("Enabling NTP time synchronization...", 1)
	ret_val = log_exec("timedatectl set-ntp true")
	write_status(ret_val, 0, 4)

# Disk partitioning

def write_par_tool_entry(key="F", par_tool="cfdisk", fg_color=3):
	write("   Enter '")
	write(key.upper(), fg_color)
	write("' to partition using ")
	write_ln(par_tool, fg_color)

def partition(tool_to_use=""):
	shell_exec("echo && lsblk && echo")
	if (tool_to_use != ""):
		write_msg("Device to partition (eg. '")
	else:
		write_msg("Partitioning command line (eg. '")
		write("fdisk ", 4)
	write("/dev/sda", 7)
	write("') ")
	write(">> ", 7)
	in_cmd = input()
	if (tool_to_use != ""):
		shell_exec(tool_to_use + " " + in_cmd)
	else:
		shell_exec(in_cmd)

def sel_par_tool(hide_guide=False):
	if (not hide_guide):
		write_ln()
		write_par_tool_entry("g", "cgdisk (recommended for UEFI)", 3)
		write_par_tool_entry("f", "cfdisk (recommended for BIOS/CSM)", 4)
		write_par_tool_entry("o", "something else", 7)
		write_ln()
	
	# ">> Selection (C/F/G/O) >> "
	write_msg("Selection (")
	write("G", 3)
	write("/")
	write("F", 4)
	write("/")
	write("O", 7)
	write(") ")
	write(">> ", 7)

	sel = input().upper()
	if (sel != ""):
		if (sel == "C"):
			shell_exec("cfdisk")
		elif (sel == "F"):
			partition("fdisk")
		elif (sel == "G"):
			partition("cgdisk")
		elif (sel == "H"):
			partition("gdisk")
		elif (sel == "O"):
			partition()
		else:
			sel_par_tool(True)
		partition_menu()

def partition_menu():
	print_header("Disk Partitioning")
	write("   Tip: ", 3)
	write("If don't need to partition (anymore), just press ")
	write_ln("ENTER", 3)
	sel_par_tool()

# Partition mounting
def mount_par(blk_dev, mount_point="/"):
	log_exec("mount " + blk_dev + " /mnt" + mount_point)


###############################
# Actual script
###############################

# Run env sanity checks
check_env()

# Check privileges
check_privs()

# Load color scheme
load_colors()

write_msg("Arch ")
write("Linux ", 7)
update_boot_mode()
write(boot_mode, 3) # 2,3,4,8
write(" live environment was detected. Press ENTER to continue...") # ", continuing..." w/ write_ln()
input()

write_msg("Loaded customized color scheme", 2)

# Check internet
check_connectivity()

# Refresh package databases
refresh_pkg_dbs()

# Load keymap
load_kbmap()

# NTP time synchronization
if (ntp_enabled):
	enable_ntp()

write_msg("Entering disk partition menu...", 2)
sleep(0.25)
partition_menu()

# repo - Switch before install & pacman -Syy
# base_pkgs - "pacstrap /mnt base python " + base_pkgs
