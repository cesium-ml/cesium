#TEMP# FROM mltsp/base_disco # not working, temporarily using base:
FROM mltsp/base

#TEMP# Just temporarily til I rebuild the base image, which includes these:
RUN pip3 install future cython

ENTRYPOINT ["python3", "/home/mltsp/run_script_in_container.py", "--extract_custom_feats"]
