import gatspy


def lomb_scargle_fast_period(t, m, e):
    """Fits a simple sinuosidal model

        y(t) = A sin(2*pi*w*t + phi) + c

    and returns the estimated period 1/w. Much faster than fitting the
    full multi-frequency model used by `features.lomb_scargle`.
    """
    dt = t.max() - t.min()
    opt_args = {"period_range": (2 * dt / len(t), dt), "quiet": True}
    model = gatspy.periodic.LombScargleFast(
        fit_period=True, optimizer_kwds=opt_args, silence_warnings=True
    )
    model.fit(t, m, e)
    return model.best_period
