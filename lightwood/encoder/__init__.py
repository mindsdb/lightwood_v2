# Encoders which should always work
from lightwood.encoder.base import BaseEncoder
from lightwood.encoder.datetime.datetime import DatetimeEncoder
from lightwood.encoder.image.img_2_vec import Img2VecEncoder
from lightwood.encoder.numeric.numeric import NumericEncoder
from lightwood.encoder.numeric.ts_numeric import TsNumericEncoder
from lightwood.encoder.text.short import ShortTextEncoder
from lightwood.encoder.text.vocab import VocabularyEncoder
from lightwood.encoder.text.rnn import RnnEncoder as TextRnnEncoder
from lightwood.encoder.categorical.onehot import OneHotEncoder
from lightwood.encoder.categorical.autoencoder import CategoricalAutoEncoder
from lightwood.encoder.time_series.rnn import TimeSeriesEncoder as TsRnnEncoder
from lightwood.encoder.time_series.plain import TimeSeriesPlainEncoder
from lightwood.encoder.categorical.multihot import MultiHotEncoder
from lightwood.encoder.text.pretrained import PretrainedLangEncoder
from lightwood.helpers.log import log

# Encoders that depend on optiona dependencies
try:
    from lightwood.encoder.audio.amplitude_ts import AmplitudeTsEncoder
except Exception:
    AmplitudeTsEncoder = None
    log.info('Unable to import AmplitudeTsEncoder, if you wish to encode audio data please install pydub and initialize lightwood again')


__all__ = ['BaseEncoder', 'DatetimeEncoder', 'Img2VecEncoder', 'NumericEncoder', 'TsNumericEncoder', 'ShortTextEncoder', 'VocabularyEncoder', 'TextRnnEncoder', 'OneHotEncoder', 'CategoricalAutoEncoder', 'TsRnnEncoder', 'TimeSeriesPlainEncoder', 'MultiHotEncoder', 'PretrainedLangEncoder', 'AmplitudeTsEncoder']