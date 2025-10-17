"""
Credit Heuristic Model Micro v2
Sistema de evaluación crediticia para micro-tiendas basado en heurísticas deterministas.
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

# Configuración por defecto del modelo Micro v2
DEFAULTS_MICRO_V2 = {
    "max_cap": 50_000,
    "distance_threshold": 10.0,
    "distance_alert": 50.0,
    "weights": {
        "know_buyer": 0.18,
        "buy_freq": 0.20,
        "avg_purchase": 0.18,
        "psych_organized": 0.12,
        "psych_plan": 0.12,
        "distance": 0.12,
        "address_verified": 0.08
    },
    "category_thresholds": [0.85, 0.70, 0.50, 0.30],
    "avg_purchase_min": 1_000,
    "avg_purchase_max": 200_000,
    # Parámetros de afinamiento
    "segment_multiplier": 1.0,    # permite alcanzar hasta max_cap (soft)
    "prudence_factor": 0.65,      # más alto que antes para outputs razonables pero no muy pequeños
    "income_prudence": 0.18,      # pequeño % del proxy de ingreso a considerar
    "base_days_income": 7.0,      # días considerados para proxy de ingreso
    "min_cupo_allowed": 800.0,    # cupo mínimo para categoría C+
}

def _norm_0_1(value: float, minv: float, maxv: float) -> float:
    """
    Normaliza un valor entre 0 y 1 con clipping seguro.
    
    Args:
        value: Valor a normalizar
        minv: Valor mínimo
        maxv: Valor máximo
        
    Returns:
        Valor normalizado entre 0 y 1
    """
    if np.isnan(value):
        return 0.0
    v = (value - minv) / (maxv - minv) if maxv > minv else 0.0
    return float(np.clip(v, 0.0, 1.0))

def feature_transform(row: Dict[str, Any], conf: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Transforma un registro de entrada a features normalizados.
    
    Args:
        row: Diccionario con datos del cliente
        conf: Configuración del modelo (opcional)
        
    Returns:
        Diccionario con features normalizados y valores crudos
    """
    if conf is None:
        conf = DEFAULTS_MICRO_V2
    
    # know_buyer: escala 0-5 → 0-1
    f1 = 0.0 if pd.isna(row.get("know_buyer")) else float(row.get("know_buyer")) / 5.0
    
    # buy_freq: escala 0-5 → 0-1
    f2 = 0.0 if pd.isna(row.get("buy_freq")) else float(row.get("buy_freq")) / 5.0
    
    # avg_purchase: log-normalización entre avg_purchase_min y avg_purchase_max
    try:
        avg_val = float(row.get("avg_purchase", conf["avg_purchase_min"]))
        if avg_val <= 0:
            avg_val = conf["avg_purchase_min"]
    except Exception:
        avg_val = conf["avg_purchase_min"]
    
    log_min = math.log(conf["avg_purchase_min"])
    log_max = math.log(conf["avg_purchase_max"])
    f3 = _norm_0_1(math.log(avg_val), log_min, log_max)
    
    # psych_organized: escala 1-5 → 0-1 (se resta 1 y divide por 4)
    f4 = 0.0 if pd.isna(row.get("psych_organized")) else (float(row.get("psych_organized")) - 1) / 4.0
    
    # psych_plan: escala 1-5 → 0-1 (se resta 1 y divide por 4)
    f5 = 0.0 if pd.isna(row.get("psych_plan")) else (float(row.get("psych_plan")) - 1) / 4.0
    
    # distance_km: convierte a feature f_distance en [0,1] con 1.0 como más cercano
    distance = row.get("distance_km", None)
    if distance is None or (isinstance(distance, float) and np.isnan(distance)):
        f6 = 1.0
    else:
        try:
            d = float(distance)
            f6 = float(np.clip(1.0 - (d / conf["distance_threshold"]), 0.0, 1.0))
        except Exception:
            f6 = 1.0
    
    # address_verified: booleano → 1.0/0.0
    addr_ver = row.get("address_verified", 0)
    f7 = 1.0 if bool(addr_ver) else 0.0
    
    return {
        "f_know_buyer": f1,
        "f_buy_freq": f2,
        "f_avg_purchase": f3,
        "f_psych_organized": f4,
        "f_psych_plan": f5,
        "f_distance": f6,
        "f_address_verified": f7,
        "avg_purchase_raw": avg_val,
        "distance_raw": distance
    }

def heuristic_micro_v2(row: Dict[str, Any], conf: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Función principal que calcula el cupo de crédito usando heurística Micro v2.
    
    Args:
        row: Diccionario con datos del cliente
        conf: Configuración del modelo (opcional)
        
    Returns:
        Diccionario con categoría, puntaje, riesgo, cupo estimado y desgloses
    """
    if conf is None:
        conf = DEFAULTS_MICRO_V2
    
    # Transformar features
    feats = feature_transform(row, conf)
    
    # Calcular score como suma ponderada de features
    w = conf["weights"]
    score = (
        w["know_buyer"] * feats["f_know_buyer"] +
        w["buy_freq"] * feats["f_buy_freq"] +
        w["avg_purchase"] * feats["f_avg_purchase"] +
        w["psych_organized"] * feats["f_psych_organized"] +
        w["psych_plan"] * feats["f_psych_plan"] +
        w["distance"] * feats["f_distance"] +
        w["address_verified"] * feats["f_address_verified"]
    )
    
    # Aplicar penalización si distance_raw > distance_alert
    if feats["distance_raw"] is not None and feats["distance_raw"] > conf["distance_alert"]:
        score *= 0.6
    
    # Clipear score entre 0 y 1
    score = float(np.clip(score, 0.0, 1.0))
    
    # Asignar categoría según umbrales
    t = conf["category_thresholds"]
    if score >= t[0]:
        cat = "A"
    elif score >= t[1]:
        cat = "B"
    elif score >= t[2]:
        cat = "C"
    elif score >= t[3]:
        cat = "D"
    else:
        cat = "E"
    
    # Calcular porcentaje de riesgo
    risk_pct = (1.0 - score) * 100.0
    
    # COMPONENTE 1: feature-based proporcional a max_cap
    f_avg = feats["f_avg_purchase"]
    comp_feature = score * f_avg * conf["max_cap"] * conf["segment_multiplier"] * conf["prudence_factor"]
    
    # COMPONENTE 2: income-proxy (avg_purchase_raw * clients_per_day)
    clients_map = {0: 0, 1: 1, 2: 3, 3: 5, 4: 8, 5: 12}
    buy_freq_raw = int(row.get("buy_freq", 0))
    clients_per_day = clients_map.get(buy_freq_raw, 3)
    income_proxy_daily = feats["avg_purchase_raw"] * clients_per_day
    comp_income = score * income_proxy_daily * conf["base_days_income"] * conf["income_prudence"]
    
    # Combinar conservativamente: tomar el promedio de ambos componentes pero asegurar no exceder max_cap
    cupo_raw = 0.5 * (comp_feature + comp_income)
    cupo = float(np.clip(cupo_raw, 0.0, conf["max_cap"]))
    
    # Asegurar un mínimo para categoría C y superior
    if cupo < conf.get("min_cupo_allowed", 0.0) and score >= conf["category_thresholds"][2]:
        cupo = conf["min_cupo_allowed"]
    
    return {
        "category": cat,
        "score_conf": round(score, 4),
        "risk_pct": round(risk_pct, 2),
        "debt_capacity_pct": round(score, 4),
        "cupo_estimated": round(cupo, 2),
        "raw_cupo": round(cupo_raw, 2),
        "comp_feature": round(comp_feature, 2),
        "comp_income": round(comp_income, 2),
        "features": feats,
        "clients_per_day": clients_per_day,
        "income_proxy_daily": round(income_proxy_daily, 2)
    }

def get_default_config() -> Dict[str, Any]:
    """
    Retorna la configuración por defecto del modelo.
    
    Returns:
        Diccionario con configuración por defecto
    """
    return DEFAULTS_MICRO_V2.copy()
