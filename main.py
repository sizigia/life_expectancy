from flask import Flask, render_template, request, url_for, Markup
import pandas as pd
import numpy as np
from scipy import stats
import logging
import datetime
import os.path

app = Flask(__name__)

app.config["DEBUG"] = True
# constructor - load once (otherwise setup a local csv copy to save on bandwidth usage)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.logger.info(BASE_DIR)

src = os.path.join(BASE_DIR, 'WHOSIS_000001,WHOSIS_000015.csv')
who_list = pd.read_csv(src)
who_list = who_list[['GHO (DISPLAY)', 'YEAR (CODE)', 'COUNTRY (DISPLAY)', 'SEX (DISPLAY)', 'Numeric']]
who_list['COUNTRY (DISPLAY)'] = [country.title() for country in who_list['COUNTRY (DISPLAY)'].values]
country_list = sorted(set(who_list['COUNTRY (DISPLAY)'].values))


def get_life_expectancy(age, country, sex):
    sub_set = who_list[who_list['COUNTRY (DISPLAY)'].str.startswith(
        country, na=False)]
    sub_set = sub_set[sub_set['SEX (DISPLAY)'] == sex]
    sub_set = sub_set.sort_values('YEAR (CODE)', ascending=False)
    sub_set_birth = sub_set[sub_set['GHO (DISPLAY)'] == 'Life expectancy at birth (years)']
    sub_set_60 = sub_set[sub_set['GHO (DISPLAY)'] == 'Life expectancy at age 60 (years)']

    if len(sub_set_birth['Numeric']) > 0 and len(sub_set_60['Numeric']) > 0:
        lf_at_birth = sub_set_birth['Numeric'].values[0]
        lf_at_60 = sub_set_60['Numeric'].values[0]

        slope, intercept, r_value, p_value, std_err = stats.linregress([0, 60], [lf_at_birth, lf_at_60])

        return (np.ceil(slope * age + intercept))
    else:
        return None


@app.route('/', methods=['POST', 'GET'])
def interact_life_expectancy():
    default_age = 'Select Age'
    selected_age = default_age
    default_sex = 'Select Gender'
    selected_sex = default_sex
    default_country = 'Select Country'
    selected_country = default_country

    string_to_print = ''
    healthy_image_list = []
    if request.method == 'POST':
        selected_age = request.form['age']
        if (selected_age == default_age):
            selected_age = int(30)
        else:
            selected_age = selected_age

        selected_sex = request.form['sex']
        if (selected_sex == default_sex):
            selected_sex = 'Both sexes'

        selected_country = request.form['country']
        if (selected_country == default_country):
            selected_country = 'Argentina'

        current_time_left = get_life_expectancy(age=int(selected_age),
                                                country=selected_country,
                                                sex=selected_sex)

        if (current_time_left is not None):
            format_str = f"You have {np.ceil(current_time_left)} healthy years left to live"
            string_to_print = Markup(format_str)
        else:
            string_to_print = Markup("Error! No data found for selected parameters")
            current_time_left = 1

        healthy_image_list = []
        healthy_years_left = int(np.ceil(current_time_left))
        image_switch = 0
        if (healthy_years_left > 0):
            for y in range(healthy_years_left):
                if image_switch == 0:
                    healthy_image_list.append('static/images')
                else:
                    image_switch += 1

    return render_template('life.html', country_list=country_list,
                           default_country=selected_country,
                           default_age=selected_age,
                           default_sex=selected_sex,
                           string_to_print=string_to_print,
                           healthy_image_list=healthy_image_list)

    if __name__ == '__main__':
        app.run(debug=True)
