FROM mltsp/base_disco

#ENTRYPOINT ["/sbin/my_init", "--"]
#CMD ["python", "/home/mltsp/mltsp/run_script_in_container.py", "--featurize"]

ENTRYPOINT /sbin/my_init -- /bin/bash -c 'python "$0" "$1"' /home/mltsp/mltsp/run_script_in_container.py --featurize
#ENTRYPOINT ["/sbin/my_init", "--", "ls", "/home/mltsp/mltsp"]


