FROM mltsp/base_disco

RUN useradd -ms /bin/bash mltsp
ENV HOME /home/mltsp
WORKDIR /home/mltsp

RUN ssh-keyscan -H localhost > /home/disco/.ssh/known_hosts
RUN ln -s /home/disco/.ssh .

ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
