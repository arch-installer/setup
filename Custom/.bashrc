#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# >> Entries added by ArchInstaller.py >>

# Setup terminal prompt
user_col='2' # Username color depending on root access
(( EUID == 0 )) && user_col='1'
PS1='[\[\e[3'$user_col'm\]\u\[\e[m\]@\[\e[36m\]\h\[\e[m\] \[\e[33m\]\W\[\e[m\]]\$ ' # '[\u@\h \W]\$ '
unset user_col

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
shopt -s progcomp_alias       # Try alias expanding for programmable completions
shopt -s autocd               # Automatically cd into typed directories
complete -cf sudo             # Sudo completions

# << End of entries added by ArchInstaller.py <<