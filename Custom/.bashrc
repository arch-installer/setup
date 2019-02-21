#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# >> Entries added by ArchInstaller.py >>

# Setup terminal prompt
PS1='[\u@\h \W]\$ '

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

# Load aliases from .bashrc.aliases
[[ -e ~/.bashrc.aliases ]] && source ~/.bashrc.aliases

# Load extra bash completions if present
[[ -r /usr/share/bash-completion/bash_completion ]] && . /usr/share/bash-completion/bash_completion

# Include a local user binary path
export PATH=$PATH:~/.local/bin

# Misc config
export HISTCONTROL=ignoredups # No duplicate command history entries
shopt -s histappend           # Append rather than overwrite history file
shopt -s xpg_echo             # Make echo expand backslash-escape sequences
shopt -s progcomp_alias       # Try alias expanding for completions
shopt -s autocd               # Automatically cd into typed directories
complete -cf sudo             # Sudo completions

# << End of entries added by ArchInstaller.py <<
