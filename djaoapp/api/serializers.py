# Copyright (c) 2018 DjaoDjin inc.
# see LICENSE

#pylint: disable=old-style-class,no-init

from django.contrib.auth import get_user_model
from django.utils import six
from rest_framework import serializers
from saas.api.serializers import OrganizationWithEndsAtByPlanSerializer
from saas.models import get_broker, Role, ChargeItem


class SessionSerializer(serializers.ModelSerializer):

    last_visited = serializers.DateTimeField(required=False)
    username = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    site = serializers.SerializerMethodField()
    invoice_keys = serializers.SerializerMethodField()
    session_key = serializers.SerializerMethodField()
    access_key = serializers.SerializerMethodField()
    secret_key = serializers.SerializerMethodField()
    security_token = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ('username', 'roles', 'site', 'last_visited', 'invoice_keys',
            'session_key', 'access_key', 'secret_key', 'security_token')
        read_only_fields = ('username', 'roles', 'site', 'last_visited',
            'invoice_keys',
            'session_key', 'access_key', 'secret_key', 'security_token')

    @staticmethod
    def get_username(request):
        return request.user.username

    @staticmethod
    def get_roles(request):
        results = {}
        for role, organizations in six.iteritems(Role.objects.accessbile_by(
                user=request.user)):
            serializer = OrganizationWithEndsAtByPlanSerializer(many=True)
            results[role.slug] = serializer.to_representation(organizations)
        return results

    @staticmethod
    def get_site(obj): #pylint:disable=unused-argument
        broker = get_broker()
        return {'printable_name': broker.printable_name, 'email': broker.email}

    def get_invoice_keys(self, request):
        rule = self.context.get('rule', None)
        if rule and rule.rule_op >= 1: # XXX Authenticated
            return [result['invoice_key']
                for result in ChargeItem.objects.to_sync(request.user).values(
                    'invoice_key').distinct()]
        return []

    @staticmethod
    def get_session_key(request):
        return request.session.session_key

    @staticmethod
    def get_access_key(request):
        return request.session.get('access_key', None)

    @staticmethod
    def get_secret_key(request):
        return request.session.get('secret_key', None)

    @staticmethod
    def get_security_token(request):
        return request.session.get('security_token', None)
