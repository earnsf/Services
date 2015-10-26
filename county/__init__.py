from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import DeferredReflection
from .models import (
    DBSession,
    Base,
    )
from views import show_county, show_med_income, show_level_income

from pyramid.events import NewRequest

def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '1728000',
        })
    event.request.add_response_callback(cors_headers)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DeferredReflection.prepare(engine)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)
    config.include('pyramid_chameleon')
    config.include('cornice')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    #config.add_view(show_county, 'county')
    #config.add_view(show_med_income, 'med_income')
    #config.add_view(show_level_income, 'level_income')
    config.scan()
    return config.make_wsgi_app()
