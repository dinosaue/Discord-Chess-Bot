import requests
import datetime
import numpy as np
import pandas as pd

model_params = pd.read_csv("/Users/austinliu/Downloads/Discord-Chess-Bot-master/data/model_params_20210805.csv")

# Convert rating history info from JSON to Dataframe
def process_rating_history(response_json):
    rating_history = dict()
    for x in response_json:
            if x['name'] in ['Bullet','Blitz','Rapid','Classical']:
                tbl = pd.DataFrame(x['points'])
                tbl.columns = ['year','month','day','rating']
                tbl['month'] = tbl['month']+1
                tbl['date'] = pd.to_datetime(tbl.year*10000+tbl.month*100+tbl.day,format='%Y%m%d')
                rating_history[x['name']] = tbl
    return(rating_history)

# Get the values that are inputs to the models
def get_predictor_values(rating_history,target_rating,variant):
    target_rating_history = rating_history[variant]
    t_minus_30 = datetime.datetime.today()-datetime.timedelta(days=30)
    t_minus_90 = datetime.datetime.today()-datetime.timedelta(days=90)
    t_minus_180 = datetime.datetime.today()-datetime.timedelta(days=180)
    target_rating_history_30 = target_rating_history.query('date>=@t_minus_30')
    target_rating_history_90 = target_rating_history.query('date>=@t_minus_90')
    target_rating_history_180 = target_rating_history.query('date>=@t_minus_180')    
    rating_latest = target_rating_history['rating'].values[-1]
    target_rating_gain = target_rating-rating_latest
    predictor_values = dict(Intercept=1,target_rating_gain=target_rating_gain,
        target_rating_gain_squared=target_rating_gain**2,
        rating_latest=rating_latest,
        rating_latest_squared = rating_latest**2,
        bullet = int(variant == 'Bullet'), blitz = int(variant == 'Blitz'),
        rapid = int(variant == 'Rapid'), classical = int(variant == 'Classical'),
        rating_peak_diff = rating_latest-target_rating_history['rating'].max(),
        rating_30_diff = rating_latest-target_rating_history_30['rating'].values[0],
        rating_90_diff = rating_latest-target_rating_history_90['rating'].values[0],
        rating_180_diff = rating_latest-target_rating_history_180['rating'].values[0],
        rating_updates_30 = len(target_rating_history_30['rating']),
        rating_updates_90 = len(target_rating_history_90['rating']),
        rating_stdev_30 = target_rating_history_30['rating'].std() if len(target_rating_history_30) > 1 else 0,
        rating_stdev_90 = target_rating_history_90['rating'].std() if len(target_rating_history_90) > 1 else 0
                                   )
    return(predictor_values)

# Calculate the probability of success given a set of predictor values and a classification model
def get_prob_success(predictor_values,model_params = model_params):
    logit_params = model_params[['var_name','logit']].dropna()
    linear_combo = 0
    for i in range(len(logit_params)):
        var_name = logit_params['var_name'].values[i]
        coef = logit_params['logit'].values[i]
        if ':' in var_name:
            var_names = var_name.split(":")
            value = 1
            for j in var_names:
                value *= predictor_values[j]
        else:
            value = predictor_values[var_name]
        linear_combo += coef*value
    return str(round(100*1/(1+np.exp(-1*(linear_combo)))))+"%"

# Calculate the predicted days until target rating given a set of predictor values and a regression model
def get_predicted_date(predictor_values,model_params = model_params):
    ols_params = model_params[['var_name','ols']].dropna()
    predicted_days = 0
    for i in range(len(ols_params)):
        var_name = ols_params['var_name'].values[i]
        coef = ols_params['ols'].values[i]
        if ':' in var_name:
            var_names = var_name.split(":")
            value = 1
            for j in var_names:
                value *= predictor_values[j]
        else:
            value = predictor_values[var_name]
        predicted_days += coef*value
    if predicted_days < 0: predicted_days = 0
    elif predicted_days > 365*2: predicted_days = 365*2
    predicted_date = (datetime.datetime.today()+datetime.timedelta(days=predicted_days)).strftime(format="%B %d, %Y")
    return(predicted_date)

# Return the predictions based on discord inputs
def score(username,target_rating,variant,model_params = model_params):
    url = f'https://lichess.org/api/user/{username}/rating-history'
    variant = variant.capitalize()
    response = requests.get(url)
    response_json = response.json()
    if not str(response.status_code).startswith('2'):
        return -1
    else:
        rating_history = process_rating_history(response_json)
        predictor_values = get_predictor_values(rating_history,target_rating,variant)
        prob_success = get_prob_success(predictor_values,model_params)
        predicted_date = get_predicted_date(predictor_values,model_params)
        return (prob_success,predicted_date)


def expected_date(name, rating, variant='Rapid'):
    if variant in ['Bullet','Blitz','Rapid','Classical']:
        (prob_success,predicted_date) = score(username = name, target_rating = rating, variant = variant, model_params = model_params)
        return(prob_success,predicted_date)
    # url = f'https://lichess.org/api/user/{name}/rating-history'
    # response = requests.get(url)
    # if not str(response.status_code).startswith('2'):
    #     return -1
    # data = requests.get(url).json()
    # rating_values = []
    # exp_rating_values = []
    # date_values = []
    # points = []
    
    # for game_type in data:
    #     if game_type['name'] != variant:
    #         continue
    #     else:
    #         points = game_type['points']

    # if len(points) < 25:
    #     return None

    # for point in points:
    #     date_values.append(datetime.date(point[0], point[1]+1, point[2]))
    #     exp_rating_values.append(3 ** (point[3] / 300))
    #     rating_values.append(point[3])

    # # Compute the best-fit line
    # start_date = min(date_values)
    # days_since_start_values = [(date-start_date).days for date in date_values]

    # coeffs = np.polyfit(days_since_start_values, exp_rating_values, 1)

    # days_since_start = ((3 ** (rating/300)) - coeffs[1])/coeffs[0]
    # print('test16')
    # return start_date + datetime.timedelta(days=days_since_start)


