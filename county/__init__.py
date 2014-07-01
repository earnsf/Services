from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import DeferredReflection
from .models import (
    DBSession,
    Base,
    )
from views import get_county


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DeferredReflection.prepare(engine)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.include('cornice')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_view(get_county, 'county')
    config.scan()
    return config.make_wsgi_app()
