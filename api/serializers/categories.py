from django.db.models import Q
from rest_framework import serializers

from api.models import Categories, Profile


class CategoriesSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    im_follow = serializers.SerializerMethodField()
    class Meta:
        model = Categories
        fields = ('id', 'global_id', 'name', 'is_active', 'subcategories', 'order', 'code', 'im_follow')

    def get_subcategories(self, obj):
        queryset = obj.subcategories.filter(is_active=True, is_optional=True, parent__isnull=False).order_by('order')
        return self.__class__(queryset, many=True).data

    def get_im_follow(self, obj):
        profile = self.context.get('profile')
        if not profile:
            return False
        return profile.categories_subscription.filter(id=obj.id).exists()


class FavouriteCategoriesSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Categories
        fields = ('id', 'global_id', 'name', 'logo_url', 'is_active', 'subcategories', 'order')

    IMAGE_URLS = {
        "NBA": "https://vylo-img.s3.us-east-1.amazonaws.com/leagues/nba.svg",
        "MLB": "https://vylo-img.s3.us-east-1.amazonaws.com/leagues/mlb.svg",
        "NFL": "https://vylo-img.s3.us-east-1.amazonaws.com/leagues/nfl.svg",
        "NHL": "https://vylo-img.s3.us-east-1.amazonaws.com/leagues/nhl.svg",
        "Soccer": "https://vylo-img.s3.us-east-1.amazonaws.com/leagues/premier-league.svg",
        "UFC": "https://vylo-img.s3.us-east-1.amazonaws.com/leagues/ufc.svg"
    }
    LEAGUE_NAMES = ["NBA", "MLB", "NFL", "NHL", "Soccer", "UFC"]

    def get_subcategories(self, obj):
        queryset = obj.subcategories.filter(
            is_active=True, parent__isnull=False, name__in=self.LEAGUE_NAMES).order_by('filter_order')
        return self.__class__(queryset, many=True).data

    def get_logo_url(self, obj):
        return self.IMAGE_URLS.get(obj.name)


class CategoriesAbstractNavigation(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ('id', 'global_id', 'name', 'order')


class ParentCategoriesNavigation(CategoriesAbstractNavigation):
    pass


class ChildCategoriesNavigation(CategoriesAbstractNavigation):
    subcategories = serializers.SerializerMethodField()
    im_follow = serializers.SerializerMethodField()

    class Meta(CategoriesAbstractNavigation.Meta):
        fields = ('id', 'global_id', 'im_follow', 'name', 'odds_type', 'subcategories', 'order')

    def get_subcategories(self, obj):
        queryset = obj.subcategories.filter(is_active=True, is_optional=True, parent__isnull=False).order_by('filter_order')
        if len(queryset) > 0:
            return self.__class__(queryset, many=True, context=self.context).data

    def get_im_follow(self, obj):
        profile = self.context.get('profile')
        if profile:
            if obj.parent.name == "Sports":
                return profile.categories_subscription.filter(id=obj.id).exists()
            else:
                return profile.categories_subscription.filter(Q(id=obj.id) | Q(id=obj.parent_id)).exists()
        return False
