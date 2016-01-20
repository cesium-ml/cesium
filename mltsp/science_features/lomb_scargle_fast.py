import numpy as np
import gatspy


def lomb_scargle_fast_period(t, m, e):
    """Fits a simple sinuosidal model

        y(t) = A sin(2*pi*w*t) + B cos(2*pi*w*t) + c

    and returns the estimated period 1/w. Much faster than fitting the
    full multi-frequency model used by `science_features.lomb_scargle`.
    """
    opt_args = {'period_range': (2*t.max() / len(t), t.max()), 'quiet': True}
    model = gatspy.periodic.LombScargleFast(fit_period=True, optimizer_kwds=opt_args)
    model.fit(t, m, e)
    return model.best_period
