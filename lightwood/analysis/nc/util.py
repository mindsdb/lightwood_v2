import numpy as np
from lightwood.api.dtype import dtype


def clean_df(df, target, is_classification, label_encoders):
    """ Returns cleaned DF for nonconformist calibration """
    # @TODO: reevaluate whether this can be streamlined inside custom nonconf
    enc = label_encoders

    y = df.pop(target).values

    if is_classification:
        if enc and isinstance(enc.categories_[0][0], str):
            cats = enc.categories_[0].tolist()
            y = np.array([cats.index(i) for i in y])
        y = y.astype(int)
    else:
        y = y.astype(float)

    return df, y


def set_conf_range(X, icp, target_type, analysis_info, positive_domain=False, std_tol=1, group='__default', significance=None):
    """ Sets confidence level and returns it plus predictions regions
    significance: desired confidence level. can be preset 0 < x <= 0.99
    """
    # numerical
    if target_type in [dtype.integer, dtype.float, dtype.array]:
        # and dtype.NUMERIC in typing_info['data_type_dist'].keys()):

        # ICP gets all possible bounds (shape: (B, 2, 99))
        all_ranges = icp.predict(X.values)

        # iterate over confidence levels until spread >= a multiplier of the dataset stddev
        if significance is not None:
            conf = int(100*(1-significance))
            return significance, all_ranges[:, :, conf]
        else:
            for tol in [std_tol, std_tol + 1, std_tol + 2]:
                for significance in range(99):
                    ranges = all_ranges[:, :, significance]
                    spread = np.mean(ranges[:, 1] - ranges[:, 0])
                    tolerance = analysis_info['train_std_dev'][group] * tol

                    if spread <= tolerance:
                        confidence = (99 - significance) / 100
                        if positive_domain:
                            ranges[ranges < 0] = 0
                        return confidence, ranges
            else:
                ranges = all_ranges[:, :, 0]
                if positive_domain:
                    ranges[ranges < 0] = 0
                return 0.9901, ranges

    # categorical
    elif target_type == dtype.categorical:  # or  #
        # (target_type == dtype.array and  # time-series w/ cat target
        #  dtype.categorical in typing_info['data_type_dist'].keys())) and \
        #   lmd['stats_v2'][target]['typing']['data_subtype'] != dtype.tags:  # no tag support yet

        pvals = icp.predict(X.values)
        conf = np.subtract(1, pvals.min(axis=1)).mean()
        return conf, pvals

    # default
    return 0.005, np.zeros((X.shape[0], 2))


def get_numerical_conf_range(all_confs, train_std_dev=None, positive_domain=False, std_tol=1, group='__default', error_rate=None):
    """ Gets prediction bounds for numerical targets, based on ICP estimation and width tolerance
        error_rate: pre-determined error rate for the ICP, used in anomaly detection tasks to adjust the
        threshold sensitivity.

        :param all_confs: numpy.ndarray, all possible bounds depending on confidence level
        :param train_std_dev: dict
        :param positive_domain: bool
        :param std_tol: int
        :param group: str
        :param error_rate: float (1 >= , can be specified to bypass automatic confidence/bound detection
    """
    if not isinstance(error_rate, float):
        error_rate = None

    if error_rate is None:
        significances = []
        conf_ranges = []
        std_dev = train_std_dev[group]
        tolerance = std_dev * std_tol

        for sample_idx in range(all_confs.shape[0]):
            sample = all_confs[sample_idx, :, :]
            for idx in range(sample.shape[1]):
                significance = (99 - idx) / 100
                diff = sample[1, idx] - sample[0, idx]
                if diff <= tolerance:
                    conf_range = list(sample[:, idx])
                    significances.append(significance)
                    conf_ranges.append(conf_range)
                    break
            else:
                significances.append(0.9991)  # default: confident that value falls inside big bounds
                bounds = sample[:, 0]
                sigma = (bounds[1] - bounds[0]) / 4
                conf_range = [bounds[0] - sigma, bounds[1] + sigma]
                conf_ranges.append(conf_range)

        conf_ranges = np.array(conf_ranges)
    else:
        # fixed error rate
        error_rate = max(0.01, min(1.0, error_rate))
        conf = 1 - error_rate
        conf_idx = int(100*error_rate) - 1
        conf_ranges = all_confs[:, :, conf_idx]
        significances = [conf for _ in range(conf_ranges.shape[0])]

    if positive_domain:
        conf_ranges[conf_ranges < 0] = 0
    return significances, conf_ranges


def get_categorical_conf(all_confs, conf_candidates):
    """ Gets ICP confidence estimation for categorical targets.
    Prediction set is always unitary and includes only the predicted label.
    :param all_confs: numpy.ndarray, all possible label sets depending on confidence level
    :param conf_candidates: list, includes preset confidence levels to check
    """
    significances = []
    for sample_idx in range(all_confs.shape[0]):
        sample = all_confs[sample_idx, :, :]
        for idx in range(sample.shape[1]):
            conf = (99 - conf_candidates[idx]) / 100
            if np.sum(sample[:, idx]) == 1:
                significances.append(conf)
                break
        else:
            significances.append(0.005)  # default: not confident label is the predicted one
    return significances


def get_anomalies(bounds, observed_series, cooldown=1):
    anomalies = []
    counter = 0

    # cast to float (safe, we only call this method if series is numerical)
    try:
        observed_series = [float(value) for value in observed_series]
    except (TypeError, ValueError):
        return [None for _ in observed_series]

    for (l, u), t in zip(bounds, observed_series):
        if t is not None:
            anomaly = not (l <= t <= u)

            if anomaly and (counter == 0 or counter >= cooldown):
                anomalies.append(anomaly)  # new anomaly event triggers, reset counter
                counter = 1
            elif anomaly and counter < cooldown:
                anomalies.append(False)  # overwrite as not anomalous if still in cooldown
                counter += 1
            else:
                anomalies.append(anomaly)
                counter = 0
        else:
            anomalies.append(None)
            counter += 1

    return anomalies
