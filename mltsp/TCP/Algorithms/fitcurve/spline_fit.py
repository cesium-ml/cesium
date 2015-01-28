from numpy import *
from scipy import array
from scipy.interpolate import splprep, splev, interp1d 


def append(arr1, arr2):
    arr1_list = []
    arr2_list = []
    gen_arr = array([4,5])
    if not(type(arr1) == type(gen_arr)):
        arr1_list.append(arr1)
        for value in arr2:
            arr2_list.append(value)
    if not(type(arr2) == type(gen_arr)):
        arr2_list.append(arr2)
        for value in arr1:
            arr1_list.append(value)
    if (type(arr1) == type(gen_arr) and (type(arr2) == type(gen_arr))):
        for value in arr1:
            arr1_list.append(value)
        for value in arr2:
            arr2_list.append(value) 
    for value in arr2_list:
        arr1_list.append(value)
    combined_arr = array(arr1_list)
    return combined_arr


# Given input arrays of times, magntidues, and requested_times, this function 
# returns the spline_fitted_magnitudes.
def spline_fitted_magnitudes(times, magnitudes, errors, requested_times, mindiff = None):
    # Spline parameters:
    k=5 # spline order
    nest=-1 # estimate of number of knots needed (-1 = maximal)
    
    fitted_errors = empty(0)
    fitted_magnitudes = empty(0)
    for rtime, window in window_creator(times, requested_times, mindiff = mindiff):
        wtimes = times[window]
        wmagnitudes = magnitudes[window]
        werrors = errors[window]
        
        # spline parameter:
        s=len(wtimes)/100. # smoothness parameter
    
        # Find the knot points.
        tckp, u = splprep([wtimes, wmagnitudes],s=s,k=k,nest=-1)
    
        # Evaluate spline, including interpolated points.
        new_times, new_magnitudes = splev(linspace(0,1,len(wtimes)),tckp)
    
        # Define an interpolating function along the spline fit.
        interpolating_function = interp1d(new_times, new_magnitudes, kind = "linear")
    
        # Interpolate linerarly along the spline at the requested times.
        fitted_magnitude = interpolating_function(rtime)
        fitted_magnitudes = append(fitted_magnitudes, fitted_magnitude)
    
        for m in range(len(wtimes)-1):
            if (rtime > wtimes[m]) and (rtime < wtimes[m+1]):
                error = (werrors[m] + werrors[m+1])*0.5
                fitted_errors = append(fitted_errors, error)
    return fitted_magnitudes, fitted_errors
    
def spline_fitted_magnitudes_brute(times, magnitudes, errors, requested_times):
    # Spline parameters:
    s=len(times)/100. # smoothness parameter
    k=5 # spline order
    nest=-1 # estimate of number of knots needed (-1 = maximal)

    # Find the knot points.
    tckp, u = splprep([times, magnitudes],s=s,k=k,nest=-1)

    # Evaluate spline, including interpolated points.
    new_times, new_magnitudes = splev(linspace(0,1,len(times)),tckp)

    # Define an interpolating function along the spline fit.
    interpolating_function = interp1d(new_times, new_magnitudes, kind = "linear")

    # Interpolate linerarly along the spline at the requested times.
    fitted_magnitudes = interpolating_function(requested_times)

    fitted_errors = array([])
    for n in range(len(requested_times)):
        for m in range(len(times)-1):
            if (requested_times[n] > times[m]) and (requested_times[n] < times[m+1]):
                error = (errors[m] + errors[m+1])*0.5
                fitted_errors = append(fitted_errors, error)
    return fitted_magnitudes, fitted_errors
    
def window_creator(times, requested_times, mindiff = None):
    if not mindiff:
        mindiff = min(abs(diff(requested_times)))
    for rtime in requested_times:
        itime = argmin(abs(times - rtime)) # index of the time that best matches the requested times
        diffs = abs(diff(times)) # spacings between times
        ibad = where(diffs > mindiff)[0] + 1 # indices where two points are too far apart for a good spline fit
        ibad = append(0, ibad) # add the edges
        ibad = append(ibad, times.size - 1)
        ibadl = ibad[ibad < itime] # indices where two points are too far apart and that are *before* the requested time (l="lower")
        ibadu = ibad[ibad > itime] # indices where two points are too far apart and that are *after* the requested time (u="upper")
        assert ibadl.size > 0, "the requested time is right at the edge of available times" 
        assert ibadu.size > 0, "the requested time is right at the edge of available times"
        nearestbadl = ibadl[-1] # closest bad time before the requested time
        nearestbadu = ibadu[0] # closest bad time after the requested time
        assert itime - nearestbadl > 1, "can't be right next to the edge"
        assert nearestbadu - itime > 1, "can't be right next to the edge"
        window = arange(nearestbadl,nearestbadu)
        assert window.size > 5, "window size is too small"
        yield rtime, window
        
def window_tttimes(times, requested_times, ttimes):
    poverlap = zeros(ttimes.size).astype(bool)
    for rtime, window in window_creator(times,requested_times):
        boundaries = (times[window[0]], times[window[-1]])
        overlap = logical_and( ttimes < boundaries[1] , ttimes > boundaries[0])
        poverlap = logical_or(overlap, poverlap)
    wttimes = ttimes[poverlap]
    return wttimes