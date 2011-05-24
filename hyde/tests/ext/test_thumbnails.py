# -*- coding: utf-8 -*-
"""
Use nose
`$ pip install nose`
`$ nosetests`
"""
from hyde.fs import File, Folder
from hyde.model import Expando
from hyde.generator import Generator
from hyde.site import Site, Resource

from unittest import TestCase
import Image
import os

THUMBNAILS_SOURCE = File(__file__).parent.child_folder('thumbnails')
TEST_SITE = File(__file__).parent.parent.child_folder('_test')


class TestThumbnails(TestCase):

    def setUp(self):
        TEST_SITE.make()
        TEST_SITE.parent.child_folder(
                    'sites/test_jinja').copy_contents_to(TEST_SITE)
        IMAGES = TEST_SITE.child_folder('content/media/images')
        IMAGES.make()
        THUMBNAILS_SOURCE.copy_contents_to(IMAGES)
        s = Site(TEST_SITE)
        s.config.plugins = ['hyde.ext.plugins.images.ImageThumbnailsPlugin']
        self.gen = Generator(s)
        self.site = s

    def tearDown(self):
        TEST_SITE.delete()

    def test_images_has_thumb_fn(self):
        for image in ['hyde.jpg', 'hyde.png']:
            source =  File(TEST_SITE.child('content/media/images/%s' % image))
            self.gen.generate_resource_at_path(source)
            source = self.site.content.resource_from_path(source)
            self.assertIn('thumb', dir(source))
            self.assertTrue(callable(source.thumb))

    def test_thumb_has_width_height(self):
        source = File(TEST_SITE.child('content/media/images/hyde.jpg'))
        self.gen.generate_resource_at_path(source)
        source = self.site.content.resource_from_path(source)
        target = source.thumb()
        self.assertIn('width', dir(target))
        self.assertIn('height', dir(target))

    def test_thumb_keep_width_or_height(self):
        source = File(TEST_SITE.child('content/media/images/hyde.jpg'))
        self.gen.generate_resource_at_path(source)
        source = self.site.content.resource_from_path(source)
        target = source.thumb(width=30, height=40)
        self.assertTrue(target.width == 30 or target.height == 40)

    def test_thumb_respect_one_value(self):
        source = File(TEST_SITE.child('content/media/images/hyde.jpg'))
        self.gen.generate_resource_at_path(source)
        source = self.site.content.resource_from_path(source)
        target = source.thumb(width=30)
        self.assertEqual(target.width, 30)
        target = source.thumb(height=30)
        self.assertEqual(target.height, 30)

    def test_thumb_advertised_dimensions(self):
        source = File(TEST_SITE.child('content/media/images/hyde.jpg'))
        self.gen.generate_resource_at_path(source)
        source = self.site.content.resource_from_path(source)
        target = source.thumb()
        path = File(Folder(self.site.config.deploy_root_path).child(target)).path
        size = Image.open(path).size
        self.assertEqual((target.width, target.height), size)
 
    def test_thumb_keep_proportions(self):
        source = File(TEST_SITE.child('content/media/images/hyde.jpg'))
        size = Image.open(source.path).size
        ratio = float(size[0])/size[1]
        self.gen.generate_resource_at_path(source)
        source = self.site.content.resource_from_path(source)
        target = source.thumb(height=400)
        size = (target.width, target.height)
        self.assertAlmostEqual(ratio, float(size[0])/size[1], places=3)

    def test_thumb_prefix(self):
        self.site.config.thumbnails = Expando(dict(prefix="mythumb_"))
        source = File(TEST_SITE.child('content/media/images/hyde.jpg'))
        self.gen.generate_resource_at_path(source)
        source = self.site.content.resource_from_path(source)
        target = str(source.thumb())
        self.assertEqual(target.split(os.sep)[-1], "mythumb_hyde.jpg")

    def test_thumb_directory(self):
        source = File(TEST_SITE.child('content/media/images/hyde.jpg'))
        self.gen.generate_resource_at_path(source)
        source = self.site.content.resource_from_path(source)
        target = str(source.thumb())
        self.assertEqual(target, "media/images/thumb_hyde.jpg")
