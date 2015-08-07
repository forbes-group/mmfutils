# This is the script used on drone.io to provide a testing
# environment.  We use miniconda to quickly install scipy and ipython.
wget -q https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O Miniconda-latest.sh
bash Miniconda-latest.sh -b -p ./miniconda
export PATH="./miniconda/bin:$PATH"
conda install -yq scipy ipython pyzmq numexpr
conda install -yqc https://conda.binstar.org/mforbes pyfftw
pip install -f https://bitbucket.org/mforbes/mypi/ persist
pip install -r requirements.txt.
python setup.py test
