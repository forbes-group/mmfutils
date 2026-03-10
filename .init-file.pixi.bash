. .init-file.bash

export PS1="\h:\W \u\$ "
export PS1="\[\e]0;\w\a\]${PIXI_PROMPT}${debian_chroot:+($debian_chroot)}\[\033[01;34m\]\w\[\033[00m\]\$ "
