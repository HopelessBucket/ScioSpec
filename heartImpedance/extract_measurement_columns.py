import matlab.engine
import pandas as pd
import numpy as np

# MATLAB starten
eng = matlab.engine.start_matlab()

# Messung ausführen
eng.eval("Measurement_Script_new", nargout=0)

# Konvertieren der Tabelle in ein Format, das leicht zu übertragen ist
eng.eval("measurement_struct = table2struct(measurement);", nargout=0)
eng.eval("field_names = fieldnames(measurement_struct);", nargout=0)
eng.eval("num_rows = length(measurement_struct);", nargout=0)

# Anzahl der Zeilen und Feldnamen abrufen
num_rows = int(eng.workspace["num_rows"])
field_names = eng.workspace["field_names"]

# Ein Dictionary für die Daten erstellen
data_dict = {field: [] for field in field_names}

# Daten aus jeder Zeile und jedem Feld extrahieren
for i in range(num_rows):
    for field in field_names:
        # Den Wert für diese Zeile und dieses Feld abrufen
        cmd = f"value = measurement_struct({i + 1}).{field};"
        eng.eval(cmd, nargout=0)

        # Den Wert aus dem MATLAB-Workspace holen
        value = eng.workspace["value"]

        # MATLAB-Arrays in Python-Listen umwandeln
        if isinstance(value, matlab.double) or isinstance(value, list):
            if hasattr(value, 'size') and len(value.size) > 0 and value.size[0] == 1 and value.size[1] == 1:
                value = float(value)

        data_dict[field].append(value)

# In DataFrame umwandeln
df = pd.DataFrame(data_dict)

# Tabelle anzeigen
print("\n--- Measurement Table ---")
print(df.to_string(index=False))

# 🔽 Jetzt: gezielt extrahieren & anzeigen
print("\n--- Startzeiten ---")
print(df["Starttime"].to_list())

print("\n--- Frequenzen (Hz) ---")
print(df["Frequency"].to_list())

print("\n--- Impedanzwerte (Ohm) ---")
print(df["Impedance"].to_list())

# MATLAB-Engine beenden
eng.quit()