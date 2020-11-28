from django.test import TestCase
from django.urls import reverse
from django.test import override_settings
from django.contrib.auth.models import User
import tempfile
import filecmp
import os
from .models import Place
from PIL import Image


# Create your tests here.
class TestHomePage(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)

    def test_homepage_shows_empty_list_for_empty_database(self):
        home_page = reverse("place_list")  # View name
        response = self.client.get(home_page)  # Getting response
        self.assertTemplateUsed(response, "travel_wishlist/wishlist.html")
        self.assertContains(response, "You have no places in your wishlist")  # checking the contents of response


class TestMarkPlaceAsVisited(TestCase):
    fixtures = ["test_places", "test_users"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)

    def test_mark_unvisited_as_visited(self):
        response = self.client.post(reverse('place_was_visited', args=(2,)), follow=True)
        self.assertTemplateUsed(response, "travel_wishlist/wishlist.html")  # Checking if right template is used or not

        place = Place.objects.get(pk=2)
        self.assertTrue(place.visited)  # checking if place is visited

    def test_mark_non_existent_place_as_visited(self):
        response = self.client.post(reverse('place_was_visited', args=(200,)), follow=True)
        self.assertEqual(404, response.status_code)

    def test_visit_someone_else_place_not_authorized(self):
        response = self.client.post(reverse('place_was_visited', args=(5,)), follow=True)
        self.assertEqual(200, response.status_code)


class TestWishList(TestCase):
    fixtures = ["test_places", "test_users"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)

    def test_view_wishlist(self):
        response = self.client.get(reverse('place_list'))
        self.assertTemplateUsed(response, "travel_wishlist/wishlist.html")

        rendered_data = list(response.context['places'])
        expected_data = list(Place.objects.filter(user=self.user).filter(visited=False))

        self.assertCountEqual(expected_data, rendered_data)

    def test_view_places_visited(self):
        response = self.client.get(reverse('places_visited'))
        self.assertTemplateUsed(response, "travel_wishlist/visited.html")

        rendered_data = list(response.context['visited'])
        expected_data = list(Place.objects.filter(user=self.user).filter(visited=True))

        self.assertCountEqual(expected_data, rendered_data)


class TestAddNewPlace(TestCase):
    fixtures = ["test_users"]

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)

    def test_add_new_unvisited_place_to_wishlist(self):
        response = self.client.get(reverse("place_list"), {'name': 'Tokyo', 'visited': False}, follow=True)

        self.assertTemplateUsed(response, "travel_wishlist/wishlist.html")

        places_response = response.context['places']
        self.assertEqual(len(places_response), 0)

    def test_add_new_visited_place_to_wishlist(self):
        response = self.client.post(reverse('place_list'), {'name': 'Tokyo', 'visited': True}, follow=True)

        self.assertTemplateUsed(response, 'travel_wishlist/wishlist.html')

        response_places = response.context['places']

        self.assertEqual(len(response_places), 0)


class TestDeletePlace(TestCase):

    fixtures = ['test_places', 'test_users']

    def setUp(self):
        user = User.objects.first()
        self.client.force_login(user)

    def test_delete_own_place(self):
        response = self.client.post(reverse('delete_place', args=(2,)), follow=True)
        place_2 = Place.objects.filter(pk=2).first()
        self.assertIsNone(place_2)   # checking place is deleted or not

    def test_delete_someone_else_place_not_auth(self):
        response = self.client.post(reverse('delete_place',  args=(5,)), follow=True)
        self.assertEqual(403, response.status_code)
        place_5 = Place.objects.get(pk=5)
        self.assertIsNotNone(place_5)    # place is in database


class TestPlaceDetail(TestCase):
    fixtures = ['test_places', 'test_users']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)

    def test_modify_someone_else_place_details_not_authorized(self):
        response = self.client.post(reverse('place_details', kwargs={'place_pk': 5}), {'notes': 'awesome'}, follow=True)
        self.assertEqual(403, response.status_code)  # 403 Forbidden

    def test_place_detail(self):
        place_1 = Place.objects.get(pk=1)

        response = self.client.get(reverse('place_details', kwargs={'place_pk': 1}))

        self.assertTemplateUsed(response, 'travel_wishlist/place_details.html')

        data_rendered = response.context['place']

        self.assertEqual(data_rendered, place_1)

        self.assertContains(response, 'Tokyo')
        self.assertContains(response, 'cool')
        self.assertContains(response, '2014-01-01')

    def test_modify_notes(self):
        response = self.client.post(reverse('place_details', kwargs={'place_pk': 1}), {'notes': 'awesome'}, follow=True)

        updated_place_1 = Place.objects.get(pk=1)

        # updated db
        self.assertEqual('awesome', updated_place_1.notes)

        self.assertEqual(response.context['place'], updated_place_1)
        # correct template
        self.assertTemplateUsed(response, 'travel_wishlist/place_details.html')

        # notes
        self.assertNotContains(response, 'cool')  # old text is gone
        self.assertContains(response, 'awesome')  # new text shown

    def test_add_notes(self):
        response = self.client.post(reverse('place_details', kwargs={'place_pk': 4}), {'notes': 'yay'}, follow=True)

        updated_place_4 = Place.objects.get(pk=4)

        # updated db
        self.assertEqual('yay', updated_place_4.notes)

        # correct object in db
        self.assertEqual(response.context['place'], updated_place_4)
        # correct template
        self.assertTemplateUsed(response, 'travel_wishlist/place_details.html')

        # correct data on page
        self.assertContains(response, 'yay')  # new text shown

    def test_add_date_visited(self):
        date_visited = '2014-01-01'

        response = self.client.post(reverse('place_details', kwargs={'place_pk': 4}), {'date_visited': date_visited},
                                    follow=True)

        updated_place_4 = Place.objects.get(pk=4)

        # database is updated
        self.assertEqual(updated_place_4.date_visited.isoformat(), date_visited)  # .isoformat is YYYY-MM-DD

        # correct object on template
        self.assertEqual(response.context['place'], updated_place_4)

        # correct template
        self.assertTemplateUsed(response, 'travel_wishlist/place_details.html')

        # correct data on page
        self.assertContains(response, date_visited)  # new text shown


def create_temp_image_file():
    handle, tmp_img_file = tempfile.mkstemp(suffix='.jpg')
    img = Image.new('RGB', (10, 10))
    img.save(tmp_img_file, format='JPEG')
    return tmp_img_file


class TestImageUpload(TestCase):
    fixtures = ['test_users', 'test_places']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)
        self.MEDIA_ROOT = tempfile.mkdtemp()

    def tearDown(self):
        print('todo delete temp directory, temp image')

    def test_upload_new_image_for_own_place(self):
        img_file_path = create_temp_image_file()

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):
            with open(img_file_path, 'rb') as img_file:
                resp = self.client.post(reverse('place_details', kwargs={'place_pk': 1}), {'photo': img_file},
                                        follow=True)

                self.assertEqual(200, resp.status_code)

                place_1 = Place.objects.get(pk=1)
                img_file_name = os.path.basename(img_file_path)
                expected_uploaded_file_path = os.path.join(self.MEDIA_ROOT, 'user_images', img_file_name)

                self.assertTrue(os.path.exists(expected_uploaded_file_path))
                self.assertIsNotNone(place_1.photo)
                self.assertTrue(filecmp.cmp(img_file_path, expected_uploaded_file_path))

    def test_change_image_for_own_place_expect_old_deleted(self):
        first_img_file_path = create_temp_image_file()
        second_img_file_path = create_temp_image_file()

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):
            with open(first_img_file_path, 'rb') as first_img_file:
                resp = self.client.post(reverse('place_details', kwargs={'place_pk': 1}), {'photo': first_img_file},
                                        follow=True)

                place_1 = Place.objects.get(pk=1)

                first_uploaded_image = place_1.photo.name

                with open(second_img_file_path, 'rb') as second_img_file:
                    resp = self.client.post(reverse('place_details', kwargs={'place_pk': 1}),
                                            {'photo': second_img_file}, follow=True)

                    # first file should not exist
                    # second file should exist

                    place_1 = Place.objects.get(pk=1)

                    second_uploaded_image = place_1.photo.name

                    first_path = os.path.join(self.MEDIA_ROOT, first_uploaded_image)
                    second_path = os.path.join(self.MEDIA_ROOT, second_uploaded_image)

                    self.assertFalse(os.path.exists(first_path))
                    self.assertTrue(os.path.exists(second_path))

    def test_upload_image_for_someone_else_place(self):
        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):
            img_file = create_temp_image_file()
            with open(img_file, 'rb') as image:
                resp = self.client.post(reverse('place_details', kwargs={'place_pk': 5}), {'photo': image}, follow=True)
                self.assertEqual(403, resp.status_code)

                place_5 = Place.objects.get(pk=5)
                self.assertFalse(place_5.photo)  # no photo set

    def test_delete_place_with_image_image_deleted(self):
        img_file_path = create_temp_image_file()

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):
            with open(img_file_path, 'rb') as img_file:
                resp = self.client.post(reverse('place_details', kwargs={'place_pk': 1}), {'photo': img_file},
                                        follow=True)

                self.assertEqual(200, resp.status_code)

                place_1 = Place.objects.get(pk=1)
                img_file_name = os.path.basename(img_file_path)

                uploaded_file_path = os.path.join(self.MEDIA_ROOT, 'user_images', img_file_name)

                # place 1 deleted

                place_1 = Place.objects.get(pk=1)
                place_1.delete()

                self.assertFalse(os.path.exists(uploaded_file_path))