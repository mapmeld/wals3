from zope.interface import implementer

from clld.interfaces import IBlog
from clld.lib import wordpress
from clld.web.util.helpers import link


@implementer(IBlog)
class Blog(object):
    def __init__(self, settings, prefix='blog.'):
        self.host = settings[prefix + 'host']
        self.wp = wordpress.Client(
            self.host, settings[prefix + 'user'], settings[prefix + 'password'])

    def url(self, path=None):
        path = path or '/'
        if not path.startswith('/'):
            path = '/' + path
        return 'http://%s%s' % (self.host, path)

    def _set_category(self, **cat):
        return self.wp.set_categories([cat]).values()[0]

    #
    # TODO: the whole blog implementation is wals specific and should be moved there!
    #
    def post_url(self, obj, req, create=False):
        res = self.url('%s/' % obj.wp_slug)
        if create and not self.wp.get_post_id_from_path(res):
            # create categories if missing:
            languageCat, chapterCat, areaCat = None, None, None

            for cat in self.wp.get_categories():
                if cat['name'] == 'Languages':
                    languageCat = cat['id']
                if cat['name'] == 'Chapters':
                    chapterCat = cat['id']
                if cat['name'] == obj.parameter.chapter.area.name:
                    areaCat = cat['id']

            if languageCat is None:
                languageCat = self._set_category(name='Languages', slug='languages')
            if chapterCat is None:
                chapterCat = self._set_category(name='Chapters', slug='chapters')
            if areaCat is None:
                areaCat = self._set_category(
                    name=obj.parameter.chapter.area.name,
                    parent_id=chapterCat)

            # now create the post:
            categories = [
                dict(name=obj.parameter.name, parent_id=areaCat),
                dict(name=obj.language.name, parent_id=languageCat)]
            self.wp.create_post(
                'Datapoint %s' % obj.name,
                'Discuss WALS Datapoint <a href="http://%s%s">%s</a>.' % (
                    req.dataset.domain, req.resource_path(obj), obj.name),
                categories=categories,
                published=True,
                wp_slug=obj.wp_slug)
        return res

    def feed_url(self, obj, req):
        return self.url('%s/feed' % (obj if isinstance(obj, basestring) else obj.wp_slug,))
