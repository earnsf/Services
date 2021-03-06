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

income_verify = Service(name='Income verification', path='/v1/county/{city}/{state}/{zipcode}/median/{level}/{income}', \
                              description='Verifying if the income is eligible for the program')

all_level_income = Service(name='All Level income', path='/v1/county/{city}/{state}/{zipcode}/median/{level}/all', \
                       description='Getting the median income for different levels')



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
        return fips.body

    data = [("city", city.title()), ("state", state.upper()), ("zipcode", zipcode), ("fips", fips)]
    return json.dumps(OrderedDict(data))



@med_income.get()
def show_med_income(request):
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = get_zipcode(request)
    fips = get_county(request)
    median_income = get_median_income(request)
    if type(median_income) != int and type(median_income) != long:

        return median_income.body
    data = [('city', city.title()), ('state', state.upper()), ('zipcode', zipcode), ('fips', fips), \
            ('median_income', median_income)]
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
        return income_threshold.body

    data = [('city', city.title()), ('state', state.upper()), ('zipcode', zipcode), ('fips', fips), \
            ('median_income', median_income), (level, income_threshold)]

    return json.dumps(OrderedDict(data))


@income_verify.get()
def show_eligibility(request):
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = get_zipcode(request)
    level = request.matchdict['level']

    income = request.matchdict['income']
    fips = get_county(request)
    median_income = get_median_income(request)
    income_threshold = get_income_threshold(request)
    eligibility = verify_income(request)
    if type(eligibility) != bool:
        return eligibility.body
    data = [('city', city.title()), ('state', state.upper()), ('zipcode', zipcode), ('fips', fips), \
            ('median_income', median_income), (level, income_threshold), ('income', int(income)), ('eligibility', eligibility)]
    return json.dumps(OrderedDict(data))


def verify_income(request):
    level = request.matchdict['level']
    try:
        income_threshold = int(get_income_threshold(request))

        try:
            income = int(request.matchdict['income'])
        except ValueError:
            print "***** Only integers are acceptable for income slot! *****"
            return Response(status_code=300, body="***** Only integers are acceptable for income slot! *****")
        except TypeError:
            return Response(status_code=300, body="***** Only integers are acceptable for income slot! *****")

    except ValueError:
        print get_income_threshold(request).body
        return get_income_threshold(request)
    except TypeError:
        return get_income_threshold(request)

    if income < 0:
        print("***** Income has to be a positive integer! *****")
        return Response(status_code=300, body="***** Income has to be a positive integer! *****")
    return income <= income_threshold


def get_zipcode(request):
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = request.matchdict['zipcode']
    check = DBSession().query(Zip_database).filter(or_(Zip_database.primary_city.__eq__(city), Zip_database.acceptable_cities.__eq__(city))).filter(Zip_database.state == state, Zip_database.zipcode == zipcode).all()

    if len(check) == 0:
        print("***** Invalid address! *****")
        return Response(status_code=300, body="***** Invalid address! *****")
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

    state_upper = str(state).upper()
    check = DBSession().query(Zip_database).filter(or_(Zip_database.primary_city.__eq__(city), Zip_database.acceptable_cities.__eq__(city))).filter(Zip_database.state == state, Zip_database.zipcode == zipcode).all()

    if len(check) == 0:
        print("***** Invalid address! *****")

        return Response(status_code=300, body="***** Invalid address! *****")  # should be blank on the browser because it is a back-end error message

    if state_upper == 'DC':               # fips for DC

        return '1100199999'

    elif state_upper == 'GU':             # fips for GU

        return '6601099999'

    # all the other special cases including 43 independent cities

    elif state_upper == 'PR' or state_upper == 'CT' or state_upper == 'ME' or state_upper == 'MA' or state_upper == 'NH' or state_upper == 'RI' or state_upper == 'VT':

        my_zip = DBSession().query(Zip_database).filter(Zip_database.zipcode == zipcode).all()

        if get_special_fips(city, state, zipcode) != 0:
            return get_special_fips(city, state, zipcode)


        else:               # Ex. East Concord are part of Concord City, so truncate the name
            word_list = str(city).split()
            if len(word_list) > 1:
                new_city = " ".join(word_list[1:])
                if get_special_fips(new_city, state, zipcode) != 0:
                    return get_special_fips(new_city, state, zipcode)


                else:          # Cities are part of acceptable cities and the fips cannot be found, so we use the primary city to look up the fips.
                    print("***** The city inputted are not in the database for now. Sorry for the inconvenience! *****")
                    return Response(status_code=300, body="***** The city inputted are not in the database for now. Sorry for the inconvenience! *****")


            else:
                my_list2 = [getattr(my_zip[0], column.name) for column in my_zip[0].__table__.columns]
                if str(city) in str(my_list2[2]):
                    primary_city = my_list2[1]
                    if get_special_fips(primary_city,state,zipcode) != 0:
                        return get_special_fips(primary_city, state, zipcode)
                    else:
                        print("***** The city inputted are not in the database for now. Sorry for the inconvenience! *****")
                        return Response(status_code=300, body="***** The city inputted are not in the database for now. Sorry for the inconvenience! *****")
                else:
                    print("***** The city inputted are not in the database for now. Sorry for the inconvenience! *****")
                    return Response(status_code=300, body="***** The city inputted are not in the database for now. Sorry for the inconvenience! *****")
    # normal case
    else:
        result = DBSession().query(Zip_database).filter(or_(Zip_database.primary_city.__eq__(city), Zip_database.acceptable_cities.__eq__(city))).filter(Zip_database.state == state, Zip_database.zipcode == zipcode).all()


        if len(result) == 1:
            my_list = [getattr(result[0], column.name) for column in result[0].__table__.columns]
            # print(my_list[1])
            # print(type(my_list[1]))
            my_county = my_list[3]
            if my_county[:3] == 'St ':
                my_county2 = my_county[:2] + '.' + my_county[2:]
                result1 = DBSession().query(County_fips2010).filter(or_(County_fips2010.county.startswith(my_county), County_fips2010.county.startswith(my_county2)), County_fips2010.state == state).all()

            elif my_county[:4] == 'Ste ':
                my_county2 = my_county[:3] + '.' + my_county[3:]
                result1 = DBSession().query(County_fips2010).filter(or_(County_fips2010.county.startswith(my_county), County_fips2010.county.startswith(my_county2)), County_fips2010.state == state).all()
            else:
                result1 = DBSession().query(County_fips2010).filter(County_fips2010.state == state, County_fips2010.county.startswith(my_county)).all()
            my_list = [getattr(result1[0], column.name) for column in result1[0].__table__.columns]

            if len(str(my_list[2])) == 9:
                return str(0) + str(my_list[2])
            return str(my_list[2])



        else:
            # print some statement or return an error page API (ask Tim)
            print("***** Invalid address! *****")
            # return Response(status_code=300, body="***** Invalid address! *****")
            return Response(status_code=300, body="***** Invalid address! *****")

def get_special_fips(city, state, zipcode):
    result_town = DBSession().query(County_fips2010).filter(County_fips2010.state == state, County_fips2010.county_town_name == city + " town").all()
    if (len(result_town)) == 1:
        my_list_town = [getattr(result_town[0], column.name) for column in result_town[0].__table__.columns]
        if len(str(my_list_town[2])) == 9:
            return str(0) + str(my_list_town[2])
        return str(my_list_town[2])
    else:
        result_city = DBSession().query(County_fips2010).filter(County_fips2010.state == state, County_fips2010.county_town_name == city + " city").all()
        if (len(result_city)) == 1:
            my_list_city = [getattr(result_city[0], column.name) for column in result_city[0].__table__.columns]
            if len(str(my_list_city[2])) == 9:
                return str(0) + str(my_list_city[2])
            return str(my_list_city[2])
        else:
            result_startwith = DBSession().query(County_fips2010).filter(County_fips2010.state == state, County_fips2010.county_town_name.startswith(city)).all()
            if (len(result_startwith)) == 1:
                my_list_start = [getattr(result_startwith[0], column.name) for column in result_startwith[0].__table__.columns]
                if len(str(my_list_start[2])) == 9:
                    return str(0) + str(my_list_start[2])
                return str(my_list_start[2])
            else:
                return 0


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
               'l30_6','l30_7','l30_8','l80_1','l80_2','l80_3','l80_4','l80_5','l80_6','l80_7','l80_8',\
               'l100_1','l100_2','l100_3','l100_4','l100_5','l100_6','l100_7','l100_8']

    if level not in my_dict:
        print("***** Invalid income level! *****")
        # return Response(status_code=300, body="***** Invalid income level! *****")
        return Response(status_code=300, body="***** Invalid income level! *****")
    elif level[1] == '5' or  level[1] == '1' or level[1] == '8' or\
 	level[1] == '3':
       
        income = DBSession().query(County_fips2010).filter(County_fips2010.fips2010 == fips).all()

        str_list = list(level)
        my_list = [getattr(income[0], column.name) for column in income[0].__table__.columns]
       
	if int(str_list[1]) == 5:
    	    return my_list[int(str_list[4]) + 4]
        elif  int(str_list[1]) == 3:
    	    return my_list[int(str_list[4]) + 12]
	# Added l100 for RedTab by persistent
	elif int(str_list[1]) == 1:
	    return my_list[int(str_list[5]) + 28]
        return my_list[int(str_list[4]) + 20]
    else:
	print("***** Only 30%, 50%, 80% or 100% area median income cutoff is required! *****")
        #return Response(status_code=300, body="***** The income threshold has to be 50% area median income! *****")
        return Response(status_code=300, body="***** Only 30%, 50%, 80% or 100% area median income cutoff is required! *****")

@all_level_income.get()
def get_all_level_income(request):
    """
    Service to return allowed income level for all 1 to 8 household sizes
    for a given city, state and zipcode
    e.g. http://lmi.earn.org:6543/v1/county/chicago/IL/60645/median/l50/all
    """
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = get_zipcode(request)
    fips = get_county(request)
    req_level = request.matchdict['level']
    data = []

    for i in xrange(1,9):
	request.matchdict['level']=req_level+"_"+str(i)
	level = "l"+str(i)
    	income_threshold = get_income_threshold(request)
    	if type(income_threshold) != int and type(income_threshold) != long:
            return income_threshold.body
	data.append((level, income_threshold))

    return json.dumps(OrderedDict(data))





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
