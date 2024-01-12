# from threading import Thread, Event
# import unittest
# import shutil
# from semantic_search_engine.chroma import ChromaSingleton
# from semantic_search_engine import constants

# def create_singleton_instance(result, event):
#     # Each thread will try to create an instance of the Singleton
#     singleton_instance = ChromaSingleton()
#     result.append(id(singleton_instance))
#     event.set()

# class TestChromaSingleton(unittest.TestCase):

#     @classmethod
#     def setUpClass(cls) -> None:
#         # create singleton instances
#         cls.instance1 = ChromaSingleton()
#         cls.instance2 = ChromaSingleton()
#         cls.instance3 = ChromaSingleton(False)

#         # get chroma clients from singleton instances
#         cls.db1 = cls.instance1.get_connection()
#         cls.db2 = cls.instance1.get_connection()
#         cls.db3 = cls.instance1.get_connection()

#     @classmethod
#     def tearDownClass(cls) -> None:
#         del()
#         shutil.rmtree(constants.CHROMA_PATH)
            
#     def test_multiple_instantiations(self):


#         self.assertEqual(self.instance1, self.instance2, "both singleton instances should be equal")
#         self.assertEqual(
#             self.instance1, 
#             self.instance3, 
#             "both singleton instances should be equal, eventhough their initializing parameters are different"
#         )

#         self.assertEqual(self.db1, self.db2, "both client instances are not equal")
#         self.assertEqual(self.db1, self.db3, "both client instances are not equal")


#     def test_singleton_thread_safety(self):
#         # Create a list to store the thread IDs
#         thread_ids = []

#         # Create an event to track thread completion
#         event = Event()

#         # Create multiple threads that will attempt to create Singleton instances
#         num_threads = 5
#         threads = [Thread(target=create_singleton_instance, args=(thread_ids, event)) for _ in range(num_threads)]

#         # Start all threads
#         for thread in threads:
#             thread.start()

#         # Wait for all threads to finish
#         for thread in threads:
#             thread.join()

#         # Wait for all events to be set (indicating thread completion)
#         event.wait()

#         self.assertNotEqual(len(thread_ids), 0, "multithreading did not work")
#         self.assertTrue(all(id == thread_ids[0] for id in thread_ids), "the threads are not similar")

# if __name__ == "__main__":
#     unittest.main()
