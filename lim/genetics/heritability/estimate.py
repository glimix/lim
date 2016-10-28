from __future__ import division
import logging
from numpy import ascontiguousarray

import numpy as np

from ...inference import BernoulliEP
from ...inference import BinomialEP
from ...inference import PoissonEP
from ...tool.normalize import stdnorm
from ...tool.kinship import gower_normalization

from limix_math.linalg import qs_decomposition_from_K
from limix_math.linalg import qs_decomposition

def bernoulli_estimate(outcomes, G=None, K=None, covariate=None):
    """Estimate the narrow-sense heritability for Bernoulli traits.

    The user must specifiy only one of the parameters G and K for defining the
    genetic background.

    Let :math:`N` be the sample size, :math:`S` the number of covariates, and
    :math:`P_b` the number of genetic markers used for Kinship estimation.

    :param numpy.ndarray outcomes: Phenotype. The domain has be the
                non-negative integers. Dimension (:math:`N\\times 0`).
    :param numpy.ndarray G: Genetic markers matrix used internally for kinship
                    estimation. Dimension (:math:`N\\times P_b`).
    :param numpy.ndarray K: Kinship matrix. Dimension (:math:`N\\times N`).
    :param tuple QS: Economic eigen decomposition of the Kinship matrix.
    :param numpy.ndarray covariate: Covariates. Default is an offset.
                                  Dimension (:math:`N\\times S`).
    :param object oucome_type: Either :class:`limix_qep.Bernoulli` (default)
                               or a :class:`limix_qep.Binomial` instance.
    :param float prevalence: Population rate of cases for dichotomous
                             phenotypes. Typically useful for case-control
                             studies.
    :return: a tuple containing the estimated heritability and additional
             information, respectively.
    """
    logger = logging.getLogger(__name__)
    logger.info('Heritability estimation for Bernoulli traits has started.')
    outcomes = ascontiguousarray(outcomes, dtype=float)

    if K is not None:
        logger.debug('Covariace matrix normalization.')
        gower_normalization(K, K)

    if G is not None:
        logger.debug('Genetic markers normalization.')
        stdnorm(G, G)
        G = G - np.mean(G, 0)
        s = np.std(G, 0)
        ok = s > 0.
        G[:,ok] /= s[ok]
        G /= np.sqrt(G.shape[1])

    if G is None and K is None:
        raise Exception('G, K, and QS cannot be all None.')

    if G:
        (Q, S) = qs_decomposition(G)
    else:
        (Q, S) = qs_decomposition_from_K(K)

    Q0 = Q[0]
    Q1 = Q[1]
    S0 = S[0]
    S0 /= np.mean(S0)

    info['Q0'] = Q0
    info['Q1'] = Q1
    info['S0'] = S0

    if covariate is None:
        logger.debug('Inserting offset covariate.')
        covariate = np.ones((y.shape[0], 1))

    info['covariate'] = covariate

    logger.debug('Constructing EP.')
    ep = BernoulliEP(outcomes, covariate, Q0, Q1, S0)

    logger.debug('EP optimization.')
    ep.optimize()

    h2 = ep.heritability
    logger.info('Found heritability before correction: %.5f.', h2)

    info['ep'] = ep

    return (h2, info)

def binomial_estimate(nsuccesses, ntrials, G=None, K=None, covariate=None):
    """Estimate the so-called narrow-sense heritability.

    It supports Bernoulli and Binomial phenotypes (see `outcome_type`).
    The user must specifiy only one of the parameters G, K, and QS for
    defining the genetic background.

    Let :math:`N` be the sample size, :math:`S` the number of covariates, and
    :math:`P_b` the number of genetic markers used for Kinship estimation.

    :param numpy.ndarray y: Phenotype. The domain has be the non-negative
                          integers. Dimension (:math:`N\\times 0`).
    :param numpy.ndarray G: Genetic markers matrix used internally for kinship
                    estimation. Dimension (:math:`N\\times P_b`).
    :param numpy.ndarray K: Kinship matrix. Dimension (:math:`N\\times N`).
    :param tuple QS: Economic eigen decomposition of the Kinship matrix.
    :param numpy.ndarray covariate: Covariates. Default is an offset.
                                  Dimension (:math:`N\\times S`).
    :param object oucome_type: Either :class:`limix_qep.Bernoulli` (default)
                               or a :class:`limix_qep.Binomial` instance.
    :param float prevalence: Population rate of cases for dichotomous
                             phenotypes. Typically useful for case-control
                             studies.
    :return: a tuple containing the estimated heritability and additional
             information, respectively.
    """
    logger = logging.getLogger(__name__)
    logger.info('Heritability estimation has started.')
    nsuccesses = asarray(nsuccesses, dtype=float)
    ntrials = asarray(ntrials, dtype=float)

    info = dict()

    if K is not None:
        logger.debug('Covariace matrix normalization.')
        K = gower_normalization(K)
        info['K'] = K

    if G is not None:
        logger.debug('Genetic markers normalization.')
        G = G - np.mean(G, 0)
        s = np.std(G, 0)
        ok = s > 0.
        G[:,ok] /= s[ok]
        G /= np.sqrt(G.shape[1])
        info['G'] = G

    if G is None and K is None:
        raise Exception('G, K, and QS cannot be all None.')

    if G:
        (Q, S) = qs_decomposition(G)
    else:
        (Q, S) = qs_decomposition_from_K(K)

    Q0 = Q[0]
    Q1 = Q[1]
    S0 = S[0]
    S0 /= np.mean(S0)

    info['Q0'] = Q0
    info['Q1'] = Q1
    info['S0'] = S0

    if covariate is None:
        logger.debug('Inserting offset covariate.')
        covariate = np.ones((y.shape[0], 1))

    info['covariate'] = covariate

    logger.debug('Constructing EP.')
    ep = BinomialEP(nsuccesses, ntrials, covariate, Q0, Q1, S0)

    logger.debug('EP optimization.')
    ep.optimize()

    h2 = ep.heritability
    logger.info('Found heritability before correction: %.5f.', h2)

    info['ep'] = ep

    return (h2, info)

def poisson_estimate(nsuccesses, G=None, K=None, covariate=None):
    """Estimate the so-called narrow-sense heritability.

    It supports Bernoulli and Poisson phenotypes (see `outcome_type`).
    The user must specifiy only one of the parameters G, K, and QS for
    defining the genetic background.

    Let :math:`N` be the sample size, :math:`S` the number of covariates, and
    :math:`P_b` the number of genetic markers used for Kinship estimation.

    :param numpy.ndarray y: Phenotype. The domain has be the non-negative
                          integers. Dimension (:math:`N\\times 0`).
    :param numpy.ndarray G: Genetic markers matrix used internally for kinship
                    estimation. Dimension (:math:`N\\times P_b`).
    :param numpy.ndarray K: Kinship matrix. Dimension (:math:`N\\times N`).
    :param tuple QS: Economic eigen decomposition of the Kinship matrix.
    :param numpy.ndarray covariate: Covariates. Default is an offset.
                                  Dimension (:math:`N\\times S`).
    :param object oucome_type: Either :class:`limix_qep.Bernoulli` (default)
                               or a :class:`limix_qep.Binomial` instance.
    :param float prevalence: Population rate of cases for dichotomous
                             phenotypes. Typically useful for case-control
                             studies.
    :return: a tuple containing the estimated heritability and additional
             information, respectively.
    """
    logger = logging.getLogger(__name__)
    logger.info('Heritability estimation has started.')
    nsuccesses = asarray(nsuccesses, dtype=float)

    info = dict()

    if K is not None:
        logger.debug('Covariace matrix normalization.')
        K = gower_normalization(K)
        info['K'] = K

    if G is not None:
        logger.debug('Genetic markers normalization.')
        G = G - np.mean(G, 0)
        s = np.std(G, 0)
        ok = s > 0.
        G[:,ok] /= s[ok]
        G /= np.sqrt(G.shape[1])
        info['G'] = G

    if G is None and K is None:
        raise Exception('G, K, and QS cannot be all None.')

    if G:
        (Q, S) = qs_decomposition(G)
    else:
        (Q, S) = qs_decomposition_from_K(K)

    Q0 = Q[0]
    Q1 = Q[1]
    S0 = S[0]
    S0 /= np.mean(S0)

    info['Q0'] = Q0
    info['Q1'] = Q1
    info['S0'] = S0

    if covariate is None:
        logger.debug('Inserting offset covariate.')
        covariate = np.ones((y.shape[0], 1))

    info['covariate'] = covariate

    logger.debug('Constructing EP.')
    ep = PoissonEP(nsuccesses, covariate, Q0, Q1, S0)

    logger.debug('EP optimization.')
    ep.optimize()

    h2 = ep.heritability
    logger.info('Found heritability before correction: %.5f.', h2)

    info['ep'] = ep

    return (h2, info)
