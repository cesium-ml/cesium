# http://zguide.zeromq.org/page:all#The-Dynamic-Discovery-Problem

import zmq

IN = 'ipc:///tmp/message_flow_in'
OUT = 'ipc:///tmp/message_flow_out'

context = zmq.Context()

feed_in = context.socket(zmq.XSUB)
feed_in.bind(IN)

feed_out = context.socket(zmq.XPUB)
feed_out.bind(OUT)

print('[message_proxy] Forwarding messages between {} and {}'.format(IN, OUT))
zmq.proxy(feed_in, feed_out)
