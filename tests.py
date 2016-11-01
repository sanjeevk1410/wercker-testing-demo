import namemycat
import unittest
import requests
import time

from flask_testing import LiveServerTestCase


class IntegrationTests(unittest.TestCase):
    def setUp(self):
            namemycat.app.config['TESTING'] = True
            self.app = namemycat.app.test_client()

            self.test_name = "Rogue"

            with namemycat.app.app_context():
                namemycat.init_db()
                namemycat.submit_cat_name(self.test_name)

    def tearDown(self):
        with namemycat.app.app_context():
            db = namemycat.get_db()
            cur = db.cursor()
            cur.execute(
                """
                DROP TABLE names;
                """
            )
            cur.close()
            db.close()

    def test_db_exists(self):
        """Make sure the DB exists"""

        with namemycat.app.app_context():
            db = namemycat.get_db()
            cur = db.cursor()
            cur.execute(
                """
                    SELECT EXISTS (
                       SELECT 1
                       FROM information_schema.tables
                       WHERE table_name = 'names'
                    );
                """
            )

            assert cur.rowcount

    def test_adding_name_validation(self):
        """Test adding a new name to the DB"""
        with namemycat.app.app_context():
            assert not namemycat.submit_cat_name("")

    def test_name_is_added(self):
        """Test adding a new name to the DB"""
        with namemycat.app.app_context():
            db = namemycat.get_db()
            cur = db.cursor()
            cur.execute(
                "SELECT * FROM names WHERE name = %s",
                [self.test_name]
            )

        assert cur.rowcount

    def test_get_name(self):
        """Test that the name added is returned"""
        with namemycat.app.app_context():
            assert namemycat.get_random_name() == self.test_name

    def test_get_random_name(self):
        """Test that the name we get back isn't always the same."""

        test_names = [
            "Simba",
            "Mufasa",
            "Nala",
            "Sarabi",
            "Sarafina",
            "Scar"
        ]

        with namemycat.app.app_context():
            for name in test_names:
                namemycat.submit_cat_name(name)

            last_name = ""

            for i in xrange(0, 1000):
                this_name = namemycat.get_random_name()

                if len(last_name) > 0:
                    if last_name != this_name:
                        return True

                last_name = this_name

    def test_homepage(self):
        """Test for a 200 from a homepage GET request"""
        response = self.app.get('/')
        assert "200" in response.status

    def test_successful_post(self):
        """Test that the user can post a name successfully"""
        response = self.app.post(
            '/',
            data=dict(name=self.test_name), follow_redirects=True
        )

        assert "200" in response.status and "Thanks" in response.data

    def test_failing_post(self):
        """Test that the user gets an error if they post nothing"""
        response = self.app.post(
            '/',
            data=dict(name=""), follow_redirects=True
        )

        assert "200" in response.status and "Sorry" in response.data


class FunctionalTests(LiveServerTestCase):

    def setUp(self):
            self.test_name = "Shadow"
            namemycat.init_db()

    def tearDown(self):
        with namemycat.app.app_context():
            db = namemycat.get_db()
            cur = db.cursor()
            cur.execute(
                """
                DROP TABLE names;
                """
            )
            cur.close()
            db.close()

    def create_app(self):
        app = namemycat.app
        app.config['TESTING'] = True
        app.config['LIVESERVER_PORT'] = 5000
        app.config['LIVESERVER_TIMEOUT'] = 10

        return app

    def test_server_is_up(self):
        """ Test that the application is up and returning the default name"""
        response = requests.get(self.get_server_url())
        assert response.status_code == 200 and "Cat" in response.content

    def test_posting_name(self):
        """ Test a POST request for a new name"""
        response = requests.post(
            self.get_server_url(),
            data={"name": self.test_name}
        )

        assert response.status_code == 200 and "Thanks" in response.content

    def test_posting_validation_fail(self):
        """ Test a POST request for a new name"""
        response = requests.post(
            self.get_server_url(),
            data={"name": ""}
        )

        assert response.status_code == 200 and "Sorry" in response.content

    def test_get_random_name(self):
        """Make sure we always get a response back from the db"""

        for i in xrange(0, 100):
            response = requests.get(self.get_server_url())
            if response.content == "Cat" or response.status_code != 200:
                return False
            # Oops, You've caught me trying to make our tests take longer...
            time.sleep(1)


if __name__ == '__main__':
    unittest.main()
