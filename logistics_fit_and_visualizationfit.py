"""
This script processes mpox outbreak data from an Excel file ("weekly AFR cases by country as of 19 January 2025(in).xlsx")
located in the same repository. It performs the following tasks:
  
1. Data Loading and Preprocessing:
   - Reads the Excel file using a relative path.
   - Converts Excel date serial numbers to datetime objects.
   - Filters and sorts the data by country and week_end_date.
   - Ensures an "iso3" column is present (adding a default value if missing).

2. Outbreak Detection and Logistic Model Fitting:
   - For each country, the script adds one week of zero data at the beginning to establish a baseline.
   - It traverses the data to detect outbreaks; an outbreak is considered ended if there are four consecutive weeks with no increase
     in cases or if the last data row is reached.
   - For each detected outbreak, the script augments the outbreak data (prepending zeros, and if ended, appending plateau values)
     and fits a logistic growth model using non-linear least squares. It computes the fitted parameters (K, r, t0) and a goodness_of_fit 
     metric (the correlation coefficient between observed and fitted values).

3. Output:
   - The logistic fitting parameters and outbreak details are saved to a CSV file.
   - An interactive plot is generated that displays each country’s overall cumulative case curve and the logistic model fits 
     for each outbreak. You can use the checkboxes to toggle each country's curves.
     
To view the interactive chart with zooming and panning functionality in Spyder, run the following command in console:
    %matplotlib qt
Then run this script. This will open the figure in a separate interactive window where you can zoom and pan.
"""

import pandas as pd
import numpy as np
import scipy.optimize as opt
import warnings
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
import math

# Use relative path because the Excel file and this script are in the same repository.
file_path = "./weekly AFR cases by country as of 19 January 2025(in).cvs"
df = pd.read_excel(file_path)

# Convert Excel serial date numbers to datetime (using Excel's origin and days unit)
df['week_end_date'] = pd.to_datetime(df['week_end_date'], origin='1899-12-30', unit='D')
df = df.sort_values(by=['country', 'week_end_date'])

if 'iso3' not in df.columns:
    df['iso3'] = 'Unknown'

all_countries = sorted(df['country'].unique())

def logistic_model(t, K, r, t0):
    return K / (1 + np.exp(-r * (t - t0)))

def fit_one_logistic(t, y, p0, bounds):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            popt, _ = opt.curve_fit(logistic_model, t, y, p0=p0, bounds=bounds, maxfev=10000)
        fitted_vals = logistic_model(t, *popt)
        if np.all(np.isfinite(fitted_vals)):
            goodness_of_fit = np.corrcoef(y, fitted_vals)[0, 1]
        else:
            goodness_of_fit = np.nan
        return popt, goodness_of_fit
    except:
        return None, None

def fit_outbreak(outbreak_idx, outbreak_start, outbreak_end,
                 outbreak_cases, outbreak_dates,
                 pre_existing_cases, reason, latest_date, iso3_code):
    orig_duration = len(outbreak_cases)
    orig_outbreak_cases = np.array(outbreak_cases) - pre_existing_cases
    total_increment = outbreak_cases[-1] - outbreak_cases[0]
    
    outbreak_cases_aug = orig_outbreak_cases.copy()
    is_ongoing = (outbreak_end == latest_date)
    if is_ongoing:
        outbreak_cases_aug = np.concatenate(([0]*5, outbreak_cases_aug))
        pre_dates = [outbreak_dates[0] - pd.Timedelta(weeks=j+1) for j in range(5)][::-1]
        outbreak_dates_aug = pre_dates + outbreak_dates
        offset = 5
    else:
        outbreak_cases_aug = np.concatenate(([0, 0, 0], outbreak_cases_aug, [outbreak_cases_aug[-1]]*3))
        pre_dates = [outbreak_dates[0] - pd.Timedelta(weeks=j+1) for j in range(3)][::-1]
        post_dates = [outbreak_dates[-1] + pd.Timedelta(weeks=j+1) for j in range(3)]
        outbreak_dates_aug = pre_dates + outbreak_dates + post_dates
        offset = 3

    t_aug = np.arange(len(outbreak_cases_aug))
    y_aug = outbreak_cases_aug
    
    K_guess = max(y_aug)*1.2 if max(y_aug)>0 else 1.0
    p0 = [K_guess, 0.1, len(t_aug)/2]
    bounds = ([0, 0, 0], [np.inf, 10, len(t_aug)*2])
    popt, goodness_of_fit = fit_one_logistic(t_aug, y_aug, p0, bounds)
    
    if popt is not None:
        vis_duration = orig_duration + 2
        t_vis = np.arange(vis_duration)
        t_vis_shifted = t_vis + offset
        fit_vis = logistic_model(t_vis_shifted, *popt) + pre_existing_cases
    else:
        t_vis, fit_vis = None, None

    return {
        "outbreak_idx": outbreak_idx,
        "start_date": outbreak_start,
        "end_date": outbreak_end,
        "duration_weeks": orig_duration,
        "termination_reason": reason,
        "total_increment": total_increment,
        "orig_dates": outbreak_dates,
        "orig_cases": outbreak_cases,
        "iso3": iso3_code,
        "logistic_fit": {
            "popt": popt,
            "goodness_of_fit": goodness_of_fit,
            "t_vis": t_vis,
            "fit_vis": fit_vis
        }
    }

def detect_outbreaks_and_fit(country_data, country_name):
    results = []
    iso3_code = country_data['iso3'].iloc[0]
    
    first_date = country_data['week_end_date'].iloc[0] - pd.Timedelta(weeks=1)
    first_cases = 0
    extra_row = pd.DataFrame({
        'week_end_date': [first_date],
        'total_confirmed_cases': [first_cases],
        'country': [country_name],
        'iso3': [iso3_code]
    })
    country_data = pd.concat([extra_row, country_data]).reset_index(drop=True)
    
    overall_dates = list(country_data['week_end_date'])
    overall_cases = list(country_data['total_confirmed_cases'])
    
    outbreak_start = None
    pre_existing_cases = 0
    outbreak_cases = []
    outbreak_dates = []
    same_count = 0
    outbreak_idx = 0
    latest_date = country_data['week_end_date'].max()
    
    for i in range(len(country_data)):
        current_cases = country_data.iloc[i]['total_confirmed_cases']
        date = country_data.iloc[i]['week_end_date']
        if i < len(country_data) - 1:
            next_cases = country_data.iloc[i+1]['total_confirmed_cases']
            if current_cases < next_cases:
                if outbreak_start is None:
                    outbreak_start = date
                    pre_existing_cases = current_cases
                    outbreak_cases = []
                    outbreak_dates = []
                outbreak_cases.append(current_cases)
                outbreak_dates.append(date)
                same_count = 0
            else:
                same_count += 1
                if outbreak_start is not None:
                    outbreak_cases.append(current_cases)
                    outbreak_dates.append(date)
                    if same_count >= 4:
                        outbreak_end = date
                        reason = "4 consecutive weeks no increase"
                        outbreak_idx += 1
                        results.append(
                            fit_outbreak(outbreak_idx, outbreak_start, outbreak_end,
                                         outbreak_cases, outbreak_dates,
                                         pre_existing_cases, reason, latest_date, iso3_code)
                        )
                        outbreak_start = None
                        outbreak_cases = []
                        outbreak_dates = []
                        same_count = 0
        else:
            if outbreak_start is not None:
                outbreak_cases.append(current_cases)
                outbreak_dates.append(date)
                outbreak_end = date
                reason = "reached last data"
                outbreak_idx += 1
                results.append(
                    fit_outbreak(outbreak_idx, outbreak_start, outbreak_end,
                                 outbreak_cases, outbreak_dates,
                                 pre_existing_cases, reason, latest_date, iso3_code)
                )
                outbreak_start = None
                outbreak_cases = []
                outbreak_dates = []
                same_count = 0

    return overall_dates, overall_cases, results

all_results = {}
overall_curves = {}
for country in all_countries:
    df_country = df[df['country'] == country].copy().sort_values(by='week_end_date')
    if df_country.empty:
        continue
    overall_dates, overall_cases, outbreaks_results = detect_outbreaks_and_fit(df_country, country)
    all_results[country] = outbreaks_results
    overall_curves[country] = (overall_dates, overall_cases)

param_list = []
for country, outbreak_list in all_results.items():
    for outbreak in outbreak_list:
        fit_info = outbreak["logistic_fit"]
        popt = fit_info["popt"]
        if popt is not None:
            entry = {
                "country": country,
                "country_code": outbreak["iso3"],
                "outbreak_idx": outbreak["outbreak_idx"],
                "start_date": outbreak["start_date"],
                "end_date": outbreak["end_date"],
                "termination_reason": outbreak["termination_reason"],
                "total_increment": outbreak["total_increment"],
                "duration_weeks": outbreak["duration_weeks"],
                "model": "Logistic",
                "goodness_of_fit": fit_info["goodness_of_fit"],
                "K": popt[0],
                "r": popt[1],
                "t0": popt[2]
            }
            param_list.append(entry)

df_params = pd.DataFrame(param_list)
output_path = "./logistic_fitted_parameters_all_countries.csv"
df_params.to_csv(output_path, index=False)
print(f"Logistic fitting parameters have been saved to {output_path}")

# To view the interactive chart with full interactivity (zoom, pan, etc.) in Spyder,
# run "%matplotlib qt" in the IPython console before running this script.
# This script below will generate a single interactive figure where you can toggle each country's curves.

import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons

fig, ax = plt.subplots(figsize=(12,8))
lines_dict = {}

for country, (dates, cases) in overall_curves.items():
    line_overall, = ax.plot(dates, cases, '-', label=f"{country} overall")
    country_color = line_overall.get_color()
    lines_dict[country] = [line_overall]
    
    for outbreak in all_results[country]:
        fit_info = outbreak["logistic_fit"]
        if fit_info["popt"] is None:
            continue
        t_vis = fit_info["t_vis"]
        fit_vis = fit_info["fit_vis"]
        vis_dates = [outbreak["start_date"] + pd.Timedelta(weeks=int(j)) for j in t_vis]
        line_fit, = ax.plot(vis_dates, fit_vis, '--', color=country_color,
                            label=f"{country} outbreak {outbreak['outbreak_idx']}")
        lines_dict[country].append(line_fit)

ax.set_xlabel("Date")
ax.set_ylabel("Cumulative Cases")
ax.set_title("Overall Cumulative Cases & Logistic Outbreak Fits (All Countries)")
ax.legend(loc="upper left", fontsize=8)
plt.tight_layout()

rax = plt.axes([0.01, 0.4, 0.15, 0.4])
labels = list(lines_dict.keys())
visibility = [True] * len(labels)
check = CheckButtons(rax, labels, visibility)

def toggle_visibility(label):
    for l in lines_dict[label]:
        l.set_visible(not l.get_visible())
    plt.draw()

check.on_clicked(toggle_visibility)
plt.show()
