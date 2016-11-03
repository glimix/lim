from __future__ import absolute_import
from __future__ import unicode_literals

from cachetools import LRUCache
from operator import attrgetter
from cachetools import cachedmethod
from cachetools.keys import hashkey

from .qtl import QTLScan
from ...inference import BinomialEP


class BinomialQTLScan(QTLScan):
    def __init__(self, nsuccesses, ntrials, covariates, X, Q0, Q1, S0):
        super(BinomialQTLScan, self).__init__(X)
        self._cache_compute_null_model = LRUCache(maxsize=1)
        self._cache_compute_alt_models = LRUCache(maxsize=1)
        self._nsuccesses = nsuccesses
        self._ntrials = ntrials
        self._covariates = covariates
        self._Q0 = Q0
        self._Q1 = Q1
        self._S0 = S0

        self._fixed_ep = None

    @cachedmethod(
        attrgetter('_cache_compute_null_model'),
        key=lambda self, progress: hashkey(self))
    def _compute_null_model(self, progress):
        nsuccesses = self._nsuccesses
        ntrials = self._ntrials
        Q0, Q1 = self._Q0, self._Q1
        S0 = self._S0
        covariates = self._covariates

        ep = BinomialEP(nsuccesses, ntrials, covariates, Q0=Q0, Q1=Q1, S0=S0)
        ep.optimize(progress=progress)
        self._null_lml = ep.lml()
        self._fixed_ep = ep.fixed_ep()

    @cachedmethod(
        attrgetter('_cache_compute_alt_models'),
        key=lambda self, progress: hashkey(self))
    def _compute_alt_models(self, progress):
        fep = self._fixed_ep
        covariates = self._covariates
        X = self._X
        self._alt_lmls, self._effect_sizes = fep.compute(covariates, X)

    def null_model(self):
        return None

    def alt_models(self):
        s = "Phenotype:\n"
        s += "    y_i = o_i + b_j x_{i,j} + u_i + e_i\n\n"
        s += "Definitions:\n"
        s += "    b_j    : effect-size of the j-th candidate marker\n"
        s += "    x_{i,j}: j-th candidate marker of the i-th sample\n"
        return s
