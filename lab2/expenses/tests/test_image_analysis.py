from io import BytesIO

from django.test import SimpleTestCase

from expenses.image_analysis import MIN_USABLE_DIMENSION, analyze_image
from expenses.tests.helpers import make_image_bytes


class AnalyzeImageTests(SimpleTestCase):
    def test_a_sharp_photo_is_not_flagged_as_blurry(self):
        result = analyze_image(BytesIO(make_image_bytes()))

        self.assertTrue(result.is_readable)
        self.assertFalse(result.is_blurry)
        self.assertEqual((result.width, result.height), (800, 1000))

    def test_a_heavily_blurred_photo_is_flagged(self):
        result = analyze_image(BytesIO(make_image_bytes(blur_radius=8)))

        self.assertTrue(result.is_readable)
        self.assertTrue(result.is_blurry)

    def test_a_too_small_photo_is_flagged_as_blurry_regardless_of_sharpness(self):
        small_side = MIN_USABLE_DIMENSION - 50
        result = analyze_image(BytesIO(make_image_bytes(width=small_side, height=small_side)))

        self.assertTrue(result.is_readable)
        self.assertTrue(result.is_blurry)

    def test_a_corrupt_file_is_not_readable_and_never_raises(self):
        result = analyze_image(BytesIO(b"this is not an image at all"))

        self.assertFalse(result.is_readable)
        self.assertIsNone(result.width)
        self.assertIsNone(result.height)

    def test_seeks_back_to_the_start_so_the_file_can_be_reused(self):
        file_obj = BytesIO(make_image_bytes())
        analyze_image(file_obj)
        self.assertEqual(file_obj.tell(), 0)
