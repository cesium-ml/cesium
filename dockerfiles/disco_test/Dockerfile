FROM mltsp/base_disco

RUN useradd -ms /bin/bash mltsp
ENV HOME /home/mltsp/mltsp
WORKDIR /home/mltsp/mltsp

RUN mkdir -p /home/disco/.ssh && rm /home/disco/.ssh/*
RUN ssh-keygen -t dsa -f /home/disco/.ssh/id_dsa
RUN cat /home/disco/.ssh/id_dsa.pub > /home/disco/.ssh/authorized_keys
RUN /usr/sbin/sshd && ssh-keyscan -H localhost > /home/disco/.ssh/known_hosts
RUN chown disco -R /home/disco/.ssh

RUN rm /etc/supervisor/conf.d/*
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
