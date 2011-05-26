# -*- coding: utf-8 -*-
"""
Contains classes to handle images related things

# Requires PIL
"""

from hyde.plugin import Plugin
from hyde.fs import File, Folder

import re
import Image
import new
import os
from functools import partial

class ImageSizerPlugin(Plugin):
    """
    Each HTML page is modified to add width and height for images if
    they are not already specified.
    """

    def __init__(self, site):
        super(ImageSizerPlugin, self).__init__(site)
        self.cache = {}

    def _handle_img(self, resource, src, width, height):
        """Determine what should be added to an img tag"""
        if height is not None and width is not None:
            return ""           # Nothing
        if src is None:
            self.logger.warn("[%s] has an img tag without src attribute" % resource)
            return ""           # Nothing
        if src not in self.cache:
            if not re.match(r"(/[^/]|[^/]).*", src):
                # Not a local link
                return ""       # Nothing
            if src.startswith("/"):
                # Absolute resource
                path = src.lstrip("/")
                image = self.site.content.resource_from_relative_deploy_path(path)
            else:
                # Relative resource
                path = resource.node.source_folder.child(src)
                image = self.site.content.resource_from_path(path)
            if image is None:
                self.logger.warn(
                    "[%s] has an unknown image" % resource)
                return ""       # Nothing
            if image.source_file.kind not in ['png', 'jpg', 'jpeg', 'gif']:
                self.logger.warn(
                        "[%s] has an img tag not linking to an image" % resource)
                return ""       # Nothing
            # Now, get the size of the image
            try:
                self.cache[src] = Image.open(image.path).size
            except IOError:
                self.logger.warn(
                    "Unable to process image [%s]" % image)
                self.cache[src] = (None, None)
                return ""       # Nothing
            self.logger.debug("Image [%s] is %s" % (src,
                                                    self.cache[src]))
        new_width, new_height = self.cache[src]
        if new_width is None or new_height is None:
            return ""           # Nothing
        if width is not None:
            return 'height="%d" ' % (int(width)*new_height/new_width)
        elif height is not None:
            return 'width="%d" ' % (int(height)*new_width/new_height)
        return 'height="%d" width="%d" ' % (new_height, new_width)

    def text_resource_complete(self, resource, text):
        """
        When the resource is generated, search for img tag and specify
        their sizes.

        Some img tags may be missed, this is not a perfect parser.
        """
        try:
            mode = self.site.config.mode
        except AttributeError:
            mode = "production"

        if not resource.source_file.kind == 'html':
            return

        if mode.startswith('dev'):
            self.logger.debug("Skipping sizer in development mode.")
            return

        pos = 0                 # Position in text
        img = None              # Position of current img tag
        state = "find-img"
        while pos < len(text):
            if state == "find-img":
                img = text.find("<img", pos)
                if img == -1:
                    break           # No more img tag
                pos = img + len("<img")
                if not text[pos].isspace():
                    continue        # Not an img tag
                pos = pos + 1
                tags = {"src": "",
                        "width": "",
                        "height": ""}
                state = "find-attr"
                continue
            if state == "find-attr":
                if text[pos] == ">":
                    # We get our img tag
                    insert = self._handle_img(resource,
                                              tags["src"] or None,
                                              tags["width"] or None,
                                              tags["height"] or None)
                    img = img + len("<img ")
                    text = "".join([text[:img], insert, text[img:]])
                    state = "find-img"
                    pos = pos + 1
                    continue
                attr = None
                for tag in tags:
                    if text[pos:(pos+len(tag)+1)] == ("%s=" % tag):
                        attr = tag
                        pos = pos + len(tag) + 1
                        break
                if not attr:
                    pos = pos + 1
                    continue
                if text[pos] in ["'", '"']:
                    pos = pos + 1
                state = "get-value"
                continue
            if state == "get-value":
                if text[pos] == ">":
                    state = "find-attr"
                    continue
                if text[pos] in ["'", '"'] or text[pos].isspace():
                    # We got our value
                    pos = pos + 1
                    state = "find-attr"
                    continue
                tags[attr] = tags[attr] + text[pos]
                pos = pos + 1
                continue

        return text

class Thumb(object):
    def __init__(self, path, **kwargs):
        self.path = path
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])
    def __str__(self):
        return self.path       

def thumb(self, defaults={}, width=None, height=None):
    """
    Generate a thumbnail for the given image
    """
    if width is None and height is None:
        width, height = defaults['width'], defaults['height']
    im = Image.open(self.path)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # Convert to a thumbnail
    if width is None:
        # height is not None
        width = im.size[0]*height/im.size[1] + 1
    elif height is None:
        # width is not None
        height = im.size[1]*width/im.size[0] + 1
    im.thumbnail((width, height), Image.ANTIALIAS)
    # Prepare path
    path = os.path.join(os.path.dirname(self.get_relative_deploy_path()),
                        "%s%s" % (defaults['prefix'],
                                  self.name))
    target = File(Folder(self.site.config.deploy_root_path).child(path))
    target.parent.make()
    if self.name.endswith(".jpg"):
        im.save(target.path, "JPEG", optimize=True, quality=75)
    else:
        im.save(target.path, "PNG", optimize=True)
    return Thumb(path, width=im.size[0], height=im.size[1])

class ImageThumbnailsPlugin(Plugin):
    """
    Provide a function to get thumbnail for any image resource.

    Each image resource will get a `thumb()` function. This function
    can take the following keywords:
      - width (int)
      - height (int)
      - prefix (string): prefix to use for thumbnails

    This plugin can be configured with the exact same keywords to set
    site defaults. The `thumb()` function will return a path to the
    thumbnail. This path will have `width` and `height` as an
    attribute.

    Thumbnails are created in the same directory of their image.

    Currently, only supports PNG and JPG.
    """

    def __init__(self, site):
        super(ImageThumbnailsPlugin, self).__init__(site)

    def begin_site(self):
        """
        Find any image resource to add them the thumb() function.
        """
        # Grab default values from config
        config = self.site.config
        defaults = { "width": None,
                     "height": 40,
                     "prefix": 'thumb_',
                     }
        if hasattr(config, 'thumbnails'):
            defaults.update(config.thumbnails)
        # Make the thumbnailing function
        thumbfn = partial(thumb, defaults=defaults)
        thumbfn.__doc__ = "Create a thumbnail for this image"

        # Add it to any image resource
        for node in self.site.content.walk():
            for resource in node.resources:
                if resource.source_file.kind not in ["jpg", "png"]:
                    continue
                self.logger.debug("Adding thumbnail function to [%s]" % resource)
                resource.thumb = new.instancemethod(thumbfn, resource, resource.__class__)
