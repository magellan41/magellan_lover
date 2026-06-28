import datetime

from entity.location import LocationModel, Location
from orm import sql_session
from utils.singleton import singleton


@singleton
class LocationOrm:
    def __init__(self):
        pass

    def insert(self, location: LocationModel, address: str):
        new_location = Location(longitude=location.longitude, latitude=location.latitude, address=address, create_time=datetime.datetime.now())
        session = sql_session.get_session()
        try:
            session.add(new_location)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def select_last(self):
        session = sql_session.get_session()
        try:
            location = session.query(Location).filter(Location.status == 1).order_by(Location.id.desc()).first()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
        return location

    def select_last_day(self):
        current_time = datetime.datetime.now()
        last_day = current_time - datetime.timedelta(days=1)
        session = sql_session.get_session()
        try:
            location = session.query(Location).filter(Location.status == 1, Location.create_time >= last_day).all()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
        return location


