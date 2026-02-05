import matplotlib.pyplot as plt
import json
import numpy as np
import pickle

class PlotEngine:
    def __init__(self, style_config=None):
        self.style = style_config # Default style
    

    def _apply_layout(self, ax, json_config):
        """Uniwersalna metoda aplikująca tytuły, labele, grid z JSONa"""

        config = json.loads(json_config)

        if "title" in config: ax.set_title(config["title"])
        if "xlabel" in config: ax.set_xlabel(config["xlabel"])
        if "ylabel" in config: ax.set_ylabel(config["ylabel"])
        if "ylim" in config and len(config["ylim"]) > 0: ax.set_ylim(config["ylim"])
        if "xlim" in config and len(config["xlim"]) > 0: ax.set_xlim(config["xlim"])
        if "grid" in config: ax.grid(config["grid"])
        # ... itd.

    def _clean_config(self, raw_config):
        """Zamienia puste stringi i zera z LabVIEW na Pythonowe None"""
        clean = {}
        for key, value in raw_config.items():
            if value == "" or value == 0 or value == []:
                clean[key] = None
            else:
                clean[key] = value
        return clean

    def plot_line(self, x_data, y_data, json_config, save_path):

        fig, ax = plt.subplots()
        ax.plot(x_data, y_data)
        self._apply_layout(ax, json_config)
        fig.savefig(save_path)
        plt.close(fig)
        return "Success"
    
    def plot_colormap(self, data_2d, x_vec, y_vec, json_config, save_path):
        """
        Generuje mapę kolorów z uwzględnieniem wektorów osi X i Y.
        """
        try:
            config = json.loads(json_config)
        except (ValueError, TypeError):
            config = {}

        fig, ax = plt.subplots()
        matrix = np.array(data_2d)
        
        # 1. Obliczanie 'extent' (zakresu osi) na podstawie wektorów X i Y
        # extent = [x_min, x_max, y_min, y_max]
        # Używamy tego tylko, jeśli wektory zostały podane i mają sensowną długość
        plot_extent = None
        
        # Domyślnie imshow rysuje macierz od góry (origin='upper').
        # Dla wykresów fizycznych (np. częstotliwość na Y rośnie w górę) zazwyczaj chcemy 'lower'.
        origin_mode = 'lower' 

        if (x_vec is not None and len(x_vec) > 1) and (y_vec is not None and len(y_vec) > 1):
            # Zakładamy, że wektory są posortowane rosnąco.
            # Jeśli LabVIEW przesyła cały wektor czasu i częstotliwości:
            x_min, x_max = x_vec[0], x_vec[-1]
            y_min, y_max = y_vec[0], y_vec[-1]
            plot_extent = [x_min, x_max, y_min, y_max]
        else:
            # Jeśli nie podano osi, rysujemy na indeksach, ale zmieniamy origin na upper,
            # żeby [0,0] było w lewym górnym rogu (jak w macierzy)
            origin_mode = 'upper'

        cmap_name = config.get("cmap", "viridis")
        if not cmap_name: cmap_name = "viridis"

        # 2. Rysowanie z parametrem extent
        im = ax.imshow(
            matrix, 
            cmap=cmap_name, 
            aspect='auto', 
            interpolation='nearest',
            extent=plot_extent,
            origin=origin_mode
        )

        if config.get("show_colorbar", True):
            # Opcjonalnie: label paska kolorów
            cbar_label = config.get("zlabel", "") 
            fig.colorbar(im, ax=ax, label=cbar_label)

        self._apply_layout(ax, json_config)
        
        fig.savefig(save_path)
        plt.close(fig)
        return "Success"
    

    def save_state(self, filepath, data, config, plot_type):
        """Metoda do zapisu edytowalnego pliku (punkt 4 twoich wymagań)"""
        payload = {
            "type": plot_type,
            "data": data,
            "config": config
        }
        with open(filepath, 'wb') as f:
            pickle.dump(payload, f)

# --- WRAPPERS FOR LABVIEW ---

def call_plot_line(engine, x_array, y_array, json_config, path):
    # Wrapper for calling PlotEngine.plot_line()
    return engine.plot_line(x_array, y_array, json_config, path)

def call_plot_colormap(engine, data_2d, x_vec, y_vec, json_config, path):
    # LabVIEW Inputs:
    # 1. Engine Obj
    # 2. 2D Array DBL (Data)
    # 3. 1D Array DBL (X Axis)
    # 4. 1D Array DBL (Y Axis)
    # 5. String (JSON)
    # 6. Path
    
    # Konwersja None (jeśli LabVIEW prześle pustą tablicę, Python może widzieć pustą listę lub None)
    # Zabezpieczenie:
    if len(x_vec) == 0: x_vec = None
    if len(y_vec) == 0: y_vec = None

    return engine.plot_colormap(data_2d, x_vec, y_vec, json_config, path)
