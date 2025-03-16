# Interdisciplinary-Research-Computing-Group-6

# Investigating factors that influence Mpox infections and predicting future outbreaks. 

## Reasearch question

What factors have a strong correlation with an increase in Mpox cases?

## Backgorund

**Mpox** is a disease cause by the monkeypox virus (MPVX).1 Mpox presents with an extensive rash, fever, cough, asthenia, and lymphadenopathy. I

-There is an ongoing struggle with the increase of Mpox cases and there is a severe lack of awareness of this outbreak, 
-This is why we chose to look into what factors contribute to the increase in cases and also visualising the data to further increase awareness. 
-Additionally, we also would like to predict future Mpox cases for African countries using machine learning, to establish if it will be a serious ongoing issue and potentially indicate if more preventative measures should be taken.  

## Data Sources:
Mpox Cases Data:
    Weekly Mpox case counts for African countries, up to 19th January 2025.
Socioeconomic Data:
    CSV file containing data on GDP per capita and access to sanitation facilities for African countries.

## Methods 
**Data Preprocessing:**
Cleaning and filtering the data .
Merging case data with socio-economic datasets for comprehensive analysis.
**Outbreak Detection:**
Outbreaks are identified based on four consecutive weeks of no increase in cases.
**Model Fitting:**
Data is fitted to Logistic, Gompertz, Weibull, and Gamma models for trend analysis.
Machine learning (Random Forest) is applied to predict potential future outbreaks.
Random forest also ranks external factors based of their importance in influencing outbreak occurrences. 

## Results

![GDP per capita graph](images\GDP_graph.png)
