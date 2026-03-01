export PS1="\h:\W \u\$ "
export PS1="\[\e]0;\w\a\]${debian_chroot:+($debian_chroot)}\[\033[01;34m\]\w\[\033[00m\]\$ "

#source $(conda info --base)/etc/profile.d/conda.sh
eval "$(micromamba shell hook --shell=bash)"

# Assume that this is set by running anaconda-project run shell
CONDA_ENV="${CONDA_PREFIX}"
micromamba deactivate
micromamba activate "${CONDA_ENV}"
#alias ap="anaconda-project"
#alias apr="anaconda-project run"

. .init-file.bash
