import os
import torch
from torch.nn.functional import softmax
from lightwood.analysis.nc.base import RegressorAdapter, ClassifierAdapter

from lightwood.model import BaseModel
# from mindsdb_native.config import CONFIG


def t_softmax(x, t=1.0, axis=1):
    """ Softmax with temperature scaling """
    # @TODO: move this, not a wrapper
    return softmax(torch.Tensor(x) / t, dim=axis).numpy()


def clear_icp_state(icp):
    """ We clear last_x and last_y to minimize file size. Model has to be cleared because it cannot be pickled. """
    icp.model.model = None
    icp.model.last_x = None
    icp.model.last_y = None
    if icp.normalizer is not None:
        icp.normalizer.model = None


def restore_icp_state(col, hmd, session):
    icps = hmd['icp'][col]
    try:
        predictor = session.transaction.model_backend.predictor
    except AttributeError:
        model_path = os.path.join(CONFIG.MINDSDB_STORAGE_PATH, hmd['name'], 'lightwood_data')
        predictor = Predictor(load_from_path=model_path)

    for group, icp in icps.items():
        if group not in ['__mdb_groups', '__mdb_group_keys']:
            icp.nc_function.model.model = predictor

    # restore model in normalizer
    for group, icp in icps.items():
        if group not in ['__mdb_groups', '__mdb_group_keys']:
            if icp.nc_function.normalizer is not None:
                icp.nc_function.normalizer.model = icp.nc_function.model.model


class ConformalRegressorAdapter(RegressorAdapter):
    def __init__(self, model, fit_params=None):
        super(ConformalRegressorAdapter, self).__init__(model, fit_params)
        self.prediction_cache = None

    def fit(self, x=None, y=None):
        """ At this point, the predictor has already been trained, but this
        has to be called to setup some things in the nonconformist backend """
        pass

    def predict(self, x=None):
        """ Same as in .fit()
        :return: np.array (n_test, n_classes) with class probability estimates """
        return self.prediction_cache


class ConformalClassifierAdapter(ClassifierAdapter):
    def __init__(self, model, fit_params=None):
        super(ConformalClassifierAdapter, self).__init__(model, fit_params)
        self.prediction_cache = None

    def fit(self, x=None, y=None):
        """ At this point, the predictor has already been trained, but this
        has to be called to setup some things in the nonconformist backend """
        pass

    def predict(self, x=None):
        """ Same as in .fit()
        :return: np.array (n_test, n_classes) with class probability estimates """
        return t_softmax(self.prediction_cache, t=0.5)
