# This script processes mpox outbreak data from an Excel file named
# "weekly AFR cases by country as of 19 January 2025(in).xlsx" located in the repository.
#
# The script performs the following tasks:
# 1. Loads the Excel file using a relative path and converts the Excel date serial numbers to datetime objects.
# 2. Filters the data to include only records from January 1, 2021 onward and sorts the data by country and date.
# 3. Ensures the presence of an "iso3" column; if absent, a default value is added.
# 4. For each country, it detects outbreaks based on the criterion that an outbreak is considered ended
#    if there are four consecutive weeks with no increase in cumulative cases or when the last data row is reached.
# 5. For each detected outbreak, the script augments the outbreak data (by prepending zeros and appending
#    plateau values, depending on whether the outbreak is ongoing or ended) to facilitate model fitting.
# 6. It then fits four different models (Logistic, Gompertz, Weibull, and Gamma) to the augmented data using
#    non-linear least squares, computing fitted parameters and a goodness-of-fit metric (the correlation coefficient).
# 7. Finally, the fitted parameters and outbreak details for each model are saved to four separate CSV files.
import pandas as pd
import numpy as np
import scipy.optimize as opt
import warnings
import math

# Use a relative path since the data and this script are in the same repository
file_path = "./weekly AFR cases by country as of 19 January 2025(in).cvs"
# Read the Excel file
df = pd.read_excel(file_path)

# Convert Excel date serial numbers to datetime format (using origin and unit)
df['week_end_date'] = pd.to_datetime(df['week_end_date'], origin='1899-12-30', unit='D')
# Filter data from January 1, 2021 onwards
df = df[df['week_end_date'] >= '2021-01-01']
# Sort data by country and date
df = df.sort_values(by=['country', 'week_end_date'])
# If the 'iso3' column is missing, add a default value
if 'iso3' not in df.columns:
    df['iso3'] = 'Unknown'

# Get a sorted list of all countries
all_countries = sorted(df['country'].unique())

# ----------------------------- Define Models -----------------------------
def logistic_model(t, K, r, t0):
    """
    Logistic Growth Model:
    f(t) = K / (1 + exp(-r * (t - t0)))
    """
    return K / (1 + np.exp(-r * (t - t0)))

def gompertz_model(t, K, alpha, beta):
    """
    Gompertz Model:
    f(t) = K * exp(-alpha * exp(-beta * t))
    """
    return K * np.exp(-alpha * np.exp(-beta * t))

def weibull_cdf_model(t, K, lam, a):
    """
    Weibull CDF Model (scaled by K):
    f(t) = K * [1 - exp(- (lam * t)^a)]
    """
    return K * (1 - np.exp(- (lam * t)**a))

def gamma_cdf_model(t, K, shape, scale):
    """
    Gamma CDF Model (scaled by K):
    f(t) = K * gammainc(shape, t/scale)
    where gammainc is the regularized lower incomplete gamma function.
    """
    from scipy.special import gammainc
    return K * gammainc(shape, t/scale)

# ----------------------- Generic Model Fitting -----------------------
def fit_model(model_func, t, y, p0, bounds):
    """
    Generic function to fit a model using curve_fit.
    Returns (popt, goodness_of_fit) where goodness_of_fit is the correlation coefficient
    between the observed data y and the fitted values.
    If the fitting fails, returns (None, None).
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            popt, _ = opt.curve_fit(model_func, t, y, p0=p0, bounds=bounds, maxfev=10000)
        fitted_vals = model_func(t, *popt)
        if np.all(np.isfinite(fitted_vals)):
            gof = np.corrcoef(y, fitted_vals)[0, 1]
        else:
            gof = np.nan
        return popt, gof
    except:
        return None, None

# ------------------- Outbreak Detection Function -------------------
def detect_outbreaks(country_data, country_name):
    """
    Detect outbreaks in a single country's data.
    1) Add one week of zero data at the beginning to establish a baseline.
    2) Traverse the data; if there are 4 consecutive weeks with no increase in cases
       or if the last data row is reached, mark the outbreak as ended.
    Returns:
      overall_dates: List of all dates (for overall curve)
      overall_cases: List of overall cumulative cases
      results: A list of outbreak dictionaries containing outbreak details.
    """
    results = []
    iso3_code = country_data['iso3'].iloc[0]
    
    # Add one week of zero data before the first record
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
                        outbreak_idx += 1
                        results.append({
                            "outbreak_idx": outbreak_idx,
                            "start_date": outbreak_start,
                            "end_date": date,
                            "duration_weeks": len(outbreak_cases),
                            "total_increment": outbreak_cases[-1] - outbreak_cases[0],
                            "iso3": iso3_code,
                            "outbreak_cases": outbreak_cases.copy(),
                            "outbreak_dates": outbreak_dates.copy(),
                            "pre_existing_cases": pre_existing_cases,
                            "termination_reason": "4 consecutive weeks no increase",
                            "latest_date": latest_date,
                            "country": country_name
                        })
                        outbreak_start = None
                        outbreak_cases = []
                        outbreak_dates = []
                        same_count = 0
        else:
            if outbreak_start is not None:
                outbreak_cases.append(current_cases)
                outbreak_dates.append(date)
                outbreak_idx += 1
                results.append({
                    "outbreak_idx": outbreak_idx,
                    "start_date": outbreak_start,
                    "end_date": date,
                    "duration_weeks": len(outbreak_cases),
                    "total_increment": outbreak_cases[-1] - outbreak_cases[0],
                    "iso3": iso3_code,
                    "outbreak_cases": outbreak_cases.copy(),
                    "outbreak_dates": outbreak_dates.copy(),
                    "pre_existing_cases": pre_existing_cases,
                    "termination_reason": "reached last data",
                    "latest_date": latest_date,
                    "country": country_name
                })
                outbreak_start = None
                outbreak_cases = []
                outbreak_dates = []
                same_count = 0
    return overall_dates, overall_cases, results

# -------------- Function to Fit Outbreaks for a Given Model --------------
def fit_outbreak_for_model(model_name, model_func, outbreak):
    """
    Fit the specified model (Logistic, Gompertz, Weibull, or Gamma) to the outbreak data.
    The outbreak data is augmented: if the outbreak is ongoing, prepend 5 weeks of zeros;
    if ended, prepend 3 weeks of zeros and append 3 weeks of plateau values.
    Returns a dictionary with outbreak details and fitted model parameters.
    """
    orig_duration = len(outbreak["outbreak_cases"])
    orig_outbreak_cases = np.array(outbreak["outbreak_cases"]) - outbreak["pre_existing_cases"]
    is_ongoing = (outbreak["end_date"] == outbreak["latest_date"])
    
    if is_ongoing:
        outbreak_cases_aug = np.concatenate(([0]*5, orig_outbreak_cases))
        offset = 5
    else:
        outbreak_cases_aug = np.concatenate(([0, 0, 0], orig_outbreak_cases, [orig_outbreak_cases[-1]]*3))
        offset = 3
    
    t_aug = np.arange(len(outbreak_cases_aug))
    y_aug = outbreak_cases_aug
    K_guess = max(y_aug)*1.2 if max(y_aug) > 0 else 1.0
    
    if model_name == "Logistic":
        p0 = [K_guess, 0.1, len(t_aug)/2]
        bounds = ([0, 0, 0], [np.inf, 10, len(t_aug)*2])
    elif model_name == "Gompertz":
        p0 = [K_guess, 1.0, 0.1]
        bounds = ([0, 0, 0], [np.inf, np.inf, np.inf])
    elif model_name == "Weibull":
        p0 = [K_guess, 0.1, 2.0]
        bounds = ([0, 1e-6, 1e-6], [np.inf, np.inf, np.inf])
    elif model_name == "Gamma":
        p0 = [K_guess, 2.0, max(1.0, len(t_aug)/4)]
        bounds = ([0, 1e-6, 1e-6], [np.inf, np.inf, np.inf])
    else:
        return None

    popt, gof = fit_model(model_func, t_aug, y_aug, p0, bounds)
    result = {
        "country": outbreak["country"],
        "country_code": outbreak["iso3"],
        "outbreak_idx": outbreak["outbreak_idx"],
        "start_date": outbreak["start_date"],
        "end_date": outbreak["end_date"],
        "termination_reason": outbreak["termination_reason"],
        "total_increment": outbreak["total_increment"],
        "duration_weeks": outbreak["duration_weeks"],
        "model": model_name,
        "goodness_of_fit": gof
    }
    if popt is not None:
        if model_name == "Logistic":
            result.update({"K": popt[0], "r": popt[1], "t0": popt[2]})
        elif model_name == "Gompertz":
            result.update({"K": popt[0], "alpha": popt[1], "beta": popt[2]})
        elif model_name == "Weibull":
            result.update({"K": popt[0], "lam": popt[1], "a": popt[2]})
        elif model_name == "Gamma":
            result.update({"K": popt[0], "shape": popt[1], "scale": popt[2]})
    return result

# ----------------------- Process All Countries -----------------------
logistic_results = []
gompertz_results = []
weibull_results = []
gamma_results = []

for country in all_countries:
    df_country = df[df['country'] == country].copy().sort_values(by='week_end_date')
    if df_country.empty:
        continue
    overall_dates, overall_cases, outbreaks = detect_outbreaks(df_country, country)
    for outbreak in outbreaks:
        res_logistic = fit_outbreak_for_model("Logistic", logistic_model, outbreak)
        if res_logistic is not None:
            logistic_results.append(res_logistic)
        res_gompertz = fit_outbreak_for_model("Gompertz", gompertz_model, outbreak)
        if res_gompertz is not None:
            gompertz_results.append(res_gompertz)
        res_weibull = fit_outbreak_for_model("Weibull", weibull_cdf_model, outbreak)
        if res_weibull is not None:
            weibull_results.append(res_weibull)
        res_gamma = fit_outbreak_for_model("Gamma", gamma_cdf_model, outbreak)
        if res_gamma is not None:
            gamma_results.append(res_gamma)

# ----------------------- Export Fitting Parameters to CSV Files -----------------------
df_logistic = pd.DataFrame(logistic_results)
df_gompertz = pd.DataFrame(gompertz_results)
df_weibull = pd.DataFrame(weibull_results)
df_gamma = pd.DataFrame(gamma_results)

df_logistic.to_csv("./logistic_fitted_parameters_all_countries.csv", index=False)
df_gompertz.to_csv("./gompertz_fitted_parameters_all_countries.csv", index=False)
df_weibull.to_csv("./weibull_fitted_parameters_all_countries.csv", index=False)
df_gamma.to_csv("./gamma_fitted_parameters_all_countries.csv", index=False)

print("All model fitting parameters have been saved to CSV files.")
