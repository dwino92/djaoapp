# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE

from django.conf.urls import url

from signup import settings
from djaoapp.forms.custom_signup import FrictionlessSignupForm, SignupForm
from djaoapp.views.custom_signup import (ActivationView, PasswordResetView,
    PasswordResetConfirmView, SigninView, SignoutView, SignupView,
    RegistrationPasswordConfirmView)

urlpatterns = [
    url(r'^register/frictionless/',
        SignupView.as_view(form_class=FrictionlessSignupForm),
        name='registration_frictionless'),
    # Normal sign up of a user
    url(r'^register/',
        SignupView.as_view(form_class=SignupForm),
        name='registration_register'),
    # When the key and/or token are wrong we don't want to give any clue
    # as to why that is so. Less information communicated to an attacker,
    # the better.
    url(r'^activate/(?P<verification_key>%s)/password/(?P<token>.+)/'
        % settings.EMAIL_VERIFICATION_PAT,
        RegistrationPasswordConfirmView.as_view(),
        name='registration_password_confirm'),
    url(r'^activate/(?P<verification_key>%s)/'
        % settings.EMAIL_VERIFICATION_PAT,
        ActivationView.as_view(), name='registration_activate'),
    url(r'^recover/',
        PasswordResetView.as_view(), name='password_reset'),
    url(r'^login/', SigninView.as_view(), name='login'),
    url(r'^logout/', SignoutView.as_view(), name='logout'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', #pylint: disable=line-too-long
        PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
