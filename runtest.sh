# Export env variables
set -o allexport
source .env
set +o allexport

# include the python path
current_dir=$(pwd)
export PYTHONPATH="$PYTHONPATH:${current_dir}/src"

# run tests
python -m unittest -v