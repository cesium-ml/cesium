import numpy as np


# TODO is this really a useful feature?
def num_alias(lomb_model):
    """Here we check for "1-day" aliases in ASAS / Deboss sources."""
    alias = [
        {
            "per": 1.0,
            "p_low": 0.92,
            "p_high": 1.08,
            "alpha_1": 8.191855,
            "alpha_2": -7.976243,
        },
        {
            "per": 0.5,
            "p_low": 0.48,
            "p_high": 0.52,
            "alpha_1": 2.438913,
            "alpha_2": 0.9837243,
        },
        {
            "per": 0.3333333333,
            "p_low": 0.325,
            "p_high": 0.342,
            "alpha_1": 2.95749,
            "alpha_2": -4.285432,
        },
        {
            "per": 0.25,
            "p_low": 0.245,
            "p_high": 0.255,
            "alpha_1": 1.347657,
            "alpha_2": 2.326338,
        },
    ]

    count = 0
    for freq_dict in lomb_model["freq_fits"]:
        period = 1.0 / freq_dict["freq"]
        for a in alias:
            cutoff = (
                a["alpha_1"] / np.power(np.abs(period - a["per"]), 0.25) + a["alpha_2"]
            )
            if (
                period >= a["p_low"]
                and period <= a["p_high"]
                and freq_dict["signif"] < cutoff
            ):
                count += 1  # this frequency has a "1 day" alias (or 0.5 or 0.33
                break  # only need to do this once per period, if an alias is found.
    return count
