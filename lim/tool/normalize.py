from __future__ import division

from numpy import ascontiguousarray
from numpy import atleast_2d
from numpy import errstate
from numpy import isnan
from numpy import copyto

def stdnorm(X, axis=None, out=None):
    X = ascontiguousarray(X)
    if out is None:
        out = X.copy()

    m = out.mean(axis)
    s = out.std(axis)
    ok = s > 0

    out -= m

    if out.ndim == 1:
        if s > 0:
            out /= s
    else:
        out[..., ok] /= s[ok]

    return out
