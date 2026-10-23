"""
Draws the age-value curve for midfielders (Figure 2 of the thesis) from the
Table 7 coefficients, and prints the turning point and the annual rate of
change at the mean age and one year either side.

Output: outputs/age_value_curve.png, outputs/age_value_curve.svg
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend to guarantee saving works
import matplotlib.pyplot as plt

plt.rcParams['svg.hashsalt'] = 'age-value-curve'  # stable element ids across runs
from pathlib import Path


def plot_age_value_curve():
    """
    Generates the value-by-age curve chart for midfielders.
    """

    # ============================================================
    # 1. Model parameters (fixed)
    # ============================================================
    const = 14.3035
    beta_age_c = -0.0875      # centered age
    beta_age_sq = -0.0127      # centered age squared
    beta_xgpm = 0.0406         # net xG balance (xG+/-)
    beta_mnmp = 0.0066         # minutes per match

    # Means (midfielders), to hold the other variables constant
    mean_age = 28.41           # years
    mean_xgpm = 0.86
    mean_mnmp = 58.23

    # ============================================================
    # 2. Building the curve (actual age from 18 to 36 years)
    # ============================================================
    age_years = np.arange(18, 36.1, 0.1)
    age_centered = age_years - mean_age

    # Log-linear model: lnV = const + beta_age_c*age_centered + beta_age_sq*(age_centered**2)
    #                    + beta_xgpm*mean_xgpm + beta_mnmp*mean_mnmp
    lnV = (const +
           beta_age_c * age_centered +
           beta_age_sq * (age_centered**2) +
           beta_xgpm * mean_xgpm +
           beta_mnmp * mean_mnmp)

    # Normalization: value index peaking at 100
    value_index = np.exp(lnV - np.max(lnV)) * 100

    # ============================================================
    # 3. Computing the peak (turning point)
    # ============================================================
    age_c_star = -beta_age_c / (2 * beta_age_sq)
    age_star = mean_age + age_c_star

    # Value at the peak (to plot the point)
    lnV_star = (const +
                beta_age_c * age_c_star +
                beta_age_sq * (age_c_star**2) +
                beta_xgpm * mean_xgpm +
                beta_mnmp * mean_mnmp)
    value_index_star = np.exp(lnV_star - np.max(lnV)) * 100

    # ============================================================
    # 4. Marginal percentage change
    # ============================================================
    # Semi-elasticity: d ln(V)/d age_c = beta_age_c + 2*beta_age_sq*age_centered
    # Exact percentage change: pct = exp(beta_age_c + 2*beta_age_sq*age_centered) - 1

    age_c_points = [-1, 0, 1]  # one year below, at the mean, one year above
    pcts = []
    age_points = []
    value_points = []

    for ac in age_c_points:
        # Percentage change
        pct = np.exp(beta_age_c + 2 * beta_age_sq * ac) - 1
        pcts.append(pct)

        # Corresponding actual age
        age_pt = mean_age + ac
        age_points.append(age_pt)

        # Value at this point (to position the annotation)
        lnv_pt = (const +
                  beta_age_c * ac +
                  beta_age_sq * (ac**2) +
                  beta_xgpm * mean_xgpm +
                  beta_mnmp * mean_mnmp)
        value_index_pt = np.exp(lnv_pt - np.max(lnV)) * 100
        value_points.append(value_index_pt)

    # ============================================================
    # 5. Chart configuration (clean, academic style)
    # ============================================================
    _, ax = plt.subplots(figsize=(8, 5))

    # Main curve
    # Labels are in English; the Portuguese original as printed in the
    # thesis is thesis/figure2_original.png/svg.
    ax.plot(age_years, value_index, linewidth=2, color='#2E86AB', label='Value curve')

    # Peak: point and annotation (above and to the left)
    ax.plot(age_star, value_index_star, 'ro', markersize=10, zorder=5)
    ax.annotate(f'Peak ≈ {age_star:.2f} years',
                xy=(age_star, value_index_star),
                xytext=(age_star - 2, value_index_star + 5),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                fontsize=11,
                color='red',
                weight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='red', alpha=0.8))

    # Annotations for the marginal percentage changes
    labels_pct = [
        f'-1 year: {pcts[0]*100:.2f}%/year',
        f'at the mean: {pcts[1]*100:.2f}%/year',
        f'+1 year: {pcts[2]*100:.2f}%/year'
    ]

    # Annotation positioning (adjusted to avoid overlap)
    # -1 year: right and above (original position)
    # at the mean: right and below
    # +1 year: right and further below
    offsets_x = [1.5, 2.0, 2.5]  # horizontal offset
    offsets_y = [8, -10, -18]     # vertical offset

    for i, (age_pt, value_pt, _, label) in enumerate(zip(age_points, value_points, pcts, labels_pct)):
        ax.annotate(label,
                   xy=(age_pt, value_pt),
                   xytext=(age_pt + offsets_x[i], value_pt + offsets_y[i]),
                   arrowprops=dict(arrowstyle='->', color='gray', lw=1, alpha=0.7),
                   fontsize=10,
                   color='darkslategray',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat', edgecolor='gray', alpha=0.7),
                   ha='center')

    # Chart style
    ax.set_xlabel('Age (years)', fontsize=12)
    ax.set_ylabel('Value index (peak = 100)', fontsize=12)

    # Light grid
    ax.grid(True, linestyle=':', alpha=0.5, linewidth=0.8)

    # Axis limits (with a small margin)
    ax.set_xlim(17.5, 36.5)
    ax.set_ylim(0, 110)

    # Final touches
    plt.tight_layout()

    # ============================================================
    # 6. Save as PNG and SVG
    # ============================================================
    output_dir = Path(__file__).resolve().parents[1] / "outputs"
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'age_value_curve.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'age_value_curve.svg', bbox_inches='tight', metadata={'Date': None})

    print(f"Chart saved to '{output_dir}'")
    print(f"Curve peak: {age_star:.2f} years")
    print("Marginal percentage changes:")
    print(f"  -1 year: {pcts[0]*100:.2f}%/year")
    print(f"  at the mean: {pcts[1]*100:.2f}%/year")
    print(f"  +1 year: {pcts[2]*100:.2f}%/year")

    # Close the figure to free memory
    plt.close()


if __name__ == "__main__":
    plot_age_value_curve()

