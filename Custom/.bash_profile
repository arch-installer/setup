#
# ~/.bash_profile
#

# Custom TTY colors
if [[ "$TERM" = "linux" ]]; then
	echo -en '\e]P00C0C0C' # Black
	echo -en '\e]P1AF1923' # Red
	echo -en '\e]P269A62A' # Green
	echo -en '\e]P3E68523' # Yellow
	echo -en '\e]P42935B1' # Blue
	echo -en '\e]P57C1FA1' # Magenta
	echo -en '\e]P62397F5' # Cyan
	echo -en '\e]P79E9E9E' # White
	clear # For avoiding coloring artifacts
fi

# If .bashrc is present, execute it on login
[[ -f ~/.bashrc ]] && . ~/.bashrc