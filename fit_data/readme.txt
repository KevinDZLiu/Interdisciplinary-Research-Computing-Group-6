These three folders, each corresponding to a different outbreak termination criterion based on consecutive weeks without case increases:

58cases-based-on-consecutive5
Outbreaks end after 5 consecutive weeks of no increase in cumulative cases (resulting in 58 total outbreaks).

65cases-based-on-consecutive4
Outbreaks end after 4 consecutive weeks of no increase in cumulative cases (resulting in 65 total outbreaks).

76cases-based-on-consecutive3
Outbreaks end after 3 consecutive weeks of no increase in cumulative cases (resulting in 76 total outbreaks).

Within each of these folders, you will find four CSV files corresponding to the four models used to fit the outbreak data:

logistic_fitted_parameters_all_countries.csv
gompertz_fitted_parameters_all_countries.csv
weibull_fitted_parameters_all_countries.csv
gamma_fitted_parameters_all_countries.csv
Each CSV file contains one row per detected outbreak. The columns typically include:

country: Name of the country.
country_code: ISO3 code of the country.
outbreak_idx: A numeric identifier for each outbreak.
start_date, end_date: The date range for the outbreak.
termination_reason: Why the outbreak ended (e.g., “consecutive weeks no increase”).
total_increment: Total increase in cumulative cases during the outbreak.
duration_weeks: The number of weeks from outbreak start to outbreak end (before data augmentation).
model: Which model was used (Logistic, Gompertz, Weibull, or Gamma).
goodness_of_fit: The correlation coefficient (R) between the model fit and the actual outbreak data.  !!this might be useful when feeding the program, maybe the better it fit, the higher weight this data has.!!
Fitted parameters (e.g., K, r, t0 for Logistic; K, alpha, beta for Gompertz; etc.).
Use these CSV files to compare how each model fits the outbreak data under different definitions of the “no-increase” termination condition.

These datasets can be used as inputs (features) for training machine learning algorithms, such as Random Forest.
By training and evaluating a Random Forest model using each dataset, we can ultimately identify which outbreak termination criterion and model fitting approach provides the best predictive performance.