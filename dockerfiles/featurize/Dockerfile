#TEMP# Just til we get base_disco working correctly:
FROM mltsp/base

#TEMP# Just temporarily til I rebuild the base image, which includes these:
RUN pip3 install future cython

ENTRYPOINT ["python3", "/home/mltsp/run_script_in_container.py", "--featurize"]
