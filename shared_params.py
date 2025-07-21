import json
from datetime import datetime
import os

PARAMS_FILE = 'analysis_params.json'

def save_analysis_params(volume_period_long, volume_period_short):
    """Salva os parâmetros da análise em arquivo JSON"""
    try:
        params = {
            'volume_period_long': volume_period_long,
            'volume_period_short': volume_period_short,
            'timestamp': datetime.now().isoformat()
        }
        with open(PARAMS_FILE, 'w') as f:
            json.dump(params, f, indent=4)
    except Exception as e:
        print(f"❌ Erro ao salvar parâmetros: {str(e)}")

def load_analysis_params():
    """Carrega os parâmetros da última análise"""
    try:
        if os.path.exists(PARAMS_FILE):
            with open(PARAMS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    
    # Parâmetros padrão se não conseguir carregar
    return {
        'volume_period_long': 60,
        'volume_period_short': 7
    } 