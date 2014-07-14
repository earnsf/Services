from pyramid.response import Response
from pyramid.view import view_config
from cornice import Service
from sqlalchemy.exc import DBAPIError
from sqlalchemy import or_

from .models import (
    DBSession,
    MyModel,
    Zip_database,
    County_fips2010,
    )

import json
from collections import OrderedDict




county = Service(name='Deriving county', path='/v1/county/{city}/{state}/{zipcode}',\
                 description='deriving the county from an address')

med_income = Service(name='Median income', path='/v1/county/{city}/{state}/{zipcode}/median', \
                     description='Getting the median income')

level_income = Service(name='Level income', path='/v1/county/{city}/{state}/{zipcode}/median/{level}', \
                       description='Getting the median income for different levels')

fifty_income_verify = Service(name='Income verification', path='/v1/county/{city}/{state}/{zipcode}/median/{level}/{income}', \
                              description='Verifying if the income is below 50% AMI')



# the original interface that presents when setting up the pyramid scaffold
@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):

    try:
        one = DBSession.query(MyModel).filter(MyModel.name == 'one').first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return {'one': one, 'project': 'county'}



@county.get()
def show_county(request):

    fips = get_county(request)
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = get_zipcode(request)
    if type(fips) != str:
        return fips

    data = {"city": city.title(), "state":state.upper(), "zipcode": zipcode, "fips": fips}
    return json.dumps(OrderedDict(data))



@med_income.get()
def show_med_income(request):
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = get_zipcode(request)
    fips = get_county(request)
    median_income = get_median_income(request)
    if type(median_income) != int and type(median_income) != long:

        return median_income
    data = {'city': city.title(), 'state':state.upper(), 'zipcode': zipcode, 'fips': fips, 'median_income': median_income}
    return json.dumps(OrderedDict(data))


@level_income.get()
def show_level_income(request):

    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = get_zipcode(request)
    fips = get_county(request)
    level = request.matchdict['level']
    median_income = get_median_income(request)
    income_threshold = get_income_threshold(request)
    if type(income_threshold) != int and type(income_threshold) != long:
        return income_threshold

    data = {'city': city.title(), 'state':state.upper(), 'zipcode': zipcode, 'fips': fips, 'median_income': median_income, \
            level: income_threshold}

    return json.dumps(OrderedDict(data))


@fifty_income_verify.get()
def show_eligibility(request):
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = get_zipcode(request)
    level = request.matchdict['level']
    str_list = list(level)
    if str_list[1] != '5':
        print("The income threshold has to be 50% area median income!")
        return Response(status_code=300)
    income = request.matchdict['income']
    fips = get_county(request)
    median_income = get_median_income(request)
    income_threshold = get_income_threshold(request)
    eligibility = verify_income(request)
    if type(eligibility) != bool:
        return eligibility
    data = {'city': city.title(), 'state':state.upper(), 'zipcode': zipcode, 'fips': fips, 'median_income': median_income, \
            level: income_threshold, 'income': int(income), 'eligibility': eligibility}
    return (json.dumps(OrderedDict(data))).replace('\\"', "\"")


def verify_income(request):
    try:
        income_threshold = int(get_income_threshold(request))
        income = int(request.matchdict['income'])
        level = request.matchdict['level']

    except ValueError as e:
        print e
        return Response(status_code=300)

    return income <= income_threshold


def get_zipcode(request):
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = request.matchdict['zipcode']
    check = DBSession().query(Zip_database).filter(or_(Zip_database.primary_city.contains(city), Zip_database.acceptable_cities.contains(city))).filter(Zip_database.state == state, Zip_database.zipcode == zipcode).all()

    if len(check) == 0:
        print("Invalid address!")
        print(check)
        return Response(status_code=300)
    else:
        my_list = [getattr(check[0], column.name) for column in check[0].__table__.columns]
        if len(str(my_list[0])) == 3:
            return '00' + str(my_list[0])
        elif len(str(my_list[0])) == 4:
            return '0' + str(my_list[0])

    return str(my_list[0])


def get_county(request):

    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = request.matchdict['zipcode']


    check = DBSession().query(Zip_database).filter(or_(Zip_database.primary_city.contains(city), Zip_database.acceptable_cities.contains(city))).filter(Zip_database.state == state, Zip_database.zipcode == zipcode).all()

    if len(check) == 0:
        print("Invalid address!")
        return Response(status_code=300)  # should be blank on the browser because it is a back-end error message


    if str(state).upper() == 'DC':               # fips for DC
        # return 1100199999
        return '1100199999'

    elif str(state).upper() == 'GU':             # fips for GU
        # return 6601099999
        return '6601099999'

    # all the other special cases including 43 independent cities

    elif str(state).upper() == 'PR' or str(state).upper() == 'CT' or str(state).upper() == 'ME' or str(state).upper() == 'MA' or str(state).upper() == 'NH' or str(state).upper() == 'RI' or str(state).upper() == 'VT':

        result = DBSession().query(County_fips2010).filter(County_fips2010.state == state, County_fips2010.county_town_name.startswith(city)).all()
        # print("length of the result is " + str(len(result)))
        if len(result) == 1:
            my_list = [getattr(result[0], column.name) for column in result[0].__table__.columns]
            if len(str(my_list[2])) == 9:
                return str(0) + str(my_list[2])
            return str(my_list[2])
        else:
            print("Invalid address!")
            return Response(status_code=300)


    else:
        result = DBSession().query(Zip_database).filter(or_(Zip_database.primary_city.contains(city), Zip_database.acceptable_cities.contains(city))).filter(Zip_database.state == state, Zip_database.zipcode == zipcode).all()

        if len(result) == 1:
            my_list = [getattr(result[0], column.name) for column in result[0].__table__.columns]
            # print(my_list[1])
            # print(type(my_list[1]))
            my_county = my_list[3]
            result1 = DBSession().query(County_fips2010).filter(County_fips2010.state == state, County_fips2010.county.startswith(my_county)).all()
            my_list = [getattr(result1[0], column.name) for column in result1[0].__table__.columns]
            if len(str(my_list[2])) == 9:
                return str(0) + str(my_list[2])
            return str(my_list[2])



        else:
            # print some statement or return an error page API (ask Tim)
            print("Invalid address!")
            return Response(status_code=300)



def get_median_income(request):

    fips = get_county(request)
    if type(fips) != str:
        return fips
    income = DBSession().query(County_fips2010).filter(County_fips2010.fips2010 == fips).all()
    my_list = [getattr(income[0], column.name) for column in income[0].__table__.columns]
    return my_list[4]




def get_income_threshold(request):

    fips = get_county(request)
    if type(fips) != str:
        return fips


    level = request.matchdict['level']



    my_dict = ['l50_1','l50_2','l50_3','l50_4','l50_5','l50_6','l50_7','l50_8','l30_1','l30_2','l30_3','l30_4','l30_5',\
               'l30_6','l30_7','l30_8','l80_1','l80_2','l80_3','l80_4','l80_5','l80_6','l80_7','l80_8',]

    if level not in my_dict:
        print("Invalid income level!")
        return Response(status_code=300)

    income = DBSession().query(County_fips2010).filter(County_fips2010.fips2010 == fips).all()

    str_list = list(level)
    my_list = [getattr(income[0], column.name) for column in income[0].__table__.columns]
    if int(str_list[1]) == 5:
        return my_list[int(str_list[4]) + 4]
    elif  int(str_list[1]) == 3:
        return my_list[int(str_list[4]) + 12]
    return my_list[int(str_list[4]) + 20]






conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_county_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""
