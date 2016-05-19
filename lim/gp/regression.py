from __future__ import division

from numpy import log
from numpy import pi
from numpy.linalg import solve
from numpy.linalg import slogdet

from ..func import merge_variables
from ..func.optimize.brent import maximize as maximize_scalar
from ..func.optimize.tnc import maximize as maximize_array

from ..random import GPSampler

class RegGP(object):
    def __init__(self, y, mean, cov):
        self._y = y
        self._cov = cov
        self._mean = mean

    def lml(self):
        y = self._y
        mean = self._mean
        cov = self._cov
        Kiym = self._Kim()

        ym = y - mean.data('learn').value()

        (s, logdet) = slogdet(cov.data('learn').value())
        assert s == 1.

        n = len(y)
        return - (logdet + ym.dot(Kiym) + n * log(2*pi)) / 2

    def lml_gradient(self):
        grad_cov = self._lml_gradient_cov()
        grad_mean = self._lml_gradient_mean()
        return grad_cov + grad_mean

    def _lml_gradient_mean(self):
        mean = self._mean

        vars_ = mean.variables().select(fixed=False)

        Kiym = self._Kim()

        g = []
        for i in range(len(vars_)):
            dm = mean.data('learn').gradient()[i]
            g.append(dm.dot(Kiym))
        return g

    def _lml_gradient_cov(self):
        cov = self._cov

        vars_ = cov.variables().select(fixed=False)
        K = cov.data('learn').value()
        Kiym = self._Kim()

        g = []
        for i in range(len(vars_)):
            dK = self._cov.data('learn').gradient()[i]
            g.append(- solve(K, dK).diagonal().sum()
                     + Kiym.dot(dK.dot(Kiym)))
        return [gi / 2 for gi in g]

    def _Kim(self):
        m = self._mean.data('learn').value()
        K = self._cov.data('learn').value()
        return solve(K, self._y - m)

    def variables(self):
        v0 = self._mean.variables().select(fixed=False)
        v1 = self._cov.variables().select(fixed=False)
        return merge_variables(dict(mean=v0, cov=v1))

    def learn(self):
        self.value = lambda: self.lml()
        self.gradient = lambda: self.lml_gradient()

        if len(self.variables()) == 0:
            return
        elif len(self.variables()) == 1:
            maximize_scalar(self)
        else:
            maximize_array(self)

    def predict(self):
        y = self._y
        mean = self._mean
        cov = self._cov

        m_p = mean.data('predict').value()
        _Kim = self._Kim()
        K_pp = cov.data('predict').value()

        cov.set_data(cov.data('learn').raw[0], cov.data('predict').raw[0],
                     purpose='learn_predict')
        K_lp = cov.data('learn_predict').value()

        est_mean = m_p + K_lp.T.dot(_Kim)

        cov.unset_data(purpose='learn_predict')

        return est_mean
