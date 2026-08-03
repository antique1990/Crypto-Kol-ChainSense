"""Central registry for all capability evaluators.

Each capability is a function:
    def my_cap(feat: pd.Series | pd.DataFrame) -> CapabilityOutput

Where feat can be either a single row (single bar eval) or a full DataFrame (vectorized).

Return signature:
    {
      'triggered': bool or Series[bool],
      'score': float or Series[float],  # -1..+1, sign = direction, magnitude = strength
      'bias': 'long'|'short'|'neutral'|None,  # canonical for single-bar mode
      'confidence': 0..1,
      'notes': str,
    }

Vectorized (pandas Series) returns are used for historical backtest panels.
"""
from dataclasses import dataclass
from typing import Callable, Any
import pandas as pd
import numpy as np

CAP_REGISTRY: dict[str, dict] = {}

@dataclass
class CapabilityOutput:
    triggered: Any  # bool or Series
    score: Any       # float or Series, signed
    bias: Any = None
    confidence: Any = 0.5
    notes: str = ''

def register(cap_id: str, cap_type: str, bias_default: str = 'neutral',
             confidence_base: float = 0.5, impl: str = 'rule', na_reason: str = ''):
    """Decorator to register a capability function.

    cap_id: canonical id e.g. 'cap_044_regime_trending_up'
    cap_type: one of pattern_setup|indicator_rule|structural_bias|macro_correlation|
              derivatives_signal|onchain_signal|cycle_time|event_reaction|risk_rule|regime_classifier
    impl: rule|approx|mock (approx = rule approximation of LLM-type cap)
    na_reason: if cap requires data we don't have, stub returns all-False and na_reason is set
    """
    def wrap(fn):
        CAP_REGISTRY[cap_id] = {
            'id': cap_id,
            'type': cap_type,
            'bias_default': bias_default,
            'confidence_base': confidence_base,
            'impl': impl,
            'na_reason': na_reason,
            'fn': fn,
            'name': fn.__name__,
        }
        return fn
    return wrap

def evaluate_all(feat):
    """Run every registered capability on `feat` (Series or DataFrame).
    Returns: DataFrame with columns = cap_ids, values = signed scores.
    Also returns bool trigger panel.
    """
    scores = {}
    triggered = {}
    for cid, meta in CAP_REGISTRY.items():
        try:
            out = meta['fn'](feat)
            if isinstance(out, CapabilityOutput):
                scores[cid] = out.score
                triggered[cid] = out.triggered
            elif isinstance(out, dict):
                scores[cid] = out.get('score', 0)
                triggered[cid] = out.get('triggered', False)
            else:
                # function returned a raw series/scalar
                scores[cid] = out
                triggered[cid] = out != 0 if hasattr(out, '__iter__') else bool(out)
        except Exception as e:
            # Fail soft: this capability is N/A
            scores[cid] = np.nan if isinstance(feat, pd.DataFrame) else 0
            triggered[cid] = False
    return scores, triggered
