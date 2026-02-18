import matplotlib.pyplot as plt
import json
import numpy as np
import pickle

class PlotEngine:
    def __init__(self, style_config=None):
        self.style = style_config # Default style

    def _apply_layout(self, ax, fig, config):
        """Universal method applying titles, labels, grid from JSON config dictionary."""
        
        if "title" in config: ax.set_title(config["title"])
        if "xlabel" in config: ax.set_xlabel(config["xlabel"])
        if "ylabel" in config: ax.set_ylabel(config["ylabel"])
        if "ylim" in config and len(config["ylim"]) > 0: ax.set_ylim(config["ylim"])
        if "xlim" in config and len(config["xlim"]) > 0: ax.set_xlim(config["xlim"])
        if "grid" in config: ax.grid(config["grid"])

        if "figsize" in config and config["figsize"]["width"] > 0 and config["figsize"]["height"] > 0:
            fig.set_figheight(config["figsize"]["height"])
            fig.set_figwidth(config["figsize"]["width"])
        
        # Legend handling
        if config.get("show_legend", False):
            ax.legend(loc=config.get("legend_loc", "best"))

    def _get_line_style(self, config, prefix=""):
        """
        Helper to extract line styling arguments from config.
        Filters out empty strings sent by LabVIEW.
        """
        style = {}
        # List of keys we want to support for styling
        keys = ["color", "linestyle", "linewidth", "marker", "alpha"]

        for key in keys:
            full_key = f"{prefix}{key}"
            if full_key in config:
                val = config[full_key]
                # CRITICAL FIX: 
                # Check if value is not None and not an empty string
                # We also explicitly allow 0 for linewidth/alpha, so we check specifically for ""
                if val is not None and val != "":
                    style[key] = val
        return style

    def plot_line(self, x_data, y_data, json_config, save_path):
        """Standard single line plot with enhanced styling."""
        try:
            config = json.loads(json_config)
        except (ValueError, TypeError):
            config = {}

        fig, ax = plt.subplots()
        
        # Get style kwargs
        style_args = self._get_line_style(config)
        
        ax.plot(x_data, y_data, **style_args)
        
        self._apply_layout(ax, fig, config)
        fig.savefig(save_path)
        plt.close(fig)
        return "Success"

    def plot_multi_line(self, x_data, y_data_2d, json_config, save_path):
        """
        Plots multiple lines on one chart.
        x_data: 1D array (shared X axis)
        y_data_2d: 2D array (rows represent individual lines)
        """
        try:
            config = json.loads(json_config)
        except (ValueError, TypeError):
            config = {}

        fig, ax = plt.subplots()
        
        # Labels for legend (optional)
        labels = config.get("labels", [])
        
        # Global line style from config
        base_style = self._get_line_style(config)

        # Iterate over rows in 2D array
        for i, y_row in enumerate(y_data_2d):
            # Determine label for this line
            lbl = labels[i] if i < len(labels) else f"Line {i+1}"
            
            # Plot
            ax.plot(x_data, y_row, label=lbl, **base_style)

        # Force legend display if not explicitly disabled
        if config.get("show_legend", True):
            config["show_legend"] = True
            
        self._apply_layout(ax, fig, config)
        fig.savefig(save_path)
        plt.close(fig)
        return "Success"

    def plot_boxplot_regression(self, data_groups, x_positions, json_config, save_path):
        """
        Boxplot with linear regression overlay.
        data_groups: 2D array (from LabVIEW). Shorter groups must be padded with NaNs.
        x_positions: 1D array of X coordinates for each group/box.
        """
        try:
            config = json.loads(json_config)
        except (ValueError, TypeError):
            config = {}

        fig, ax = plt.subplots()

        # 1. Clean the data (remove NaNs from LabVIEW 2D array padding)
        cleaned_groups = []
        valid_x_positions = []
        
        for i, group in enumerate(data_groups):
            # Filter out NaN values from the current row
            clean_group = [val for val in group if not np.isnan(val)]
            
            # Keep the group only if it has actual data
            if len(clean_group) > 0:
                cleaned_groups.append(clean_group)
                # Keep the corresponding X position
                if x_positions is not None and i < len(x_positions):
                    valid_x_positions.append(x_positions[i])

        # Safety check: exit if no valid data remains after filtering
        if not cleaned_groups:
            plt.close(fig)
            return "Error: No valid data found (all NaNs or empty)"

        # 2. Draw Boxplot
        box_color = config.get("box_color")
        if not box_color: 
            box_color = "black"
        props = dict(color=box_color)
        
        # Use positions only if the arrays match in size
        use_positions = valid_x_positions if (x_positions is not None and len(valid_x_positions) == len(cleaned_groups)) else None

        bp = ax.boxplot(cleaned_groups, 
                        positions=use_positions,
                        boxprops=props,
                        widths=config.get("box_width", 0.5))

        # 3. Linear Regression Calculation
        if use_positions is not None:
            
            # Flatten data for regression (create 1D X and Y arrays for every single point)
            flat_x = []
            flat_y = []
            
            for i, group in enumerate(cleaned_groups):
                pos = use_positions[i]
                flat_x.extend([pos] * len(group))
                flat_y.extend(group)
            
            if len(flat_x) > 1:
                flat_x = np.array(flat_x)
                flat_y = np.array(flat_y)

                # Fit linear model (deg=1)
                slope, intercept = np.polyfit(flat_x, flat_y, 1)
                
                # Calculate R^2
                y_pred = slope * flat_x + intercept
                residuals = flat_y - y_pred
                ss_res = np.sum(residuals**2)
                ss_tot = np.sum((flat_y - np.mean(flat_y))**2)
                
                # Avoid division by zero if all points have the same Y value
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

                # 4. Draw Regression Line
                # Generate line points spanning the exact range of X
                x_range = np.linspace(min(flat_x), max(flat_x), 100)
                y_range = slope * x_range + intercept
                
                # Get regression specific style (prefix 'reg_')
                reg_style = self._get_line_style(config, prefix="reg_")
                if not reg_style:
                    reg_style = {"color": "red", "linestyle": "--", "linewidth": 1.5}
                
                ax.plot(x_range, y_range, **reg_style)

                # 5. Display Stats (Equation and R^2)
                if config.get("show_stats", True):
                    sign = "+" if intercept >= 0 else "-"
                    stats_text = f"y = {slope:.2f}x {sign} {abs(intercept):.2f}\n$R^2$ = {r_squared:.3f}"
                    
                    # Place text on plot (top-left)
                    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                            fontsize=config.get("font_size", 10),
                            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self._apply_layout(ax, fig, config)
        fig.savefig(save_path)
        plt.close(fig)
        return "Success"

    def plot_colormap(self, data_2d, x_vec, y_vec, json_config, save_path):
        """
        Generates a heatmap/colormap using X and Y vectors for axes.
        """
        try:
            config = json.loads(json_config)
        except (ValueError, TypeError):
            config = {}

        fig, ax = plt.subplots()
        matrix = np.array(data_2d)
        
        plot_extent = None
        origin_mode = 'lower' 

        if (x_vec is not None and len(x_vec) > 1) and (y_vec is not None and len(y_vec) > 1):
            x_min, x_max = x_vec[0], x_vec[-1]
            y_min, y_max = y_vec[0], y_vec[-1]
            plot_extent = [x_min, x_max, y_min, y_max]
        else:
            origin_mode = 'upper'

        cmap_name = config.get("cmap", "viridis")

        im = ax.imshow(
            matrix, 
            cmap=cmap_name, 
            aspect='auto', 
            interpolation='nearest',
            extent=plot_extent,
            origin=origin_mode
        )

        if config.get("show_colorbar", True):
            cbar_label = config.get("zlabel", "") 
            fig.colorbar(im, ax=ax, label=cbar_label)

        self._apply_layout(ax, fig, config)
        
        fig.savefig(save_path)
        plt.close(fig)
        return "Success"

# --- WRAPPERS FOR LABVIEW ---

def call_plot_line(engine, x_array, y_array, json_config, path):
    return engine.plot_line(x_array, y_array, json_config, path)

def call_plot_multi_line(engine, x_array, y_data_2d, json_config, path):
    """
    Wrapper for multi-line plot.
    y_data_2d should be passed from LabVIEW as a 2D Array of Doubles.
    """
    return engine.plot_multi_line(x_array, y_data_2d, json_config, path)

def call_plot_boxplot_regression(engine, data_groups, x_positions, json_config, path):
    """
    Wrapper for Boxplot + Regression.
    data_groups: Can be a 2D Array (if groups have equal size) or List of Lists (if uneven).
                 LabVIEW Python Node maps 2D Array -> List of Lists usually.
    x_positions: 1D Array of X coordinates.
    """
    # Safety check for empty inputs
    if len(data_groups) == 0: return "Error: No Data"
    return engine.plot_boxplot_regression(data_groups, x_positions, json_config, path)

def call_plot_colormap(engine, data_2d, x_vec, y_vec, json_config, path):
    # Safety checks for None/Empty arrays from LabVIEW
    if len(x_vec) == 0: x_vec = None
    if len(y_vec) == 0: y_vec = None
    return engine.plot_colormap(data_2d, x_vec, y_vec, json_config, path)