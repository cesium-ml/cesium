"""
   v0.1 A module which can be imported and used to break existing code
        using kill signal SIGUSR1.

   See:
        http://stackoverflow.com/questions/132058/getting-stack-trace-fom-a-running-python-application

   Use: (in code to be debugged):

from signal_break import *
listen()

   Use: (manually triggering a break using Python):

os.kill(pid, signal.SIGUSR1)

"""


import code, traceback, signal

def debug(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging."""
    d={'_frame':frame}         # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    i = code.InteractiveConsole(d)
    message  = "Signal recieved : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)

def listen():
    signal.signal(signal.SIGUSR1, debug)  # Register handler
