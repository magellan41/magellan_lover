from entity.Memes import Memes
from orm import sql_session
from utils.singleton import singleton


@singleton
class MemesOrm:
    def __init__(self):
        pass

    def insert(self, path: str, url: str, md5_val: str):
        session = sql_session.get_session()
        try:
            new_meme = Memes(path=path, url=url, md5_val=md5_val)
            session.add(new_meme)
            session.commit()
            return new_meme.id
        finally:
            session.close()

    def find_never_try_save(self, limit: int = 10):
        session = sql_session.get_session()
        try:
            memes = session.query(Memes).filter(Memes.try_to_save_vector == 0, Memes.status == 1).limit(limit).all()
        finally:
            session.close()
        return memes

    def mark_save_in_vector(self, ids: list[int]):
        session = sql_session.get_session()
        try:
            session.query(Memes).filter(Memes.id.in_(ids)).update({Memes.try_to_save_vector: 1, Memes.vector_status: 1}, synchronize_session=False)
            session.commit()
        finally:
            session.close()

    def mark_fail_save_in_vector(self, ids: list[int]):
        session = sql_session.get_session()
        try:
            session.query(Memes).filter(Memes.id.in_(ids)).update({Memes.try_to_save_vector: 1, Memes.vector_status: 0}, synchronize_session=False)
            session.commit()
        finally:
            session.close()

    def select_by_id(self, id: int):
        session = sql_session.get_session()
        try:
            memes = session.query(Memes).filter(Memes.id == id).first()
        finally:
            session.close()
        return memes

    def select_by_md5_val(self, md5_val: str):
        session = sql_session.get_session()
        try:
            memes = session.query(Memes).filter(Memes.md5_val == md5_val).first()
        finally:
            session.close()
        return memes
