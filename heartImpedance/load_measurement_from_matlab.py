import matlab.engine
import pandas as pd
import numpy as np

def load_measurement(eng):
    # Messung ausführen
    eng.eval("Measurement_Script_new", nargout=0)

    # Einzelne Workspace-Variablen holen
    res_time_offset = np.array(eng.workspace['resTimeOffset']).flatten()
    res_impedance   = np.array(eng.workspace['resImpedColumn']).flatten()
    res_frequencies = np.array(eng.workspace['resFrequencies']).flatten()

    # Impedanz (real + imag) in komplexe Zahlen umwandeln
    res_impedance_complex = np.array([complex(z) for z in res_impedance])

    # DataFrame erzeugen
    df = pd.DataFrame({
        'Offset': res_time_offset,
        'Frequency': res_frequencies,
        'Impedance': res_impedance_complex
    })

    return df