# import unittest
# from semantic_search_engine import db
# from peewee import SqliteDatabase
# import os
# from semantic_search_engine import constants

# class TestSQLDatabase(unittest.TestCase):

#     @classmethod
#     def setUpClass(cls) -> None:
#         cls.db = db.db

#         cls.db.connect()

#         cls.db.create_tables([
#             db.User,
#             db.Chat,
#             db.ChatMemberRelationship
#         ])

#     @classmethod
#     def tearDownClass(cls) -> None:
#         cls.db.close()

#         try:
#             os.remove(constants.SQLITE_DB_PATH)
#         except:
#             pass
    
#     def test_db_instantiation(self):
#         self.assertIsInstance(db.db, SqliteDatabase, "Should be an sqlite database")

#     def test_db_tables_exist(self):
#         tables = self.db.get_tables()
#         self.assertEqual(tables, ['chat', 'chatmemberrelationship', 'user'], "Tables should exist")