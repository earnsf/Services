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

county = Service(name='Deriving county', path='/county/{city}/{state}/{zipcode}',description='deriving the county from an address')
med_income = Service(name='Median income', path='/county/{city}/{state}/{zipcode}/{household_size}', description='Getting the median income')




# the original interface that presents when setting up the pyramid scaffold
@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):

    try:
        one = DBSession.query(MyModel).filter(MyModel.name == 'one').first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return {'one': one, 'project': 'county'}


@county.get()
def get_county(request):
    city = request.matchdict['city']
    state = request.matchdict['state']
    zipcode = request.matchdict['zipcode']


    if state == 'DC':               # fips for DC
        return 1100199999

    elif state == 'GU':             # fips for GU
        return 6601099999

    elif state == 'PR' or state == 'CT' or state == 'ME' or state == 'MA' or state == 'NH' or state == 'RI' or state == 'VT':             # fips for PR (don't really care)
        #result = DBSession().query(County_fips2010).filter(County_fips2010.State == state, County_fips2010.county_town_name == city + " Municipio").all()
        result = DBSession().query(County_fips2010).filter(County_fips2010.State == state, County_fips2010.county_town_name.startswith(city)).all()
        #print(len(result))  == 0
        if len(result) == 1:
            my_list = [getattr(result[0], column.name) for column in result[0].__table__.columns]
            return int(my_list[2])

        else:
            # print some statement or return an error page API (ask Tim)
            return Response(status_code=300)


    else:
        result = DBSession().query(Zip_database).filter(Zip_database.state == state, Zip_database.zipcode == zipcode, or_(Zip_database.primary_city == city, Zip_database.acceptable_cities.like(city))).all()
        if len(result) == 1:
            my_list = [getattr(result[0], column.name) for column in result[0].__table__.columns]
            my_county = my_list[3]
            result1 = DBSession().query(County_fips2010).filter(County_fips2010.State == state, County_fips2010.County_Name.startswith(my_county)).all()
            my_list = [getattr(result1[0], column.name) for column in result1[0].__table__.columns]
            return int(my_list[2])

        else:
            # print some statement or return an error page API (ask Tim)
            return Response(status_code=300)


"""
    elif state == 'CT' or state == 'ME' or state == 'MA' or state == 'NH' or state == 'RI' or state == 'VT':
        my_list = []
        result = DBSession().query(County_fips2010).filter(County_fips2010.State == state, County_fips2010.county_town_name == city + " town").all()
        if len(result) != 0:
            my_list = [getattr(result[0], column.name) for column in result[0].__table__.columns]
            return int(my_list[2])
        else:
            result1 = DBSession().query(County_fips2010).filter(County_fips2010.State == state, County_fips2010.county_town_name == city + " city").all()
            if len(result1) != 0:
                my_list = [getattr(result1[0], column.name) for column in result1[0].__table__.columns]
                return int(my_list[2])
            else:
                result2 = DBSession().query(County_fips2010).filter(County_fips2010.State == state, County_fips2010.county_town_name == city + " UT").all()
                if len(result2) != 0:
                    my_list = [getattr(result2[0], column.name) for column in result2[0].__table__.columns]
                    return int(my_list[2])
                else:
                    result3 = DBSession().query(County_fips2010).filter(County_fips2010.State == state, County_fips2010.county_town_name.like('%'))

"""



    #result = DBSession().query(Zip_database).first()
    #for a in result:
    #    for column in a.__table__.columns:         # 94704 Bekreley / Alameda County CA
    #        print(getattr(result, column.name))






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
